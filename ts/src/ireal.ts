/**
 * iReal Pro URL parsing: the twin of `accompy.util.parse_ireal_url`, and of the parts of
 * pyRealParser (MIT, by its authors) that it reaches (`Tune.parse_ireal_url`, the
 * "1r34LbKcu7" unscrambling and the chord-string flattening behind
 * `Tune.measures_as_strings`).
 *
 * Three tiers, each falling through to the next on any error, exactly as in Python:
 * 1. pyRealParser's playlist parser (first tune that parses), measures not normalized;
 * 2. a `Tune` rebuilt from single-`=` fields (URLs whose empty fields make `===`);
 * 3. a dependency-free best-effort parser, which goes through `ensureScore` (normalized)
 *    and throws `ValueError` (a RangeError) when the URL has fewer than 6 fields.
 *
 * Python semantics are kept where JS differs: `\s`, `\d`, `\w` and `str.strip` are
 * Unicode-aware as in `re`, `.` excludes only `\n`, string indices count code points,
 * `urllib.parse.unquote` is lenient (bad escapes stay literal, bad UTF-8 becomes U+FFFD),
 * and `re.sub` replacement strings are expanded as Python templates (`\1`, `\n`, ...).
 */
import { ensureScore, type Score } from "./chart.js";
import { PY_WHITESPACE } from "./data.generated.js";
import { digitValue, isPySpace, pyStrip, ValueError } from "./py.js";

const PREFIX = "1r34LbKcu7";
/** Python's `re` `\s` (= `str.isspace`) as the body of a `u`-flag character class. */
const WS = PY_WHITESPACE.map((cp) => `\\u{${cp.toString(16)}}`).join("");

/** Compile a Python-`re` source: `\s`, `\d`, `\w` get Python's Unicode meaning (outside classes). */
const py = (src: string, flags = ""): RegExp =>
  new RegExp(
    src.replace(/\\([sdw])/g, (_, c: string) => ({ s: `[${WS}]`, d: "\\p{Nd}", w: "[\\p{L}\\p{N}_]" })[c]!),
    "u" + flags,
  );
const sub = (s: string, src: string, rep: string): string => s.replace(py(src, "g"), () => rep);

// --------------------------------------------------------------------------------------
// urllib.parse.unquote (UTF-8, errors="replace")

function utf8Decode(b: number[]): string {
  let out = "";
  for (let i = 0; i < b.length; ) {
    const c = b[i]!;
    if (c < 0x80) {
      out += String.fromCharCode(c);
      i++;
      continue;
    }
    let need = 0, lo = 0x80, hi = 0xbf, cp = 0;
    if (c >= 0xc2 && c <= 0xdf) [need, cp] = [1, c & 0x1f];
    else if (c >= 0xe0 && c <= 0xef) {
      [need, cp] = [2, c & 0x0f];
      if (c === 0xe0) lo = 0xa0;
      if (c === 0xed) hi = 0x9f;
    } else if (c >= 0xf0 && c <= 0xf4) {
      [need, cp] = [3, c & 0x07];
      if (c === 0xf0) lo = 0x90;
      if (c === 0xf4) hi = 0x8f;
    }
    let j = i + 1;
    for (; need && j <= i + need; j++) {
      const d = b[j];
      if (d === undefined || d < lo || d > hi) break;
      cp = (cp << 6) | (d & 0x3f);
      [lo, hi] = [0x80, 0xbf];
    }
    // A complete sequence decodes; otherwise its maximal valid prefix becomes one U+FFFD.
    out += need && j === i + need + 1 ? String.fromCodePoint(cp) : "�";
    i = j;
  }
  return out;
}

function unquote(s: string): string {
  if (!s.includes("%")) return s;
  // Python decodes each ASCII run on its own; non-ASCII text passes through untouched.
  return s.replace(/[\x00-\x7f]+/g, (run) => {
    const [head, ...bits] = run.split("%");
    const bytes = [...head!].map((ch) => ch.charCodeAt(0));
    for (const item of bits) {
      const ok = /^[0-9A-Fa-f]{2}/.test(item);
      if (ok) bytes.push(parseInt(item.slice(0, 2), 16));
      else bytes.push(0x25);
      for (const ch of ok ? item.slice(2) : item) bytes.push(ch.charCodeAt(0));
    }
    return utf8Decode(bytes);
  });
}

