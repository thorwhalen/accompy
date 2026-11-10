// The golden cases in ../fixtures/cases.json, run against the TypeScript twin.
// The Python twin runs the same file (tests/test_twin.py); accompy/_fixtures.py documents
// the JSON conventions this runner mirrors.
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as accompy from "./index.js";
import type { NoteEvent, Score, StylePatterns } from "./index.js";

interface Case {
  fn: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
  expected: unknown;
}

const { functions, cases } = JSON.parse(
  readFileSync(new URL("../../fixtures/cases.json", import.meta.url), "utf-8"),
) as { functions: string[]; cases: Case[] };

type AnyFn = (...args: never[]) => unknown;

/** Python name -> the TS twin; keyword-only arguments become a trailing options object. */
const FUNCTIONS: Record<string, AnyFn> = {
  normalize_chord_symbol: accompy.normalizeChordSymbol,
  parse_chord_string: accompy.parseChordString,
  parse_time_sig: accompy.parseTimeSig,
  ensure_score: accompy.ensureScore,
  score_from_chord_specs: accompy.scoreFromChordSpecs,
  score_to_chord_sequence: accompy.scoreToChordSequence,
  parse_ireal_url: accompy.parseIrealUrl,
  transpose_note: accompy.transposeNote,
  transpose_chord: accompy.transposeChord,
  transpose_score: accompy.transposeScore,
  tonal_resolver: accompy.tonalResolver,
  get_patterns: accompy.getPatterns,
  chord_events: accompy.chordEvents,
  generate_events: accompy.generateEvents,
  resolve_skeleton: accompy.resolveSkeleton,
  apply_skeleton: accompy.applySkeleton,
  list_skeletons: accompy.listSkeletons,
};

const scoreToJson = (s: Score) => ({
  measures: s.measures,
  title: s.title,
  composer: s.composer,
  key: s.key,
  time_signature: s.timeSignature,
});
const eventsToJson = (events: NoteEvent[]) => events.map((e) => [e.time, e.channel, e.note, e.velocity, e.duration]);

/** Results whose JSON form differs from the TS value. */
const ENCODERS: Record<string, (result: never) => unknown> = {
  ensure_score: scoreToJson,
  score_from_chord_specs: scoreToJson,
  parse_ireal_url: scoreToJson,
  transpose_score: scoreToJson,
  chord_events: eventsToJson,
  generate_events: eventsToJson,
  get_patterns: (p: StylePatterns) => ({
    drums: p.drums.map((d) => ({ name: d.name, beats_per_bar: d.beatsPerBar, hits: d.hits })),
    bass: p.bass.map((b) => ({
      name: b.name,
      notes: b.notes.map((n) => ({ beat: n.beat, pitch_offset: n.pitchOffset, duration: n.duration, velocity: n.velocity })),
    })),
    comp: p.comp,
  }),
};

/** An argument in JSON form -> the TS value (a mapping with "measures" is a Score). */
function decode(value: unknown): unknown {
  if (typeof value === "object" && value !== null && !Array.isArray(value) && "measures" in value) {
    const v = value as Record<string, unknown>;
    return {
      measures: v.measures,
      title: v.title ?? "Untitled",
      composer: v.composer ?? "",
      key: v.key ?? "C",
      timeSignature: v.time_signature ?? [4, 4],
    };
  }
  return value;
}

const camel = (snake: string) => snake.replace(/_([a-z])/g, (_, c: string) => c.toUpperCase());

/** Python exception name -> the JS error the twin throws (KeyError and ValueError share one). */
const RAISES: Record<string, string> = { ValueError: "RangeError", KeyError: "RangeError", TypeError: "TypeError" };

function call(c: Case): unknown {
  const fn = FUNCTIONS[c.fn];
  if (fn === undefined) throw new Error(`no TS twin for ${c.fn}`);
  const args = (c.args ?? []).map(decode);
  if (c.kwargs && Object.keys(c.kwargs).length > 0) {
    args.push(Object.fromEntries(Object.entries(c.kwargs).map(([k, v]) => [camel(k), decode(v)])));
  }
  try {
    const result = (fn as (...a: unknown[]) => unknown)(...args);
    const encode = ENCODERS[c.fn] as ((r: unknown) => unknown) | undefined;
    return encode ? encode(result) : result;
  } catch (error) {
    const expected = (c.expected as { $raises?: string } | null)?.$raises;
    if (expected !== undefined && RAISES[expected] === (error as Error).name) return { $raises: expected };
    throw error;
  }
}

describe("fixtures/cases.json", () => {
  it("the TS twin covers exactly the Python twin's functions", () => {
    expect(Object.keys(FUNCTIONS).sort()).toEqual([...functions].sort());
    expect(new Set(cases.map((c) => c.fn))).toEqual(new Set(functions));
  });

  it.each(cases.map((c, i) => [`${i} ${c.fn}${JSON.stringify(c.args)}`.slice(0, 90), c] as const))(
    "%s",
    (_, c) => {
      // Compared as JSON text: order matters, as it does on the Python side.
      expect(JSON.stringify(call(c))).toBe(JSON.stringify(c.expected));
    },
  );
});
