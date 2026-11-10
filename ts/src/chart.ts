/**
 * Chord charts: from text, measures, symbols or `[chord, beats]` pairs to a {@link Score}.
 *
 * Twin of `accompy.util` (normalisation, chart strings, time signatures, chord specs,
 * transposition) and `accompy.base.ensure_score`. Chord symbols are rewritten to iReal
 * spellings (`Cm7` -> `C-7`, `Cmaj7` -> `C^7`), as in Python.
 */
import {
  CHORD_SYMBOL_REPLACEMENTS,
  FLAT_KEYS,
  FLAT_NOTES,
  NOTE_TO_SEMITONE,
  SHARP_NOTES,
  UNNORMALIZED_SYMBOLS,
} from "./data.generated.js";
import { parseIrealUrl } from "./ireal.js";
import { pyFloorDiv, pyInt, pyMod, pySplit, pyStrip } from "./py.js";

/** A chord chart: measures of chord symbols (a measure's chords share it evenly). */
export interface Score {
  measures: string[][];
  title: string;
  composer: string;
  key: string;
  timeSignature: [number, number];
}

/** A chord and how many beats it lasts. */
export type ChordSpec = [chord: string, beats: number];

/** Options shared by the chart readers (Python's keyword-only arguments). */
export interface ChartOptions {
  title?: string;
  key?: string;
  timeSignature?: [number, number];
}

function makeScore(measures: string[][], opts: ChartOptions = {}, composer = ""): Score {
  return {
    measures,
    title: opts.title ?? "Untitled",
    composer,
    key: opts.key ?? "C",
    timeSignature: opts.timeSignature ?? [4, 4],
  };
}

/**
 * Rewrite a chord symbol to iReal spelling (`Cmaj7` -> `C^7`, `Dm7b5` -> `Dh7`).
 *
 * Each rewrite in `CHORD_SYMBOL_REPLACEMENTS` applies, in order, at the end of the symbol
 * or before a slash. (Python quirk kept for parity: `Cdim` becomes `Cdi-`.)
 */
export function normalizeChordSymbol(symbol: string): string {
  const s = pyStrip(symbol);
  if (!s || (UNNORMALIZED_SYMBOLS as readonly string[]).includes(s)) return s;
  let result = s;
  for (const [old, replacement] of CHORD_SYMBOL_REPLACEMENTS) {
    if (result.endsWith(old)) result = result.slice(0, result.length - old.length) + replacement;
    else if (result.includes(`${old}/`)) result = result.split(`${old}/`).join(`${replacement}/`);
  }
  return result;
}

/**
 * Measures of normalised chord symbols from a chart string.
 *
 * With bar lines (`| C Am | F G |`), each bar is a measure and `%` or `x` repeats the
 * previous chord; without, each whitespace-separated symbol is a bar.
 */
export function parseChordString(chordString: string): string[][] {
  const s = pyStrip(chordString);
  if (!s.includes("|")) return pySplit(s).map((c) => [normalizeChordSymbol(c)]);
  const measures: string[][] = [];
  let last: string | null = null;
  for (const part of s.split("|")) {
    const bar = pyStrip(part);
    if (!bar) continue;
    const normalized: string[] = [];
    for (const token of pySplit(bar)) {
      const chord = normalizeChordSymbol(token === "%" || token === "x" ? (last || "C") : token);
      normalized.push(chord);
      last = chord;
    }
    if (normalized.length) measures.push(normalized);
  }
  return measures;
}

/** `"3/4"` -> `[3, 4]`; anything unreadable (or empty) -> `[4, 4]`. */
export function parseTimeSig(ts: string | [number, number] | null | undefined): [number, number] {
  if (!ts) return [4, 4];
  if (Array.isArray(ts)) return ts;
  try {
    const parts = ts.split("/");
    if (parts.length < 2) return [4, 4];
    return [pyInt(parts[0]!), pyInt(parts[1]!)];
  } catch (error) {
    if (error instanceof RangeError) return [4, 4];
    throw error;
  }
}

/**
 * A Score from `[chord, beats]` pairs: whole bars become bars, shorter chords are grouped
 * into bars (durations that do not fill bars exactly are approximated). No-chord symbols
 * and non-positive durations are dropped.
 */
