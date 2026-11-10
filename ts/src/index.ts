/**
 * accompy: chord charts to accompaniment note events (drums, bass, piano), in the browser.
 *
 * The TypeScript twin of the Python package `accompy` (same repository): chart parsing,
 * chord resolution, the builtin styles and the rhythmic skeletons, held to Python by the
 * golden cases in `fixtures/cases.json`. It produces timed note events and no audio:
 * render them with Web Audio, a sampler or MIDI. Names are camelCase; Python's
 * keyword arguments are a trailing options object.
 *
 * @example
 * import { generateEvents, beatsToSeconds } from "accompy";
 * const events = generateEvents("| Dm7 | G7 | C^7 |", { style: "bossa" });
 * // [{ time: 0, channel: 9, note: 37, velocity: 56, duration: 0.25 }, ...]
 * const startSeconds = beatsToSeconds(events[0].time, 120);
 */
export {
  ensureScore,
  normalizeChordSymbol,
  parseChordString,
  parseTimeSig,
  scoreFromChordSpecs,
  scoreToChordSequence,
  transposeChord,
  transposeNote,
  transposeScore,
  type ChartOptions,
  type ChordSpec,
  type Score,
} from "./chart.js";
export { parseIrealUrl } from "./ireal.js";
export { tonalResolver, type ChordResolver } from "./resolve.js";
export {
  getPatternRegistry,
  getPatterns,
  PatternRegistry,
  registerStyle,
  selectPatterns,
  STYLES,
  type BassNote,
  type BassPattern,
  type CompingPattern,
  type DrumHit,
  type DrumPattern,
  type PatternSource,
  type StylePatterns,
} from "./patterns.js";
export {
  bassPitch,
  beatsToSeconds,
  CHANNELS,
  compVoicing,
  pitchClasses,
  resolvePitchOffset,
  chordEvents,
  fallbackChordNotes,
  generateEvents,
  type ChordEventsOptions,
  type GenerateOptions,
  type Instruments,
  type NoteEvent,
  type Volumes,
} from "./events.js";
export {
  applySkeleton,
  listSkeletons,
  registerSkeleton,
  resolveSkeleton,
  RHYTHMIC_SKELETONS,
  type Skeleton,
} from "./skeletons.js";
export { DRUMS } from "./data.generated.js";
export { KeyError, ValueError, ZeroDivisionError } from "./py.js";
