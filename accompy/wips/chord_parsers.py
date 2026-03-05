"""
Chord sheet parsers — convert various text formats to ChordSequence.

Registered converters: ChordSheet -> ChordSequence

Supported formats:
- Plain text: "C Am F G" or "| Dm7 | G7 | Cmaj7 |"
- iReal Pro URLs: "irealb://..."
- ChordPro: "[C]lyrics [Am]more lyrics"
- MusicGen-Chord format: "C D:min G:7 C" (space-separated bars)

Each parser is registered in the global converter registry so you can do::

    from accompy.wips.types import convert, ChordSheet, ChordSequence
    cs = convert(ChordSheet("| Dm7 | G7 | Cmaj7 |"), ChordSequence)
"""

from __future__ import annotations

import re
from typing import Optional

from .types import ChordSequence, ChordSheet, converter


# ---------------------------------------------------------------------------
# Plain-text chord sheet parser
# ---------------------------------------------------------------------------


def parse_plain_text(
    sheet: str | ChordSheet,
    *,
    beats_per_bar: int = 4,
    tempo: int = 120,
    title: str = "",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> ChordSequence:
    """Parse a plain-text chord sheet into a ChordSequence.

    Supports:
    - Bar-line format: "| C | Am | F | G |"
    - Multi-chord bars: "| C Am | F G |"
    - Space-separated: "C Am F G"
    - Repeat markers: "%" repeats previous chord/bar

    >>> cs = parse_plain_text("| Dm7 | G7 | Cmaj7 |")
    >>> cs.symbols
    ['Dm7', 'G7', 'Cmaj7']
    >>> cs.durations
    [4.0, 4.0, 4.0]

    >>> cs = parse_plain_text("| C Am | F G |")
    >>> cs.symbols
    ['C', 'Am', 'F', 'G']
    >>> cs.durations
    [2.0, 2.0, 2.0, 2.0]

    >>> cs = parse_plain_text("C Am F G")
    >>> len(cs)
    4
    """
    sheet = str(sheet).strip()
    beats_per_bar = time_signature[0] if time_signature else beats_per_bar
    chords: list[tuple[str, float]] = []

    if "|" in sheet:
        # Bar-line format
        bars = [b.strip() for b in sheet.split("|") if b.strip()]
        last_chord = "C"
        for bar in bars:
            symbols = bar.split()
            beats_each = beats_per_bar / len(symbols) if symbols else beats_per_bar
            for sym in symbols:
                if sym in ("%", "x"):
                    sym = last_chord
                chords.append((sym, float(beats_each)))
                last_chord = sym
    else:
        # Space-separated, one chord per bar
        symbols = sheet.split()
        last_chord = "C"
        for sym in symbols:
            if sym in ("%", "x"):
                sym = last_chord
            chords.append((sym, float(beats_per_bar)))
            last_chord = sym

    return ChordSequence(
        chords=chords,
        title=title,
        key=key,
        tempo=tempo,
        time_signature=time_signature,
    )


# ---------------------------------------------------------------------------
# iReal Pro URL parser
# ---------------------------------------------------------------------------


def parse_ireal_url(
    url: str | ChordSheet,
    *,
    beats_per_bar: int = 4,
) -> ChordSequence:
    """Parse an iReal Pro URL into a ChordSequence.

    Uses pyRealParser if available, falls back to basic extraction.

    >>> # Can't test without real URL, but structure is tested
    """
    url = str(url)
    try:
        from pyRealParser import Tune

        tunes = Tune.parse_ireal_url(url)
        if not tunes:
            raise ValueError("No songs found in URL")
        tune = tunes[0]
        measures = tune.measures_as_strings
        chords = [
            (chord, float(beats_per_bar))
            for chord in measures
            if chord and chord.strip()
        ]
        ts = _parse_ts_string(tune.time_signature)
        return ChordSequence(
            chords=chords,
            title=tune.title or "",
            key=tune.key or "C",
            tempo=int(tune.bpm) if hasattr(tune, "bpm") and tune.bpm else 120,
            time_signature=ts,
        )
    except ImportError:
        return _parse_ireal_url_fallback(url, beats_per_bar=beats_per_bar)


def _parse_ts_string(ts: Optional[str]) -> tuple[int, int]:
    """Parse '3/4' -> (3, 4), default (4, 4)."""
    if not ts:
        return (4, 4)
    try:
        parts = ts.split("/")
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return (4, 4)


def _parse_ireal_url_fallback(
    url: str, *, beats_per_bar: int = 4
) -> ChordSequence:
    """Minimal iReal URL parser without pyRealParser."""
    from urllib.parse import unquote

    raw = url
    if raw.startswith(("irealbook://", "irealb://")):
        raw = raw.split("://", 1)[1]
    raw = unquote(raw)
    parts = raw.split("=")

    title = parts[0] if parts else "Untitled"
    key = parts[3] if len(parts) > 3 and parts[3] else "C"

    if len(parts) < 6:
        raise ValueError("Invalid iReal Pro URL format")

    chord_data = parts[5]
    for marker in ["{", "}", "[", "]", "Z", "*", "Y", "Q", "S", "T"]:
        chord_data = chord_data.replace(marker, " ")
    chord_data = re.sub(r"\*[A-Za-z]", " ", chord_data)
    chord_data = re.sub(r"N\d", " ", chord_data)
    chord_data = re.sub(r"<[^>]*>", " ", chord_data)

    tokens = re.split(r"[|\s]+", chord_data)
    chords: list[tuple[str, float]] = []
    for token in tokens:
        token = token.strip()
        if not token or token in ("n", "x", "r", "%", "p", "s", "l"):
            continue
        match = re.match(r"^([A-G][#b]?)(.*)", token)
        if match:
            chords.append((match.group(0), float(beats_per_bar)))

    return ChordSequence(chords=chords, title=title, key=key)


# ---------------------------------------------------------------------------
# ChordPro parser
# ---------------------------------------------------------------------------


def parse_chordpro(
    sheet: str | ChordSheet,
    *,
    beats_per_bar: int = 4,
    tempo: int = 120,
) -> ChordSequence:
    """Parse ChordPro format into a ChordSequence.

    ChordPro embeds chords in brackets within lyrics:
    "[Am]Hello [G]world [C]"

    Extracts just the chord symbols, one per bar by default.

    >>> cs = parse_chordpro("[Am]Hello [G]world [C]")
    >>> cs.symbols
    ['Am', 'G', 'C']
    """
    sheet = str(sheet)
    # Extract chord symbols from [brackets]
    symbols = re.findall(r"\[([A-G][^\]]*)\]", sheet)

    # Extract metadata directives
    title = ""
    key = "C"
    title_match = re.search(r"\{title:\s*([^}]+)\}", sheet, re.IGNORECASE)
    if title_match:
        title = title_match.group(1).strip()
    key_match = re.search(r"\{key:\s*([^}]+)\}", sheet, re.IGNORECASE)
    if key_match:
        key = key_match.group(1).strip()
    tempo_match = re.search(r"\{tempo:\s*(\d+)\}", sheet, re.IGNORECASE)
    if tempo_match:
        tempo = int(tempo_match.group(1))

    chords = [(sym, float(beats_per_bar)) for sym in symbols if sym.strip()]
    return ChordSequence(
        chords=chords, title=title, key=key, tempo=tempo,
    )


# ---------------------------------------------------------------------------
# MusicGen-Chord format parser
# ---------------------------------------------------------------------------


def parse_musicgen_chord_format(
    sheet: str | ChordSheet,
    *,
    beats_per_bar: int = 4,
    tempo: int = 120,
) -> ChordSequence:
    """Parse MusicGen-Chord text format into ChordSequence.

    MusicGen-Chord uses space-separated bars with colon for quality:
    "C D:min G:7 C" means C | Dm | G7 | C

    Within a bar, comma separates chords:
    "C:maj,G:maj E:min,A:min" means C G | Em Am

    >>> cs = parse_musicgen_chord_format("C D:min G:7 C")
    >>> cs.symbols
    ['C', 'D:min', 'G:7', 'C']
    >>> cs.durations
    [4.0, 4.0, 4.0, 4.0]

    >>> cs = parse_musicgen_chord_format("C:maj,G:maj E:min")
    >>> len(cs)
    3
    """
    sheet = str(sheet).strip()
    bars = sheet.split()
    chords: list[tuple[str, float]] = []

    for bar in bars:
        if "," in bar:
            sub_chords = bar.split(",")
            beats_each = beats_per_bar / len(sub_chords)
            for sc in sub_chords:
                chords.append((sc.strip(), float(beats_each)))
        else:
            chords.append((bar, float(beats_per_bar)))

    return ChordSequence(chords=chords, tempo=tempo)


# ---------------------------------------------------------------------------
# Auto-detect parser
# ---------------------------------------------------------------------------


def parse_chord_sheet(
    sheet: str | ChordSheet,
    *,
    beats_per_bar: int = 4,
    tempo: int = 120,
    title: str = "",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> ChordSequence:
    """Auto-detect format and parse a chord sheet into ChordSequence.

    Detects:
    - iReal Pro URLs (starts with 'irealb://' or 'irealbook://')
    - ChordPro (contains '[' chord brackets AND text between them)
    - MusicGen-Chord format (contains ':' colons in chord symbols)
    - Plain text (everything else)

    >>> cs = parse_chord_sheet("| Dm7 | G7 | Cmaj7 |")
    >>> cs.symbols
    ['Dm7', 'G7', 'Cmaj7']

    >>> cs = parse_chord_sheet("[Am]Hello [G]world")
    >>> cs.symbols
    ['Am', 'G']
    """
    sheet = str(sheet).strip()

    if sheet.startswith(("irealb://", "irealbook://")):
        return parse_ireal_url(sheet, beats_per_bar=beats_per_bar)

    if re.search(r"\[[A-G]", sheet) and re.search(r"\][^|[\]]+\[", sheet):
        return parse_chordpro(sheet, beats_per_bar=beats_per_bar, tempo=tempo)

    if ":" in sheet and not "|" in sheet:
        return parse_musicgen_chord_format(
            sheet, beats_per_bar=beats_per_bar, tempo=tempo
        )

    return parse_plain_text(
        sheet,
        beats_per_bar=beats_per_bar,
        tempo=tempo,
        title=title,
        key=key,
        time_signature=time_signature,
    )


# ---------------------------------------------------------------------------
# Register converters
# ---------------------------------------------------------------------------

converter.register(
    ChordSheet,
    ChordSequence,
    parse_chord_sheet,
    name="auto_detect",
    is_default=True,
)

converter.register(
    ChordSheet, ChordSequence, parse_plain_text, name="plain_text"
)

converter.register(
    ChordSheet, ChordSequence, parse_chordpro, name="chordpro"
)

converter.register(
    ChordSheet,
    ChordSequence,
    parse_musicgen_chord_format,
    name="musicgen_chord",
)

# Also register str -> ChordSequence for convenience
converter.register(
    str, ChordSequence, parse_chord_sheet, name="auto_detect", is_default=True
)
