/**
 * iReal Pro URL decoding: the twin of `accompy.ireal` (and of `accompy.util.parse_ireal_url`
 * on top of it). Its unscrambling and chord-string cleanup started from pyRealParser (MIT,
 * notice below), with the changes listed in `accompy/ireal.py`'s docstring.
 *
 * Python semantics are kept where JS differs: `\s`, `\d`, `\w` and `str.strip` are
 * Unicode-aware as in `re`, `.` excludes only `\n`, string indices count code points, and
 * `urllib.parse.unquote` is lenient (bad escapes stay literal, bad UTF-8 becomes U+FFFD).
 */
/*! Parts of accompy's iReal decoding derive from pyRealParser, under this licence:

MIT License

Copyright (c) 2018 Daniel Stephan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/
import type { Score } from "./chart.js";
import { PY_WHITESPACE } from "./data.generated.js";
import { digitValue, isPySpace, pySplit, pyStrip, ValueError } from "./py.js";

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
  const chars = Array.from(scrambled), n = chars.length;
  let out = "", i = 0;
  while (n - i > 50) {
    const block = chars.slice(i, i + 50);
    i += 50;
    if (n - i >= 2) {
      const r = [...block];
      for (const k of swaps) [r[k], r[49 - k]] = [block[49 - k]!, block[k]!];
      out += r.join("");
    } else out += block.join("");
  }
  return out + chars.slice(i).join("");
}

function cleanupChordString(s: string): string {
  const steps: Array<[string, string]> = [
    ["LZ|K|Z", "|"], ["cl", "x"], ["\\*\\s*\\*", ""], ["Y+", ""], ["XyQ|,", " "],
    ["\\|\\s*\\|", "|"], ["\\|\\s+", "|"], ["\\s+", " "],
  ];
  for (const [src, rep] of steps) s = sub(s, src, rep);
  let end = s.length;
  while (end && isPySpace(s[end - 1]!)) end--;
  return s.slice(0, end);
}

/** Remove each `start...end` span (no `stop` inside) in one linear pass (a regex is quadratic on `<<<<...`). */
function dropSpans(text: string, start: string, end: string, stop = ""): string {
  let out = "", i = 0;
  for (let j: number, k: number; (j = text.indexOf(start, i)) >= 0 && (k = text.indexOf(end, j + 1)) >= 0; ) {
    const inside = stop ? text.slice(j + 1, k).indexOf(stop) : -1;
    if (inside >= 0) {
      const cut = j + 1 + inside;
      out += text.slice(i, cut + 1);
      i = cut + 1;
    } else {
      out += text.slice(i, j);
      i = k + 1;
    }
  }
  return out + text.slice(i);
}

function removeAnnotations(s: string): string {
  s = dropSpans(dropSpans(s, "<", ">", "\n"), "(", ")").replaceAll('"', ""); // a stray quote (HTML) is not music
  const steps: Array<[string, string]> = [
    ["(?<!a)l(?!t)|f", ""], ["(?<!su)s(?!us)", ""], ["\\*\\w", ""], ["T\\d+", ""],
  ];
  for (const [src, rep] of steps) s = sub(s, src, rep);
  return s;
}

const removeMarkers = (s: string): string => sub(s, "U|S|Q|N\\d", "");

/** A bar as written: its text (chords and marks) and the barlines around it. */
interface Bar {
  text: string;
  opener: string; // "{" (repeat start), "[" (section start) or ""
  closes: boolean; // ends with "}"
  ending: number | null; // the ending (volta) it starts, from `N<digit>`
}

function splitBars(s: string): Bar[] {
  const bars: Bar[] = [];
  let opener = "", pos = 0;
  const bar = (text: string, closes: boolean): Bar => {
    const ending = py("N(\\d)").exec(text);
    return { text, opener, closes, ending: ending ? digitValue(ending[1]!) : null };
  };
  for (const m of s.matchAll(/[|[\]{}]/g)) {
    bars.push(bar(s.slice(pos, m.index), m[0] === "}"));
    [opener, pos] = [m[0] === "{" || m[0] === "[" ? m[0] : "", m.index + 1];
  }
  bars.push(bar(s.slice(pos), false));
  return bars;
}

/** The order bars are played in (Python `_expand_repeats`: indices, or the text of a part-bar before a mid-bar ending), one linear pass. */
/** The start of a bar whose ending is written mid-bar (Python `_Head`): played with the next bar. */
interface Head {
  head: string;
}
type Played = number | string | Head;

