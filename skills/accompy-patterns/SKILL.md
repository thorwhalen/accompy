---
name: accompy-patterns
description: Use when creating, modifying, or debugging musical patterns (drum, bass, comping, rhythmic skeletons) in the accompy pattern system. Triggers on DrumPattern, BassPattern, CompingPattern, PatternRegistry, rhythmic_skeletons, resolve_skeleton, apply_skeleton, rhythm_to_midi, or when working with accompy/patterns/ or accompy/rhythmic_skeletons.py.
---

# accompy Pattern System

## Architecture

Patterns are separated into three concerns:
- **Data structures**: `accompy/patterns/dataclasses.py` — `DrumPattern`, `BassPattern`, `CompingPattern`
- **Built-in patterns**: `accompy/patterns/builtin.py` — predefined patterns for each style
- **Registry**: `accompy/patterns/__init__.py` — `PatternRegistry` (MutableMapping interface)
- **Rendering**: `accompy/renderers/midi.py` — turns patterns into MidiEvent iterators

## Pattern Dataclasses

### DrumPattern
```python
@dataclass(frozen=True)
class DrumPattern:
    hits: tuple[DrumHit, ...]  # (beat, drum, velocity) per hit
    time_signature: tuple[int, int] = (4, 4)
```

### BassPattern
```python
@dataclass(frozen=True)
class BassPattern:
    notes: tuple[BassNote, ...]  # (beat, pitch_offset, velocity, duration)
    time_signature: tuple[int, int] = (4, 4)
```
`pitch_offset` is relative to chord root (0=root, 7=fifth, etc. in semitones).

### CompingPattern
```python
@dataclass(frozen=True)
class CompingPattern:
    events: tuple[CompEvent, ...]  # (beat, velocity, duration)
    time_signature: tuple[int, int] = (4, 4)
```

## Creating a New Pattern

1. Define it in `accompy/patterns/builtin.py` following existing examples
2. Register it in the `BUILTIN_PATTERNS` dict keyed by style name
3. Each style needs all three: drum, bass, and comping patterns
4. Patterns are frozen dataclasses — immutable by design

## Registry Usage

```python
from accompy.patterns import pattern_registry

pattern_registry["my_style"] = {"drums": my_drum, "bass": my_bass, "comping": my_comp}
del pattern_registry["my_style"]  # remove
```

## Rhythmic Skeletons

A simpler, more abstract layer than full patterns. Lives in `accompy/rhythmic_skeletons.py`.

A skeleton is a tuple of beat durations summing to the measure length (e.g. `(1.5, 1.5, 1)`) — no pitches, velocities, or instruments. It defines *when* to restrike block chords within a measure.

### Key functions
- `resolve_skeleton(skeleton)` — accepts key (`"tresillo"`), name (`"Charleston"`), style (`"reggae"`), or raw tuple
- `apply_skeleton(cs, skeleton)` — expands a `ChordSequence`, respecting chord boundaries within measures
- `register_skeleton(key, pattern, ...)` — add custom skeletons at runtime
- `list_skeletons(...)` — list keys, optionally filtered by `beats_per_measure` or `style`

### Pipeline
- `rhythm_to_midi(chords, skeleton=..., ...)` — applies skeleton then runs `chords_to_midi`
- `rhythm_to_audio(chords, skeleton=..., ...)` — same, renders to audio

### Data: `RHYTHMIC_SKELETONS` dict
~30 built-in entries (whole_note, tresillo, charleston, waltz variants, etc.). Each has `pattern`, `name`, `beats_per_measure`, `styles`.

### Tests
`python -m pytest tests/test_rhythmic_skeletons.py -v`

## Rules

- All pattern dataclasses must be frozen (immutable)
- Beat positions are float (0.0 = beat 1, 1.0 = beat 2, etc.)
- Velocity range: 0-127 (MIDI standard)
- Duration in beats (float)
- Always provide all three instrument patterns for a style
- Rhythmic skeletons: durations must be positive and sum to `beats_per_measure`
- Test patterns: `python -m pytest tests/test_patterns.py -v`
- Test skeletons: `python -m pytest tests/test_rhythmic_skeletons.py -v`
