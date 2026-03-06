"""
Utility functions for chord parsing and normalization.

Contains helpers for chord symbol normalization, chord string parsing,
and iReal URL parsing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import unquote


def normalize_chord_symbol(symbol: str) -> str:
    """
    Normalize chord symbols to a standard format.

    Handles conversions like:
    - Cm -> C-
    - Cmaj7 -> C^7
    - Cdim -> Co
    - Cm7b5 -> Ch7 (half-diminished)

    Example:
        >>> normalize_chord_symbol("Cmaj7")
        'C^7'
        >>> normalize_chord_symbol("Dm7b5")
        'Dh7'
    """
    symbol = symbol.strip()
    if not symbol or symbol in ("", "n", "N.C.", "NC", "%", "x"):
        return symbol

    # Common normalizations
    replacements = [
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
    ]

    result = symbol
    for old, new in replacements:
        # Only replace if it's at the end or followed by a slash
        if result.endswith(old):
            result = result[: -len(old)] + new
        elif f"{old}/" in result:
            result = result.replace(f"{old}/", f"{new}/")

    return result


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
    try:
        parts = ts_str.split("/")
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return (4, 4)


def parse_ireal_url(url: str):
    """
    Parse an iReal Pro URL into a Score object.

    Tries to use pyRealParser if available, falls back to built-in parser.
    """
    try:
        from pyRealParser import Tune

        tunes = Tune.parse_ireal_url(url)
        if not tunes:
            raise ValueError("No songs found in URL")

        tune = tunes[0]
        measures = [[chord] for chord in tune.measures_as_strings if chord]

        from .base import Score

        return Score(
            measures=measures,
            title=tune.title or "Untitled",
            composer=tune.composer or "",
            key=tune.key or "C",
            time_signature=parse_time_sig(tune.time_signature),
        )
    except ImportError:
        # Best-effort fallback parser (no external deps)
        return parse_ireal_url_fallback(url)


def parse_ireal_url_fallback(url: str):
    """
    Best-effort iReal Pro URL parser (no external dependencies).

    This is intentionally conservative: it extracts a usable chord progression but
    does not attempt to perfectly replicate iReal Pro's full encoding.
    """
    from .base import Score, ChordSpec

    raw = url
    if raw.startswith("irealbook://") or raw.startswith("irealb://"):
        raw = raw.split("://", 1)[1]

    raw = unquote(raw)
    parts = raw.split("=")

    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled"
    composer = parts[1] if len(parts) > 1 else ""
    key = parts[3] if len(parts) > 3 and parts[3] else "C"

    if len(parts) < 6:
        raise ValueError("Invalid iReal Pro URL format")

    chord_data = parts[5]

    # Clean up structural markers
    for marker in ["{", "}", "[", "]", "Z", "*", "Y", "Q", "S", "T"]:
        chord_data = chord_data.replace(marker, " ")

    # Remove section markers like *A, *B, N1, N2
    chord_data = re.sub(r"\*[A-Za-z]", " ", chord_data)
    chord_data = re.sub(r"N\d", " ", chord_data)
    chord_data = re.sub(r"<[^>]*>", " ", chord_data)

    # Split by barlines/whitespace
    tokens = re.split(r"[|\s]+", chord_data)

    chords: list[ChordSpec] = []
    for token in tokens:
        token = token.strip()
        if not token or token in ("n", "x", "r", "%", "p", "s", "l"):
            continue

        match = re.match(r"^([A-G][#b]?)(.*)", token)
        if not match:
            continue

        root = match.group(1)
        suffix = match.group(2)

        # Convert iReal notation to more standard symbols
        suffix = suffix.replace("^", "maj")
        suffix = suffix.replace("-", "m")
        suffix = suffix.replace("h", "m7b5")
        suffix = suffix.replace("o", "dim")
        suffix = suffix.replace("+", "aug")

        # Handle slash chords (ignore bass note)
        if "/" in suffix:
            suffix = suffix.split("/")[0]

        # Handle commas (multiple chords per bar) - take first
        if "," in suffix:
            suffix = suffix.split(",")[0]

        chord = root + suffix
        if chord:
            chords.append((chord, 4))

    from .base import ensure_score

    score = ensure_score(chords, title=title, key=key)
    score.composer = composer
    return score


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
