# accompy.chord_resolvers

Chord resolvers — convert chord symbols to MIDI note numbers.

Registered converters: ChordSequence -> NoteSequence

Multiple backends, each wrapping a different music theory library:

- pychord: lightweight, good coverage of standard chord types
- music21: comprehensive, heavyweight, handles edge cases well
- mingus: pure Python music theory, no C dependencies
- tonal: the existing accompy dependency (thorwhalen/tonal)

Each resolver is a function: chord_symbol (str) -> list[int] (MIDI notes).
We also provide converters that operate on whole ChordSequences.

### Functions

| [`chordseq_to_noteseq_mingus`](#accompy.chord_resolvers.chordseq_to_noteseq_mingus)(cs)                  | Convert ChordSequence to NoteSequence using mingus.           |
|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| [`chordseq_to_noteseq_music21`](#accompy.chord_resolvers.chordseq_to_noteseq_music21)(cs)                 | Convert ChordSequence to NoteSequence using music21.          |
| [`chordseq_to_noteseq_pychord`](#accompy.chord_resolvers.chordseq_to_noteseq_pychord)(cs)                 | Convert ChordSequence to NoteSequence using pychord.          |
| [`chordseq_to_noteseq_tonal`](#accompy.chord_resolvers.chordseq_to_noteseq_tonal)(cs)                   | Convert ChordSequence to NoteSequence using tonal.            |
| [`resolve_with_mingus`](#accompy.chord_resolvers.resolve_with_mingus)(symbol, \*[, root_octave])  | Resolve a chord symbol to MIDI notes using mingus.            |
| [`resolve_with_music21`](#accompy.chord_resolvers.resolve_with_music21)(symbol, \*[, root_octave]) | Resolve a chord symbol to MIDI notes using music21.           |
| [`resolve_with_pychord`](#accompy.chord_resolvers.resolve_with_pychord)(symbol, \*[, root_octave]) | Resolve a chord symbol to MIDI notes using pychord.           |
| [`resolve_with_tonal`](#accompy.chord_resolvers.resolve_with_tonal)(symbol, \*[, transpose])     | Resolve a chord symbol to MIDI notes using the tonal package. |

### accompy.chord_resolvers.chordseq_to_noteseq_mingus(cs)

Convert ChordSequence to NoteSequence using mingus.

* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)

### accompy.chord_resolvers.chordseq_to_noteseq_music21(cs)

Convert ChordSequence to NoteSequence using music21.

* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)

### accompy.chord_resolvers.chordseq_to_noteseq_pychord(cs)

Convert ChordSequence to NoteSequence using pychord.

* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)

### accompy.chord_resolvers.chordseq_to_noteseq_tonal(cs)

Convert ChordSequence to NoteSequence using tonal.

* **Return type:**
  [`NoteSequence`](accompy.converters.html.md#accompy.converters.NoteSequence)

### accompy.chord_resolvers.resolve_with_mingus(symbol, , root_octave=3)

Resolve a chord symbol to MIDI notes using mingus.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> resolve_with_mingus("Cmaj7")
[36, 40, 43, 47]
```

### accompy.chord_resolvers.resolve_with_music21(symbol, , root_octave=3)

Resolve a chord symbol to MIDI notes using music21.

Handles the widest range of chord types including altered chords.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> resolve_with_music21("Cmaj7")
[48, 52, 55, 59]
```

### accompy.chord_resolvers.resolve_with_pychord(symbol, , root_octave=3)

Resolve a chord symbol to MIDI notes using pychord.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> resolve_with_pychord("Cmaj7")
[48, 52, 55, 59]
>>> resolve_with_pychord("Am")
[57, 60, 64]
```

### accompy.chord_resolvers.resolve_with_tonal(symbol, , transpose=-12)

Resolve a chord symbol to MIDI notes using the tonal package.

This is accompy’s existing default resolver.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]

```pycon
>>> resolve_with_tonal("Cmaj7")
[48, 52, 55, 59]
```
