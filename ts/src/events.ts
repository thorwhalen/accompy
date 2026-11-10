/**
 * Chart -> timed note events, the twin of accompy's builtin backend
 * (`accompy.renderers.midi`: `generate_events`, `chord_events`, `generate_midi_events`).
 *
 * Times and durations are in beats. Generation reads no tempo, keeps no state between
 * chords and uses no randomness: the same chart, style, repeats, instruments and volumes
 * always give the same events. Use {@link beatsToSeconds} at whatever tempo you play.
 */
import {
  DEFAULT_INSTRUMENTS,
  DEFAULT_VOLUMES,
  FALLBACK_CHORD_NOTES,
  NO_CHORD_SYMBOLS,
  NOTE_TO_SEMITONE,
} from "./data.generated.js";
import { ensureScore, type Score } from "./chart.js";
import {
  getPatternRegistry,
  selectPatterns,
  type BassPattern,
  type CompingPattern,
  type DrumPattern,
  type PatternSource,
} from "./patterns.js";
import { pyFloorDiv, pyTrunc } from "./py.js";
import { tonalResolver, type ChordResolver } from "./resolve.js";

/** One note: Python's `MidiEvent`. Channel 9 is drums, 0 bass, 1 piano. */
export interface NoteEvent {
  /** Start, in beats from the beginning. */
  time: number;
  channel: number;
  /** MIDI note number (for drums, the GM percussion sound). */
  note: number;
  /** 0-127. */
  velocity: number;
  /** Length, in beats. */
  duration: number;
}

/** Which instruments play (`drums`, `bass`, `piano`); a missing one plays. */
export type Instruments = Record<string, boolean>;
/** Volume per instrument, 0-1, scaling pattern velocities; missing ones use the defaults. */
export type Volumes = Record<string, number>;

/** MIDI channels of the parts. */
export const CHANNELS = Object.freeze({ drums: 9, bass: 0, piano: 1 });

/** Seconds from beats at `tempo` beats per minute. */
export function beatsToSeconds(beats: number, tempo: number): number {
  return (beats * 60) / tempo;
}

const NO_CHORD = new Set<string>(NO_CHORD_SYMBOLS);
const SEMITONES = new Map<string, number>(NOTE_TO_SEMITONE as readonly (readonly [string, number])[]);

/**
 * What the renderer plays for a symbol its resolver cannot read: a major triad on the
 * symbol's leading note name, either case, `#`/`b` or `♯`/`♭` (`G#13(b9)` -> G# major),
 * or on C without one.
 */
