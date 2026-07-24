# Patterns

This document explains the **builtin accompaniment pattern** system.

The core goal is separation of concerns:

- Pattern *definitions* live in the `accompy/patterns/` package (see `accompy/patterns/builtin.py`).
- Pattern *data structures* live in `accompy/patterns/dataclasses.py`.
- Pattern *rendering* (turning patterns into MIDI events) lives in `accompy/renderers/midi.py`.

## What is a pattern?

A pattern is a small, reusable template that says *when* to play notes (beat offsets), and (for pitched instruments) *which chord-relative tone* to play.

Patterns are grouped by `style` (e.g. `"swing"`, `"bossa"`, `"rock"`).

### Drum patterns

- Dataclass: `DrumPattern`
- Events: `DrumHit(beat, drum, velocity)`

A `DrumPattern` is a list of drum hits within a bar.

### Bass patterns

- Dataclass: `BassPattern`
- Events: `NoteEvent(beat, pitch_offset, duration, velocity)`

For bass, `pitch_offset` is a **semitone offset from the chord root** (0 = root, 7 = fifth, etc.).

Important: Rendering is **chord-aware**. For chord tones that vary by quality (notably the 3rd), the renderer prefers a matching chord tone from `chord_notes`.

Example: a walking pattern may request `pitch_offset=4` ("3rd"), but over a minor chord the renderer will choose the minor 3rd (3 semitones) if it is present in the chord.

### Comping (piano/guitar) patterns

- Dataclass: `CompingPattern`
- Events: tuples `(beat, duration, velocity)`

A comping event triggers a block chord (the current `chord_notes`) at the given beat.

## How patterns are selected

Use `accompy.patterns.get_patterns(style)`.

It returns a dict with these keys:

- `"drums"`: list of `DrumPattern`
- `"bass"`: list of `BassPattern`
- `"comp"`: list of `CompingPattern`

The builtin renderer chooses the first pattern of each category as the default for that style.

## How patterns are rendered

Rendering happens in the builtin MIDI generator in `accompy/renderers/midi.py`:

- `_add_drum_pattern(...)` consumes a `DrumPattern`.
- `_add_bass_pattern(...)` consumes a `BassPattern` and uses `chord_notes` to pick chord-appropriate tones.
- `_add_piano_pattern(...)` consumes a `CompingPattern`.

## Extending patterns

To add a new style or groove:

1. Add new `DrumPattern` / `BassPattern` / `CompingPattern` objects in `accompy/patterns/builtin.py`.
2. Register them in `DRUM_PATTERNS`, `BASS_PATTERNS`, and `COMP_PATTERNS`.
3. (Optional) Add tests in `tests/test_patterns.py` if you introduce new invariants (e.g. time signature, velocity range).

Design guidance:

- Keep pattern data small and declarative.
- Avoid embedding MIDI rendering logic in `accompy/patterns/builtin.py`.
- Prefer using `pitch_offset` values that describe musical intent (root/3rd/5th/7th/approach), letting the renderer adapt to chord quality.

## Rhythmic skeletons

Rhythmic skeletons are a simpler, more abstract layer than the full pattern system. They live in `accompy/rhythmic_skeletons.py` (not in `accompy/patterns/`).

A skeleton is a tuple of durations (in beats) that sum to the measure length — e.g. `(1.5, 1.5, 1)` — describing **when** you strike within a measure and **for how long**, with no pitches, voicings, velocities, or instrument assignments. The same skeleton describes both a Charleston and a tresillo — they differ only in stylistic context.

### Purpose

Skeletons provide a gravitational center for simple chord renderings. Rather than full multi-instrument accompaniment (drums + bass + piano via the pattern system), a skeleton just restrikes block chords with a rhythmic feel. This is useful for:

- Quick chord-chart demos
- Feeding rhythmic seeds to AI generation (e.g., Suno via arioso)
- Providing a lightweight rhythmic "feel" without full arrangement

### Data structure

Each entry in `RHYTHMIC_SKELETONS` is a dict with:

- `pattern`: tuple of float durations summing to `beats_per_measure`
- `name`: human-readable name
- `beats_per_measure`: measure length (4 for 4/4, 3 for 3/4)
- `styles`: list of associated style tags

### Key functions

- `resolve_skeleton(skeleton)` — accepts a key, name, style, or raw tuple; returns a duration tuple
- `apply_skeleton(cs, skeleton)` — expands a `ChordSequence` according to the skeleton, respecting chord boundaries within measures
- `register_skeleton(key, pattern, ...)` — add custom skeletons at runtime
- `list_skeletons(...)` — list available skeleton keys, optionally filtered

### Pipeline integration

`rhythm_to_midi()` and `rhythm_to_audio()` in `accompy/pipeline.py` compose `apply_skeleton` with the existing converter pipeline:

```python
from accompy import rhythm_to_midi

midi = rhythm_to_midi("| Dm7 | G7 | Cmaj7 |", skeleton="tresillo", tempo=120)
```

### Relationship to the full pattern system

| Aspect | Rhythmic skeletons | Full patterns (Drum/Bass/Comp) |
|--------|-------------------|-------------------------------|
| Scope | Duration only | Beat position + pitch/drum + velocity + duration |
| Instruments | Single (block chords) | Multi-instrument (drums, bass, piano) |
| Rendering | Via existing `chords_to_midi` pipeline | Via `renderers/midi.py` event generator |
| Complexity | Minimal seed | Full arrangement |
| Module | `rhythmic_skeletons.py` | `patterns/` subpackage |