export function scoreFromChordSpecs(chords: Iterable<ChordSpec>, opts: ChartOptions = {}): Score {
  const beatsPerBar = (opts.timeSignature ?? [4, 4])[0];
  const measures: string[][] = [];
  let bar: string[] = [];
  let barBeats = 0;
  for (const [raw, beats] of chords) {
    const chord = normalizeChordSymbol(raw);
    if (chord === "" || chord === "n" || chord === "N.C." || chord === "NC") continue;
    if (beats <= 0) continue;
    const fullBars = pyFloorDiv(beats, beatsPerBar);
    const rem = beats - fullBars * beatsPerBar;
    for (let i = 0; i < fullBars; i++) measures.push([chord]);
    if (rem) {
      bar.push(chord);
      barBeats += rem;
      if (barBeats >= beatsPerBar - 1e-9) {
        measures.push(bar);
        bar = [];
        barBeats = 0;
      }
    }
  }
  if (bar.length) measures.push(bar);
  return makeScore(measures, opts);
}

/** The Score as `[chord, beats]` pairs, each chord taking its share of the bar. */
export function scoreToChordSequence(score: Score): ChordSpec[] {
  const beatsPerBar = score.timeSignature[0];
  const out: ChordSpec[] = [];
  for (const measure of score.measures) {
    if (!measure.length) continue;
    for (const symbol of measure) out.push([symbol, beatsPerBar / measure.length]);
  }
  return out;
}

function isScore(value: unknown): value is Score {
  return typeof value === "object" && value !== null && !Array.isArray(value) && "measures" in value;
}

/**
 * Coerce any chart form to a {@link Score}: a Score (returned as is), a chart string or an
 * iReal URL (`irealb://`, `irealbook://`), measures (`[["C", "Am"], ["F"]]`), chord
 * symbols one per bar, or `[chord, beats]` pairs. Anything else throws a TypeError.
 */
export function ensureScore(chords: unknown, opts: ChartOptions = {}): Score {
  if (isScore(chords)) return chords;
  if (typeof chords === "string") {
    const s = pyStrip(chords);
    if (s.startsWith("irealbook://") || s.startsWith("irealb://")) return parseIrealUrl(s);
    return makeScore(parseChordString(s), opts);
  }
  if (Array.isArray(chords)) {
    const items: unknown[] = chords;
    const isMeasure = (x: unknown) => Array.isArray(x) && x.every((c) => typeof c === "string");
    if (items.length && items.every(isMeasure)) {
      return makeScore((items as string[][]).map((m) => m.map(normalizeChordSymbol)), opts);
    }
    if (!items.length) return makeScore([], opts);
    if (items.every((x) => typeof x === "string")) {
      return makeScore((items as string[]).map((x) => [normalizeChordSymbol(x)]), opts);
    }
    const isSpec = (x: unknown) =>
      Array.isArray(x) && x.length === 2 && typeof x[0] === "string" && typeof x[1] === "number";
    if (items.every(isSpec)) return scoreFromChordSpecs(items as ChordSpec[], opts);
  }
  throw new TypeError(
    "Unsupported chords input. Expected Score, chord string, iReal URL, " +
      "list of (chord, beats) tuples, iterable of chord symbols, or measures list.",
  );
}

const NOTE_INDEX = new Map<string, number>(NOTE_TO_SEMITONE as readonly (readonly [string, number])[]);

/** Transpose a note name (`C`, `Eb`, `F#`); flats by default when going down. */
export function transposeNote(name: string, semitones: number, opts: { useFlat?: boolean | null } = {}): string {
  const index = NOTE_INDEX.get(name);
  if (index === undefined) return name;
  const useFlat = opts.useFlat ?? semitones < 0;
  return (useFlat ? FLAT_NOTES : SHARP_NOTES)[pyMod(index + semitones, 12)]!;
}

/** Transpose a chord symbol's root (and slash bass); the quality is kept as written. */
export function transposeChord(chord: string, semitones: number, opts: { useFlat?: boolean | null } = {}): string {
  if (!chord || chord === "N.C." || chord === "NC") return chord;
  const slash = chord.indexOf("/");
  if (slash >= 0) {
    return `${transposeChord(chord.slice(0, slash), semitones, opts)}/${transposeChord(chord.slice(slash + 1), semitones, opts)}`;
  }
  const match = /^([A-G][#b]?)(.*)/.exec(chord);
  if (!match) return chord;
  return transposeNote(match[1]!, semitones, opts) + match[2]!;
}

/** The Score in `targetKey` (spelled with flats for flat keys), titled `"<title> (<key>)"`. */
export function transposeScore(score: Score, targetKey: string): Score {
  const semitones = (NOTE_INDEX.get(targetKey) ?? 0) - (NOTE_INDEX.get(score.key) ?? 0);
  const useFlat = targetKey.includes("b") || (FLAT_KEYS as readonly string[]).includes(targetKey);
  return {
    measures: score.measures.map((m) => m.map((c) => transposeChord(c, semitones, { useFlat }))),
    title: `${score.title} (${targetKey})`,
    composer: score.composer,
    key: targetKey,
    timeSignature: score.timeSignature,
  };
}