// --------------------------------------------------------------------------------------
// re.sub replacement templates (patterns here have exactly one group)

const TEMPLATE_ESCAPES: Record<string, string> = {
  a: "\x07", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t", v: "\v", "\\": "\\",
};

function pyTemplate(tpl: string, groups: [string, string]): string {
  const ch = Array.from(tpl);
  const bad = (): never => {
    throw new Error(`bad replacement template ${JSON.stringify(tpl)}`);
  };
  const group = (n: string): string => (Number(n) <= 1 ? groups[Number(n) as 0 | 1] : bad());
  const isIn = (set: string, c: string | undefined) => c !== undefined && set.includes(c);
  let out = "";
  for (let i = 0; i < ch.length; i++) {
    if (ch[i] !== "\\") {
      out += ch[i];
      continue;
    }
    const c = ch[++i] ?? bad();
    if (c === "g") {
      const end = ch[i + 1] === "<" ? ch.indexOf(">", i + 2) : -1;
      const name = end < 0 ? bad() : ch.slice(i + 2, end).join("");
      out += /^[0-9]+$/.test(name) ? group(name) : bad();
      i = end;
    } else if (c === "0") {
      let oct = c;
      while (oct.length < 3 && isIn("01234567", ch[i + 1])) oct += ch[++i];
      out += String.fromCharCode(parseInt(oct, 8));
    } else if (isIn("0123456789", c)) {
      let num = c;
      if (isIn("0123456789", ch[i + 1])) {
        num += ch[++i];
        if (isIn("01234567", c) && isIn("01234567", num[1]) && isIn("01234567", ch[i + 1])) {
          const v = parseInt(num + ch[++i], 8);
          out += v > 0o377 ? bad() : String.fromCharCode(v);
          continue;
        }
      }
      out += group(num);
    } else if (c in TEMPLATE_ESCAPES) out += TEMPLATE_ESCAPES[c];
    else out += /[A-Za-z]/.test(c) ? bad() : "\\" + c;
  }
  return out;
}

// --------------------------------------------------------------------------------------
// pyRealParser.Tune

interface Tune {
  title: string;
  composer: string;
  key: string;
  timeSignature: [number, number];
  measures: string[];
}

function unscramble(scrambled: string): string {
  const swaps = [0, 1, 2, 3, 4, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23];
  let rest = Array.from(scrambled), out = "";
  while (rest.length > 50) {
    const block = rest.slice(0, 50);
    rest = rest.slice(50);
    if (rest.length >= 2) {
      const r = [...block];
      for (const i of swaps) [r[i], r[49 - i]] = [block[49 - i]!, block[i]!];
      out += r.join("");
    } else out += block.join("");
  }
  return out + rest.join("");
}

function cleanup(s: string): string {
  s = sub(s, "LZ|K", "|");
  s = sub(s, "cl", "x");
  s = sub(s, "\\*\\s*\\*", "");
  s = sub(s, "Y+", "");
  s = sub(s, "XyQ|,", " ");
  s = sub(s, "\\|\\s*\\|", "|");
  s = sub(s, "Z", "");
  s = sub(s, "\\|\\s+", "|");
  s = sub(s, "\\s+", " ");
  let end = s.length;
  while (end && isPySpace(s[end - 1]!)) end--;
  return s.slice(0, end);
}

function removeAnnotations(s: string): string {
  s = sub(s, "[\\[\\]]", "|");
  s = sub(s, "\\|\\s*\\|", "|");
  s = sub(s, "<[^\\n]*?>", "");
  s = sub(s, "\\([^)]*\\)", "");
  s = sub(s, "[lf]", "");
  s = sub(s, "(?<!su)s(?!us)", "");
  s = sub(s, "\\*\\w", "");
  return sub(s, "T\\d+", "");
}

