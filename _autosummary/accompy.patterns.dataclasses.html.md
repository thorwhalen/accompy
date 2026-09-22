# accompy.patterns.dataclasses

Pattern data structures for accompaniment generation.

Contains the core pattern dataclasses: DrumHit, NoteEvent, DrumPattern,
BassPattern, and CompingPattern.

### Classes

| [`BassPattern`](#accompy.patterns.dataclasses.BassPattern)(name, notes)                          | A bass pattern template.                            |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| [`CompingPattern`](#accompy.patterns.dataclasses.CompingPattern)(name, hits)                        | A piano/guitar comping (accompaniment) pattern.     |
| [`DrumHit`](#accompy.patterns.dataclasses.DrumHit)(beat, drum, velocity)                     | A single drum hit in a pattern.                     |
| [`DrumPattern`](#accompy.patterns.dataclasses.DrumPattern)(name, beats_per_bar, hits)            | A drum pattern for one or more measures.            |
| [`NoteEvent`](#accompy.patterns.dataclasses.NoteEvent)(beat, pitch_offset, duration, velocity) | A melodic note event for bass or other instruments. |

### *class* accompy.patterns.dataclasses.BassPattern(name, notes)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A bass pattern template.

Uses pitch_offset in NoteEvent to specify intervals from the chord root.
The actual pitches are determined when the pattern is applied to specific chords.

### *class* accompy.patterns.dataclasses.CompingPattern(name, hits)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A piano/guitar comping (accompaniment) pattern.

#### name

Pattern identifier

#### hits

Sequence of (beat, duration, velocity) tuples

### *class* accompy.patterns.dataclasses.DrumHit(beat, drum, velocity)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single drum hit in a pattern.

#### beat

Beat position (0-based within measure)

#### drum

MIDI note number for the drum sound

#### velocity

Hit velocity (0-127)

### *class* accompy.patterns.dataclasses.DrumPattern(name, beats_per_bar, hits)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A drum pattern for one or more measures.

### Example

```pycon
>>> pattern = DrumPattern("rock", 4, [DrumHit(0, KICK, 100)])
>>> pattern.beats_per_bar
4
```

#### at_tempo(tempo)

Return pattern duration in seconds at a given tempo.

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### *class* accompy.patterns.dataclasses.NoteEvent(beat, pitch_offset, duration, velocity)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A melodic note event for bass or other instruments.

#### beat

Beat position within measure

#### pitch_offset

Offset from chord root in semitones (0=root, 7=5th, etc.)

#### duration

Note duration in beats

#### velocity

Note velocity (0-127)
