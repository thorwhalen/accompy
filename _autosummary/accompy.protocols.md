# accompy.protocols

Protocols defining extensibility contracts for accompy.

These protocols (structural interfaces) enable dependency injection and
allow users to provide custom implementations of core components.

Key protocols:

- ChordResolver: Convert chord symbols to MIDI notes
- PatternSource: Provide patterns for styles
- MidiEventGenerator: Generate MIDI events from scores
- AudioRenderer: Render MIDI to audio

See PEP 544 for more on Protocol types.

### Classes

| [`AudioRenderer`](#accompy.protocols.AudioRenderer)(\*args, \*\*kwargs)      | Renders MIDI events to audio.                  |
|-----------------------------------------------------------------------------------------|------------------------------------------------|
| [`ChordResolver`](#accompy.protocols.ChordResolver)(\*args, \*\*kwargs)      | Convert chord symbols to MIDI note numbers.    |
| [`MidiEventGenerator`](#accompy.protocols.MidiEventGenerator)(\*args, \*\*kwargs) | Generates MIDI events from score and patterns. |
| [`PatternSource`](#accompy.protocols.PatternSource)(\*args, \*\*kwargs)      | Provides musical patterns for a given style.   |
| [`SynthesizerBackend`](#accompy.protocols.SynthesizerBackend)(\*args, \*\*kwargs) | Audio synthesis backend.                       |

### *class* accompy.protocols.AudioRenderer(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Renders MIDI events to audio.

This protocol abstracts audio synthesis, enabling:

- Different synthesis backends (FluidSynth, Pyo, etc.)
- Real-time vs. batch rendering
- Alternative output formats

#### render(events, config)

Render MIDI events to PCM audio data.

* **Parameters:**
  * **events** ([`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`MidiEvent`](accompy.base.md#accompy.base.MidiEvent)]) – Iterator of MIDI events
  * **config** ([`AccompanimentConfig`](accompy.base.md#accompy.base.AccompanimentConfig)) – Rendering configuration (tempo, sample rate, etc.)
* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)
* **Returns:**
  Raw PCM audio bytes

#### render_to_file(events, config, output_path)

Render MIDI events directly to an audio file.

* **Parameters:**
  * **events** ([`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`MidiEvent`](accompy.base.md#accompy.base.MidiEvent)]) – Iterator of MIDI events
  * **config** ([`AccompanimentConfig`](accompy.base.md#accompy.base.AccompanimentConfig)) – Rendering configuration
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Where to save the audio file
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created file

### *class* accompy.protocols.ChordResolver(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Convert chord symbols to MIDI note numbers.

Example implementation:

```pycon
>>> def my_resolver(symbol: str) -> list[int]:
...     # Return MIDI notes for chord
...     return [60, 64, 67]  # C major
```

### *class* accompy.protocols.MidiEventGenerator(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Generates MIDI events from score and patterns.

This protocol enables alternative MIDI generation strategies
(e.g., more sophisticated voicings, real-time adaptation).

#### generate(score, config, , chord_resolver, pattern_source)

Generate MIDI events from a score.

* **Parameters:**
  * **score** ([`Score`](accompy.base.md#accompy.base.Score)) – Musical score with chord progression
  * **config** ([`AccompanimentConfig`](accompy.base.md#accompy.base.AccompanimentConfig)) – Accompaniment configuration
  * **chord_resolver** ([`ChordResolver`](#accompy.protocols.ChordResolver)) – Function to resolve chords to notes
  * **pattern_source** ([`PatternSource`](#accompy.protocols.PatternSource)) – Source of musical patterns
* **Yields:**
  MidiEvent objects in time order
* **Return type:**
  [*Iterator*](https://docs.python.org/3/library/typing.html#typing.Iterator)[[*MidiEvent*](accompy.base.md#accompy.base.MidiEvent)]

### *class* accompy.protocols.PatternSource(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Provides musical patterns for a given style.

### Example

```pycon
>>> class MyPatternSource:
...     def get_patterns(self, style: str) -> dict:
...         return {'drums': [...], 'bass': [...], 'comp': [...]}
...     def available_styles(self) -> list[str]:
...         return ['swing', 'bossa']
```

#### available_styles()

List all available style names.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of style names

#### get_patterns(style)

Get patterns for a style.

* **Parameters:**
  **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Style name (e.g., “swing”, “bossa”, “rock”)
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)]
* **Returns:**
  Dict with ‘drums’, ‘bass’, ‘comp’ keys containing pattern lists

### *class* accompy.protocols.SynthesizerBackend(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Audio synthesis backend.

Simpler protocol than AudioRenderer, focused just on synthesis.
Used by the synthesis module.

#### *classmethod* is_available()

Check if this backend’s dependencies are installed.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if the backend can be used

#### render_to_bytes(midi_path, , sample_rate=44100)

Render a MIDI file to PCM bytes (for streaming).

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path to MIDI file
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio sample rate
* **Return type:**
  [`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)
* **Returns:**
  Raw PCM audio bytes

#### render_to_file(midi_path, output_path, , sample_rate=44100)

Render a MIDI file to audio.

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path to MIDI file
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Where to save audio
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio sample rate
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created audio file
