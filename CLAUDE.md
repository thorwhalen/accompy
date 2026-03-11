# accompy — AI Agent Instructions

## What This Project Is

accompy generates backing track audio from chord charts (like a scriptable iReal Pro). Input: chord progressions as strings, Score objects, iReal URLs, or tuples. Output: multi-instrument audio (drums, bass, piano) in styles like swing, bossa, rock, ballad, funk, latin, waltz, blues.

**Version**: 0.3.4 (alpha — breaking changes possible)
**Python**: 3.10+

## Key Entry Points

- `accompy.generate_accompaniment()` — the main API
- `accompy.Score` / `accompy.ensure_score()` — unified chord representation
- `accompy.verify_and_setup()` — setup wizard
- `accompy.pipeline` — type-centric converter pipeline (ChordSheet → Audio)
- `accompy.patterns` — PatternRegistry (MutableMapping) for drum/bass/comp patterns

## Architecture Overview

```
chord input → Score → pattern application → MIDI events → audio synthesis
                        ↑                      ↑              ↑
                   patterns/              renderers/      synthesis/
                   (registry)             (midi.py)       (fluidsynth.py)
```

**Key patterns**: Protocol-oriented (PEP 544), Registry (MutableMapping), Event-based MIDI (yield MidiEvent), Dependency Injection via AccompanimentConfig, Strategy for chord resolvers and synthesis backends.

### Module Map

| Module | Responsibility |
|--------|---------------|
| `base.py` | Score, ChordEvent, AccompanimentConfig, MidiEvent, ensure_score() |
| `main.py` | generate_accompaniment(), MMA integration, play_audio() |
| `patterns/` | PatternRegistry, DrumPattern/BassPattern/CompingPattern, builtin styles |
| `renderers/midi.py` | Event-based MIDI generation from patterns + chords |
| `synthesis/fluidsynth.py` | FluidSynth backend: MIDI → WAV/MP3/FLAC |
| `protocols.py` | ChordResolver, PatternSource, AudioRenderer, SynthesizerBackend |
| `chord_resolution.py` | Pluggable chord-to-notes (tonal, music21, mingus, pychord) |
| `converters.py` | Pipeline types: ChordSequence, NoteSequence, MidiData, AudioData |
| `pipeline.py` | High-level: chords_to_sequence/notes/midi/audio |
| `util.py` | Chord parsing, normalization, iReal URL parsing |
| `setup_utils.py` | verify_and_setup(), diagnose_issues(), SoundFont management |
| `tools.py` | MMA tools, variation generation |

## Documentation

**Read `misc/docs/docs_guide.md` first** — it indexes all documentation with synopses so you can decide what's relevant to your task. Key docs include architecture decisions, refactoring plans, pattern system details, tool compatibility notes, and research on accompaniment systems.

## System Dependencies

accompy needs external (non-Python) dependencies:
- **FluidSynth** — audio synthesis (`brew install fluid-synth` / `apt install fluidsynth`)
- **SoundFont** — instrument samples (~200MB, e.g. MuseScore General)
- **MMA** (optional) — Musical MIDI Accompaniment for professional grooves

Use `accompy.verify_and_setup(interactive=True)` to check/install these.

## Testing

```bash
python -m pytest tests/ -v
```

Tests mock audio rendering (no FluidSynth needed). Test files:
- `test_core.py` (39 tests) — chord normalization, parsing, Score, MIDI, config
- `test_patterns.py` (28 tests) — pattern structures, validation, built-in patterns
- `test_audio_production.py` (25 tests) — full audio workflows, all styles
- `test_converters.py` (13 tests) — converter pipeline
- `test_types.py` (7 tests) — pipeline type validation
- `test_pipeline.py` (4 tests) — high-level API

## Development Rules

1. **Run tests after changes**: `python -m pytest tests/ -v` — all tests must pass
2. **Maintain backward compatibility** during v0.x while architecture stabilizes
3. **Follow existing patterns**: protocols for extensibility, registry for patterns, event iterators for MIDI
4. **Check `dev_plan_2026_01_05.md`** before major refactoring — it has detailed phase-by-phase instructions
5. **Two backends**: "builtin" (pure Python patterns) and "mma" (MMA external tool). Both must work.
6. **Chord input flexibility**: any change must preserve support for strings, Score, tuples, and iReal URLs
