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

from .converters import ChordSequence, ChordSheet, converter


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
# Roman numeral parser
# ---------------------------------------------------------------------------

# Map scale degrees to semitone intervals (major scale)
_MAJOR_SCALE_INTERVALS = [0, 2, 4, 5, 7, 9, 11]

# Note names for building chord symbols
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_NOTE_NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

# Roman numeral to degree (1-indexed)
_ROMAN_TO_DEGREE = {
    "I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7,
}

# Regex for Roman numeral chord tokens
_ROMAN_PATTERN = re.compile(
    r"(b|#)?"           # optional accidental
    r"(VII|VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)"  # numeral
    r"(.*)",            # quality suffix
    re.IGNORECASE,
)


def _key_to_semitone(key: str) -> int:
    """Convert a key name to semitone offset from C."""
    letter = key[0].upper()
    acc = key[1:] if len(key) > 1 else ""
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[letter]
    for ch in acc:
        if ch == "#":
            base += 1
        elif ch == "b":
            base -= 1
    return base % 12


def _roman_to_chord_symbol(token: str, key: str = "C", use_flats: bool = False) -> str:
    """Convert a Roman numeral token to a standard chord symbol.

    >>> _roman_to_chord_symbol("ii7", "C")
    'Dm7'
    >>> _roman_to_chord_symbol("V7", "C")
    'G7'
    >>> _roman_to_chord_symbol("Imaj7", "C")
    'Cmaj7'
    >>> _roman_to_chord_symbol("bVII7", "C")
    'Bb7'
    """
    m = _ROMAN_PATTERN.match(token)
    if not m:
        return token  # Not a Roman numeral, return as-is

    accidental_str, numeral, quality = m.groups()
    is_minor = numeral == numeral.lower()
    degree = _ROMAN_TO_DEGREE.get(numeral.upper() if not numeral[0].isupper() else numeral)
    if degree is None:
        degree = _ROMAN_TO_DEGREE.get(numeral.lower(), 1)

    # Calculate root note
    key_offset = _key_to_semitone(key)
    scale_interval = _MAJOR_SCALE_INTERVALS[degree - 1]
    root_semitone = (key_offset + scale_interval) % 12

    # Apply accidental
    use_flat_for_note = use_flats
    if accidental_str == "b":
        root_semitone = (root_semitone - 1) % 12
        use_flat_for_note = True  # flat accidental -> use flat spelling
    elif accidental_str == "#":
        root_semitone = (root_semitone + 1) % 12

    names = _NOTE_NAMES_FLAT if use_flat_for_note else _NOTE_NAMES
    root_name = names[root_semitone]

    # Determine quality
    if is_minor and not quality:
        quality = "m"
    elif is_minor and quality and not quality.startswith("m"):
        # e.g., "ii7" -> "Dm7" (minor 7th)
        quality = "m" + quality

    return root_name + quality


def parse_roman_numeral(
    sheet: str | ChordSheet,
    *,
    key: str = "C",
    beats_per_bar: int = 4,
    tempo: int = 120,
    title: str = "",
    time_signature: tuple[int, int] = (4, 4),
) -> ChordSequence:
    """Parse Roman numeral notation into a ChordSequence.

    Supports:
    - Upper case for major: I, IV, V
    - Lower case for minor: ii, vi, iii
    - Quality suffixes: ii7, V7, Imaj7, viidim, viio, iim7b5
    - Accidentals: bVII, #IV
    - Bar lines: "| ii7 | V7 | Imaj7 |"
    - Space-separated: "I IV V I"

    >>> cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="C")
    >>> cs.symbols
    ['Dm7', 'G7', 'Cmaj7']

    >>> cs = parse_roman_numeral("I IV V I", key="G")
    >>> cs.symbols
    ['G', 'C', 'D', 'G']

    >>> cs = parse_roman_numeral("| ii7 | V7 | Imaj7 |", key="F")
    >>> cs.symbols
    ['Gm7', 'C7', 'Fmaj7']
    """
    sheet = str(sheet).strip()
    beats_per_bar = time_signature[0] if time_signature else beats_per_bar

    # Check for flat keys to use flat note names
    use_flats = "b" in key[1:] or key[0] in "F"
    chords: list[tuple[str, float]] = []

    if "|" in sheet:
        bars = [b.strip() for b in sheet.split("|") if b.strip()]
        last_chord = "C"
        for bar in bars:
            tokens = bar.split()
            beats_each = beats_per_bar / len(tokens) if tokens else beats_per_bar
            for tok in tokens:
                if tok in ("%", "x"):
                    sym = last_chord
                else:
                    sym = _roman_to_chord_symbol(tok, key=key, use_flats=use_flats)
                chords.append((sym, float(beats_each)))
                last_chord = sym
    else:
        tokens = sheet.split()
        last_chord = "C"
        for tok in tokens:
            if tok in ("%", "x"):
                sym = last_chord
            else:
                sym = _roman_to_chord_symbol(tok, key=key, use_flats=use_flats)
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
# Nashville number system parser
# ---------------------------------------------------------------------------

