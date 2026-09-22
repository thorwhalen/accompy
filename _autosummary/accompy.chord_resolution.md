# accompy.chord_resolution

Chord symbol to MIDI notes resolution.

Provides pluggable chord resolution with multiple backends (tonal, music21).
Implements dependency injection pattern for flexibility.

### Functions

| [`chord_to_notes`](#accompy.chord_resolution.chord_to_notes)(symbol)                    | Convert chord symbol to MIDI notes using the current default resolver.   |
|--------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`get_chord_resolver`](#accompy.chord_resolution.get_chord_resolver)()                      | Get the current default chord resolver.                                  |
| [`music21_resolver`](#accompy.chord_resolution.music21_resolver)(symbol, \*[, transpose]) | Resolve chord symbol using music21 library (alternative).                |
| [`set_chord_resolver`](#accompy.chord_resolution.set_chord_resolver)(resolver)              | Set the default chord resolver.                                          |
| [`tonal_resolver`](#accompy.chord_resolution.tonal_resolver)(symbol, \*[, transpose])   | Resolve chord symbol to MIDI notes using the tonal package (default).    |

### accompy.chord_resolution.chord_to_notes(symbol)

Convert chord symbol to MIDI notes using the current default resolver.

This is the main entry point for chord resolution in accompy.

* **Parameters:**
  **symbol** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol (e.g., “Dm7”, “G7”)
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  List of MIDI note numbers

### Example

```pycon
>>> notes = chord_to_notes("C")
>>> len(notes) > 0
True
```

### accompy.chord_resolution.get_chord_resolver()

Get the current default chord resolver.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]]
* **Returns:**
  The active chord resolution function

### Example

```pycon
>>> resolver = get_chord_resolver()
>>> notes = resolver("C")
>>> len(notes) > 0
True
```

### accompy.chord_resolution.music21_resolver(symbol, , transpose=-12)

Resolve chord symbol using music21 library (alternative).

Music21 is a comprehensive music analysis library. It provides more
sophisticated chord parsing but has heavier dependencies.

* **Parameters:**
  * **symbol** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitone offset to apply (default: -12)
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  List of MIDI note numbers

#### NOTE
Requires: pip install music21
This is provided as an alternative for advanced use cases.
Consider using tonal_resolver for standard accompaniment generation.

### accompy.chord_resolution.set_chord_resolver(resolver)

Set the default chord resolver.

This enables global customization of chord-to-notes resolution.

* **Parameters:**
  **resolver** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]]) – A function that takes a chord symbol (str) and returns MIDI notes (list[int])
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> def my_resolver(symbol: str) -> list[int]:
...     # Custom chord voicing logic
...     return [60, 64, 67]  # C major triad
>>> set_chord_resolver(my_resolver)
```

### accompy.chord_resolution.tonal_resolver(symbol, , transpose=-12)

Resolve chord symbol to MIDI notes using the tonal package (default).

The tonal package is lightweight and designed for music theory operations.
It anchors chord roots around C4=60. We apply a default -12 semitone transpose
to voice chords closer to C3=48 for better bass/piano range.

* **Parameters:**
  * **symbol** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Chord symbol (e.g., “Dm7”, “G7”, “Cmaj7”)
  * **transpose** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Semitone offset to apply (default: -12)
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`int`](https://docs.python.org/3/builtins/functions.html#int)]
* **Returns:**
  List of MIDI note numbers

### Example

```pycon
>>> notes = tonal_resolver("Cmaj7")
>>> len(notes) > 0
True
```

#### NOTE
Requires: pip install tonal
See: [https://github.com/thorwhalen/tonal](https://github.com/thorwhalen/tonal)
