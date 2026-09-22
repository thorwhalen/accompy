# accompy.synthesis

Audio synthesis backends for accompy.

Provides abstraction over different synthesis engines:

- FluidSynth: Default, uses SoundFonts for realistic instrument sounds
- Pyo: Real-time synthesis (future integration with hum package)

The synthesis backends are used to convert MIDI files to audio.

### Functions

| [`get_default_backend`](#accompy.synthesis.get_default_backend)()   | Get the best available synthesis backend.   |
|--------------------------------------------------------------------------|---------------------------------------------|

### Classes

| [`SynthesizerBackend`](#accompy.synthesis.SynthesizerBackend)()   | Abstract base for audio synthesis backends.   |
|-------------------------------------------------------------------------|-----------------------------------------------|

### *class* accompy.synthesis.SynthesizerBackend

Bases: [`ABC`](https://docs.python.org/3/library/abc.html#abc.ABC)

Abstract base for audio synthesis backends.

Subclasses implement specific synthesis engines (FluidSynth, Pyo, etc.).

#### *abstractmethod classmethod* is_available()

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

#### NOTE
Default implementation not provided - subclasses should override
for streaming support.

#### *abstractmethod* render_to_file(midi_path, output_path, , sample_rate=44100)

Render a MIDI file to an audio file.

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path to input MIDI file
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Path for output audio file
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Audio sample rate in Hz
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the created audio file

### accompy.synthesis.get_default_backend()

Get the best available synthesis backend.

* **Return type:**
  [`SynthesizerBackend`](#accompy.synthesis.SynthesizerBackend)
* **Returns:**
  An instance of an available SynthesizerBackend
* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If no synthesis backend is available

### Modules

| [`fluidsynth`](accompy.synthesis.fluidsynth.md#module-accompy.synthesis.fluidsynth)   | FluidSynth synthesis backend.   |
|---------------------------------------------------------------------------------------------------|---------------------------------|
