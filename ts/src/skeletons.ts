/**
 * Rhythmic skeletons: duration-only measure patterns (when to strike, for how long), the
 * twin of `accompy.rhythmic_skeletons`. The builtin skeletons are generated from Python.
 */
import { RHYTHMIC_SKELETONS as BUILTIN } from "./data.generated.js";
import type { ChordSpec } from "./chart.js";
import { pySum } from "./py.js";

/** A skeleton's entry: its durations (beats), display name, measure length and styles. */
export interface Skeleton {
  pattern: number[];
  name: string;
  beatsPerMeasure: number;
  styles: string[];
}

/** The skeletons by key, builtin ones first; {@link registerSkeleton} adds to it. */
export const RHYTHMIC_SKELETONS = new Map<string, Skeleton>(
  Object.entries(BUILTIN).map(([key, s]) => [
    key,
    { pattern: [...s.pattern], name: s.name, beatsPerMeasure: s.beats_per_measure, styles: [...s.styles] },
  ]),
);

function byName(name: string): string | undefined {
  for (const [key, s] of RHYTHMIC_SKELETONS) if (s.name.toLowerCase() === name) return key;
  return undefined;
}

function byStyle(style: string): string[] {
  return [...RHYTHMIC_SKELETONS].filter(([, s]) => s.styles.includes(style)).map(([key]) => key);
}

/**
 * A skeleton's durations from a duration list (returned as is), a key (`"tresillo"`), a
 * name, case-insensitively (`"Dotted half + quarter"`), or a style (`"reggae"`: its first
 * skeleton). Throws RangeError when nothing matches (Python: KeyError), TypeError for
 * anything but a string or an array.
 */
export function resolveSkeleton(skeleton: string | readonly number[]): number[] {
  if (Array.isArray(skeleton)) return [...skeleton];
  if (typeof skeleton !== "string") {
    throw new TypeError(`skeleton must be a str, tuple, or list, got ${typeof skeleton}`);
  }
  const exact = RHYTHMIC_SKELETONS.get(skeleton);
  if (exact) return [...exact.pattern];
  const lower = skeleton.toLowerCase();
  const key = byName(lower) ?? byStyle(lower)[0];
  if (key !== undefined) return [...RHYTHMIC_SKELETONS.get(key)!.pattern];
  throw new RangeError(`Unknown skeleton: '${skeleton}'`);
}

const EPSILON = 1e-9;

function groupIntoMeasures(chords: readonly ChordSpec[], beatsPerMeasure: number): ChordSpec[][] {
  const measures: ChordSpec[][] = [];
  let current: ChordSpec[] = [];
  let remaining = beatsPerMeasure;
  for (const [symbol, duration] of chords) {
    let left = duration;
    while (left > EPSILON) {
      const take = Math.min(left, remaining);
      current.push([symbol, take]);
      remaining -= take;
      left -= take;
      if (remaining < EPSILON) {
        measures.push(current);
        current = [];
        remaining = beatsPerMeasure;
      }
    }
  }
  if (current.length) measures.push(current);
  return measures;
}

function expandMeasure(chords: readonly ChordSpec[], starts: number[], durations: readonly number[]): ChordSpec[] {
  const map: [string, number, number][] = [];
  let pos = 0;
  for (const [symbol, dur] of chords) {
    map.push([symbol, pos, pos + dur]);
    pos += dur;
  }
  const out: ChordSpec[] = [];
  starts.forEach((strike, i) => {
    const end = strike + durations[i]!;
    for (const [symbol, chordStart, chordEnd] of map) {
      const overlap = Math.min(end, chordEnd) - Math.max(strike, chordStart);
      if (overlap > EPSILON) out.push([symbol, overlap]);
    }
  });
  return out;
}

/**
 * Restrike `[chord, beats]` pairs on a skeleton: each strike of each measure plays the
 * chord active at that beat, split where a chord changes under it.
 *
 * @example
 * applySkeleton([["Dm7", 4], ["G7", 4]], "tresillo");
 * // [["Dm7", 1.5], ["Dm7", 1.5], ["Dm7", 1], ["G7", 1.5], ["G7", 1.5], ["G7", 1]]
 */
export function applySkeleton(chords: readonly ChordSpec[], skeleton: string | readonly number[]): ChordSpec[] {
  const pattern = resolveSkeleton(skeleton);
  const starts: number[] = [];
  let t = 0;
  for (const dur of pattern) {
    starts.push(t);
    t += dur;
  }
  return groupIntoMeasures(chords, pySum(pattern)).flatMap((m) => expandMeasure(m, starts, pattern));
}

/** Add (or replace) a skeleton; its measure length defaults to the sum of its durations. */
export function registerSkeleton(
  key: string,
  pattern: readonly number[],
  opts: { name?: string; beatsPerMeasure?: number; styles?: string[] } = {},
): void {
  RHYTHMIC_SKELETONS.set(key, {
    pattern: [...pattern],
    name: opts.name || key,
    beatsPerMeasure: opts.beatsPerMeasure ?? pySum(pattern),
    styles: opts.styles ? [...opts.styles] : [],
  });
}

/** Skeleton keys, optionally only those of a measure length and/or a style. */
export function listSkeletons(opts: { beatsPerMeasure?: number; style?: string } = {}): string[] {
  let keys = [...RHYTHMIC_SKELETONS.keys()];
  if (opts.beatsPerMeasure !== undefined) {
    keys = keys.filter((k) => RHYTHMIC_SKELETONS.get(k)!.beatsPerMeasure === opts.beatsPerMeasure);
  }
  if (opts.style !== undefined) {
    const inStyle = new Set(byStyle(opts.style));
    keys = keys.filter((k) => inStyle.has(k));
  }
  return keys;
}
