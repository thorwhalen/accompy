# Pipeline Architecture: Chord-to-Audio Conversion System

## Overview

The `accompy.wips` package implements a **type-centric, registry-based pipeline** for converting chord progressions to audio. The key insight is that there are **5 distinct data types** on the path from chord notation to audio, and **many interchangeable converter functions** between them.

## The Type Pipeline

```
ChordSheet (str)          Raw text in any notation format
    |
    v  [parsers: auto_detect, plain_text, chordpro, musicgen_chord]
ChordSequence             List of (chord_symbol, duration_beats) with metadata
    |
    v  [resolvers: pychord, music21, mingus, tonal]
NoteSequence              List of (midi_notes, duration_beats)
    |
    v  [midi_generators: pretty_midi, midiutil, mido]
MidiData                  MIDI bytes or pretty_midi object
    |
    v  [audio_renderers: pretty_midi, fluidsynth, tonal]
AudioData                 numpy waveform array + sample rate
```

Plus **shortcut converters** that skip intermediate steps:
- `ChordSequence -> MidiData` (combines resolver + MIDI gen)
- `ChordSequence -> AudioData` (combines resolver + MIDI gen + audio renderer)

## Core Design Principles

### 1. Explicit Types
Each pipeline stage has a dedicated dataclass (`ChordSequence`, `NoteSequence`, `MidiData`, `AudioData`). This makes data flow visible and testable.

### 2. Converter Registry
All converters are registered in a global `ConverterRegistry` keyed by `(source_type, target_type)`. Multiple converters can be registered for the same type pair, distinguished by name:

```python
from accompy.wips.types import converter

# Get the default converter
to_notes = converter[ChordSequence, NoteSequence]

# Get a specific named converter
to_notes_m21 = converter.get(ChordSequence, NoteSequence, "music21")

# List all available converters for a pair
converter.list_converters(ChordSequence, NoteSequence)
# -> ['pychord', 'music21', 'mingus', 'tonal']
```

### 3. DRY via Factories
The `_make_sequence_converter()` and `_make_chordseq_to_midi()` factories avoid repeating the same boilerplate for each backend. A single-chord resolver is wrapped into a full-sequence converter automatically.

### 4. Dependency Injection by Name
Users select backends by name string, not by importing specific implementations:

```python
from accompy.wips.pipeline import chords_to_midi

# Use defaults
md = chords_to_midi("| C | Am | F | G |")

# Or specify every backend explicitly
md = chords_to_midi("| C | Am |", resolver="music21", midi_gen="mido")
```

## Module Layout

```
accompy/wips/
├── __init__.py          # Package docstring
├── types.py             # Core types (ChordSequence, NoteSequence, MidiData, AudioData)
│                        # + ConverterRegistry + global `converter` instance
├── chord_parsers.py     # ChordSheet -> ChordSequence converters
├── chord_resolvers.py   # ChordSequence -> NoteSequence converters
├── midi_generators.py   # NoteSequence -> MidiData converters
├── audio_renderers.py   # MidiData -> AudioData converters
└── pipeline.py          # High-level API (chords_to_midi, chords_to_audio, etc.)
```

## Converter Inventory

### Parsers (str -> ChordSequence)
| Name | Input Format | Example |
|------|-------------|---------|
| `auto_detect` | Any format (auto-detected) | `"| C | Am |"` |
| `plain_text` | Bar-line or space-separated | `"| Dm7 | G7 | Cmaj7 |"` |
| `chordpro` | ChordPro notation | `"[Am]Hello [G]world"` |
| `musicgen_chord` | MusicGen-Chord text | `"C D:min G:7 C"` |

### Resolvers (ChordSequence -> NoteSequence)
| Name | Backend | Strengths |
|------|---------|-----------|
| `pychord` | pychord | Lightweight, good standard chord coverage |
| `music21` | music21 | Most comprehensive, handles altered/extended chords |
| `mingus` | mingus | Pure Python, no C dependencies |
| `tonal` | tonal (thorwhalen) | Existing accompy dependency |

### MIDI Generators (NoteSequence -> MidiData)
| Name | Backend | Notes |
|------|---------|-------|
| `pretty_midi` | pretty_midi | Most Pythonic API, good for programmatic work |
| `midiutil` | midiutil | Existing accompy dep, simpler API |
| `mido` | mido | Lowest-level, message-based |

### Audio Renderers (MidiData -> AudioData)
| Name | Backend | Notes |
|------|---------|-------|
| `pretty_midi` | pyfluidsynth | Default. Uses FluidSynth C library via Python binding |
| `fluidsynth` | FluidSynth CLI | Calls `fluidsynth` binary directly |
| `tonal` | tonal.midi_to_wav | Uses tonal package's built-in converter |

## Testing

98 tests across 3 test files:
- `test_wips_types.py` — 26 tests for core types and registry
- `test_wips_converters.py` — 48 tests for all converters + consistency checks
- `test_wips_pipeline.py` — 24 tests for high-level API + real-world progressions

All 4 chord resolvers are cross-validated: they must agree on pitch classes for common chords and produce valid MIDI range (0-127).

## Future Directions

### Additional converters to add:
- **DawDreamer** audio renderer (VST hosting, highest quality)
- **MMA** MIDI generator (sophisticated accompaniment patterns)
- **MusicGen-Chord** direct chord-to-audio (AI-based, skip MIDI)
- **Score** format from existing accompy (bridge to accompaniment patterns)

### Integration with existing accompy:
The `accompy.wips` types can be bridged to `accompy.base.Score`:
- `ChordSequence` -> `Score` (for use with existing pattern engine)
- `Score` -> `ChordSequence` (for use with new converter pipeline)
