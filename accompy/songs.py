"""Songs as backing-track input: a ``songleaf`` Song becomes a ChordSequence.

``songleaf`` keeps a song as lyrics plus standoff chord annotations anchored on
syllables; it has no durations. :func:`song_to_chord_sequence` supplies them with
two simple, explicit heuristics:

- ``beats_per_chord=N``: every chord lasts ``N`` beats;
- ``bars_per_line=N``: every chord-carrying line lasts ``N`` bars, shared equally by
  the chords on it (so a two-chord line at ``bars_per_line=1`` gives each chord half a
  bar);
- neither (the default): every chord lasts one bar.

The converter reads a Song by shape (``text``, ``annotations`` of ``kind``/``start``/
``body``, ``meta``), so ``songleaf`` is not a dependency of ``accompy``.

>>> from types import SimpleNamespace as NS
>>> song = NS(
...     text="Hello there\\nGoodbye now",
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
"""

from __future__ import annotations

from typing import Any, Optional

from .converters import ChordSequence

#: Meta keys tried, in order, for the key of the chart.
_KEY_FIELDS = ("key",)


def _line_index(starts: list[int], offset: int) -> int:
    """Index of the line containing ``offset`` (``starts`` are the lines' start offsets)."""
    index = 0
    for i, start in enumerate(starts):
        if start <= offset:
            index = i
    return index


def song_to_chord_sequence(
    song: Any,
    *,
    bars_per_line: Optional[float] = None,
    beats_per_chord: Optional[float] = None,
    beats_per_bar: int = 4,
    tempo: int = 120,
) -> ChordSequence:
    """Convert a songleaf-shaped ``song`` to a :class:`~accompy.converters.ChordSequence`.

    Args:
        song: Anything with ``text``, ``annotations`` and ``meta`` as songleaf's ``Song``.
        bars_per_line: Bars each chord-carrying line lasts, shared by its chords.
        beats_per_chord: Beats every chord lasts. Exclusive with ``bars_per_line``.
        beats_per_bar: Beats in a bar (the time signature's numerator).
        tempo: Tempo in BPM (the song's ``meta["tempo"]`` wins when it is a number).

    Returns:
        A ChordSequence whose ``sections`` follow the song's ``section`` annotations
        (ranges over the chords), with the song's title and key.

    Raises:
        ValueError: if both ``bars_per_line`` and ``beats_per_chord`` are given, or
            either is not positive.
    """
    if bars_per_line is not None and beats_per_chord is not None:
        raise ValueError("give bars_per_line or beats_per_chord, not both")
    for name, value in (("bars_per_line", bars_per_line), ("beats_per_chord", beats_per_chord)):
        if value is not None and value <= 0:
            raise ValueError(f"{name} must be positive, got {value!r}")

    text = song.text
    starts, offset = [], 0
    for line in text.split("\n"):
        starts.append(offset)
        offset += len(line) + 1

    chord_notes = [
        a for a in song.annotations
        if a.kind == "chord" and str(a.body.get("symbol", "")).strip()
    ]
    by_line: dict[int, list[Any]] = {}
    for note in chord_notes:
        by_line.setdefault(_line_index(starts, note.start), []).append(note)

    events: list[tuple[str, float]] = []
    positions: list[int] = []  # the text offset each event came from (for sections)
    for line in sorted(by_line):
        notes = by_line[line]
        if beats_per_chord is not None:
            share = float(beats_per_chord)
        elif bars_per_line is not None:
            share = bars_per_line * beats_per_bar / len(notes)
        else:
            share = float(beats_per_bar)
        for note in notes:
            events.append((str(note.body["symbol"]).strip(), float(share)))
            positions.append(note.start)

    sections = []
    for sec in (a for a in song.annotations if a.kind == "section"):
        # A bare label marker (start == end) holds no chords of its own.
        inside = [i for i, pos in enumerate(positions) if sec.start <= pos < max(sec.end, sec.start + 1)]
        if inside:
            sections.append((str(sec.body.get("label", "")), inside[0], inside[-1] + 1))

    meta = getattr(song, "meta", {}) or {}
    tempo_meta = meta.get("tempo")
    return ChordSequence(
        chords=events,
        title=str(meta.get("title", "")),
        key=next((str(meta[k]) for k in _KEY_FIELDS if meta.get(k)), "C"),
        tempo=int(tempo_meta) if isinstance(tempo_meta, (int, float)) else tempo,
        time_signature=(beats_per_bar, 4),
        sections=sections,
    )
