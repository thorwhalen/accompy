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
    if isinstance(ts_str, tuple):
        return ts_str  # already a tuple
    try:
        parts = ts_str.split("/")
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError, AttributeError):
        return (4, 4)


def parse_ireal_url(url: str):
    """
    Parse an iReal Pro URL into a Score object.

    Tries pyRealParser's ``parse_ireal_url`` first, then falls back to
    constructing a ``Tune`` directly (handles URLs with empty ``==`` fields),
    and finally to a no-dependency best-effort parser.
    """
    from .base import Score

    try:
        from pyRealParser import Tune
    except ImportError:
        return parse_ireal_url_fallback(url)

    # --- Tier 1: pyRealParser.parse_ireal_url (standard path) ---
    try:
        tunes = Tune.parse_ireal_url(url)
        if tunes:
            tune = tunes[0]
            measures = [[chord] for chord in tune.measures_as_strings if chord]
            if measures:
                return Score(
                    measures=measures,
                    title=tune.title or "Untitled",
                    composer=tune.composer or "",
                    key=tune.key or "C",
                    time_signature=parse_time_sig(tune.time_signature),
                )
    except Exception:
        pass

    # --- Tier 2: construct Tune directly from URL fields ---
    # Some iReal URLs (especially single-song HTML exports) have empty fields
    # that cause ``==`` in the URL, which pyRealParser.parse_ireal_url can't
    # handle.  We decode the URL ourselves and construct a Tune manually.
    try:
        tune = _tune_from_ireal_url(url)
        measures = [[chord] for chord in tune.measures_as_strings if chord]
        if measures:
            return Score(
                measures=measures,
                title=tune.title or "Untitled",
                composer=getattr(tune, "composer", "") or "",
                key=tune.key or "C",
                time_signature=parse_time_sig(
                    getattr(tune, "time_signature", None)
                ),
            )
    except Exception:
        pass

    # --- Tier 3: no-dependency fallback ---
    return parse_ireal_url_fallback(url)


def _tune_from_ireal_url(url: str):
    """Construct a ``pyRealParser.Tune`` directly from an iReal URL.

    The iReal single-song URL format (after decoding) is::

        title=composer==style=key=??=chorddata=compstyle=bpm=repeats

    ``parse_ireal_url`` splits on ``==`` (playlist separator) and chokes when
    an empty field produces ``==`` inside a single song.  This helper splits
    on single ``=`` and reconstructs the tune string that the ``Tune()``
    constructor expects.
    """
    from pyRealParser import Tune

    raw = url
    if raw.startswith(("irealbook://", "irealb://")):
        raw = raw.split("://", 1)[1]
    raw = unquote(raw)

    # Split on *single* '=' to preserve empty-field boundaries
    parts = raw.split("=")

    # Find the chord-data part: it contains the scramble prefix
    prefix = "1r34LbKcu7"
    chord_idx = None
    for i, part in enumerate(parts):
        if prefix in part:
            chord_idx = i
            break

    if chord_idx is None:
        raise ValueError("Could not locate chord data in iReal URL")

    # Resolve fields relative to chord_idx
    title = parts[0] if parts[0] else "Untitled"
    composer = parts[1] if len(parts) > 1 else ""
    # key is 2 positions before chord data
    key = parts[chord_idx - 2] if chord_idx >= 2 and len(parts[chord_idx - 2]) <= 2 else "C"
    # style is 1 position before key
    style = parts[chord_idx - 3] if chord_idx >= 3 else ""

    chord_data = parts[chord_idx]

    # Fields after chord data: comp_style, bpm, repeats
    comp_style = parts[chord_idx + 1] if chord_idx + 1 < len(parts) else ""
    bpm_str = parts[chord_idx + 2] if chord_idx + 2 < len(parts) else ""
    repeats_str = parts[chord_idx + 3] if chord_idx + 3 < len(parts) else ""

    # Reconstruct the tune string for pyRealParser.Tune()
    # Expected format: title=composer=style=key=chorddata=compstyle=bpm=repeats
    tune_str = "=".join([title, composer, style, key, chord_data, comp_style, bpm_str, repeats_str])
    return Tune(tune_str)


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
_NOTE_TO_SEMITONE = {n: i for notes in [_SHARP_NOTES, _FLAT_NOTES] for i, n in enumerate(notes)}
# Add enharmonic extras
_NOTE_TO_SEMITONE.update({"Fb": 4, "E#": 5, "Cb": 11, "B#": 0})

_FLAT_KEYS = frozenset({"F", "Bb", "Eb", "Ab", "Db", "Gb"})


def transpose_note(name: str, semitones: int, *, use_flat: Optional[bool] = None) -> str:
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


def transpose_chord(chord: str, semitones: int, *, use_flat: Optional[bool] = None) -> str:
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
