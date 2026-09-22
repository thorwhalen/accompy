# accompy.tools

Tools for generating accompaniment audio from Score objects.

Provides a pluggable `score_to_wav` engine architecture.  The default engine
uses MMA (Musical MIDI Accompaniment), but any callable with the
[`ScoreToWav`](#accompy.tools.ScoreToWav) signature can be swapped in — including engines built from
accompy’s own converter pipeline.

Quick start:

```default
>>> from accompy import Score, generate_wav
>>> score = Score.from_string("| Dm7 | G7 | C^7 |")
>>> generate_wav(score, "/tmp/test.wav", groove="BossaNova", tempo=140)
```

Using an alternative engine:

```default
>>> from accompy.tools import make_converter_engine, generate_wav
>>> engine = make_converter_engine(resolver="pychord", midi_gen="pretty_midi",
...                                 audio_renderer="fluidsynth")
>>> generate_wav(score, "/tmp/test.wav", score_to_wav=engine, tempo=140)
```

### Module Attributes

| [`generate_mma_wav`](#accompy.tools.generate_mma_wav)(score, output_path, \*[, ...])   | Alias for [`mma_score_to_wav()`](#accompy.tools.mma_score_to_wav).   |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|

### Functions

| [`generate_mma_wav`](#accompy.tools.generate_mma_wav)(score, output_path, \*[, ...])   | Alias for [`mma_score_to_wav()`](#accompy.tools.mma_score_to_wav).                                 |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------|
| [`generate_variations`](#accompy.tools.generate_variations)(score, output_dir, \*[, ...]) | Batch-generate WAV files for many key / tempo / groove combinations.                                           |
| [`generate_wav`](#accompy.tools.generate_wav)(score, output_path, \*[, ...])       | Generate a WAV file from a Score using a pluggable engine.                                                     |
| [`make_converter_engine`](#accompy.tools.make_converter_engine)(\*[, resolver, ...])        | Create a [`ScoreToWav`](#accompy.tools.ScoreToWav) engine from accompy's converter pipeline. |
| [`mma_score_to_wav`](#accompy.tools.mma_score_to_wav)(score, output_path, \*[, ...])   | Render a Score to WAV using MMA (Musical MIDI Accompaniment).                                                  |

### Classes

| [`ScoreToWav`](#accompy.tools.ScoreToWav)(\*args, \*\*kwargs)   | Callable that renders a `Score` to a WAV file.   |
|-----------------------------------------------------------------------------------|--------------------------------------------------|

### *class* accompy.tools.ScoreToWav(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Callable that renders a `Score` to a WAV file.

Any function matching this signature can be used as a `score_to_wav`
engine in [`generate_wav()`](#accompy.tools.generate_wav) and [`generate_variations()`](#accompy.tools.generate_variations).

### accompy.tools.generate_mma_wav(score, output_path, , groove='Swing', tempo=120, repeats=1)

Alias for [`mma_score_to_wav()`](#accompy.tools.mma_score_to_wav).  Kept for backward compatibility.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### accompy.tools.generate_variations(score, output_dir, , keys=('C',), tempos=(120,), grooves=('Swing',), repeats=1, filename_template='{title}_{key}_{tempo}bpm_{groove}.wav', score_to_wav=None)

Batch-generate WAV files for many key / tempo / groove combinations.

Produces one WAV for each `(key, tempo, groove)` triple (cycled from the
shortest sequences).  Useful for creating practice backing-track
collections.

* **Parameters:**
  * **score** ([`Score`](accompy.base.md#accompy.base.Score)) – Base `Score` (will be transposed per key).
  * **output_dir** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Directory for output files.
  * **keys** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Keys to transpose to.
  * **tempos** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]) – Tempos in BPM to cycle through.
  * **grooves** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Groove / style names to cycle through.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of repeats per file.
  * **filename_template** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Template for filenames. Placeholders:
    `{title}`, `{key}`, `{tempo}`, `{groove}`.
  * **score_to_wav** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ScoreToWav`](#accompy.tools.ScoreToWav)]) – Engine callable.  Defaults to [`mma_score_to_wav()`](#accompy.tools.mma_score_to_wav).
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]
* **Returns:**
  List of Paths to successfully generated files.

Example:

```default
>>> from accompy import Score, generate_variations
>>> score = Score.from_string("| C6 | Do | C6/E | Fo |", key="C")
>>> generate_variations(
...     score, "/tmp/variations",
...     keys=["C", "G", "F"],
...     tempos=[100, 120],
...     grooves=["Swing", "BossaNova"],
... )

>>> # With a custom engine:
>>> from accompy.tools import make_converter_engine
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_variations(
...     score, "/tmp/variations",
...     keys=["C", "G"],
...     tempos=[100, 120],
...     grooves=["Swing"],
...     score_to_wav=engine,
... )
```

### accompy.tools.generate_wav(score, output_path, , groove='Swing', tempo=120, repeats=1, score_to_wav=None)

Generate a WAV file from a Score using a pluggable engine.

By default uses MMA (Musical MIDI Accompaniment).  Pass a custom
`score_to_wav` callable to use a different backend — for instance one
built with [`make_converter_engine()`](#accompy.tools.make_converter_engine).

* **Parameters:**
  * **score** ([`Score`](accompy.base.md#accompy.base.Score)) – A `Score` with chord measures.
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Destination WAV file path.
  * **groove** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Groove / style name (interpretation depends on the engine).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression.
  * **score_to_wav** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ScoreToWav`](#accompy.tools.ScoreToWav)]) – Engine callable.  Defaults to [`mma_score_to_wav()`](#accompy.tools.mma_score_to_wav).
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated WAV file.

Example:

```default
>>> from accompy import Score, generate_wav
>>> score = Score.from_string("| Dm7 | G7 | C^7 |")
>>> generate_wav(score, "/tmp/test.wav", groove="BossaNova", tempo=140)
PosixPath('/tmp/test.wav')

>>> # With a custom engine:
>>> from accompy.tools import make_converter_engine
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_wav(score, "/tmp/test.wav", score_to_wav=engine, tempo=140)
```

### accompy.tools.make_converter_engine(, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, sr=44100)

Create a [`ScoreToWav`](#accompy.tools.ScoreToWav) engine from accompy’s converter pipeline.

This wraps the `ChordSequence → NoteSequence → MidiData → AudioData`
converter chain into the same interface that [`generate_wav()`](#accompy.tools.generate_wav) expects,
so you can swap it in place of the default MMA engine.

* **Parameters:**
  * **resolver** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Chord resolver name (e.g. `"pychord"`, `"tonal"`).
  * **midi_gen** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – MIDI generator name (e.g. `"pretty_midi"`, `"midiutil"`).
  * **audio_renderer** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Audio renderer name (e.g. `"fluidsynth"`, `"pretty_midi"`).
  * **soundfont** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Path to a SoundFont file (for FluidSynth-based renderers).
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate.
* **Return type:**
  [`ScoreToWav`](#accompy.tools.ScoreToWav)
* **Returns:**
  A callable matching the [`ScoreToWav`](#accompy.tools.ScoreToWav) protocol.

Example:

```default
>>> engine = make_converter_engine(audio_renderer="fluidsynth")
>>> generate_wav(score, "/tmp/out.wav", score_to_wav=engine, tempo=120)
```

### accompy.tools.mma_score_to_wav(score, output_path, , groove='Swing', tempo=120, repeats=1)

Render a Score to WAV using MMA (Musical MIDI Accompaniment).

Accepts any valid MMA groove name (e.g. `"Bebop"`, `"GypsyJazz"`).
Run `mma -Dg` to list available grooves.

* **Parameters:**
  * **score** ([`Score`](accompy.base.md#accompy.base.Score)) – A `Score` with chord measures.
  * **output_path** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]) – Destination WAV file path.
  * **groove** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – MMA groove name (case-sensitive).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM.
  * **repeats** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of times to repeat the progression.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
* **Returns:**
  Path to the generated WAV file.
* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – If MMA is not installed or the groove is invalid.
