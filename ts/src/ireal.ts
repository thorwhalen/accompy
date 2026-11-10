/**
 * iReal Pro URL decoding: the twin of `accompy.ireal` (and of `accompy.util.parse_ireal_url`
 * on top of it). Its unscrambling and bar flattening started from pyRealParser (MIT, by its
 * authors), with the fixes listed in `accompy/ireal.py`'s docstring.
 *
 * Python semantics are kept where JS differs: `\s`, `\d`, `\w` and `str.strip` are
 * Unicode-aware as in `re`, `.` excludes only `\n`, string indices count code points, and
 * `urllib.parse.unquote` is lenient (bad escapes stay literal, bad UTF-8 becomes U+FFFD).
 */
import type { Score } from "./chart.js";
import { PY_WHITESPACE } from "./data.generated.js";
import { digitValue, isPySpace, pySplit, ValueError } from "./py.js";

/** The start of a scrambled (`irealb://`) music field. */
const SCRAMBLE_PREFIX = "1r34LbKcu7";
/** Time-signature codes that are not `T<numerator><denominator>` (Python's TIME_SIGNATURE_EXCEPTIONS). */
const TIME_SIGNATURE_EXCEPTIONS: Record<string, [number, number]> = { "1,2": [12, 8] };
/** Fields of an `irealbook://` song, and the index of its music. */
const [PLAIN_SONG_FIELDS, PLAIN_MUSIC_INDEX] = [6, 5];
/** Offset from a scrambled song's music field to its key; the fields before its music. */
const [KEY, FIELDS_BEFORE_MUSIC] = [-2, 6];

/** Python's `re` `\s` (= `str.isspace`) as the body of a `u`-flag character class. */
const WS = PY_WHITESPACE.map((cp) => `\\u{${cp.toString(16)}}`).join("");

/** Compile a Python-`re` source: `\s`, `\d`, `\w` get Python's Unicode meaning (outside classes). */
const py = (src: string, flags = ""): RegExp =>
  new RegExp(
    src.replace(/\\([sdw])/g, (_, c: string) => ({ s: `[${WS}]`, d: "\\p{Nd}", w: "[\\p{L}\\p{N}_]" })[c]!),
    "u" + flags,
  );
const sub = (s: string, src: string, rep: string): string => s.replace(py(src, "g"), () => rep);
/** First characters of a chord (`n` is no chord, N.C.), which a `p` or `W` can repeat. */
const ROOTS = "ABCDEFGn";
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
// accompy.ireal

