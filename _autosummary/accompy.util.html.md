# accompy.util

Utility functions for chord parsing and normalization.

Contains helpers for chord symbol normalization, chord string parsing,
and iReal URL parsing.

### Module Attributes

| [`CHORD_SYMBOL_REPLACEMENTS`](#accompy.util.CHORD_SYMBOL_REPLACEMENTS)   | each `old` becomes `new` at the end of the symbol or of a part before a slash (longest `old` wins).                               |
|------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| [`UNNORMALIZED_SYMBOLS`](#accompy.util.UNNORMALIZED_SYMBOLS)        | Symbols [`normalize_chord_symbol()`](#accompy.util.normalize_chord_symbol) returns unchanged (no chord, or a repeat sign). |

### Functions

| [`normalize_chord_symbol`](#accompy.util.normalize_chord_symbol)(symbol)                    | Normalize chord symbols to a standard format.                        |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`parse_chord_string`](#accompy.util.parse_chord_string)(chord_string)                  | Parse a chord string into measures, each containing chord symbols.   |
| [`parse_ireal_html`](#accompy.util.parse_ireal_html)(html_path)                       | Extract a Score from an iReal Pro HTML export file.                  |
| [`parse_ireal_url`](#accompy.util.parse_ireal_url)(url)                              | Parse an iReal Pro URL (`irealb://` or `irealbook://`) into a Score. |
| [`parse_time_sig`](#accompy.util.parse_time_sig)(ts_str)                            | Parse time signature string like '4/4' into tuple.                   |
| [`score_from_chord_specs`](#accompy.util.score_from_chord_specs)(chords, \*[, title, ...])  | Create a `Score` from `(chord, beats)` pairs.                        |
| [`transpose_chord`](#accompy.util.transpose_chord)(chord, semitones, \*[, use_flat]) | Transpose a chord symbol by *semitones*.                             |
| [`transpose_note`](#accompy.util.transpose_note)(name, semitones, \*[, use_flat])   | Transpose a single note name by *semitones*.                         |
| [`transpose_score`](#accompy.util.transpose_score)(score, target_key)                | Transpose a `Score` to a new key.                                    |

### accompy.util.CHORD_SYMBOL_REPLACEMENTS *= (('maj7', '^7'), ('maj9', '^9'), ('maj', '^'), ('min7', '-7'), ('min', '-'), ('m7', '-7'), ('m9', '-9'), ('m', '-'), ('dim7', 'o7'), ('dim', 'o'), ('m7b5', 'h7'), ('ø7', 'h7'), ('ø', 'h'), ('sus4', 'sus'), ('sus2', 'sus2'), ('add9', 'add9'), ('add2', 'add2'))*

each `old` becomes
`new` at the end of the symbol or of a part before a slash (longest `old` wins).

* **Type:**
  The suffix rewrites [`normalize_chord_symbol()`](#accompy.util.normalize_chord_symbol) applies

### accompy.util.UNNORMALIZED_SYMBOLS *= ('', 'n', 'N.C.', 'NC', '%', 'x')*

Symbols [`normalize_chord_symbol()`](#accompy.util.normalize_chord_symbol) returns unchanged (no chord, or a repeat sign).

### accompy.util.normalize_chord_symbol(symbol)

Normalize chord symbols to a standard format.

Handles conversions like:

- Cm -> C-
- Cmaj7 -> C^7
- Cdim -> Co
- Cm7b5 -> Ch7 (half-diminished)

Each `/`-separated part of the symbol has its longest matching suffix from
[`CHORD_SYMBOL_REPLACEMENTS`](#accompy.util.CHORD_SYMBOL_REPLACEMENTS) rewritten, once (so `dim` is never read as a
word ending in `m`).

### Example

```pycon
>>> normalize_chord_symbol("Cmaj7")
'C^7'
>>> normalize_chord_symbol("Dm7b5")
'Dh7'
>>> normalize_chord_symbol("Cdim7"), normalize_chord_symbol("Bbm7/F")
('Co7', 'Bb-7/F')
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### accompy.util.parse_chord_string(chord_string)

Parse a chord string into measures, each containing chord symbols.

### Example

```pycon
>>> parse_chord_string("| C | Am | F | G |")
[['C'], ['A-'], ['F'], ['G']]
>>> parse_chord_string("| C Am | F G |")
[['C', 'A-'], ['F', 'G']]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

### accompy.util.parse_ireal_html(html_path)

Extract a Score from an iReal Pro HTML export file.

iReal Pro can export songs as HTML files containing an `irealb://` link.
This function reads the file, extracts that link, and parses it into a
`Score`.

* **Parameters:**
  **html_path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to the HTML file exported from iReal Pro.
* **Return type:**
  Score
* **Returns:**
  A Score with measures, title, key, and time signature.
* **Raises:**
  * [**FileNotFoundError**](https://docs.python.org/3/builtins/exceptions.html#FileNotFoundError) – If *html_path* does not exist.
  * [**ValueError**](https://docs.python.org/3/builtins/exceptions.html#ValueError) – If no iReal URL is found in the HTML.

Example:

```default
>>> score = parse_ireal_html("/path/to/song.html")
>>> score.title
'Autumn Leaves'
```

### accompy.util.parse_ireal_url(url)

Parse an iReal Pro URL (`irealb://` or `irealbook://`) into a Score.

Decoding is [`accompy.ireal.decode_ireal_url()`](accompy.ireal.html.md#accompy.ireal.decode_ireal_url); the Score is the first tune of
the URL that has chords, each bar the list of its chords as written (iReal chord
notation). Raises `ValueError` when no tune has chords.

```pycon
>>> score = parse_ireal_url("irealbook://Blues=Me=Swing=F=n=[T34F7 |Bb7 Bo7 |C7 Z")
>>> score.measures, score.time_signature
([['F7'], ['Bb7', 'Bo7'], ['C7']], (3, 4))
```

### accompy.util.parse_time_sig(ts_str)

Parse time signature string like ‘4/4’ into tuple.

### Example

```pycon
>>> parse_time_sig("3/4")
(3, 4)
>>> parse_time_sig("6/8")
(6, 8)
>>> parse_time_sig(None)
(4, 4)
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### accompy.util.score_from_chord_specs(chords, , title='Untitled', key='C', time_signature=(4, 4))

Create a `Score` from `(chord, beats)` pairs.

Durations that are multiples of the bar length map cleanly to repeated bars.
Other durations are approximated by grouping chords into bars.

### accompy.util.transpose_chord(chord, semitones, , use_flat=None)

Transpose a chord symbol by *semitones*.

Handles slash chords (e.g. `"C6/E"`).

* **Parameters:**
  * **chord** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol like `"Am7"`, `"C6/E"`, `"G#o"`.
  * **semitones** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of semitones.
  * **use_flat** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – Force flat/sharp spelling (see [`transpose_note()`](#accompy.util.transpose_note)).
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> transpose_chord("Am7", 2)
'Bm7'
>>> transpose_chord("C6/E", 5)
'F6/A'
>>> transpose_chord("G#o", -2, use_flat=True)
'Gbo'
```

### accompy.util.transpose_note(name, semitones, , use_flat=None)

Transpose a single note name by *semitones*.

* **Parameters:**
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Note name like `"C"`, `"Eb"`, `"F#"`.
  * **semitones** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of semitones (positive = up, negative = down).
  * **use_flat** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – Force flat (True) or sharp (False) spelling.
    `None` (default) uses flats for downward transposition.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> transpose_note("C", 5)
'F'
>>> transpose_note("A", -2)
'G'
>>> transpose_note("C", 1, use_flat=True)
'Db'
```

### accompy.util.transpose_score(score, target_key)

Transpose a `Score` to a new key.

The spelling (sharp vs flat) is chosen automatically based on the
*target_key*.

* **Parameters:**
  * **score** – A `Score` instance.
  * **target_key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Target key, e.g. `"Eb"`, `"G"`, `"F#"`.
* **Return type:**
  Score
* **Returns:**
  A new Score in the target key with an updated title.

### Example

```pycon
>>> from accompy import Score
>>> s = Score.from_string("| C | Am | F | G |", key="C")
>>> t = transpose_score(s, "G")
>>> [m[0] for m in t.measures]
['G', 'E-', 'C', 'D']
```
