"""Run and record the golden cases in ``fixtures/cases.json``, the behaviour both twins share.

accompy's TypeScript twin (``ts/``) ports the chart-to-note-events engine: chart parsing,
chord resolution, the builtin styles and the rhythmic skeletons. :data:`TWIN_FUNCTIONS`
names the Python side of that surface; the TypeScript runner maps the same names to its
camelCase functions, and both test suites check they cover exactly this list.

A case is ``{"fn": <name>, "args": [...], "kwargs": {...}, "expected": ...}`` in JSON form:

- tuples are lists; a :class:`~accompy.base.Score` is
  ``{"measures", "title", "composer", "key", "time_signature"}`` (an argument with a
  ``"measures"`` key is decoded to a Score); a ``MidiEvent`` is
  ``[time, channel, note, velocity, duration]``, to keep the file small;
- an exception is ``{"$raises": <Python exception name>}``: ``ValueError``, ``KeyError``,
  ``ZeroDivisionError`` or ``TypeError``. The TypeScript twin throws errors with the same
  ``name`` (the first three are RangeError subclasses it exports);
- ``kwargs`` may only name keyword-only parameters, which the TypeScript twin takes as a
  trailing options object (keys in snake_case on both sides of the file; the TS runner
  converts them).

Floats: durations in cases are sums of powers of two, so they add exactly in any order
(Python 3.12's ``sum`` compensates rounding and 3.10's does not; exact sums agree).

Results are compared as JSON text, so order matters everywhere. To add a case, append it
with any ``expected`` and run ``python -m accompy._fixtures``: it rewrites every
``expected`` from Python, so review the diff (a changed expectation is a behaviour
change on both sides).

>>> run_case({"fn": "normalize_chord_symbol", "args": ["Cmaj7"]})
'C^7'
>>> run_case({"fn": "tonal_resolver", "args": ["Xyz"]})
{'$raises': 'ValueError'}
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from accompy.base import MidiEvent, Score, ensure_score
from accompy.chord_resolution import tonal_resolver
from accompy.patterns import get_patterns
from accompy.renderers.midi import chord_events, fallback_chord_notes, generate_events
from accompy.rhythmic_skeletons import list_skeletons, resolve_skeleton
from accompy.util import (
    normalize_chord_symbol,
    parse_chord_string,
    parse_ireal_url,
    parse_time_sig,
    score_from_chord_specs,
    transpose_chord,
    transpose_note,
    transpose_score,
)

#: The repository root (where ``fixtures/`` and ``ts/`` live, next to the package).
REPO_ROOT = Path(__file__).resolve().parent.parent

#: The golden cases, relative to the repository root.
CASES_PATH = Path("fixtures") / "cases.json"

#: The exceptions a case may expect.
RAISES = (ValueError, KeyError, ZeroDivisionError, TypeError)


def score_to_chord_sequence(score: Score) -> list:
    """``score``'s chords as ``(symbol, beats)`` pairs (:meth:`Score.to_chord_sequence`)."""
    return list(score.to_chord_sequence().chords)


def apply_skeleton(chords: list, skeleton) -> list:
    """:func:`accompy.rhythmic_skeletons.apply_skeleton` on ``(symbol, beats)`` pairs."""
    from accompy.converters import ChordSequence
    from accompy.rhythmic_skeletons import apply_skeleton as _apply

    return list(_apply(ChordSequence([tuple(c) for c in chords]), skeleton).chords)


#: The twin's surface: Python name -> the Python function both twins must agree with.
TWIN_FUNCTIONS = {
    f.__name__: f
    for f in (
        normalize_chord_symbol,
        parse_chord_string,
        parse_time_sig,
        ensure_score,
        score_from_chord_specs,
        score_to_chord_sequence,
        parse_ireal_url,
        transpose_note,
        transpose_chord,
        transpose_score,
        tonal_resolver,
        get_patterns,
        chord_events,
        generate_events,
        fallback_chord_notes,
        resolve_skeleton,
        apply_skeleton,
        list_skeletons,
    )
}


def _decode(value):
    if isinstance(value, dict) and "measures" in value:
        return Score(
            measures=value["measures"],
            title=value.get("title", "Untitled"),
            composer=value.get("composer", ""),
            key=value.get("key", "C"),
            time_signature=tuple(value.get("time_signature", (4, 4))),
        )
    return value


def _decode_kwarg(name: str, value):
    return tuple(value) if name == "time_signature" else _decode(value)


def to_json(value):
    """``value`` in the JSON form cases use."""
    if isinstance(value, Score):
        return {
            "measures": to_json(value.measures),
            "title": value.title,
            "composer": value.composer,
            "key": value.key,
            "time_signature": to_json(value.time_signature),
        }
    if isinstance(value, MidiEvent):
        return [value.time, value.channel, value.note, value.velocity, value.duration]
    if hasattr(value, "__dataclass_fields__"):  # a pattern
        return {k: to_json(getattr(value, k)) for k in value.__dataclass_fields__}
    if isinstance(value, (tuple, list)):
        return [to_json(v) for v in value]
    if isinstance(value, dict):
        return {k: to_json(v) for k, v in value.items()}
    return value


def _check_kwargs(name: str, func, kwargs: dict) -> None:
    params = inspect.signature(func).parameters
    for kw in kwargs:
        if kw not in params or params[kw].kind is not inspect.Parameter.KEYWORD_ONLY:
            raise ValueError(
                f"Case for {name}: {kw!r} is not a keyword-only parameter; pass it in args"
            )


def run_case(case: dict):
    """Call the case's function on its arguments; return the result in JSON form."""
    name = case["fn"]
    if name not in TWIN_FUNCTIONS:
        raise ValueError(
            f"Unknown function in case: {name!r}; one of {list(TWIN_FUNCTIONS)}"
        )
    func = TWIN_FUNCTIONS[name]
    kwargs = case.get("kwargs", {})
    _check_kwargs(name, func, kwargs)
    try:
        args = [_decode(a) for a in case.get("args", [])]
        result = func(*args, **{k: _decode_kwarg(k, v) for k, v in kwargs.items()})
    except RAISES as error:
        return {"$raises": type(error).__name__}
    return to_json(result)


def same(result, expected) -> bool:
    """Whether two JSON values are equal, order included (what both test suites check)."""
    return json.dumps(result, ensure_ascii=False) == json.dumps(
        expected, ensure_ascii=False
    )


def load(root: Path | str = REPO_ROOT) -> dict:
    """The parsed ``<root>/fixtures/cases.json``."""
    return json.loads((Path(root) / CASES_PATH).read_text(encoding="utf-8"))


def record(root: Path | str = REPO_ROOT) -> Path:
    """Rewrite every case's ``expected`` (and the ``functions`` list) from Python."""
    path = Path(root) / CASES_PATH
    data = load(root)
    data["functions"] = list(TWIN_FUNCTIONS)
    for case in data["cases"]:
        case["expected"] = run_case(case)
    path.write_text(dumps(data), encoding="utf-8")
    return path


def dumps(data: dict) -> str:
    """The cases file's text: one case per line, so a diff shows exactly which cases changed."""

    def line(obj) -> str:
        return json.dumps(obj, ensure_ascii=False)

    head = {k: v for k, v in data.items() if k != "cases"}
    rows = ",\n".join("  " + line(case) for case in data["cases"])
    fields = "".join(f"\n {line(k)}: {line(v)}," for k, v in head.items())
    return "{" + fields + '\n "cases": [\n' + rows + "\n ]\n}\n"


if __name__ == "__main__":
    print(record())
