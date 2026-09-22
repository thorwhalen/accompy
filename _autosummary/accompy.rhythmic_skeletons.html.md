# accompy.rhythmic_skeletons

Rhythmic skeletons — duration-only measure patterns for simple accompaniment.

A rhythmic skeleton is a tuple of durations (in beats) that sum to the time
signature, describing when you strike within a measure and for how long each
strike sustains, with no regard for what you play. No pitches, no voicings, no
velocities, no instrument assignments.

The purpose of separating this layer out is to provide a gravitational center
for more sophisticated generation. A human accompanist doesn’t mechanically
repeat a fixed pattern — they vary, anticipate, syncopate, and breathe around
a characteristic rhythmic feel. By defining that feel as a minimal skeleton, we
give downstream processes a clear, lightweight seed to elaborate from.

Example:

```default
>>> from accompy.rhythmic_skeletons import resolve_skeleton, apply_skeleton
>>> resolve_skeleton("tresillo")
(1.5, 1.5, 1)
>>> resolve_skeleton((2, 2))
(2, 2)

>>> from accompy.converters import ChordSequence
>>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
>>> expanded = apply_skeleton(cs, "tresillo")
>>> [(sym, dur) for sym, dur in expanded]
[('Dm7', 1.5), ('Dm7', 1.5), ('Dm7', 1.0), ('G7', 1.5), ('G7', 1.5), ('G7', 1.0)]
```

### Functions

| [`apply_skeleton`](#accompy.rhythmic_skeletons.apply_skeleton)(cs, skeleton)                     | Apply a rhythmic skeleton to a chord sequence.            |
|---------------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| [`list_skeletons`](#accompy.rhythmic_skeletons.list_skeletons)(\*[, beats_per_measure, style])   | List available skeleton keys, optionally filtered.        |
| [`register_skeleton`](#accompy.rhythmic_skeletons.register_skeleton)(key, pattern, \*[, name, ...]) | Register a custom rhythmic skeleton.                      |
| [`resolve_skeleton`](#accompy.rhythmic_skeletons.resolve_skeleton)(skeleton)                       | Resolve a skeleton specification to a tuple of durations. |

### accompy.rhythmic_skeletons.apply_skeleton(cs, skeleton)

Apply a rhythmic skeleton to a chord sequence.

The skeleton defines strike positions within each *measure*. Each strike
plays whatever chord is active at that beat position. If a strike spans a
chord boundary within a measure, it is split so the chord change is
respected.

* **Parameters:**
  * **cs** – A ChordSequence (from `accompy.converters`).
  * **skeleton** (Union[str, tuple, Sequence]) – Skeleton key, name, style, or duration tuple.
* **Return type:**
  ChordSequence
* **Returns:**
  A new ChordSequence with chords expanded according to the skeleton.

### Example

```pycon
>>> from accompy.converters import ChordSequence
>>> cs = ChordSequence([("Dm7", 2.0), ("G7", 2.0)])
>>> result = apply_skeleton(cs, "tresillo")
>>> [(s, d) for s, d in result]
[('Dm7', 1.5), ('Dm7', 0.5), ('G7', 1.0), ('G7', 1.0)]
```

### accompy.rhythmic_skeletons.list_skeletons(, beats_per_measure=None, style=None)

List available skeleton keys, optionally filtered.

* **Parameters:**
  * **beats_per_measure** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter to skeletons matching this measure length.
  * **style** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Filter to skeletons associated with this style.
* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
* **Returns:**
  List of skeleton key strings.

### Examples

```pycon
>>> "tresillo" in list_skeletons()
True
>>> all(RHYTHMIC_SKELETONS[k]["beats_per_measure"] == 3
...     for k in list_skeletons(beats_per_measure=3))
True
```

### accompy.rhythmic_skeletons.register_skeleton(key, pattern, , name='', beats_per_measure=None, styles=None)

Register a custom rhythmic skeleton.

* **Parameters:**
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Unique string key for the skeleton.
  * **pattern** ([`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)) – Tuple of beat durations.
  * **name** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Human-readable name (defaults to key).
  * **beats_per_measure** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Measure length in beats (defaults to sum of pattern).
  * **styles** ([`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – List of associated style strings.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Example

```pycon
>>> register_skeleton("my_groove", (1, 0.5, 0.5, 2), name="My Groove")
>>> resolve_skeleton("my_groove")
(1, 0.5, 0.5, 2)
```

### accompy.rhythmic_skeletons.resolve_skeleton(skeleton)

Resolve a skeleton specification to a tuple of durations.

Accepts:

> - A tuple or list of numbers (pass-through)
> - A skeleton key (e.g., `"tresillo"`, `"whole_note"`)
> - A skeleton name, case-insensitive (e.g., `"Tresillo"`)
> - A style string (e.g., `"reggae"`) — returns the first match
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)
* **Returns:**
  Tuple of beat durations summing to the measure length.
* **Raises:**
  [**KeyError**](https://docs.python.org/3/builtins/exceptions.html#KeyError) – If the skeleton cannot be resolved.

### Examples

```pycon
>>> resolve_skeleton("whole_note")
(4,)
>>> resolve_skeleton("tresillo")
(1.5, 1.5, 1)
>>> resolve_skeleton((2, 2))
(2, 2)
>>> resolve_skeleton("Dotted half + quarter")
(3, 1)
```
