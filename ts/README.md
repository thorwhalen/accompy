# accompy (TypeScript)

Chord charts to accompaniment note events (drums, bass, piano), in the browser or Node. The TypeScript twin of the Python package [accompy](https://github.com/thorwhalen/accompy): same charts in, same events out, held identical by shared golden cases.

```ts
import { generateEvents, beatsToSeconds } from "accompy";

const events = generateEvents("| Dm7 | G7 | Cmaj7 | A7b9 |", { style: "bossa" });
// [{ time: 0, channel: 9, note: 37, velocity: 56, duration: 0.25 }, ...]
const seconds = beatsToSeconds(events[0].time, 120);
```

It produces note events and no sound: play them with Web Audio, a sampler, a soundfont player or Web MIDI. No runtime dependencies; about 12 KB gzipped.

## The note event

```ts
interface NoteEvent {
  time: number;     // start, in beats from the beginning
  channel: number;  // 9 drums, 0 bass, 1 piano (CHANNELS)
  note: number;     // MIDI note (General MIDI percussion on channel 9)
  velocity: number; // 0-127
  duration: number; // in beats
}
```

This is Python's `accompy.MidiEvent`, field for field.

**Guarantees.** Events are a function of the chart, style, repeats, instruments and volumes only:

- **Tempo-free**: nothing in generation reads a tempo; convert beats to seconds at play time (`beatsToSeconds`), so one set of events plays at any tempo.
- **Stateless across chords**: each chord's events depend only on that chord's notes, start and length (no walking-line continuity, voice leading or fills), so rendering a chart a bar at a time with `chordEvents` gives exactly the events of the whole chart.
- **Deterministic**: no randomness.

Events come in generation order (chord by chord; drums, bass, then piano within a chord). Sort by `time` if your scheduler needs it.

## Charts

`generateEvents` and `ensureScore` read every form Python's `ensure_score` reads:

```ts
generateEvents("| C Am | F G |");                     // chart text: bars, chords split the bar
generateEvents("C Am F G");                           // one chord per bar
generateEvents([["C", "Am"], ["F"], ["G7"]]);         // measures
generateEvents(["C", "Am", "F", "G7"]);               // symbols, one per bar
generateEvents([["C", 2], ["G", 2], ["F", 4]]);       // [chord, beats] pairs
generateEvents("irealb://...");                       // an iReal Pro URL (first tune)
generateEvents("| C | G |", { style: "waltz", timeSignature: [3, 4] });
```

`%` and `x` repeat the previous chord; `N.C.` is silent. Symbols are rewritten to iReal spellings (`Cm7` becomes `C-7`, `Cmaj7` becomes `C^7`), and resolved to notes with the tables of the Python `tonal` package.

## One chord at a time

```ts
import { chordEvents, tonalResolver } from "accompy";

chordEvents(tonalResolver("D-7"), { style: "swing", startBeat: 8, duration: 4 });
chordEvents([50, 53, 57, 60], { style: "bossa", startBeat: 0, duration: 2 }); // notes, root first
```

## Styles, patterns and seams

`STYLES` lists the builtin styles (swing, bossa, rock, funk, ballad, latin, waltz, blues); `getPatterns(style)` returns their drum, bass and comping patterns as data. `registerStyle(name, { drums, bass, comp })` adds one, or pass your own `PatternRegistry` as `patternSource`. `chordResolver` replaces the chord-to-notes step. Rhythmic skeletons (`resolveSkeleton`, `applySkeleton`, `listSkeletons`, `registerSkeleton`) restrike `[chord, beats]` pairs on a rhythm such as `"tresillo"` or `"charleston"`.

## Demo

```bash
cd ts && npm install && npm run demo   # http://localhost:5174/demo/
```

A chart box, a style menu and a Play button, with a tiny Web Audio synth (oscillators and noise) that is part of the demo, not the package.

## Parity with Python

- The tables (patterns, skeletons, chord spellings, tonal's chord qualities) are generated from Python into `src/data.generated.ts` by `python -m accompy._codegen`; a Python test fails when that file is stale.
- The golden cases in `../fixtures/cases.json` (about 670 calls over every function above, errors included) are recorded from Python by `python -m accompy._fixtures` and run by both `pytest` and `vitest`, compared as JSON text.
- Python quirks are kept on purpose, so both sides agree: for example `Cdim` normalises to `Cdi-` and then plays the fallback C major triad. Fixes go to the Python side first, then both twins.
- Out of scope: the MMA backend, audio rendering, and the Python converter pipeline's ChordPro, Roman-numeral and Nashville parsers and its pychord/music21/mingus resolvers.

Names are camelCase; Python's keyword arguments are a trailing options object. Python's `KeyError` and `ValueError` are thrown as `RangeError`, `TypeError` as `TypeError`.

## Licence

MIT.
