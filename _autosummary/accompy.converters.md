# accompy.converters

Core types for the chord-to-audio pipeline.

Defines the data types that flow through the pipeline, plus a converter
registry that maps (source_type, target_type) pairs to converter functions.

The key types form a DAG:

```default
ChordSheet --> ChordSequence --> NoteSequence --> MidiData --> AudioData

(Plus shortcut converters that skip intermediate steps.)
```

Usage:

```default
>>> from accompy.wips.types import converter, ChordSequence, MidiData
>>> # Get a specific converter
>>> to_midi = converter[ChordSequence, MidiData]
>>> # Or convert in one call
>>> midi = convert(chord_seq, MidiData)
```

### Functions

| [`convert`](#accompy.converters.convert)(source, target_type, \*[, via])   | Convert source to target_type using the registered converter.   |
|--------------------------------------------------------------------------------------------|-----------------------------------------------------------------|

### Classes

| [`AudioData`](#accompy.converters.AudioData)(waveform[, sr])                       | Container for audio data — numpy array + sample rate.                     |
|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`ChordSequence`](#accompy.converters.ChordSequence)(chords[, title, key, tempo, ...]) | Ordered sequence of (chord_symbol, duration_beats) pairs with metadata.   |
| [`ConverterRegistry`](#accompy.converters.ConverterRegistry)()                             | Registry mapping (source_type, target_type) to named converter functions. |
| [`MidiData`](#accompy.converters.MidiData)([bytes_, pretty_midi_obj, tempo, ...]) | Container for MIDI data — either as bytes or as a pretty_midi object.     |
| [`NoteSequence`](#accompy.converters.NoteSequence)(notes[, tempo, time_signature])    | Ordered sequence of (midi_notes, duration_beats) with metadata.           |

### *class* accompy.converters.AudioData(waveform, sr=44100)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Container for audio data — numpy array + sample rate.

```pycon
>>> import numpy as np
>>> ad = AudioData(waveform=np.zeros(44100), sr=44100)
>>> ad.duration_seconds
1.0
```

#### to_wav_bytes()

Convert to WAV file bytes.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

#### write(path)

Write audio to a WAV file. Returns the path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* accompy.converters.ChordSequence(chords, title='', key='C', tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Ordered sequence of (chord_symbol, duration_beats) pairs with metadata.

This is the canonical internal representation of a chord progression.

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 8.0)])
>>> len(cs)
3
>>> cs[0]
('Dm7', 4.0)
>>> cs.total_beats
16.0
```

#### *property* durations *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[float](https://docs.python.org/3/builtins/functions.html#float)]*

Just the durations, without symbols.

#### *property* symbols *: [list](https://docs.python.org/3/builtins/stdtypes.html#list)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

Just the chord symbols, without durations.

#### to_score()

Convert to an accompy Score for pattern-based accompaniment.

### Example

```pycon
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
>>> score = cs.to_score()
>>> len(score)
2
```

### *class* accompy.converters.ConverterRegistry

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Registry mapping (source_type, target_type) to named converter functions.

Supports multiple converters for the same type pair, distinguished by name.
The first registered converter becomes the default.

```pycon
>>> reg = ConverterRegistry()
>>> reg.register(str, int, int, name='builtin')
>>> reg[str, int]('42')
42
>>> reg.list_converters(str, int)
['builtin']
```

#### get(source_type, target_type, name=None)

Get a specific named converter, or the default if name is None.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)

#### list_converters(source_type, target_type)

List available converter names for a type pair.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### list_pairs()

List all registered (source, target) type name pairs.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

#### register(source_type, target_type, func, , name='', is_default=False)

Register a converter function.

* **Parameters:**
  * **source_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The input type
  * **target_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The output type
  * **func** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)) – The converter function (source -> target)
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Name for this converter (defaults to func._\_name_\_)
  * **is_default** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, make this the default converter for this pair
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### set_default(source_type, target_type, name)

Change the default converter for a type pair.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### *class* accompy.converters.MidiData(bytes_=None, pretty_midi_obj=None, tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Container for MIDI data — either as bytes or as a pretty_midi object.

Wraps MIDI content so converters have a uniform interface regardless
of which MIDI library produced the data.

```pycon
>>> import io
>>> md = MidiData(bytes_=b'MThd...', tempo=120)
>>> md.has_bytes
True
```

#### to_bytes()

Get MIDI as bytes, converting from pretty_midi if needed.

* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)

#### to_pretty_midi()

Get as pretty_midi.PrettyMIDI, converting from bytes if needed.

#### write(path)

Write MIDI to a file. Returns the path.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* accompy.converters.NoteSequence(notes, tempo=120, time_signature=(4, 4))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Ordered sequence of (midi_notes, duration_beats) with metadata.

Represents resolved chords — chord symbols have been converted to
concrete MIDI note numbers.

```pycon
>>> ns = NoteSequence([([60, 64, 67], 4.0), ([62, 65, 69], 4.0)])
>>> ns[0]
([60, 64, 67], 4.0)
```

### accompy.converters.convert(source, target_type, , via=None)

Convert source to target_type using the registered converter.

* **Parameters:**
  * **source** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – The source data
  * **target_type** ([`type`](https://docs.python.org/3/builtins/functions.html#type)) – The desired output type
  * **via** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional converter name (uses default if None)
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
* **Returns:**
  Converted data of target_type

Example:

```default
>>> # After converters are registered:
>>> # audio = convert(chord_seq, AudioData)
```
