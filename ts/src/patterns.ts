/**
 * Style patterns (drums, bass, comping) and the registry of styles: the twin of
 * `accompy.patterns`. The builtin styles are generated from the Python patterns.
 */
import { BASS_PATTERNS, COMP_PATTERNS, DRUM_PATTERNS } from "./data.generated.js";
import { KeyError, ValueError } from "./py.js";

/** A drum hit: beat in the bar (0-based), GM percussion note, velocity 0-127. */
export interface DrumHit {
  beat: number;
  drum: number;
  velocity: number;
}

/** A drum pattern for one bar of `beatsPerBar` beats. */
export interface DrumPattern {
  name: string;
  beatsPerBar: number;
  hits: DrumHit[];
}

/** A bass note: beat, semitones above the chord root (resolved against the chord), beats, velocity. */
export interface BassNote {
  beat: number;
  pitchOffset: number;
  duration: number;
  velocity: number;
}

/** A bass pattern: notes relative to the chord root. */
export interface BassPattern {
  name: string;
  notes: BassNote[];
}

/** A comping pattern: `[beat, duration, velocity]` hits, each playing the whole chord. */
export interface CompingPattern {
  name: string;
  hits: [beat: number, duration: number, velocity: number][];
}

/** What a style plays: the renderer takes the first of each list (drums: by time signature). */
export interface StylePatterns {
  drums: DrumPattern[];
  bass: BassPattern[];
  comp: CompingPattern[];
}

/** Where the renderer gets a style's patterns (Python's PatternSource protocol). */
export interface PatternSource {
  getPatterns(style: string): StylePatterns;
}

function builtin(style: string): StylePatterns {
  const drums = DRUM_PATTERNS[style as keyof typeof DRUM_PATTERNS] ?? [];
  const bass = BASS_PATTERNS[style as keyof typeof BASS_PATTERNS] ?? [];
  const comp = COMP_PATTERNS[style as keyof typeof COMP_PATTERNS] ?? [];
  return {
    drums: drums.map((p) => ({
      name: p.name,
      beatsPerBar: p.beats_per_bar,
      hits: p.hits.map(([beat, drum, velocity]) => ({ beat, drum, velocity })),
    })),
    bass: bass.map((p) => ({
      name: p.name,
      notes: p.notes.map(([beat, pitchOffset, duration, velocity]) => ({ beat, pitchOffset, duration, velocity })),
    })),
    comp: comp.map((p) => ({ name: p.name, hits: p.hits.map(([b, d, v]) => [b, d, v]) })),
  };
}

/** Styles by name, starting with the builtin ones. Twin of Python's PatternRegistry. */
export class PatternRegistry implements PatternSource {
  readonly #styles = new Map<string, StylePatterns>();

  /** A registry holding the builtin styles (`builtins: false` for an empty one). */
  constructor({ builtins = true }: { builtins?: boolean } = {}) {
    if (builtins) for (const style of Object.keys(DRUM_PATTERNS)) this.#styles.set(style, builtin(style));
  }

  /** The style's patterns; throws KeyError (a RangeError) for an unknown style. */
  getPatterns(style: string): StylePatterns {
    const patterns = this.#styles.get(style);
    if (patterns === undefined) {
      throw new KeyError(`Unknown style: ${style}. Available: ${this.styles().join(", ")}`);
    }
    return patterns;
  }

  /** Add or replace a style. */
  register(style: string, patterns: StylePatterns): void {
    for (const key of ["drums", "bass", "comp"] as const) {
      if (!Array.isArray(patterns[key])) throw new ValueError("Pattern dict must have keys: drums, bass, comp");
    }
    this.#styles.set(style, patterns);
  }

  /** Remove a style; returns whether it was there. */
  unregister(style: string): boolean {
    return this.#styles.delete(style);
  }

  /** The style names, in registration order. */
  styles(): string[] {
    return [...this.#styles.keys()];
  }
}

let registry: PatternRegistry | undefined;

/** The shared registry the renderer uses by default. */
export function getPatternRegistry(): PatternRegistry {
  registry ??= new PatternRegistry();
  return registry;
}

/** A style's patterns from the shared registry. */
export function getPatterns(style: string): StylePatterns {
  return getPatternRegistry().getPatterns(style);
}

/** Register a style in the shared registry. */
export function registerStyle(style: string, patterns: StylePatterns): void {
  getPatternRegistry().register(style, patterns);
}

/** The builtin style names (swing, bossa, rock, funk, ballad, latin, waltz, blues). */
export const STYLES: readonly string[] = Object.freeze(Object.keys(DRUM_PATTERNS));

/**
 * The `[drums, bass, comp]` patterns the renderer plays from a style's lists: the first
 * drum pattern whose `beatsPerBar` matches (else the first), the first bass and comping
 * pattern; `null` where a list is empty.
 */
export function selectPatterns(
  patterns: StylePatterns,
  beatsPerBar: number,
): [DrumPattern | null, BassPattern | null, CompingPattern | null] {
  const drums = patterns.drums.find((p) => p.beatsPerBar === beatsPerBar) ?? patterns.drums[0] ?? null;
  return [drums, patterns.bass[0] ?? null, patterns.comp[0] ?? null];
}
