# accompy.pipeline

High-level pipeline API — one-call chord-to-audio conversion.

This module provides convenience functions that compose the registered
converters into complete pipelines. It’s the simplest entry point.

Usage:

```default
>>> from accompy.wips.pipeline import chords_to_midi, chords_to_audio
>>> midi_data = chords_to_midi("| Dm7 | G7 | Cmaj7 |")
>>> midi_data.write("output.mid")

>>> audio = chords_to_audio("| C | Am | F | G |")
>>> audio.write("output.wav")

>>> # Or with explicit control over which backend to use at each step
>>> midi_data = chords_to_midi("| C | Am |", resolver="music21", midi_gen="mido")
```

### Functions

| [`chords_to_audio`](#accompy.pipeline.chords_to_audio)(chords, \*[, resolver, ...])    | Convert chord string to audio.                                         |
|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`chords_to_midi`](#accompy.pipeline.chords_to_midi)(chords, \*[, resolver, ...])     | Convert chord string to MIDI data.                                     |
| [`chords_to_notes`](#accompy.pipeline.chords_to_notes)(chords, \*[, resolver, tempo])  | Convert chord string or ChordSequence to resolved MIDI notes.          |
| [`chords_to_sequence`](#accompy.pipeline.chords_to_sequence)(chords, \*[, parser, ...])   | Parse a chord string into a ChordSequence.                             |
| [`file_to_audio`](#accompy.pipeline.file_to_audio)(filepath, \*[, output_path, ...]) | Convert an iReal Pro HTML/URL file to audio.                           |
| [`file_to_midi`](#accompy.pipeline.file_to_midi)(filepath, \*[, output_path, ...])  | Convert an iReal Pro HTML/URL file to MIDI.                            |
| [`list_available_converters`](#accompy.pipeline.list_available_converters)()                     | List all available converters organized by pipeline stage.             |
| [`midi_to_audio`](#accompy.pipeline.midi_to_audio)(midi_data, \*[, ...])             | Convert MidiData to audio.                                             |
| [`rhythm_to_audio`](#accompy.pipeline.rhythm_to_audio)(chords, \*[, skeleton, ...])    | Convert chords to audio using a rhythmic skeleton for restrike timing. |
| [`rhythm_to_midi`](#accompy.pipeline.rhythm_to_midi)(chords, \*[, skeleton, ...])     | Convert chords to MIDI using a rhythmic skeleton for restrike timing.  |

### accompy.pipeline.chords_to_audio(chords, , resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=120, sr=44100, output_path=None)

Convert chord string to audio.

This is the complete pipeline: parse -> resolve -> MIDI -> audio.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Chord resolver (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator (‘pretty_midi’, ‘midiutil’, ‘mido’)
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer (‘pretty_midi’, ‘fluidsynth’, ‘tonal’)
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to SoundFont file
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write WAV file
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData with waveform and sample rate

```pycon
>>> audio = chords_to_audio("| C | Am | F | G |")
>>> audio.write("output.wav")
```

### accompy.pipeline.chords_to_midi(chords, , resolver=None, midi_gen=None, tempo=120, output_path=None)

Convert chord string to MIDI data.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Resolver name (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator name (‘pretty_midi’, ‘midiutil’, ‘mido’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write MIDI file
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData object

```pycon
>>> md = chords_to_midi("| C | Am | F | G |")
>>> md.to_bytes()[:4]
b'MThd'
```

### accompy.pipeline.chords_to_notes(chords, , resolver=None, tempo=120)

Convert chord string or ChordSequence to resolved MIDI notes.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Resolver name (‘pychord’, ‘music21’, ‘mingus’, ‘tonal’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (used if chords is a string)
* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)
* **Returns:**
  NoteSequence with MIDI note numbers

```pycon
>>> ns = chords_to_notes("| C | Am |")
>>> len(ns)
2
>>> all(0 <= n <= 127 for notes, _ in ns for n in notes)
True
```

### accompy.pipeline.chords_to_sequence(chords, , parser=None, tempo=120, title='', key='C', time_signature=(4, 4))

Parse a chord string into a ChordSequence.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord string in any supported format
  * **parser** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Parser name (‘auto_detect’, ‘plain_text’, ‘chordpro’, ‘musicgen_chord’)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (default 120)
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Song title
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Key signature
  * **time_signature** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Time signature tuple
* **Return type:**
  [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)
* **Returns:**
  ChordSequence with parsed chords

```pycon
>>> cs = chords_to_sequence("| Dm7 | G7 | Cmaj7 |", tempo=140)
>>> cs.symbols
['Dm7', 'G7', 'Cmaj7']
>>> cs.tempo
140
```

### accompy.pipeline.file_to_audio(filepath, , output_path=None, n_repeats=1, transpose=0, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=None, sr=44100)

Convert an iReal Pro HTML/URL file to audio.

Handles:

- iReal Pro HTML files (exported from the app)
- iReal Pro URL strings
- Plain chord text files

Supports repeating the progression and transposing.

* **Parameters:**
  * **filepath** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to an iReal HTML file, or a chord text file
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Where to write audio. If None, uses filepath with .wav extension
  * **n_repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression (default 1)
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose (positive=up, negative=down)
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer backend
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to SoundFont file
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Override BPM (None = use file’s tempo or 120)
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData

Example:

```default
>>> file_to_audio("/path/to/song.html")
>>> file_to_audio("/path/to/song.html", n_repeats=40)
>>> file_to_audio("/path/to/song.html", transpose=5)
```

### accompy.pipeline.file_to_midi(filepath, , output_path=None, n_repeats=1, transpose=0, resolver=None, midi_gen=None, tempo=None)

Convert an iReal Pro HTML/URL file to MIDI.

Same as file_to_audio but outputs MIDI instead.

* **Parameters:**
  * **filepath** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to an iReal HTML file, or a chord text file
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Where to write MIDI. If None, uses filepath with .mid extension
  * **n_repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Override BPM
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData

### accompy.pipeline.list_available_converters()

List all available converters organized by pipeline stage.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Dict mapping stage names to lists of converter names.

```pycon
>>> info = list_available_converters()
>>> 'parsers' in info
True
>>> 'resolvers' in info
True
```

### accompy.pipeline.midi_to_audio(midi_data, , audio_renderer=None, soundfont=None, sr=44100, output_path=None)

Convert MidiData to audio.

* **Parameters:**
  * **midi_data** ([`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)) – MidiData object
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer name
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to SoundFont file
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate
  * **output_path** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Optional path to write WAV file
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData

```pycon
>>> audio = midi_to_audio(some_midi_data)
```

### accompy.pipeline.rhythm_to_audio(chords, , skeleton='whole_note', resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, tempo=120, sr=44100, output_path=None)

Convert chords to audio using a rhythmic skeleton for restrike timing.

Same as [`rhythm_to_midi()`](#accompy.pipeline.rhythm_to_midi) but renders all the way to audio.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string or ChordSequence.
  * **skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Skeleton key, name, style, or duration tuple.
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver name.
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator name.
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer name.
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to SoundFont file.
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate.
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional path to write WAV file.
* **Return type:**
  [`AudioData`](accompy.converters.html.md#accompy.converters.AudioData)
* **Returns:**
  AudioData with waveform and sample rate.

### Example

```pycon
>>> audio = rhythm_to_audio("| C | Am |", skeleton="half_notes")
```

### accompy.pipeline.rhythm_to_midi(chords, , skeleton='whole_note', resolver=None, midi_gen=None, tempo=120, output_path=None)

Convert chords to MIDI using a rhythmic skeleton for restrike timing.

The skeleton defines when chords are struck within each measure. Each
chord is sustained for the skeleton’s duration at that beat position.

* **Parameters:**
  * **chords** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)) – Chord string (e.g., `"| Dm7 | G7 | Cmaj7 |"`) or ChordSequence.
  * **skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Skeleton key, name, style, or duration tuple.
    Defaults to `"whole_note"` (one strike per measure).
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver name (e.g., `"pychord"`, `"tonal"`).
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator name (e.g., `"pretty_midi"`, `"midiutil"`).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – BPM (used if chords is a string).
  * **output_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional path to write MIDI file.
* **Return type:**
  [`MidiData`](accompy.converters.html.md#accompy.converters.MidiData)
* **Returns:**
  MidiData object.

### Example

```pycon
>>> md = rhythm_to_midi("| C | Am | F | G |", skeleton="tresillo")
>>> md.to_bytes()[:4]
b'MThd'
```
