# accompy.renderers.midi

MIDI event generation (stateless, iterator-based).

This module provides event-based MIDI generation that separates event creation
from file writing, enabling both batch file creation and future real-time streaming.

Key functions:

- generate_midi_events: Pure function that yields MIDI events
- events_to_midi_file: Side-effect function that writes events to a file

### Module Attributes

| [`NO_CHORD_SYMBOLS`](#accompy.renderers.midi.NO_CHORD_SYMBOLS)     | the renderer leaves their beats silent.                                        |
|-----------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`FALLBACK_CHORD_NOTES`](#accompy.renderers.midi.FALLBACK_CHORD_NOTES) | The notes used when the chord resolver cannot read a symbol (a C major triad). |

### Functions

| [`chord_events`](#accompy.renderers.midi.chord_events)(chord_notes, \*[, style, ...])        | The drum, bass and piano events `style` plays over one chord.                      |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`events_to_midi_file`](#accompy.renderers.midi.events_to_midi_file)(events, path, tempo[, ...])    | Write MIDI events to a MIDI file.                                                  |
| [`generate_builtin_midi`](#accompy.renderers.midi.generate_builtin_midi)(score, config, \*, ...)      | Generate a MIDI file using the built-in renderer.                                  |
| [`generate_events`](#accompy.renderers.midi.generate_events)(chords, \*[, style, repeats, ...]) | The note events the builtin backend plays for `chords`, without writing a file.    |
| [`generate_midi_events`](#accompy.renderers.midi.generate_midi_events)(score, config, \*, ...)       | Generate MIDI events from score.                                                   |
| [`select_patterns`](#accompy.renderers.midi.select_patterns)(patterns, beats_per_bar)           | The `(drum, bass, comp)` patterns the renderer plays from a style's pattern lists. |

### accompy.renderers.midi.FALLBACK_CHORD_NOTES *= (48, 52, 55)*

The notes used when the chord resolver cannot read a symbol (a C major triad).

### accompy.renderers.midi.NO_CHORD_SYMBOLS *= ('', 'n', 'N.C.', 'NC')*

the renderer leaves their beats silent.

* **Type:**
  Chord symbols that mean “no chord here”

### accompy.renderers.midi.chord_events(chord_notes, , style='swing', start_beat=0, duration=4, beats_per_bar=4, instruments=None, volumes=None, pattern_source=None)

The drum, bass and piano events `style` plays over one chord.

This is one step of [`generate_midi_events()`](#accompy.renderers.midi.generate_midi_events), which calls it for every chord of
a score: `chord_notes` are the chord’s MIDI notes, root first (what a chord
resolver returns), `start_beat` where the chord starts and `duration` how many
beats it lasts. It reads no tempo and keeps no state between chords.

```pycon
>>> [(e.time, e.channel, e.note) for e in chord_events([48, 52, 55], style="rock",
...     duration=1)]
[(0, 9, 36), (0, 9, 42), (0.5, 9, 42), (0, 0, 36), (0, 1, 60), (0, 1, 64),
 (0, 1, 67)]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`MidiEvent`](accompy.base.html.md#accompy.base.MidiEvent)]

### accompy.renderers.midi.events_to_midi_file(events, path, tempo, time_signature=(4, 4))

Write MIDI events to a MIDI file.

* **Parameters:**
  * **events** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`MidiEvent`](accompy.base.html.md#accompy.base.MidiEvent)]) – Sequence of MIDI events (must be subscriptable, not just iterable)
  * **path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Output file path
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM
  * **time_signature** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Time signature (numerator, denominator)
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created MIDI file

#### NOTE
Requires midiutil: pip install midiutil

### accompy.renderers.midi.generate_builtin_midi(score, config, , pattern_source, chord_resolver)

Generate a MIDI file using the built-in renderer.

This is a convenience function that combines event generation and file writing.

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – Musical score
  * **config** ([`AccompanimentConfig`](accompy.base.html.md#accompy.base.AccompanimentConfig)) – Configuration
  * **pattern_source** – Pattern provider
  * **chord_resolver** – Chord resolution function
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated MIDI file

### accompy.renderers.midi.generate_events(chords, , style='swing', repeats=1, time_signature=(4, 4), instruments=None, volumes=None, pattern_source=None, chord_resolver=None)

The note events the builtin backend plays for `chords`, without writing a file.

`chords` is anything [`accompy.ensure_score()`](accompy.html.md#accompy.ensure_score) accepts (a chord string, an iReal
URL, measures, chord symbols, `(chord, beats)` pairs, a Score);
`time_signature` applies to the forms that do not carry one. Times and durations
are in beats: the events do not depend on tempo. `repeats` defaults to 1, as in
[`accompy.generate_accompaniment()`](accompy.html.md#accompy.generate_accompaniment).

```pycon
>>> events = generate_events("| C | G |", style="bossa")
>>> events[0]
MidiEvent(time=0, channel=9, note=37, velocity=56, duration=0.25)
>>> max(e.time for e in events) < 8
True
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`MidiEvent`](accompy.base.html.md#accompy.base.MidiEvent)]

### accompy.renderers.midi.generate_midi_events(score, config, , pattern_source, chord_resolver)

Generate MIDI events from score.

Yields events in time order. Does NOT write files.
This enables real-time streaming or batch file creation.

* **Parameters:**
  * **score** ([`Score`](accompy.base.html.md#accompy.base.Score)) – Musical score with chord progression
  * **config** ([`AccompanimentConfig`](accompy.base.html.md#accompy.base.AccompanimentConfig)) – Accompaniment configuration
  * **pattern_source** – Source providing patterns (must have get_patterns method)
  * **chord_resolver** – Function to convert chord symbols to MIDI notes
* **Yields:**
  [`MidiEvent`](accompy.base.html.md#accompy.base.MidiEvent) – MidiEvent objects in chronological order
* **Return type:**
  [*Iterator*](https://docs.python.org/3/library/typing.html#typing.Iterator)[[*MidiEvent*](accompy.base.html.md#accompy.base.MidiEvent)]

### Example

```pycon
>>> from accompy.base import Score, AccompanimentConfig
>>> from accompy.patterns import get_patterns
>>> from accompy.chord_resolution import chord_to_notes
>>> score = Score.from_string("| C | Am | F | G |")
>>> config = AccompanimentConfig()
>>> events = generate_midi_events(score, config,
...     pattern_source=type('PS', (), {'get_patterns': get_patterns})(),
...     chord_resolver=chord_to_notes)
>>> first_event = next(events)
```

### accompy.renderers.midi.select_patterns(patterns, beats_per_bar)

The `(drum, bass, comp)` patterns the renderer plays from a style’s pattern lists.

The drum pattern is the first one whose `beats_per_bar` matches (else the first);
bass and comping take the first of their list. A missing one is `None`.

```pycon
>>> from accompy.patterns import get_patterns
>>> [p.name for p in select_patterns(get_patterns("swing"), 4)]
['swing_basic', 'walking', 'swing_comp']
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)