export function fallbackChordNotes(symbol: string): number[] {
  const root = /^([A-Ga-g])([#b\u266f\u266d]?)/.exec(symbol);
  if (!root) return [...FALLBACK_CHORD_NOTES];
  const name = root[1]!.toUpperCase() + root[2]!.replace("\u266f", "#").replace("\u266d", "b");
  return FALLBACK_CHORD_NOTES.map((n) => n + (SEMITONES.get(name) ?? 0));
}
const DRUM_DURATION = 0.25;

function drumEvents(pattern: DrumPattern, start: number, duration: number, volume: number): NoteEvent[] {
  return pattern.hits
    .filter((hit) => hit.beat < duration)
    .map((hit) => ({
      time: start + hit.beat,
      channel: CHANNELS.drums,
      note: hit.drum,
      velocity: pyTrunc(hit.velocity * volume),
      duration: DRUM_DURATION,
    }));
}

/** The semitone offset a pattern asks for, moved to the chord's own 3rd when it has one. */
function resolveOffset(rootPc: number, chordPcs: number[], target: number): number {
  if (!chordPcs.length) return target;
  const intervals = chordPcs.map((pc) => (((pc - rootPc) % 12) + 12) % 12);
  if (intervals.includes(target)) return target;
  if (target === 3 || target === 4) {
    if (intervals.includes(3)) return 3;
    if (intervals.includes(4)) return 4;
  }
  return target;
}

function bassEvents(
  pattern: BassPattern,
  start: number,
  duration: number,
  root: number,
  notes: readonly number[],
  volume: number,
): NoteEvent[] {
  const bassRoot = (((root % 12) + 12) % 12) + 36;
  const rootPc = bassRoot % 12;
  const chordPcs = [...new Set(notes.map((n) => ((n % 12) + 12) % 12))].sort((a, b) => a - b);
  const out: NoteEvent[] = [];
  for (const note of pattern.notes) {
    if (note.beat >= duration) continue;
    const dur = Math.min(note.duration, Math.max(0, duration - note.beat));
    if (dur <= 0) continue;
    out.push({
      time: start + note.beat,
      channel: CHANNELS.bass,
      note: bassRoot + resolveOffset(rootPc, chordPcs, note.pitchOffset),
      velocity: pyTrunc(note.velocity * volume),
      duration: dur,
    });
  }
  return out;
}

function compEvents(
  pattern: CompingPattern | null,
  start: number,
  duration: number,
  chordNotes: readonly number[],
  volume: number,
): NoteEvent[] {
  const notes = chordNotes.length ? chordNotes.slice(0, 4).map((n) => (((n % 12) + 12) % 12) + 60) : [60, 64, 67];
  const out: NoteEvent[] = [];
  if (pattern === null || !pattern.hits.length) {
    // No comping pattern: a block chord on each beat.
    const velocity = pyTrunc(90 * volume);
    for (let i = 0; i < Math.min(pyTrunc(duration), 4); i++) {
      for (const note of notes) out.push({ time: start + i, channel: CHANNELS.piano, note, velocity, duration: 0.9 });
    }
    return out;
  }
  for (const [beat, hitDuration, hitVelocity] of pattern.hits) {
    if (beat >= duration) continue;
    const dur = Math.min(hitDuration, Math.max(0, duration - beat));
    if (dur <= 0) continue;
    const velocity = pyTrunc(hitVelocity * volume);
    for (const note of notes) out.push({ time: start + beat, channel: CHANNELS.piano, note, velocity, duration: dur });
  }
  return out;
}

const volumeOf = (volumes: Volumes, part: string, fallback: number) => volumes[part] ?? fallback;
const plays = (instruments: Instruments, part: string) => instruments[part] ?? true;

function playChord(
  notes: readonly number[],
  [drums, bass, comp]: ReturnType<typeof selectPatterns>,
  start: number,
  duration: number,
  instruments: Instruments,
  volumes: Volumes,
): NoteEvent[] {
  const root = notes.length ? notes[0]! : 48;
  const out: NoteEvent[] = [];
  if (plays(instruments, "drums") && drums) out.push(...drumEvents(drums, start, duration, volumeOf(volumes, "drums", 0.8)));
  if (plays(instruments, "bass") && bass) {
    out.push(...bassEvents(bass, start, duration, root, notes, volumeOf(volumes, "bass", 0.9)));
  }
  if (plays(instruments, "piano")) out.push(...compEvents(comp, start, duration, notes, volumeOf(volumes, "piano", 0.7)));
  return out;
}

/** Options of {@link chordEvents}. */
export interface ChordEventsOptions {
  style?: string;
  startBeat?: number;
  duration?: number;
  beatsPerBar?: number;
  instruments?: Instruments;
  volumes?: Volumes;
  patternSource?: PatternSource;
}

/**
 * The drum, bass and piano events `style` plays over one chord, given the chord's MIDI
 * notes (root first, as a {@link ChordResolver} returns them). One step of
 * {@link generateEvents}: call it per chord to render a chart a bar at a time.
 *
 * @example
 * chordEvents([48, 52, 55], { style: "bossa", startBeat: 4, duration: 4 });
 */
export function chordEvents(chordNotes: readonly number[], opts: ChordEventsOptions = {}): NoteEvent[] {
  const source = opts.patternSource ?? getPatternRegistry();
  return playChord(
    chordNotes,
    selectPatterns(source.getPatterns(opts.style ?? "swing"), opts.beatsPerBar ?? 4),
    opts.startBeat ?? 0,
    opts.duration ?? 4,
    opts.instruments ?? DEFAULT_INSTRUMENTS,
    opts.volumes ?? DEFAULT_VOLUMES,
  );
}

/** Options of {@link generateEvents}. */
export interface GenerateOptions {
  style?: string;
  /** How many times the chart is played (default 1). */
  repeats?: number;
  /** For chart forms that carry none (default `[4, 4]`). */
  timeSignature?: [number, number];
  instruments?: Instruments;
  volumes?: Volumes;
  patternSource?: PatternSource;
  chordResolver?: ChordResolver;
}

/**
 * The note events of a whole chart (any form {@link ensureScore} reads), in the order the
 * builtin backend generates them: chord by chord, drums then bass then piano. Each chord
 * of a bar gets `beatsPerBar // chords` beats; no-chord symbols are silent; a symbol the
 * resolver cannot read plays a major triad on its root ({@link fallbackChordNotes}).
 *
 * @example
 * const events = generateEvents("| Dm7 | G7 | C^7 |", { style: "swing" });
 */
export function generateEvents(chords: string | Score | unknown, opts: GenerateOptions = {}): NoteEvent[] {
  const score = ensureScore(chords, { timeSignature: opts.timeSignature ?? [4, 4] });
  const source = opts.patternSource ?? getPatternRegistry();
  const resolve = opts.chordResolver ?? ((s: string) => tonalResolver(s));
  const instruments = opts.instruments ?? DEFAULT_INSTRUMENTS;
  const volumes = opts.volumes ?? DEFAULT_VOLUMES;
  const beatsPerBar = score.timeSignature[0];
  const patterns = selectPatterns(source.getPatterns(opts.style ?? "swing"), beatsPerBar);
  const repeats = opts.repeats ?? 1;
  if (!Number.isInteger(repeats)) throw new TypeError(`repeats must be an integer, got ${repeats}`);
  const out: NoteEvent[] = [];
  for (let repeat = 0; repeat < repeats; repeat++) {
    let beat = repeat * score.measures.length * beatsPerBar;
    for (const measure of score.measures) {
      const perChord = measure.length ? pyFloorDiv(beatsPerBar, measure.length) : beatsPerBar;
      measure.forEach((symbol, i) => {
        if (NO_CHORD.has(symbol)) return;
        let notes: readonly number[];
        try {
          notes = resolve(symbol);
        } catch {
          notes = fallbackChordNotes(symbol);
        }
        out.push(...playChord(notes, patterns, beat + i * perChord, perChord, instruments, volumes));
      });
      beat += beatsPerBar;
    }
  }
  return out;
}