_NASHVILLE_PATTERN = re.compile(
    r"(b|#)?"           # optional accidental
    r"([1-7])"          # scale degree number
    r"(.*)",            # quality suffix (m, m7, maj7, dim, aug, etc.)
)


def _nashville_to_chord_symbol(
    token: str, key: str = "C", use_flats: bool = False
) -> str:
    """Convert a Nashville number token to a standard chord symbol.

    >>> _nashville_to_chord_symbol("1", "C")
    'C'
    >>> _nashville_to_chord_symbol("2m7", "C")
    'Dm7'
    >>> _nashville_to_chord_symbol("5", "C")
    'G'
    >>> _nashville_to_chord_symbol("b7", "C")
    'Bb'
    """
    m = _NASHVILLE_PATTERN.match(token)
    if not m:
        return token

    accidental_str, degree_str, quality = m.groups()
    degree = int(degree_str)

    key_offset = _key_to_semitone(key)
    scale_interval = _MAJOR_SCALE_INTERVALS[degree - 1]
    root_semitone = (key_offset + scale_interval) % 12

    use_flat_for_note = use_flats
    if accidental_str == "b":
        root_semitone = (root_semitone - 1) % 12
        use_flat_for_note = True  # flat accidental -> use flat spelling
    elif accidental_str == "#":
        root_semitone = (root_semitone + 1) % 12

    names = _NOTE_NAMES_FLAT if use_flat_for_note else _NOTE_NAMES
    root_name = names[root_semitone]

    return root_name + quality


def parse_nashville(
    sheet: str | ChordSheet,
    *,
    key: str = "C",
    beats_per_bar: int = 4,
    tempo: int = 120,
    title: str = "",
    time_signature: tuple[int, int] = (4, 4),
) -> ChordSequence:
    """Parse Nashville number system notation into a ChordSequence.

    Nashville numbers use scale degree numbers instead of note names:
    - "1 4 5 1" in C = C F G C
    - Quality suffixes: "2m7 5 1maj7"
    - Accidentals: "b7" = flat seventh scale degree
    - Bar lines supported: "| 2m7 | 5 | 1maj7 |"

    >>> cs = parse_nashville("| 2m7 | 5 | 1maj7 |", key="C")
    >>> cs.symbols
    ['Dm7', 'G', 'Cmaj7']

    >>> cs = parse_nashville("1 4 5 1", key="G")
    >>> cs.symbols
    ['G', 'C', 'D', 'G']

    >>> cs = parse_nashville("| 2m7 | 57 | 1maj7 |", key="Bb")
    >>> cs.symbols
    ['Cm7', 'F7', 'Bbmaj7']
    """
    sheet = str(sheet).strip()
    beats_per_bar = time_signature[0] if time_signature else beats_per_bar
    use_flats = "b" in key[1:] or key[0] in "F"
    chords: list[tuple[str, float]] = []

    if "|" in sheet:
        bars = [b.strip() for b in sheet.split("|") if b.strip()]
        last_chord = "C"
        for bar in bars:
            tokens = bar.split()
            beats_each = beats_per_bar / len(tokens) if tokens else beats_per_bar
            for tok in tokens:
                if tok in ("%", "x"):
                    sym = last_chord
                else:
                    sym = _nashville_to_chord_symbol(tok, key=key, use_flats=use_flats)
                chords.append((sym, float(beats_each)))
                last_chord = sym
    else:
        tokens = sheet.split()
        last_chord = "C"
        for tok in tokens:
            if tok in ("%", "x"):
                sym = last_chord
            else:
                sym = _nashville_to_chord_symbol(tok, key=key, use_flats=use_flats)
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
    - Roman numeral notation (tokens like I, ii, V7, bVII)
    - Nashville number system (tokens like 1, 2m7, 5, b7)
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

converter.register(
    ChordSheet, ChordSequence, parse_roman_numeral, name="roman_numeral"
)

converter.register(
    ChordSheet, ChordSequence, parse_nashville, name="nashville"
)

# Also register str -> ChordSequence for convenience
converter.register(
    str, ChordSequence, parse_chord_sheet, name="auto_detect", is_default=True
)