function expandRepeats(bars: Bar[]): Played[] {
  const n = bars.length;
  const following = new Array<number>(n + 1).fill(n); // the next bar at or after i with chords or an ending
  for (let i = n - 1; i >= 0; i--) {
    const filled = bars[i]!.ending !== null || pyStrip(removeMarkers(bars[i]!.text)) !== "";
    following[i] = filled ? i : following[i + 1]!;
  }
  const order: Played[] = [];
  const play = (items: Played[]) => {
    for (const item of items) order.push(item); // no spread: it overflows the stack on long charts
  };
  let region = 0, opened: number | null = null, body: Played[] = [], ending = 0;
  bars.forEach((bar, i) => {
    if (bar.opener === "{") [region, opened, ending] = [i, i, 0];
    else if (bar.opener === "[") region = i;
    order.push(i);
    if (!bar.closes) return;
    const j = following[i + 1]!;
    const nextEnding = j < n ? bars[j]!.ending : null;
    if (ending && opened === null) {
      // The "}" closing ending number `ending`: replay only before a further ending.
      if (nextEnding === ending + 1) {
        play(body);
        ending = nextEnding;
      } else ending = 0;
    } else {
      const start = opened ?? region;
      const endings: number[] = [];
      for (let k = start; k <= i; k++) if (bars[k]!.ending !== null) endings.push(k);
      body = [];
      for (let k = start; k < (endings[0] ?? i + 1); k++) body.push(k);
      if (endings.length) {
        // An ending written mid-bar: its bar's start is played each time.
        const text = bars[endings[0]!]!.text, head = text.slice(0, py("N\\d").exec(text)!.index);
        if (pyStrip(removeMarkers(head))) body.push({ head });
      }
      if (endings.length > 1) {
        // Several endings inside the braces: one pass each (the first pass stops at N2).
        order.length -= i + 1 - endings[1]!;
        endings.slice(1).forEach((a, e) => {
          play(body);
          for (let k = a; k < (endings[e + 2] ?? i + 1); k++) order.push(k);
        });
      } else play(body);
      const last = endings.length ? bars[endings[endings.length - 1]!]!.ending : null;
      if (last !== null && nextEnding === last + 1) {
        if (endings.length > 1) play(body);
        ending = nextEnding;
      } else ending = 0;
    }
    [region, opened] = [i + 1, null];
  });
  return order;
}

/** The played bars' texts, with a D.C./D.S. al Coda (two `Q`s) written out (Python `_fill_codas`). */
function fillCodas(bars: Bar[], order: Played[]): Array<string | Head> {
  const texts = order.map((i) => (typeof i === "number" ? bars[i]!.text : i));
  const qs = bars.reduce((n, b) => n + [...b.text].filter((c) => c === "Q").length, 0);
  if (qs > 2) throw new ValueError(`Could not parse codas: expected 0, 1 or 2 Qs, not ${qs}`);
  const qBars = bars.flatMap((b, i) => (b.text.includes("Q") ? [i] : []));
  if (qs < 2 || qBars.length < 2) return texts;
  const [p1, p2] = [order.indexOf(qBars[0]!), order.indexOf(qBars[1]!)];
  if (p1 >= p2) return texts;
  const segnoBar = bars.findIndex((b) => b.text.includes("S"));
  const segno = segnoBar >= 0 ? order.indexOf(segnoBar) : null;
  const cut = (text: string, mark: string): [string, string] => {
    const k = text.indexOf(mark);
    return k >= 0 ? [text.slice(0, k), text.slice(k + 1)] : [text, ""];
  };
  const toCoda = cut(texts[p1] as string, "Q")[0];
  let replay: Array<string | Head>;
  if (segno === null || segno > p1) replay = [...texts.slice(0, p1), toCoda];
  else if (segno < p1) replay = [cut(texts[segno] as string, "S")[1], ...texts.slice(segno + 1, p1), toCoda];
  else replay = [cut(cut(texts[p1] as string, "S")[1], "Q")[0]];
  const [before, coda] = cut(texts[p2] as string, "Q");
  return [...texts.slice(0, p2), before, ...replay, coda, ...texts.slice(p2 + 1)];
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
  const bars = splitBars(removeAnnotations(cleanupChordString(chordString)));
  const played: string[][] = [];
  let carried: string[] = []; // a Head's chords, waiting for the bar they share
  for (const text of fillCodas(bars, expandRepeats(bars))) {
    const tokens = barTokens(removeMarkers(typeof text === "string" ? text : text.head));
    if (typeof text !== "string") carried = carried.concat(tokens);
    else if (tokens.length) {
      played.push(carried.concat(tokens));
      carried = [];
    }
  }
  if (carried.length) played.push(carried);
  return fillSlashes(fillRepeatSigns(played));
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
  let body = unquote(url.split('"', 1)[0]!); // a raw `"` ends the URL; `%22` is a quote in it
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
