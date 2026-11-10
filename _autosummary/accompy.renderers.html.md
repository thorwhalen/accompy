# accompy.renderers

MIDI and MMA rendering backends for accompy.

This module provides different backends for generating MIDI from scores:

- midi: Built-in MIDI generation using midiutil
- mma: MMA (Musical MIDI Accompaniment) backend for more realistic grooves

### Functions

| [`chord_events`](#accompy.renderers.chord_events)(chord_notes, \*[, style, ...])        | The drum, bass and piano events `style` plays over one chord.                      |
|-----------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`bass_pitch`](#accompy.renderers.bass_pitch)(root, chord_notes, pitch_offset)        | The bass note a pattern's `pitch_offset` plays over a chord.                       |
| [`comp_voicing`](#accompy.renderers.comp_voicing)(chord_notes)                          | The notes the piano plays for a chord: its first four notes moved into C4-B4.      |
| [`pitch_classes`](#accompy.renderers.pitch_classes)(notes)                               | Return unique pitch classes (0-11) as a tuple.                                     |
| [`resolve_pitch_offset`](#accompy.renderers.resolve_pitch_offset)(\*, root_pc, chord_pcs, ...)  | Resolve a pitch offset against a chord.                                            |
| [`generate_events`](#accompy.renderers.generate_events)(chords, \*[, style, repeats, ...]) | The note events the builtin backend plays for `chords`, without writing a file.    |
| [`select_patterns`](#accompy.renderers.select_patterns)(patterns, beats_per_bar)           | The `(drum, bass, comp)` patterns the renderer plays from a style's pattern lists. |
| [`generate_midi_events`](#accompy.renderers.generate_midi_events)(score, config, \*, ...)       | Generate MIDI events from score.                                                   |
| [`events_to_midi_file`](#accompy.renderers.events_to_midi_file)(events, path, tempo[, ...])    | Write MIDI events to a MIDI file.                                                  |

### accompy.renderers.bass_pitch(root, chord_notes, pitch_offset)

The bass note a pattern’s `pitch_offset` plays over a chord.

The chord’s root is moved to C2-B2, then the offset is resolved against the chord
([`resolve_pitch_offset()`](#accompy.renderers.resolve_pitch_offset)), so a pattern’s “3rd” follows the chord’s quality.

```pycon
>>> bass_pitch(57, [57, 60, 64], 4), bass_pitch(48, [48, 52, 55], 4)
(48, 40)
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### accompy.renderers.chord_events(chord_notes, , style='swing', start_beat=0, duration=4, beats_per_bar=4, instruments=None, volumes=None, pattern_source=None)

The drum, bass and piano events `style` plays over one chord.

This is one step of [`generate_midi_events()`](#accompy.renderers.generate_midi_events), which calls it for every chord of
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

### accompy.renderers.comp_voicing(chord_notes)

The notes the piano plays for a chord: its first four notes moved into C4-B4.

A chord with no notes is voiced as a C major triad.

```pycon
>>> comp_voicing([50, 53, 57, 60, 64]), comp_voicing([])
([62, 65, 69, 60], [60, 64, 67])
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

### accompy.renderers.events_to_midi_file(events, path, tempo, time_signature=(4, 4))

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

### accompy.renderers.generate_events(chords, , style='swing', repeats=1, time_signature=(4, 4), instruments=None, volumes=None, pattern_source=None, chord_resolver=None)

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

### accompy.renderers.generate_midi_events(score, config, , pattern_source, chord_resolver)

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

### accompy.renderers.pitch_classes(notes)

Return unique pitch classes (0-11) as a tuple.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### accompy.renderers.resolve_pitch_offset(, root_pc, chord_pcs, target_offset)

Resolve a pitch offset against a chord.

The patterns use semitone offsets (0=root, 7=5th, etc.). When an offset
represents a chord tone which varies by quality (e.g. 3rd), we prefer a
matching chord tone from `chord_pcs`.

### Examples

For a minor chord, a pattern might request offset 4 (“3rd”); this
function will choose 3 if the chord contains a minor 3rd.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### accompy.renderers.select_patterns(patterns, beats_per_bar)

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

### Modules

| [`midi`](accompy.renderers.midi.html.md#module-accompy.renderers.midi)   | MIDI event generation (stateless, iterator-based).   |
|---------------------------------------------------------------------------------------|------------------------------------------------------|
