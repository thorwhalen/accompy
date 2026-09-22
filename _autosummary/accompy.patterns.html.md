# accompy.patterns

Pattern registry and access for accompany patterns.

This module provides access to musical patterns (drums, bass, comping) for
different styles. Includes a MutableMapping-based PatternRegistry for
runtime pattern registration.

### Functions

| [`get_pattern_registry`](#accompy.patterns.get_pattern_registry)()                   | Get the global pattern registry, initializing if needed.   |
|-------------------------------------------------------------------------------------------|------------------------------------------------------------|
| [`get_patterns`](#accompy.patterns.get_patterns)(style)                      | Get all patterns for a given style.                        |
| [`register_style`](#accompy.patterns.register_style)(style, drums, bass, comp) | Register a custom style with the global registry.          |

### Classes

| [`DrumPattern`](#accompy.patterns.DrumPattern)(name, beats_per_bar, hits)            | A drum pattern for one or more measures.            |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| [`BassPattern`](#accompy.patterns.BassPattern)(name, notes)                          | A bass pattern template.                            |
| [`CompingPattern`](#accompy.patterns.CompingPattern)(name, hits)                        | A piano/guitar comping (accompaniment) pattern.     |
| [`DrumHit`](#accompy.patterns.DrumHit)(beat, drum, velocity)                     | A single drum hit in a pattern.                     |
| [`NoteEvent`](#accompy.patterns.NoteEvent)(beat, pitch_offset, duration, velocity) | A melodic note event for bass or other instruments. |
| [`PatternRegistry`](#accompy.patterns.PatternRegistry)()                                 | Registry of accompaniment patterns by style.        |

### *class* accompy.patterns.BassPattern(name, notes)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A bass pattern template.

Uses pitch_offset in NoteEvent to specify intervals from the chord root.
The actual pitches are determined when the pattern is applied to specific chords.

### *class* accompy.patterns.CompingPattern(name, hits)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A piano/guitar comping (accompaniment) pattern.

#### name

Pattern identifier

#### hits

Sequence of (beat, duration, velocity) tuples

### *class* accompy.patterns.DrumHit(beat, drum, velocity)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single drum hit in a pattern.

#### beat

Beat position (0-based within measure)

#### drum

MIDI note number for the drum sound

#### velocity

Hit velocity (0-127)

### *class* accompy.patterns.DrumPattern(name, beats_per_bar, hits)

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

### *class* accompy.patterns.NoteEvent(beat, pitch_offset, duration, velocity)

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

### *class* accompy.patterns.PatternRegistry

Bases: [`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

Registry of accompaniment patterns by style.

Implements MutableMapping for intuitive access:

```default
registry['bossa']  # Get patterns
registry['my_style'] = {...}  # Register custom
del registry['my_style']  # Remove
```

### Example

```pycon
>>> registry = PatternRegistry()
>>> registry.register_builtin_patterns()
>>> 'swing' in registry
True
>>> registry['swing']['drums'][0].name
'swing_basic'
```

#### available_styles()

Get list of all available style names.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### get_patterns(style)

Get patterns for a style (PatternSource protocol method).

* **Parameters:**
  **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Style name
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  Dict with ‘drums’, ‘bass’, ‘comp’ keys

#### register_builtin_patterns()

Load all built-in patterns.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### accompy.patterns.get_pattern_registry()

Get the global pattern registry, initializing if needed.

* **Return type:**
  [`PatternRegistry`](#accompy.patterns.PatternRegistry)
* **Returns:**
  The global PatternRegistry instance

### Example

```pycon
>>> registry = get_pattern_registry()
>>> 'swing' in registry
True
```

### accompy.patterns.get_patterns(style)

Get all patterns for a given style.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
* **Returns:**
  Dict with ‘drums’, ‘bass’, ‘comp’ keys containing pattern lists

### Example

```pycon
>>> patterns = get_patterns("bossa")
>>> drums = patterns["drums"][0]
>>> drums.name
'bossa'
```

### accompy.patterns.register_style(style, drums, bass, comp)

Register a custom style with the global registry.

* **Parameters:**
  * **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Style name
  * **drums** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of DrumPattern objects
  * **bass** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of BassPattern objects
  * **comp** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)) – List of CompingPattern objects
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> registry = get_pattern_registry()
>>> register_style('my_funk', [my_drum_pattern], [my_bass_pattern], [])
```

### Modules

| [`builtin`](accompy.patterns.builtin.html.md#module-accompy.patterns.builtin)         | Built-in pattern definitions for all supported styles.   |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------|
| [`dataclasses`](accompy.patterns.dataclasses.html.md#module-accompy.patterns.dataclasses) | Pattern data structures for accompaniment generation.    |
