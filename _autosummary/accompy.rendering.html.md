# accompy.rendering

High-quality chord rendering pipeline — from chord charts to AI-enhanced audio.

Collapses the multi-step workflow of rendering MIDI audio and enhancing it via
AI music generation (e.g. Suno) into a single `render_chords()` call.

Pipeline:

```default
chords + params → ChordSequence → MIDI audio (WAV) → AI-enhanced audio (MP3)
```

Quick start:

```default
>>> from accompy.rendering import render_chords
>>> path = render_chords("| Dm7 | G7 | C^7 |", ai_enhance=False)
```

With AI enhancement (requires `arioso` and Suno API key):

```default
>>> path = render_chords(
...     "| Dm7 | G7 | C^7 |",
...     genre="jazz",
...     instruments=["piano", "upright bass", "brushes"],
... )
```

Batch rendering:

```default
>>> paths = render_chords_batch([
...     dict(chords="| Dm7 | G7 | C^7 |", genre="jazz"),
...     dict(chords="| Dm7 | G7 | C^7 |", genre="lofi chill hop"),
... ], bpm=100)
```

### Functions

| [`render_chords`](#accompy.rendering.render_chords)(chords, \*[, ...])                | Render chords to a high-quality audio file, optionally AI-enhanced.                        |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| [`render_chords_batch`](#accompy.rendering.render_chords_batch)(configs, \*\*shared_kwargs) | Run [`render_chords()`](#accompy.rendering.render_chords) for each config dict. |

### accompy.rendering.render_chords(chords, , rhythmic_skeleton='whole_note', bpm=100, transpose=0, n_loops=None, max_seconds=None, ai_enhance=True, suno_mode='cover', prompt_template='{genre} backing track with {instruments}', genre='jazz', instruments=None, audio_weight=0.99, style_weight=0.51, weirdness=0.0, model='', instrumental=True, wait_for_completion=True, poll_interval=15.0, timeout=600.0, chords_to_midi_audio=None, audio_to_enhanced_audio=None, midi_store=None, midi_audio_store=None, enhanced_audio_store=None, resolver=None, midi_gen=None, audio_renderer=None, soundfont=None, sr=44100)

Render chords to a high-quality audio file, optionally AI-enhanced.

* **Parameters:**
  * **chords** – Chord input — string (`"| Dm7 | G7 | C^7 |"`), iReal URL,
    [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence), [`Score`](accompy.base.html.md#accompy.base.Score),
    or list of `(chord, beats)` tuples.
  * **rhythmic_skeleton** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]) – Restrike pattern within each measure.
  * **bpm** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in beats per minute.
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitones to transpose (positive=up, negative=down).
  * **n_loops** ([`int`](https://docs.python.org/3/builtins/functions.html#int) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Explicit number of loops. Mutually exclusive with *max_seconds*.
  * **max_seconds** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Target maximum duration; computes loop count automatically.
    Defaults to 210 (3.5 min) when neither *n_loops* nor *max_seconds*
    is given.
  * **ai_enhance** (`Union`[[`bool`](https://docs.python.org/3/builtins/functions.html#bool), [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – `True` for default Suno enhancement, `False`/`None`
    to skip, or a callable `(audio_path, prompt, **kw) → bytes`.
  * **suno_mode** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – `"cover"` (default, re-generates in style) or `"extend"`.
  * **prompt_template** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Template with `{genre}` and `{instruments}` placeholders.
  * **genre** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Genre/style tags for the AI prompt.
  * **instruments** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Instrument list for the AI prompt. Defaults to
    `["piano", "bass", "drums"]`.
  * **audio_weight** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – How much the source audio influences AI output (0–1).
  * **style_weight** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – How much the style prompt influences AI output (0–1).
  * **weirdness** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Creative deviation for cover mode (0–1).
  * **model** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Suno model version (e.g. `"V4_5"`).
  * **instrumental** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, generate without vocals.
  * **wait_for_completion** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, poll until AI generation is ready.
  * **poll_interval** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds between AI status checks.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Max seconds to wait for AI completion.
  * **chords_to_midi_audio** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)]) – Override for the MIDI audio rendering step.
    Callable: `(ChordSequence, **kw) → AudioData`.
  * **audio_to_enhanced_audio** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)]) – Override for the AI enhancement step.
    Callable: `(audio_path, prompt, **kw) → bytes`.
  * **midi_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Optional store for MIDI files. `None` = don’t persist MIDI.
  * **midi_audio_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Store for rendered MIDI audio. `None` = default
    file store under `~/.local/share/accompy/artifacts/midi_audio/`.
  * **enhanced_audio_store** ([`MutableMapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Store for AI-enhanced audio. `None` = default
    file store under `~/.local/share/accompy/artifacts/enhanced_audio/`.
  * **resolver** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Chord resolver backend name.
  * **midi_gen** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – MIDI generator backend name.
  * **audio_renderer** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Audio renderer backend name.
  * **soundfont** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Path to a SoundFont file.
  * **sr** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Sample rate for MIDI audio rendering.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  Filesystem path to the final audio file.

### accompy.rendering.render_chords_batch(configs, \*\*shared_kwargs)

Run [`render_chords()`](#accompy.rendering.render_chords) for each config dict.

Each dict in *configs* is merged with *shared_kwargs* (per-config values
take priority over shared defaults).

* **Parameters:**
  * **configs** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]) – Iterable of dicts, each containing keyword arguments for
    [`render_chords()`](#accompy.rendering.render_chords).
  * **\*\*shared_kwargs** – Default arguments applied to every config.
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of filesystem paths to the final audio files.

Example:

```default
>>> from itertools import product
>>> configs = [
...     dict(chords="| Dm7 | G7 | C^7 |", genre=g, bpm=b)
...     for g, b in product(["jazz", "lofi"], [100, 120])
... ]
>>> paths = render_chords_batch(configs, ai_enhance=False)
```
