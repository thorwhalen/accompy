# Patterns

This document explains the **builtin accompaniment pattern** system.

The core goal is separation of concerns:

- Pattern *definitions* live in `accompy/patterns.py`.
- Pattern *rendering* (turning patterns into MIDI events) lives in `accompy/accompy.py`.

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

Rendering happens in the builtin MIDI generator in `accompy/accompy.py`:

- `_add_drum_pattern(...)` consumes a `DrumPattern`.
- `_add_bass_pattern(...)` consumes a `BassPattern` and uses `chord_notes` to pick chord-appropriate tones.
- `_add_piano_pattern(...)` consumes a `CompingPattern`.

## Extending patterns

To add a new style or groove:

1. Add new `DrumPattern` / `BassPattern` / `CompingPattern` objects in `accompy/patterns.py`.
2. Register them in `DRUM_PATTERNS`, `BASS_PATTERNS`, and `COMP_PATTERNS`.
3. (Optional) Add tests in `tests/test_patterns.py` if you introduce new invariants (e.g. time signature, velocity range).

Design guidance:

- Keep pattern data small and declarative.
- Avoid embedding MIDI rendering logic in `patterns.py`.
- Prefer using `pitch_offset` values that describe musical intent (root/3rd/5th/7th/approach), letting the renderer adapt to chord quality.
