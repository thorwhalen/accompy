# accompy.main

Main accompaniment generation module.

Integrates all components (patterns, chord resolution, MIDI rendering,
synthesis) to provide the main accompy API.

### Functions

| [`check_dependencies`](#accompy.main.check_dependencies)()                             | Check which dependencies are available.                        |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------|
| [`generate_accompaniment`](#accompy.main.generate_accompaniment)(chords, \*[, style, ...]) | Generate an accompaniment audio file from a chord progression. |
| [`play_audio`](#accompy.main.play_audio)(audio_path)                           | Play an audio file using the system's default audio player.    |
| [`print_setup_instructions`](#accompy.main.print_setup_instructions)()                       | Print installation instructions for missing dependencies.      |

### accompy.main.check_dependencies()

Check which dependencies are available.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]
* **Returns:**
  Dict mapping dependency name to availability status

### Example

```pycon
>>> deps = check_dependencies()
>>> 'midiutil' in deps
True
```

### accompy.main.generate_accompaniment(chords, , style='swing', tempo=120, repeats=1, output_path=None, output_format=None, config=None, use_mma=True, backend=None, autoplay=False)

Generate an accompaniment audio file from a chord progression.

This is the main entry point for accompy. It generates backing tracks
with bass, drums, and piano from chord progressions.

* **Parameters:**
  * **chords** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Chord progression (string, Score, list of tuples, iReal URL)
  * **style** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'swing'`, `'bossa'`, `'rock'`, `'ballad'`, `'funk'`, `'latin'`, `'waltz'`, `'blues'`]) – Musical style (swing, bossa, rock, ballad, funk, latin, waltz, blues)
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Where to save the file (None = temp file)
  * **output_format** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'wav'`, `'mp3'`, `'flac'`, `'midi'`, `'mid'`]]) – Output format (wav, mp3, flac, midi)
  * **config** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`AccompanimentConfig`](accompy.base.md#accompy.base.AccompanimentConfig)]) – Full configuration object (overrides other params if provided)
  * **use_mma** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True and MMA available, use MMA backend
  * **backend** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'auto'`, `'mma'`, `'builtin'`]]) – Explicitly select backend (‘auto’, ‘mma’, ‘builtin’)
  * **autoplay** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, automatically play the generated audio
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated audio/MIDI file

### Example

```pycon
>>> from accompy import generate_accompaniment
>>> path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=140)
>>> print(f"Generated: {path}")
```

#### NOTE
Requires FluidSynth and a SoundFont for audio rendering.
For MIDI-only output, use output_format=”midi”.

### accompy.main.play_audio(audio_path)

Play an audio file using the system’s default audio player.

* **Parameters:**
  **audio_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Path to the audio file
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
* **Returns:**
  True if playback started successfully, False otherwise

### Example

```pycon
>>> from accompy import play_audio
>>> play_audio("/path/to/audio.wav")
```

### accompy.main.print_setup_instructions()

Print installation instructions for missing dependencies.
