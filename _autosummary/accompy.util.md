# accompy.util

Utility functions for chord parsing and normalization.

Contains helpers for chord symbol normalization, chord string parsing,
and iReal URL parsing.

### Functions

| [`normalize_chord_symbol`](#accompy.util.normalize_chord_symbol)(symbol)                    | Normalize chord symbols to a standard format.                      |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| [`parse_chord_string`](#accompy.util.parse_chord_string)(chord_string)                  | Parse a chord string into measures, each containing chord symbols. |
| [`parse_ireal_html`](#accompy.util.parse_ireal_html)(html_path)                       | Extract a Score from an iReal Pro HTML export file.                |
| [`parse_ireal_url`](#accompy.util.parse_ireal_url)(url)                              | Parse an iReal Pro URL into a Score object.                        |
| [`parse_ireal_url_fallback`](#accompy.util.parse_ireal_url_fallback)(url)                     | Best-effort iReal Pro URL parser (no external dependencies).       |
| [`parse_time_sig`](#accompy.util.parse_time_sig)(ts_str)                            | Parse time signature string like '4/4' into tuple.                 |
| [`score_from_chord_specs`](#accompy.util.score_from_chord_specs)(chords, \*[, title, ...])  | Create a `Score` from `(chord, beats)` pairs.                      |
| [`transpose_chord`](#accompy.util.transpose_chord)(chord, semitones, \*[, use_flat]) | Transpose a chord symbol by *semitones*.                           |
| [`transpose_note`](#accompy.util.transpose_note)(name, semitones, \*[, use_flat])   | Transpose a single note name by *semitones*.                       |
| [`transpose_score`](#accompy.util.transpose_score)(score, target_key)                | Transpose a `Score` to a new key.                                  |

### accompy.util.normalize_chord_symbol(symbol)

Normalize chord symbols to a standard format.

Handles conversions like:

- Cm -> C-
- Cmaj7 -> C^7
- Cdim -> Co
- Cm7b5 -> Ch7 (half-diminished)

### Example

```pycon
>>> normalize_chord_symbol("Cmaj7")
'C^7'
>>> normalize_chord_symbol("Dm7b5")
'Dh7'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### accompy.util.parse_chord_string(chord_string)

Parse a chord string into measures, each containing chord symbols.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]

### Example

```pycon
>>> parse_chord_string("| C | Am | F | G |")
[['C'], ['A-'], ['F'], ['G']]
>>> parse_chord_string("| C Am | F G |")
[['C', 'A-'], ['F', 'G']]
```

### accompy.util.parse_ireal_html(html_path)

Extract a Score from an iReal Pro HTML export file.

iReal Pro can export songs as HTML files containing an `irealb://` link.
This function reads the file, extracts that link, and parses it into a
`Score`.

* **Parameters:**
  **html_path** (str) – Path to the HTML file exported from iReal Pro.
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

Parse an iReal Pro URL into a Score object.

Tries pyRealParser’s `parse_ireal_url` first, then falls back to
constructing a `Tune` directly (handles URLs with empty `==` fields),
and finally to a no-dependency best-effort parser.

### accompy.util.parse_ireal_url_fallback(url)

Best-effort iReal Pro URL parser (no external dependencies).

This is intentionally conservative: it extracts a usable chord progression but
does not attempt to perfectly replicate iReal Pro’s full encoding.

### accompy.util.parse_time_sig(ts_str)

Parse time signature string like ‘4/4’ into tuple.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### Example

```pycon
>>> parse_time_sig("3/4")
(3, 4)
>>> parse_time_sig("6/8")
(6, 8)
>>> parse_time_sig(None)
(4, 4)
```

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
  * **target_key** (str) – Target key, e.g. `"Eb"`, `"G"`, `"F#"`.
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
