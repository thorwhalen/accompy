# accompy.synthesis.fluidsynth

FluidSynth synthesis backend.

Uses FluidSynth with SoundFonts to render MIDI to high-quality audio.
FluidSynth is the default and most widely-supported backend for accompy.

### Functions

| [`convert_audio`](#accompy.synthesis.fluidsynth.convert_audio)(input_path, output_path)   | Convert audio between formats using ffmpeg or pydub.   |
|-------------------------------------------------------------------------------------------|--------------------------------------------------------|
| [`find_default_soundfont`](#accompy.synthesis.fluidsynth.find_default_soundfont)()                 | Find the default SoundFont file in standard locations. |

### Classes

| [`FluidSynthBackend`](#accompy.synthesis.fluidsynth.FluidSynthBackend)([soundfont_path])   | FluidSynth-based synthesis.   |
|----------------------------------------------------------------------------------------|-------------------------------|

### *class* accompy.synthesis.fluidsynth.FluidSynthBackend(soundfont_path=None)

Bases: [`SynthesizerBackend`](accompy.synthesis.md#accompy.synthesis.SynthesizerBackend)

FluidSynth-based synthesis.

Uses SoundFont files (.sf2) to render MIDI with realistic instrument sounds.
Supports both Python wrapper (midi2audio) and command-line FluidSynth.

### Example

```pycon
>>> backend = FluidSynthBackend()
>>> backend.render_to_file(midi_path, output_path)
```

#### *classmethod* is_available()

Check if FluidSynth is available.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### render_to_file(midi_path, output_path, , sample_rate=44100)

Render MIDI file to audio using FluidSynth.

Tries Python wrapper (midi2audio) first, then falls back to command-line FluidSynth.

* **Parameters:**
  * **midi_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Input MIDI file
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Output audio file (.wav, .mp3, .flac)
  * **sample_rate** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate in Hz
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to created audio file

### accompy.synthesis.fluidsynth.convert_audio(input_path, output_path)

Convert audio between formats using ffmpeg or pydub.

* **Parameters:**
  * **input_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Input audio file
  * **output_path** ([`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Output audio file
* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If neither ffmpeg nor pydub is available
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### accompy.synthesis.fluidsynth.find_default_soundfont()

Find the default SoundFont file in standard locations.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]
* **Returns:**
  Path to SoundFont file, or None if not found
