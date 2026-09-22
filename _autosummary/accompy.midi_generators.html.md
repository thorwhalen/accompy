# accompy.midi_generators

MIDI generators — convert NoteSequence to MidiData.

Registered converters: NoteSequence -> MidiData

Multiple backends:

- pretty_midi: most Pythonic API, good for programmatic construction
- midiutil: accompy’s existing dependency, simpler
- mido: lowest-level, message-based

Also provides ChordSequence -> MidiData shortcut converters that
combine chord resolution + MIDI generation in one step.

### Functions

| [`chordseq_to_midi_builtin_accompaniment`](#accompy.midi_generators.chordseq_to_midi_builtin_accompaniment)(cs, \*)   | Convert ChordSequence to multi-track MIDI using accompy's pattern engine.   |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`chordseq_to_midi_mma`](#accompy.midi_generators.chordseq_to_midi_mma)(cs, \*[, style, repeats])   | Convert ChordSequence to MIDI using MMA (Musical MIDI Accompaniment).       |
| [`noteseq_to_midi_midiutil`](#accompy.midi_generators.noteseq_to_midi_midiutil)(ns)                     | Convert NoteSequence to MidiData using midiutil (MIDIFile).                 |
| [`noteseq_to_midi_mido`](#accompy.midi_generators.noteseq_to_midi_mido)(ns)                         | Convert NoteSequence to MidiData using mido.                                |
| [`noteseq_to_midi_pretty_midi`](#accompy.midi_generators.noteseq_to_midi_pretty_midi)(ns, \*[, ...])       | Convert NoteSequence to MidiData using pretty_midi.                         |

### accompy.midi_generators.chordseq_to_midi_builtin_accompaniment(cs, , style='swing', repeats=1)

Convert ChordSequence to multi-track MIDI using accompy’s pattern engine.

This bridges the converter pipeline to the existing pattern-based
accompaniment engine (drums, bass, piano).

* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
>>> md = chordseq_to_midi_builtin_accompaniment(cs, style="swing")
>>> md.has_bytes
True
```

### accompy.midi_generators.chordseq_to_midi_mma(cs, , style='swing', repeats=1)

Convert ChordSequence to MIDI using MMA (Musical MIDI Accompaniment).

MMA generates sophisticated multi-instrument accompaniment patterns
from chord symbols, similar to Band-in-a-Box.

Requires: `mma` CLI on PATH.
See [https://www.mellowood.ca/mma/](https://www.mellowood.ca/mma/) for installation.

* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
>>> md = chordseq_to_midi_mma(cs, style="swing")
```

### accompy.midi_generators.noteseq_to_midi_midiutil(ns)

Convert NoteSequence to MidiData using midiutil (MIDIFile).

* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)

```pycon
>>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
>>> md = noteseq_to_midi_midiutil(ns)
>>> md.has_bytes
True
```

### accompy.midi_generators.noteseq_to_midi_mido(ns)

Convert NoteSequence to MidiData using mido.

* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)

```pycon
>>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
>>> md = noteseq_to_midi_mido(ns)
>>> md.has_bytes
True
```

### accompy.midi_generators.noteseq_to_midi_pretty_midi(ns, , program=0, instrument_name='Piano')

Convert NoteSequence to MidiData using pretty_midi.

Renders each chord as a block of simultaneous notes.

* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)

```pycon
>>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
>>> md = noteseq_to_midi_pretty_midi(ns)
>>> md.has_pretty_midi
True
```
