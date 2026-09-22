# accompy.chord_parsers

Chord sheet parsers — convert various text formats to ChordSequence.

Registered converters: ChordSheet -> ChordSequence

Supported formats:

- Plain text: “C Am F G” or “| Dm7 | G7 | Cmaj7 

  ```
  |
  ```

  ”
- iReal Pro URLs: “irealb://…”
- ChordPro: “[C]lyrics [Am]more lyrics”
- MusicGen-Chord format: “C D:min G:7 C” (space-separated bars)

Each parser is registered in the global converter registry so you can do:

```default
from accompy.wips.types import convert, ChordSheet, ChordSequence
cs = convert(ChordSheet("| Dm7 | G7 | Cmaj7 |"), ChordSequence)
```

### Functions

| [`parse_chord_sheet`](#accompy.chord_parsers.parse_chord_sheet)(sheet, \*[, beats_per_bar, ...])   | Auto-detect format and parse a chord sheet into ChordSequence.   |
|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`parse_chordpro`](#accompy.chord_parsers.parse_chordpro)(sheet, \*[, beats_per_bar, tempo])    | Parse ChordPro format into a ChordSequence.                      |
| [`parse_ireal_url`](#accompy.chord_parsers.parse_ireal_url)(url, \*[, beats_per_bar])            | Parse an iReal Pro URL into a ChordSequence.                     |
| [`parse_musicgen_chord_format`](#accompy.chord_parsers.parse_musicgen_chord_format)(sheet, \*[, ...])        | Parse MusicGen-Chord text format into ChordSequence.             |
| [`parse_nashville`](#accompy.chord_parsers.parse_nashville)(sheet, \*[, key, ...])               | Parse Nashville number system notation into a ChordSequence.     |
| [`parse_plain_text`](#accompy.chord_parsers.parse_plain_text)(sheet, \*[, beats_per_bar, ...])    | Parse a plain-text chord sheet into a ChordSequence.             |
| [`parse_roman_numeral`](#accompy.chord_parsers.parse_roman_numeral)(sheet, \*[, key, ...])           | Parse Roman numeral notation into a ChordSequence.               |

### accompy.chord_parsers.parse_chord_sheet(sheet, , beats_per_bar=4, tempo=120, title='', key='C', time_signature=(4, 4))

Auto-detect format and parse a chord sheet into ChordSequence.

Detects:

- iReal Pro URLs (starts with ‘irealb://’ or ‘irealbook://’)
- ChordPro (contains ‘[’ chord brackets AND text between them)
- MusicGen-Chord format (contains ‘:’ colons in chord symbols)
- Roman numeral notation (tokens like I, ii, V7, bVII)
- Nashville number system (tokens like 1, 2m7, 5, b7)
- Plain text (everything else)

```pycon
>>> cs = parse_chord_sheet("| Dm7 | G7 | Cmaj7 |")
>>> cs.symbols
['Dm7', 'G7', 'Cmaj7']
```

```pycon
>>> cs = parse_chord_sheet("[Am]Hello [G]world")
>>> cs.symbols
['Am', 'G']
```

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

### accompy.chord_parsers.parse_chordpro(sheet, , beats_per_bar=4, tempo=120)

Parse ChordPro format into a ChordSequence.

ChordPro embeds chords in brackets within lyrics:
“[Am]Hello [G]world [C]”

Extracts just the chord symbols, one per bar by default.

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

```pycon
>>> cs = parse_chordpro("[Am]Hello [G]world [C]")
>>> cs.symbols
['Am', 'G', 'C']
```

### accompy.chord_parsers.parse_ireal_url(url, , beats_per_bar=4)

Parse an iReal Pro URL into a ChordSequence.

Uses pyRealParser if available, falls back to basic extraction.

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

```pycon
>>> # Can't test without real URL, but structure is tested
```

### accompy.chord_parsers.parse_musicgen_chord_format(sheet, , beats_per_bar=4, tempo=120)

Parse MusicGen-Chord text format into ChordSequence.

MusicGen-Chord uses space-separated bars with colon for quality:
“C D:min G:7 C” means C | Dm | G7 | C

Within a bar, comma separates chords:
“C:maj,G:maj E:min,A:min” means C G | Em Am

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

```pycon
>>> cs = parse_musicgen_chord_format("C D:min G:7 C")
>>> cs.symbols
['C', 'D:min', 'G:7', 'C']
>>> cs.durations
[4.0, 4.0, 4.0, 4.0]
```

```pycon
>>> cs = parse_musicgen_chord_format("C:maj,G:maj E:min")
>>> len(cs)
3
```

### accompy.chord_parsers.parse_nashville(sheet, , key='C', beats_per_bar=4, tempo=120, title='', time_signature=(4, 4))

Parse Nashville number system notation into a ChordSequence.

Nashville numbers use scale degree numbers instead of note names:

- “1 4 5 1” in C = C F G C
- Quality suffixes: “2m7 5 1maj7”
- Accidentals: “b7” = flat seventh scale degree
- Bar lines supported: “| 2m7 | 5 | 1maj7 

  ```
  |
  ```

  ”

```pycon
>>> cs = parse_nashville("| 2m7 | 5 | 1maj7 |", key="C")
>>> cs.symbols
['Dm7', 'G', 'Cmaj7']
```

```pycon
>>> cs = parse_nashville("1 4 5 1", key="G")
>>> cs.symbols
['G', 'C', 'D', 'G']
```

```pycon
>>> cs = parse_nashville("| 2m7 | 57 | 1maj7 |", key="Bb")
>>> cs.symbols
['Cm7', 'F7', 'Bbmaj7']
```

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

### accompy.chord_parsers.parse_plain_text(sheet, , beats_per_bar=4, tempo=120, title='', key='C', time_signature=(4, 4))

Parse a plain-text chord sheet into a ChordSequence.

Supports:

- Bar-line format: “| C | Am | F | G 

  ```
  |
  ```

  ”
- Multi-chord bars: “| C Am | F G 

  ```
  |
  ```

  ”
- Space-separated: “C Am F G”
- Repeat markers: “%” repeats previous chord/bar

```pycon
>>> cs = parse_plain_text("| Dm7 | G7 | Cmaj7 |")
>>> cs.symbols
['Dm7', 'G7', 'Cmaj7']
>>> cs.durations
[4.0, 4.0, 4.0]
```

```pycon
>>> cs = parse_plain_text("| C Am | F G |")
>>> cs.symbols
['C', 'Am', 'F', 'G']
>>> cs.durations
[2.0, 2.0, 2.0, 2.0]
```

```pycon
>>> cs = parse_plain_text("C Am F G")
>>> len(cs)
4
```

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)

### accompy.chord_parsers.parse_roman_numeral(sheet, , key='C', beats_per_bar=4, tempo=120, title='', time_signature=(4, 4))

Parse Roman numeral notation into a ChordSequence.

Supports:

- Upper case for major: I, IV, V
- Lower case for minor: ii, vi, iii
- Quality suffixes: ii7, V7, Imaj7, viidim, viio, iim7b5
- Accidentals: bVII, #IV
- Bar lines: “| ii7 | V7 | Imaj7 

  ```
  |
  ```

  ”
- Space-separated: “I IV V I”

```pycon
>>> cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="C")
>>> cs.symbols
['Dm7', 'G7', 'Cmaj7']
```

```pycon
>>> cs = parse_roman_numeral("I IV V I", key="G")
>>> cs.symbols
['G', 'C', 'D', 'G']
```

```pycon
>>> cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="F")
>>> cs.symbols
['Gm7', 'C7', 'Fmaj7']
```

* **Return type:**
  [`ChordSequence`](accompy.converters.md#accompy.converters.ChordSequence)
