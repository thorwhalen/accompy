# accompy.songs

Songs as backing-track input: a `songleaf` Song becomes a ChordSequence.

`songleaf` keeps a song as lyrics plus standoff chord annotations anchored on
syllables; it has no durations. [`song_to_chord_sequence()`](#accompy.songs.song_to_chord_sequence) supplies them with
two simple, explicit heuristics:

- `beats_per_chord=N`: every chord lasts `N` beats;
- `bars_per_line=N`: every chord-carrying line lasts `N` bars, shared equally by
  the chords on it (so a two-chord line at `bars_per_line=1` gives each chord half a
  bar);
- neither (the default): every chord lasts one bar.

The converter reads a Song by shape (`text`, `annotations` of `kind`/`start`/
`body`, `meta`), so `songleaf` is not a dependency of `accompy`.

```pycon
>>> from types import SimpleNamespace as NS
>>> song = NS(
...     text="Hello there\nGoodbye now",
...     annotations=[
...         NS(kind="section", start=0, end=23, body={"label": "Verse"}),
...         NS(kind="chord", start=0, end=0, body={"symbol": "C"}),
...         NS(kind="chord", start=6, end=6, body={"symbol": "G"}),
...         NS(kind="chord", start=12, end=12, body={"symbol": "Am"}),
...     ],
...     meta={"title": "Hi", "key": "C"},
... )
>>> cs = song_to_chord_sequence(song, bars_per_line=1)
>>> cs.chords
[('C', 2.0), ('G', 2.0), ('Am', 4.0)]
>>> cs.sections
[('Verse', 0, 3)]
```

### Functions

| [`song_to_chord_sequence`](#accompy.songs.song_to_chord_sequence)(song, \*[, ...])   | Convert a songleaf-shaped `song` to a [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence).   |
|--------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|

### accompy.songs.song_to_chord_sequence(song, , bars_per_line=None, beats_per_chord=None, beats_per_bar=4, tempo=120)

Convert a songleaf-shaped `song` to a [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence).

* **Parameters:**
  * **song** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – Anything with `text`, `annotations` and `meta` as songleaf’s `Song`.
  * **bars_per_line** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – Bars each chord-carrying line lasts, shared by its chords.
  * **beats_per_chord** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – Beats every chord lasts. Exclusive with `bars_per_line`.
  * **beats_per_bar** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Beats in a bar (the time signature’s numerator).
  * **tempo** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Tempo in BPM (the song’s `meta["tempo"]` wins when it is a number).
* **Return type:**
  [`ChordSequence`](accompy.converters.html.md#accompy.converters.ChordSequence)
* **Returns:**
  A ChordSequence whose `sections` follow the song’s `section` annotations
  (ranges over the chords), with the song’s title and key.
* **Raises:**
  [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – if both `bars_per_line` and `beats_per_chord` are given, or
      either is not positive.