/** One song of an iReal URL (Python's `IrealTune`; the fields the twin needs). */
interface IrealTune {
  title: string;
  composer: string;
  key: string;
  timeSignature: [number, number];
  measures: string[][];
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

function cleanupChordString(s: string): string {
  const steps: Array<[string, string]> = [
    ["LZ|K", "|"], ["cl", "x"], ["\\*\\s*\\*", ""], ["Y+", ""], ["XyQ|,", " "],
    ["\\|\\s*\\|", "|"], ["Z", ""], ["\\|\\s+", "|"], ["\\s+", " "],
  ];
  for (const [src, rep] of steps) s = sub(s, src, rep);
  let end = s.length;
  while (end && isPySpace(s[end - 1]!)) end--;
  return s.slice(0, end);
}

function removeAnnotations(s: string): string {
  const steps: Array<[string, string]> = [
    ["[\\[\\]]", "|"], ["\\|\\s*\\|", "|"], ["<[^\\n]*?>", ""], ["\\([^)]*\\)", ""],
    ["(?<!a)l(?!t)|f", ""], ["(?<!su)s(?!us)", ""], ["\\*\\w", ""], ["T\\d+", ""],
  ];
  for (const [src, rep] of steps) s = sub(s, src, rep);
  return s;
}

const removeMarkers = (s: string): string => sub(s, "U|S|Q|N\\d", "");

function fillLongRepeats(s: string): string {
  for (let m; (m = py("\\{([^{\\n]+?)\\}").exec(s)); ) {
    const body = m[1]!, before = s.slice(0, m.index), after = s.slice(m.index + m[0].length);
    if (!py("N(\\d)").test(body)) {
      s = before + "|" + body + " |" + removeMarkers(body) + after + "|";
      continue;
    }
    let out = before + "|" + sub(body, "N\\d", "") + after;
    const head = py("([^N]+)N\\d").exec(body);
    if (!head) throw new ValueError(`Repeat with an ending but no body: ${body}`);
    const replay = "|" + removeMarkers(head[1]!);
    while (py("\\|\\s*N(\\d)").test(out)) out = sub(out, "\\|\\s*N(\\d)", replay);
    return out;
  }
  return s;
}

function fillCodas(s: string): string {
  const qs = [...s].filter((c) => c === "Q").length;
  if (qs > 2) throw new ValueError(`Could not parse codas: expected 0, 1 or 2 Qs, not ${qs}`);
  if (qs === 1) return s.replaceAll("Q", "");
  if (qs === 2) {
    const q1 = s.indexOf("Q"), q2 = s.indexOf("Q", q1 + 1);
    // From after the segno, else after the first character (a code point, as in Python).
    const segno = s.indexOf("S");
    const from = segno >= 0 ? segno + 1 : [...s][0]!.length;
    return (s.slice(0, q2) + s.slice(from, q1) + " |" + s.slice(q2 + 1)).replace(/[QS]/g, "");
  }
  return s;
}

function fillRepeatSigns(bars: string[][]): string[][] {
  const out: string[][] = [];
  for (const bar of bars) {
    const sign = bar.length === 1 ? bar[0] : undefined;
    if (sign === "x") out.push(...out.slice(-1));
    else if (sign === "r") out.push(...(out.length >= 2 ? out.slice(-2) : []));
    else out.push(bar);
  }
  return out;
}

/** A bar's chords and signs: split at the source's separators, then before each root (`A`-`G`, or `W`, not after a `/`) and around each `p`. */
const barTokens = (bar: string): string[] =>
  pySplit(bar).flatMap((token) => token.split(/(?<!\/)(?=[A-GW])|(?=p)|(?<=p)/u).filter((piece) => piece));

/** Write out `p` (the previous chord again) and `W` (an invisible root); drop them with no previous chord. */
function fillSlashes(bars: string[][]): string[][] {
  let last = "";
  return bars.map((bar) => {
    const chords: string[] = [];
    for (let token of bar) {
      if (token === "p") token = last;
      else if (token.startsWith("W")) token = last ? (token.length > 1 ? last.split("/")[0]! + token.slice(1) : last) : "";
      if (token && ROOTS.includes(token[0]!)) last = token;
      if (token) chords.push(token);
    }
    return chords;
  });
}

function flattenMeasures(chordString: string): string[][] {
  const s = removeMarkers(fillCodas(fillLongRepeats(removeAnnotations(cleanupChordString(chordString)))));
  const bars = s.split(/\||LZ|K|Z|\{|\}|\[|\]/u).map(barTokens);
  return fillSlashes(fillRepeatSigns(bars.filter((bar) => bar.length)));
}

function timeSignature(chordString: string): [number, number] {
  const m = py("T(\\d)(\\d)").exec(chordString);
  if (!m) return [4, 4];
  const ts: [number, number] = [digitValue(m[1]!), digitValue(m[2]!)];
  return TIME_SIGNATURE_EXCEPTIONS[ts.join(",")] ?? ts;
}

type Meta = { title: string; composer: string; key: string };

function* scrambledSongs(fields: string[]): Generator<[string, Meta]> {
  const at = (i: number) => (i >= 0 && i < fields.length ? fields[i]! : "");
  let previous = -1;
  for (const [m, music] of fields.entries()) {
    if (!music.startsWith(SCRAMBLE_PREFIX)) continue;
    // A song starts right after the previous one, or at the standard offset when a `===`
    // separator (two empty fields) comes just before that offset.
    const standard = m - FIELDS_BEFORE_MUSIC;
    const start = standard > previous + 1 && at(standard - 1) === "" && at(standard - 2) === "" ? standard : previous + 1;
    previous = m;
    const before = fields.slice(start, m);
    let meta: Meta;
    if (before.length >= FIELDS_BEFORE_MUSIC) meta = { title: at(start), composer: at(start + 1), key: at(m + KEY) };
    else {
      const [title = "", composer = "", , key = ""] = before.filter((f) => f);
      meta = { title, composer, key };
    }
    yield [unscramble(music.slice(SCRAMBLE_PREFIX.length)), meta];
  }
}

function* plainSongs(fields: string[]): Generator<[string, Meta]> {
  for (let s = 0; s + PLAIN_SONG_FIELDS <= fields.length; s += PLAIN_SONG_FIELDS)
    yield [fields[s + PLAIN_MUSIC_INDEX]!, { title: fields[s]!, composer: fields[s + 1]!, key: fields[s + 3]! }];
}

/** Python `accompy.ireal.decode_ireal_url`: the tunes that decode, in order. */
function decodeIrealUrl(url: string): IrealTune[] {
  let body = unquote(url).split('"', 1)[0]!;
  for (const scheme of ["irealbook://", "irealb://"])
    if (body.startsWith(scheme)) {
      body = body.slice(scheme.length);
      break;
    }
  const fields = body.split("=");
  const songs = fields.some((f) => f.startsWith(SCRAMBLE_PREFIX)) ? scrambledSongs(fields) : plainSongs(fields);
  const tunes: IrealTune[] = [];
  for (const [music, meta] of songs) {
    const chordString = cleanupChordString(music);
    try {
      tunes.push({ ...meta, timeSignature: timeSignature(chordString), measures: flattenMeasures(chordString) });
    } catch (error) {
      if (!(error instanceof ValueError)) throw error;
    }
  }
  return tunes;
}

// --------------------------------------------------------------------------------------
// accompy.util

/**
 * Parse an iReal Pro URL (`irealb://` or `irealbook://`) into a Score, as
 * `accompy.util.parse_ireal_url` does: the first tune with chords, each bar the list of
 * its chords as written.
 * Throws `ValueError` when no tune has chords.
 */
export function parseIrealUrl(url: string): Score {
  for (const tune of decodeIrealUrl(url)) {
    const measures = tune.measures.filter((bar) => bar.length);
    if (measures.length)
      return {
        measures,
        title: tune.title || "Untitled",
        composer: tune.composer,
        key: tune.key || "C",
        timeSignature: tune.timeSignature,
      };
  }
  throw new ValueError("No chords found in iReal Pro URL");
}
