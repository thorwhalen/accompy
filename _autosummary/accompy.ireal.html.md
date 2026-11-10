# accompy.ireal

Decode iReal Pro URLs (`irealb://` and `irealbook://`) into tunes and bars.

accompy owns this decoding; the TypeScript twin (`ts/src/ireal.ts`) is its exact
counterpart. The unscrambling and the chord-string cleanup started as a copy of the parts
of pyRealParser ([https://github.com/drs251/pyRealParser](https://github.com/drs251/pyRealParser), MIT licence, notice below) that
accompy used. Changes from it:

- `T12` is 12/8; every other time-signature code `T<a><b>` is a/b;
- the chart is read bar by bar in one linear pass: every `{...}` repeat is written out
  with its own endings (`}N2`, `}` then `[N2`, three endings; a `}` closing the
  last ending replays nothing), a `}` with no `{` repeats from the last `[`, the
  previous `}` or the top, a `{` inside an open repeat restarts it (iReal has no
  nesting), and the `}` stays a barline;
- a D.C./D.S. al Coda replays from the segno `S` (or the top) to the first `Q`, as
  whole bars, then plays the coda;
- `r` (repeat the previous two bars) makes two bars and keeps the bar after it;
- `p` (the previous chord again) and `W` (an invisible root) with no chord before
  them are dropped; `x` or `r` with nothing to repeat is dropped;
- backslashes in chord text are literal text;
- song fields are read by position, so an empty field (an empty composer) shifts nothing;
- each bar is a list of its chords (pyRealParser glued them into one string per bar), and
  end, segno and coda marks are left out of the chords;
- the `l` (large print) mark is removed without eating the `l` of `alt`;
- `Z` (final double bar) is a barline.

Regex digit and word classes follow Python’s Unicode tables; the twin’s JavaScript ones can
be a version newer (characters added in Unicode 15.1/16 differ; iReal uses none of them).

The URL layout. `irealb://` holds songs joined by `===`, then an optional playlist
name; a song is ten `=`-separated fields, `title=composer=(unused)=style=key=transpose=
music=comp_style=bpm=repeats`, whose music starts with [`SCRAMBLE_PREFIX`](#accompy.ireal.SCRAMBLE_PREFIX) and is
scrambled. Empty fields can make `===` inside a song, so songs are found by their music
field, not by splitting on `===`. `irealbook://` (the older format) holds six-field
songs, `title=composer=style=key=n=music`, with the music in plain text.

```pycon
>>> [t.measures for t in decode_ireal_url("irealbook://Blues=Me=Swing=F=n=[T34F7 |Bb7 p|r| |C7 Z")]
[[['F7'], ['Bb7', 'Bb7'], ['F7'], ['Bb7', 'Bb7'], ['C7']]]
```

### Module Attributes

| [`SCRAMBLE_PREFIX`](#accompy.ireal.SCRAMBLE_PREFIX)           | The start of a scrambled (`irealb://`) music field.                           |
|----------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| [`TIME_SIGNATURE_EXCEPTIONS`](#accompy.ireal.TIME_SIGNATURE_EXCEPTIONS) | Time-signature codes that are not `T<numerator><denominator>`.                |
| [`PLAIN_SONG_FIELDS`](#accompy.ireal.PLAIN_SONG_FIELDS)         | Number of fields in an `irealbook://` song, and the index of its music field. |
| [`PLAIN_MUSIC_INDEX`](#accompy.ireal.PLAIN_MUSIC_INDEX)         | Number of fields in an `irealbook://` song, and the index of its music field. |

### Functions

| [`cleanup_chord_string`](#accompy.ireal.cleanup_chord_string)(chord_string)   | Unify bar lines (`Z`, the final double bar, is one too) and repeat signs; drop spacers and empty bars.                                                                   |
|---------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`decode_ireal_url`](#accompy.ireal.decode_ireal_url)(url)                | The tunes of an iReal URL (a playlist has several), skipping those that do not decode.                                                                                   |
| [`flatten_measures`](#accompy.ireal.flatten_measures)(chord_string)       | The bars of an (unscrambled) chord string, each a list of its chords, with repeats, endings, codas and signs written out (a `p` repeats the previous chord on its beat). |
| [`time_signature`](#accompy.ireal.time_signature)(chord_string)         | The first time signature (`T44`, `T34`, `T12` = 12/8, ...), else 4/4.                                                                                                    |
| [`unscramble`](#accompy.ireal.unscramble)(scrambled)                | Undo iReal's scrambling of a music field (after [`SCRAMBLE_PREFIX`](#accompy.ireal.SCRAMBLE_PREFIX)).                                                       |

### Classes

| [`IrealTune`](#accompy.ireal.IrealTune)([title, composer, style, key, ...])   | One song of an iReal URL: its metadata, cleaned chord string and flattened bars.   |
|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|

### *class* accompy.ireal.IrealTune(title='', composer='', style='', key='', transpose='', comp_style='', bpm='', repeats='', chord_string='', time_signature=(4, 4), measures=list())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One song of an iReal URL: its metadata, cleaned chord string and flattened bars.

`measures` holds one list of chords per bar (e.g. `['D-7', 'G7']`), with
repeats, endings, codas and repeat signs written out.

#### chord_specs(, beats_per_bar=None)

`(chord, beats)` pairs: each bar shared evenly by its chords. Bars last
`beats_per_bar` beats, by default the time signature’s numerator.

```pycon
>>> IrealTune(measures=[["C"], ["D-7", "G7"]], time_signature=(3, 4)).chord_specs()
[('C', 3.0), ('D-7', 1.5), ('G7', 1.5)]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]]

#### *property* tempo *: [int](https://docs.python.org/3/builtins/functions.html#int) | [None](https://docs.python.org/3/builtins/constants.html#None)*

The tempo in BPM, or None when unset (empty, not a number, or not above 0).

### accompy.ireal.PLAIN_MUSIC_INDEX *= 5*

Number of fields in an `irealbook://` song, and the index of its music field.

### accompy.ireal.PLAIN_SONG_FIELDS *= 6*

Number of fields in an `irealbook://` song, and the index of its music field.

### accompy.ireal.SCRAMBLE_PREFIX *= '1r34LbKcu7'*

The start of a scrambled (`irealb://`) music field.

### accompy.ireal.TIME_SIGNATURE_EXCEPTIONS *= {(1, 2): (12, 8)}*

Time-signature codes that are not `T<numerator><denominator>`.

### accompy.ireal.cleanup_chord_string(chord_string)

Unify bar lines (`Z`, the final double bar, is one too) and repeat signs; drop
spacers and empty bars.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### accompy.ireal.decode_ireal_url(url)

The tunes of an iReal URL (a playlist has several), skipping those that do not decode.

The URL ends at its first raw `"` (as when cut out of an HTML `href`; a `%22`
is a quote inside a title or comment) and is then percent-decoded; the `irealb://` / `irealbook://` scheme is optional. Music fields that
start with [`SCRAMBLE_PREFIX`](#accompy.ireal.SCRAMBLE_PREFIX) are read as `irealb` songs; a URL with none is
read as `irealbook` six-field songs.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`IrealTune`](#accompy.ireal.IrealTune)]

### accompy.ireal.flatten_measures(chord_string)

The bars of an (unscrambled) chord string, each a list of its chords, with repeats,
endings, codas and signs written out (a `p` repeats the previous chord on its beat).

```pycon
>>> flatten_measures("{C^7 p|A-7 D7 |N1D-7,G7 }N2G-7 C7 F7 |F^7 Z")
[['C^7', 'C^7'], ['A-7', 'D7'], ['D-7', 'G7'], ['C^7', 'C^7'], ['A-7', 'D7'], ['G-7', 'C7', 'F7'], ['F^7']]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

### accompy.ireal.time_signature(chord_string)

The first time signature (`T44`, `T34`, `T12` = 12/8, …), else 4/4.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### accompy.ireal.unscramble(scrambled)

Undo iReal’s scrambling of a music field (after [`SCRAMBLE_PREFIX`](#accompy.ireal.SCRAMBLE_PREFIX)).

Every full 50-character block that is not the last (or followed by fewer than 2
characters) has characters 0-4 and 10-23 swapped with their mirror (49 - i). The
operation is its own inverse.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