const removeMarkers = (s: string): string => sub(s, "U|S|Q|N\\d", "");

function fillLongRepeats(s: string): string {
  // pyRealParser recurses on simple repeats and returns after the first one with endings.
  for (;;) {
    const m = py("\\{([^\\n]+?)\\}").exec(s);
    if (!m) return s;
    const body = m[1]!, before = s.slice(0, m.index), after = s.slice(m.index + m[0].length);
    if (!py("N(\\d)").test(body)) {
      s = before + "|" + body + " |" + removeMarkers(body) + after + "|";
      continue;
    }
    let out = before + "|" + sub(body, "N\\d", "") + after;
    const head = py("([^N]+)N\\d").exec(body);
    if (!head) throw new Error("repeat ending without a body");
    const tpl = "|" + removeMarkers(head[1]!);
    const ending = py("\\|\\s*N(\\d)", "g");
    while (py("\\|\\s*N(\\d)").test(out))
      out = out.replace(ending, (m0: string, g1: string) => pyTemplate(tpl, [m0, g1]));
    return out;
  }
}

function fillCodas(s: string): string {
  const qs = [...s].filter((c) => c === "Q").length;
  if (qs > 2) throw new Error(`Could not parse codas: ${qs} Qs`);
  if (qs === 1) return s.replaceAll("Q", "");
  if (qs === 2) {
    const q1 = s.indexOf("Q"), q2 = s.indexOf("Q", q1 + 1);
    const segno = Math.max(s.indexOf("S"), 0);
    const out = s.slice(0, q2) + s.slice(segno + 1, q1) + " |" + s.slice(q2 + 1);
    return out.replace(/[QS]/g, "");
  }
  return s;
}

