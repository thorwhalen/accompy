"""
Utility functions for chord parsing and normalization.

Contains helpers for chord symbol normalization, chord string parsing,
and iReal URL parsing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional


#: The suffix rewrites :func:`normalize_chord_symbol` applies: each ``old`` becomes
#: ``new`` at the end of the symbol or of a part before a slash (longest ``old`` wins).
CHORD_SYMBOL_REPLACEMENTS = (
    ("maj7", "^7"),
    ("maj9", "^9"),
    ("maj", "^"),
    ("min7", "-7"),
    ("min", "-"),
    ("m7", "-7"),
    ("m9", "-9"),
    ("m", "-"),
    ("dim7", "o7"),
    ("dim", "o"),
    ("m7b5", "h7"),
    ("ø7", "h7"),
    ("ø", "h"),
    ("sus4", "sus"),
    ("sus2", "sus2"),
    ("add9", "add9"),
    ("add2", "add2"),
)

# Longest first (a stable sort: equal lengths keep the table's order).
_REPLACEMENTS_LONGEST_FIRST = sorted(
    CHORD_SYMBOL_REPLACEMENTS, key=lambda pair: len(pair[0]), reverse=True
)

#: Symbols :func:`normalize_chord_symbol` returns unchanged (no chord, or a repeat sign).
UNNORMALIZED_SYMBOLS = ("", "n", "N.C.", "NC", "%", "x")


def normalize_chord_symbol(symbol: str) -> str:
    """
    Normalize chord symbols to a standard format.

    Handles conversions like:
    - Cm -> C-
    - Cmaj7 -> C^7
    - Cdim -> Co
    - Cm7b5 -> Ch7 (half-diminished)

    Each ``/``-separated part of the symbol has its longest matching suffix from
    :data:`CHORD_SYMBOL_REPLACEMENTS` rewritten, once (so ``dim`` is never read as a
    word ending in ``m``).

    Example:
        >>> normalize_chord_symbol("Cmaj7")
        'C^7'
        >>> normalize_chord_symbol("Dm7b5")
        'Dh7'
        >>> normalize_chord_symbol("Cdim7"), normalize_chord_symbol("Bbm7/F")
        ('Co7', 'Bb-7/F')
    """
    symbol = symbol.strip()
    if not symbol or symbol in UNNORMALIZED_SYMBOLS:
        return symbol
    return "/".join(_rewrite_suffix(part) for part in symbol.split("/"))


def _rewrite_suffix(part: str) -> str:
    """``part`` with its longest suffix in :data:`CHORD_SYMBOL_REPLACEMENTS` rewritten."""
    for old, new in _REPLACEMENTS_LONGEST_FIRST:
        if part.endswith(old):
            return part[: -len(old)] + new
    return part


def parse_chord_string(chord_string: str) -> list[list[str]]:
    """
    Parse a chord string into measures, each containing chord symbols.

    Example:
        >>> parse_chord_string("| C | Am | F | G |")
        [['C'], ['A-'], ['F'], ['G']]
        >>> parse_chord_string("| C Am | F G |")
        [['C', 'A-'], ['F', 'G']]
    """
    # Clean up
    chord_string = chord_string.strip()

    # Split by bar lines if present
    if "|" in chord_string:
        parts = [p.strip() for p in chord_string.split("|") if p.strip()]
    else:
        # Space-separated, one chord per bar
        parts = [[c] for c in chord_string.split() if c.strip()]
        return [[normalize_chord_symbol(c) for c in measure] for measure in parts]

    measures = []
    last_chord = None

    for part in parts:
        chords_in_bar = [c.strip() for c in part.split() if c.strip()]
        normalized = []

        for chord in chords_in_bar:
            if chord in ("%", "x"):
                # Repeat previous bar
                chord = last_chord if last_chord else "C"
            chord = normalize_chord_symbol(chord)
            normalized.append(chord)
            last_chord = chord

        if normalized:
            measures.append(normalized)

    return measures


def parse_time_sig(ts_str: Optional[str]) -> tuple[int, int]:
    """
    Parse time signature string like '4/4' into tuple.

    Example:
        >>> parse_time_sig("3/4")
        (3, 4)
        >>> parse_time_sig("6/8")
        (6, 8)
        >>> parse_time_sig(None)
        (4, 4)
    """
    if not ts_str:
        return (4, 4)
    if isinstance(ts_str, tuple):
        return ts_str  # already a tuple
    try:
        parts = ts_str.split("/")
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError, AttributeError):
        return (4, 4)


def parse_ireal_url(url: str):
    """
    Parse an iReal Pro URL (``irealb://`` or ``irealbook://``) into a Score.

    Decoding is :func:`accompy.ireal.decode_ireal_url`; the Score is the first tune of
    the URL that has chords, each bar the list of its chords as written (iReal chord
    notation). Raises ``ValueError`` when no tune has chords.

    >>> score = parse_ireal_url("irealbook://Blues=Me=Swing=F=n=[T34F7 |Bb7 Bo7 |C7 Z")
    >>> score.measures, score.time_signature
    ([['F7'], ['Bb7', 'Bo7'], ['C7']], (3, 4))
    """
    from .base import Score
    from .ireal import decode_ireal_url

    for tune in decode_ireal_url(url):
        measures = [bar for bar in tune.measures if bar]
        if measures:
            return Score(
                measures=measures,
                title=tune.title or "Untitled",
                composer=tune.composer,
                key=tune.key or "C",
                time_signature=tune.time_signature,
            )
    raise ValueError("No chords found in iReal Pro URL")


def parse_ireal_html(html_path: str) -> "Score":
    """
    Extract a Score from an iReal Pro HTML export file.

    iReal Pro can export songs as HTML files containing an ``irealb://`` link.
    This function reads the file, extracts that link, and parses it into a
    :class:`Score`.

    Args:
        html_path: Path to the HTML file exported from iReal Pro.

    Returns:
        A Score with measures, title, key, and time signature.

    Raises:
        FileNotFoundError: If *html_path* does not exist.
        ValueError: If no iReal URL is found in the HTML.

    Example::

        >>> score = parse_ireal_html("/path/to/song.html")  # doctest: +SKIP
        >>> score.title  # doctest: +SKIP
        'Autumn Leaves'
    """
    path = Path(html_path)
    html = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r'href="(irealb://[^"]+)"', html)
    if not match:
        # Maybe the file *is* a raw iReal URL
        stripped = html.strip()
        if stripped.startswith(("irealb://", "irealbook://")):
            return parse_ireal_url(stripped)
        raise ValueError(f"No iReal URL found in {html_path}")
    return parse_ireal_url(match.group(1))


def score_from_chord_specs(
    chords: Iterable,  # ChordSpec
    *,
    title: str = "Untitled",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
):
    """
    Create a `Score` from `(chord, beats)` pairs.

    Durations that are multiples of the bar length map cleanly to repeated bars.
    Other durations are approximated by grouping chords into bars.
    """
    from .base import Score

    beats_per_bar = time_signature[0]

    measures: list[list[str]] = []
    current_bar: list[str] = []
    current_beats: float = 0.0

    for chord, beats in chords:
        chord = normalize_chord_symbol(chord)
        if chord in ("", "n", "N.C.", "NC"):
            continue

        if beats <= 0:
            continue

        beats_f = float(beats)
        full_bars = int(beats_f // beats_per_bar)
        rem = beats_f - (full_bars * beats_per_bar)

        for _ in range(full_bars):
            measures.append([chord])

        if rem:
            current_bar.append(chord)
            current_beats += rem
            if current_beats >= beats_per_bar - 1e-9:
                measures.append(current_bar)
                current_bar = []
                current_beats = 0.0

    if current_bar:
        measures.append(current_bar)

    return Score(measures=measures, title=title, key=key, time_signature=time_signature)


# ---------------------------------------------------------------------------
# Transposition helpers
# ---------------------------------------------------------------------------

_SHARP_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT_NOTES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
_NOTE_TO_SEMITONE = {
    n: i for notes in [_SHARP_NOTES, _FLAT_NOTES] for i, n in enumerate(notes)
}
# Add enharmonic extras
_NOTE_TO_SEMITONE.update({"Fb": 4, "E#": 5, "Cb": 11, "B#": 0})

_FLAT_KEYS = frozenset({"F", "Bb", "Eb", "Ab", "Db", "Gb"})


def transpose_note(
    name: str, semitones: int, *, use_flat: Optional[bool] = None
) -> str:
    """Transpose a single note name by *semitones*.

    Args:
        name: Note name like ``"C"``, ``"Eb"``, ``"F#"``.
        semitones: Number of semitones (positive = up, negative = down).
        use_flat: Force flat (True) or sharp (False) spelling.
            ``None`` (default) uses flats for downward transposition.

    Example:
        >>> transpose_note("C", 5)
        'F'
        >>> transpose_note("A", -2)
        'G'
        >>> transpose_note("C", 1, use_flat=True)
        'Db'
    """
    if name not in _NOTE_TO_SEMITONE:
        return name
    idx = (_NOTE_TO_SEMITONE[name] + semitones) % 12
    if use_flat is None:
        use_flat = semitones < 0
    notes = _FLAT_NOTES if use_flat else _SHARP_NOTES
    return notes[idx]


def transpose_chord(
    chord: str, semitones: int, *, use_flat: Optional[bool] = None
) -> str:
    """Transpose a chord symbol by *semitones*.

    Handles slash chords (e.g. ``"C6/E"``).

    Args:
        chord: Chord symbol like ``"Am7"``, ``"C6/E"``, ``"G#o"``.
        semitones: Number of semitones.
        use_flat: Force flat/sharp spelling (see :func:`transpose_note`).

    Example:
        >>> transpose_chord("Am7", 2)
        'Bm7'
        >>> transpose_chord("C6/E", 5)
        'F6/A'
        >>> transpose_chord("G#o", -2, use_flat=True)
        'Gbo'
    """
    if not chord or chord in ("", "N.C.", "NC"):
        return chord

    # Handle slash chords
    if "/" in chord:
        parts = chord.split("/", 1)
        main = transpose_chord(parts[0], semitones, use_flat=use_flat)
        bass = transpose_chord(parts[1], semitones, use_flat=use_flat)
        return f"{main}/{bass}"

    match = re.match(r"^([A-G][#b]?)(.*)", chord)
    if not match:
        return chord

    root, quality = match.group(1), match.group(2)
    new_root = transpose_note(root, semitones, use_flat=use_flat)
    return new_root + quality


def transpose_score(score, target_key: str) -> "Score":
    """Transpose a :class:`Score` to a new key.

    The spelling (sharp vs flat) is chosen automatically based on the
    *target_key*.

    Args:
        score: A :class:`Score` instance.
        target_key: Target key, e.g. ``"Eb"``, ``"G"``, ``"F#"``.

    Returns:
        A new Score in the target key with an updated title.

    Example:
        >>> from accompy import Score
        >>> s = Score.from_string("| C | Am | F | G |", key="C")
        >>> t = transpose_score(s, "G")
        >>> [m[0] for m in t.measures]
        ['G', 'E-', 'C', 'D']
    """
    from .base import Score as _Score

    src_idx = _NOTE_TO_SEMITONE.get(score.key, 0)
    tgt_idx = _NOTE_TO_SEMITONE.get(target_key, 0)
    semitones = tgt_idx - src_idx
    use_flat = "b" in target_key or target_key in _FLAT_KEYS

    new_measures = [
        [transpose_chord(c, semitones, use_flat=use_flat) for c in measure]
        for measure in score.measures
    ]
    return _Score(
        measures=new_measures,
        title=f"{score.title} ({target_key})",
        composer=score.composer,
        key=target_key,
        time_signature=score.time_signature,
    )
