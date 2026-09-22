# accompy.renderers

MIDI and MMA rendering backends for accompy.

This module provides different backends for generating MIDI from scores:

- midi: Built-in MIDI generation using midiutil
- mma: MMA (Musical MIDI Accompaniment) backend for more realistic grooves

### Functions

| [`generate_midi_events`](#accompy.renderers.generate_midi_events)(score, config, \*, ...)    | Generate MIDI events from score.   |
|--------------------------------------------------------------------------------------------------|------------------------------------|
| [`events_to_midi_file`](#accompy.renderers.events_to_midi_file)(events, path, tempo[, ...]) | Write MIDI events to a MIDI file.  |

### accompy.renderers.events_to_midi_file(events, path, tempo, time_signature=(4, 4))

Write MIDI events to a MIDI file.

* **Parameters:**
  * **events** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`MidiEvent`](accompy.base.md#accompy.base.MidiEvent)]) – Sequence of MIDI events (must be subscriptable, not just iterable)
  * **path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Output file path
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM
  * **time_signature** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Time signature (numerator, denominator)
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created MIDI file

#### NOTE
Requires midiutil: pip install midiutil

### accompy.renderers.generate_midi_events(score, config, , pattern_source, chord_resolver)

Generate MIDI events from score.

Yields events in time order. Does NOT write files.
This enables real-time streaming or batch file creation.

* **Parameters:**
  * **score** ([`Score`](accompy.base.md#accompy.base.Score)) – Musical score with chord progression
  * **config** ([`AccompanimentConfig`](accompy.base.md#accompy.base.AccompanimentConfig)) – Accompaniment configuration
  * **pattern_source** – Source providing patterns (must have get_patterns method)
  * **chord_resolver** – Function to convert chord symbols to MIDI notes
* **Yields:**
  MidiEvent objects in chronological order
* **Return type:**
  [*Iterator*](https://docs.python.org/3/library/typing.html#typing.Iterator)[[*MidiEvent*](accompy.base.md#accompy.base.MidiEvent)]

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

### Modules

| [`midi`](accompy.renderers.midi.md#module-accompy.renderers.midi)   | MIDI event generation (stateless, iterator-based).   |
|---------------------------------------------------------------------------------------|------------------------------------------------------|