function lastChord(s: string): string {
  const all = [...s.matchAll(/(?<!\/)([A-Gn][^A-G/]*(?:\/[A-G][#b]?)?)/gu)];
  if (!all.length) throw new Error("no chord before slash");
  return all[all.length - 1]![1]!;
}

function getMeasures(s: string): string[] {
  s = fillCodas(fillLongRepeats(removeAnnotations(cleanup(s))));
  const ms = s
    .split(/\||LZ|K|Z|\{|\}|\[|\]/u)
    .filter((m) => pyStrip(m) !== "")
    .map((m) => m.replaceAll(" ", ""));
  const n = ms.length;
  for (let i = 1; i < n; i++) if (ms[i] === "x") ms[i] = removeMarkers(ms[i - 1]!);
  for (let i = 2; i < n - 1; i++)
    if (ms[i] === "r") {
      ms[i] = removeMarkers(ms[i - 2]!);
      ms[i + 1] = removeMarkers(ms[i - 1]!);
    }
  for (let i = 1; i < n; i++) {
    for (let slash = ms[i]!.indexOf("p"); slash !== -1; slash = ms[i]!.indexOf("p")) {
      const m = ms[i]!;
      if (slash === 0) {
        const prev = lastChord(ms[i - 1]!);
        // Python then runs re.sub(r'^(p+)', prev, ...): a no-op (the measure now starts with
        // prev, a chord), except that compiling `prev` as a template can raise.
        pyTemplate(prev, ["", ""]);
        ms[i] = prev + m.slice(1);
      } else ms[i] = m.slice(0, slash) + lastChord(m.slice(0, slash)) + m.slice(slash + 1);
    }
  }
  return ms;
}

function parseTune(tuneString: string): Tune {
  const parts = tuneString.split(/=+/);
  // Python raises unless parts[4] starts with the prefix (the transpose branch's int() of a
  // string containing the prefix always fails).
  if (parts.length < 5 || !parts[4]!.startsWith(PREFIX)) throw new Error("not a tune");
  const chords = cleanup(unscramble(parts[4]!.split(PREFIX)[1]!));
  const ts = py("T(\\d)(\\d)").exec(chords);
  return {
    title: parts[0]!,
    composer: parts[1]!,
    key: parts[3]!,
    timeSignature: ts ? [digitValue(ts[1]!), digitValue(ts[2]!)] : [4, 4],
    measures: getMeasures(chords),
  };
}

// --------------------------------------------------------------------------------------
// accompy.util

/** Score from a parsed tune, or null when it has no measures (Python falls through). */
function scoreFromTune(t: Tune): Score | null {
  const measures = t.measures.filter((c) => c).map((c) => [c]);
  if (!measures.length) return null;
  return {
    measures,
    title: t.title || "Untitled",
    composer: t.composer || "",
    key: t.key || "C",
    timeSignature: t.timeSignature,
  };
}

function stripScheme(url: string): string {
  return url.startsWith("irealbook://") || url.startsWith("irealb://")
    ? url.slice(url.indexOf("://") + 3)
    : url;
}

/** pyRealParser's `Tune.parse_ireal_url(url)[0]`. */
function firstTune(url: string): Tune {
  const m = /^irealb:\/\/([^"]+)/u.exec(unquote(url));
  if (!m) throw new Error("Provided string is not a valid iReal url!");
  for (const song of m[1]!.split("==="))
    if (song !== "")
      try {
        return parseTune(song);
      } catch {
        /* pyRealParser skips songs it cannot import */
      }
  throw new Error("no tunes");
}

/** accompy.util._tune_from_ireal_url */
function tuneFromFields(url: string): Tune {
  const parts = unquote(stripScheme(url)).split("=");
  const ci = parts.findIndex((p) => p.includes(PREFIX));
  if (ci < 0) throw new Error("Could not locate chord data in iReal URL");
  const at = (i: number) => parts[i] ?? "";
  const key = ci >= 2 && Array.from(at(ci - 2)).length <= 2 ? at(ci - 2) : "C";
  const style = ci >= 3 ? at(ci - 3) : "";
  const fields = [at(0) || "Untitled", parts.length > 1 ? at(1) : "", style, key];
  return parseTune([...fields, at(ci), at(ci + 1), at(ci + 2), at(ci + 3)].join("="));
}

/** accompy.util.parse_ireal_url_fallback */
function parseIrealUrlFallback(url: string): Score {
  const parts = unquote(stripScheme(url)).split("=");
  const title = parts[0] || "Untitled";
  const composer = parts.length > 1 ? parts[1]! : "";
  const key = parts[3] || "C";
  if (parts.length < 6) throw new ValueError("Invalid iReal Pro URL format");
  let data = parts[5]!;
  for (const marker of ["{", "}", "[", "]", "Z", "*", "Y", "Q", "S", "T"])
    data = data.replaceAll(marker, " ");
  data = sub(sub(sub(data, "\\*[A-Za-z]", " "), "N\\d", " "), "<[^>]*>", " ");
  const chords: Array<[string, number]> = [];
  for (let token of data.split(new RegExp(`[|${WS}]+`, "u"))) {
    token = pyStrip(token);
    if (!token || ["n", "x", "r", "%", "p", "s", "l"].includes(token)) continue;
    const m = /^([A-G][#b]?)([^\n]*)/u.exec(token);
    if (!m) continue;
    let suffix = m[2]!;
    for (const [a, b] of [["^", "maj"], ["-", "m"], ["h", "m7b5"], ["o", "dim"], ["+", "aug"]])
      suffix = suffix.replaceAll(a!, b!);
    suffix = suffix.split("/")[0]!.split(",")[0]!;
    chords.push([m[1]! + suffix, 4]);
  }
  return { ...ensureScore(chords, { title, key }), composer };
}

/**
 * Parse an iReal Pro URL (`irealb://` or `irealbook://`) into a Score, as
 * `accompy.util.parse_ireal_url` does. Throws `ValueError` (a RangeError) where Python raises it.
 */
export function parseIrealUrl(url: string): Score {
  for (const tier of [firstTune, tuneFromFields]) {
    try {
      const score = scoreFromTune(tier(url));
      if (score) return score;
    } catch {
      /* fall through to the next tier, as Python does */
    }
  }
  return parseIrealUrlFallback(url);
}
