# accompy.base

Core domain models for accompy.

Contains Score, ChordEvent, AccompanimentConfig and related data structures.

### Functions

| [`ensure_score`](#accompy.base.ensure_score)(chords, \*[, title, key, ...])   | Coerce common chord-progression formats into a `Score`.   |
|------------------------------------------------------------------------------------------------|-----------------------------------------------------------|

### Classes

| [`AccompanimentConfig`](#accompy.base.AccompanimentConfig)([style, tempo, repeats, ...])   | Configuration for accompaniment generation.           |
|------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| [`ChordEvent`](#accompy.base.ChordEvent)(symbol[, beats])                         | A chord at a specific position in the progression.    |
| [`MidiEvent`](#accompy.base.MidiEvent)(time, channel, note, velocity, ...)       | A single MIDI event.                                  |
| [`Score`](#accompy.base.Score)(measures[, title, composer, key, ...])        | A musical score containing chord events and metadata. |

### *class* accompy.base.AccompanimentConfig(style='swing', tempo=120, repeats=2, instruments=<factory>, volumes=<factory>, soundfont=None, sample_rate=44100, output_format='wav', chord_resolver=None, pattern_source=None, synthesis_backend=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Configuration for accompaniment generation.

This is the single source of truth for all configuration options,
including dependency injection hooks for extensibility.

#### style

Musical style (swing, bossa, rock, etc.)

#### tempo

Beats per minute

#### repeats

Number of times to play through the form

#### instruments

Which instruments to include

#### volumes

Relative volume for each instrument (0.0-1.0)

#### soundfont

Path to SoundFont file for synthesis

#### sample_rate

Audio sample rate

#### output_format

Output file format

#### chord_resolver

Optional custom chord resolution function

#### pattern_source

Optional custom pattern provider

#### synthesis_backend

Optional custom synthesis backend

#### with_overrides(\*\*kwargs)

Create a new config with specified overrides.

This enables immutable updates to configuration.

* **Return type:**
  [`AccompanimentConfig`](#accompy.base.AccompanimentConfig)

### Example

```pycon
>>> config = AccompanimentConfig(tempo=120)
>>> fast_config = config.with_overrides(tempo=180)
>>> config.tempo, fast_config.tempo
(120, 180)
```

### *class* accompy.base.ChordEvent(symbol, beats=4)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A chord at a specific position in the progression.

### Example

```pycon
>>> event = ChordEvent("Dm7", beats=4)
>>> event.symbol
'D-7'
```

### *class* accompy.base.MidiEvent(time, channel, note, velocity, duration)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A single MIDI event.

Used for event-based MIDI generation that enables both batch file creation
and future real-time streaming.

#### time

Event time in beats

#### channel

MIDI channel (0-15)

#### note

MIDI note number (0-127)

#### velocity

Note velocity (0-127)

#### duration

Note duration in beats

### *class* accompy.base.Score(measures, title='Untitled', composer='', key='C', time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A musical score containing chord events and metadata.

This is the domain model for chord progressions. It provides a unified
representation regardless of input format (string, iReal URL, tuples, etc.).

### Example

```pycon
>>> score = Score.from_string("| C | Am | F | G |", time_signature=(4, 4))
>>> list(score.measures)
[['C'], ['A-'], ['F'], ['G']]
```

#### *classmethod* from_ireal_url(url)

Parse an iReal Pro URL into a Score.

* **Return type:**
  [`Score`](#accompy.base.Score)

Example::
: url = “irealb://Autumn%20Leaves=…”
  score = Score.from_ireal_url(url)

#### *classmethod* from_string(chord_string, , title='Untitled', key='C', time_signature=(4, 4))

Parse a chord string into a Score.

Supports formats:

- Simple: “C Am F G” (space-separated, one chord per bar)
- Bar lines: “| C | Am | F | G 

  ```
  |
  ```

  ”
- Multi-chord bars: “| C Am | F G 

  ```
  |
  ```

  ” (chords split evenly)
- iReal-style: “C-7 F7 | Bb^7 | Eh7 A7b9 

  ```
  |
  ```

  ”

### Example

```pycon
>>> Score.from_string("| Dm7 | G7 | C^7 | % |").measures  # % means repeat
[['D-7'], ['G7'], ['C^7'], ['C^7']]
```

* **Return type:**
  [`Score`](#accompy.base.Score)

#### to_chord_sequence(, tempo=120)

Convert Score to a ChordSequence (from the converter pipeline).

Each chord gets a duration proportional to its share of the bar.

### Example

```pycon
>>> score = Score.from_string("| Dm7 | G7 | C^7 |")
>>> cs = score.to_chord_sequence(tempo=160)
>>> len(cs)
3
```

### accompy.base.ensure_score(chords, , title='Untitled', key='C', time_signature=(4, 4))

Coerce common chord-progression formats into a `Score`.

Supported inputs:

- `Score`: returned as-is
- `str`: chord string (e.g. `"| C | Am | F | G |"`) OR iReal URL (`irealbook://...`)
- `Iterable[tuple[str, int|float]]`: list of `(chord, beats)` like in `accompany`
- `Iterable[str]`: chord symbols, one per bar
- `list[list[str]]`: already-parsed measures

### Notes

- `Score.measures` in `accompy` does not encode per-chord durations within a bar.
  For `(chord, beats)` inputs, durations not equal to whole bars are approximated
  by grouping chords into bars.

### Examples

```pycon
>>> ensure_score("| C | Am | F | G |", time_signature=(4, 4)).measures
[['C'], ['A-'], ['F'], ['G']]
>>> ensure_score([("F#m7b5", 4), ("B7", 4), ("Em", 8)], key="E").measures[:3]
[['F#h7'], ['B7'], ['E-']]
```

* **Return type:**
  [`Score`](#accompy.base.Score)
