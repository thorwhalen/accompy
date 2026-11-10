"""Decode iReal Pro URLs (``irealb://`` and ``irealbook://``) into tunes and bars.

accompy owns this decoding; the TypeScript twin (``ts/src/ireal.ts``) is its exact
counterpart. The unscrambling and the bar flattening started as a copy of the parts of
pyRealParser (MIT licence, by its authors: https://github.com/drs251/pyRealParser) that
accompy used, with these changes:

- ``T12`` is 12/8; every other time-signature code ``T<a><b>`` is a/b;
- ``r`` (repeat the previous two bars) makes two bars and keeps the bar after it;
- ``p`` (repeat the previous chord) with no chord before it is dropped, in any bar;
- ``x`` or ``r`` with nothing to repeat is dropped;
- backslashes in chord text are literal text;
- long runs of ``{...}`` repeats are expanded in a loop (no recursion limit);
- song fields are read by position, so an empty field (an empty composer) shifts nothing;
- each bar is a list of its chords (pyRealParser glued them into one string per bar), a
  ``p`` within a bar is the previous chord again, ``W`` an invisible root, and end, segno
  and coda marks are left out of the chords;
- the ``l`` (large print) mark is removed without eating the ``l`` of ``alt``.

The URL layout. ``irealb://`` holds songs joined by ``===``, then an optional playlist
name; a song is ten ``=``-separated fields, ``title=composer=(unused)=style=key=transpose=
music=comp_style=bpm=repeats``, whose music starts with :data:`SCRAMBLE_PREFIX` and is
scrambled. Empty fields can make ``===`` inside a song, so songs are found by their music
field, not by splitting on ``===``. ``irealbook://`` (the older format) holds six-field
songs, ``title=composer=style=key=n=music``, with the music in plain text.

>>> [t.measures for t in decode_ireal_url("irealbook://Blues=Me=Swing=F=n=[T34F7 |Bb7 p|r| |C7 Z")]
[[['F7'], ['Bb7', 'Bb7'], ['F7'], ['Bb7', 'Bb7'], ['C7']]]
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import unquote

#: The start of a scrambled (``irealb://``) music field.
SCRAMBLE_PREFIX = "1r34LbKcu7"

#: Time-signature codes that are not ``T<numerator><denominator>``.
TIME_SIGNATURE_EXCEPTIONS = {(1, 2): (12, 8)}

#: Number of fields in an ``irealbook://`` song, and the index of its music field.
PLAIN_SONG_FIELDS, PLAIN_MUSIC_INDEX = 6, 5

#: Offsets from a scrambled song's music field to its style and key fields.
_STYLE, _KEY = -3, -2
#: The fields in a standard ``irealb://`` song before its music field.
_FIELDS_BEFORE_MUSIC = 6

#: First characters of a chord (``n`` is no chord, N.C.), which a ``p`` or ``W`` can repeat.
_ROOTS = "ABCDEFGn"


@dataclass
class IrealTune:
    """One song of an iReal URL: its metadata, cleaned chord string and flattened bars.

    ``measures`` holds one list of chords per bar (e.g. ``['D-7', 'G7']``), with
    repeats, endings, codas and repeat signs written out.
    """

    title: str = ""
    composer: str = ""
    style: str = ""
    key: str = ""
    transpose: str = ""
    comp_style: str = ""
    bpm: str = ""
    repeats: str = ""
    chord_string: str = ""
    time_signature: tuple[int, int] = (4, 4)
    measures: list[list[str]] = field(default_factory=list)


def unscramble(scrambled: str) -> str:
    """Undo iReal's scrambling of a music field (after :data:`SCRAMBLE_PREFIX`).

    Every full 50-character block that is not the last (or followed by fewer than 2
    characters) has characters 0-4 and 10-23 swapped with their mirror (49 - i). The
    operation is its own inverse.
    """
    out = []
    while len(scrambled) > 50:
        block, scrambled = scrambled[:50], scrambled[50:]
        if len(scrambled) >= 2:
            chars = list(block)
            for i in (*range(5), *range(10, 24)):
                chars[i], chars[49 - i] = block[49 - i], block[i]
            block = "".join(chars)
        out.append(block)
    return "".join(out) + scrambled


def cleanup_chord_string(chord_string: str) -> str:
    """Unify bar lines and repeat signs, drop spacers, empty bars and end marks."""
    for pattern, repl in (
        (r"LZ|K", "|"),
        (r"cl", "x"),
        (r"\*\s*\*", ""),
        (r"Y+", ""),
        (r"XyQ|,", " "),
        (r"\|\s*\|", "|"),
        (r"Z", ""),
        (r"\|\s+", "|"),
        (r"\s+", " "),
    ):
        chord_string = re.sub(pattern, repl, chord_string)
    return chord_string.rstrip()


def _remove_annotations(chord_string: str) -> str:
    for pattern, repl in (
        (r"[\[\]]", "|"),
        (r"\|\s*\|", "|"),
        (r"<.*?>", ""),  # comments
        (r"\([^)]*\)", ""),  # alternate chords
        (r"(?<!a)l(?!t)|f", ""),  # large print (not the l of alt), fermata
        (r"(?<!su)s(?!us)", ""),  # small print (not the s of sus)
        (r"\*\w", ""),  # section marks
        (r"T\d+", ""),  # time signatures
    ):
        chord_string = re.sub(pattern, repl, chord_string)
    return chord_string


def _remove_markers(chord_string: str) -> str:
    """Drop the end mark, segno, coda and ending numbers."""
    return re.sub(r"U|S|Q|N\d", "", chord_string)


def _fill_long_repeats(chord_string: str) -> str:
    """Write out ``{...}`` repeats; stops after the first repeat that has endings.

    A repeat's body holds no ``{`` (with unbalanced braces, the innermost one is taken),
    so each pass removes one ``{`` and the expansion cannot grow without bound.
    """
    while (repeat := re.search(r"{([^{\n]+?)}", chord_string)) is not None:
        body = repeat.group(1)
        before, after = chord_string[: repeat.start()], chord_string[repeat.end() :]
        if re.search(r"N(\d)", body) is None:
            chord_string = (
                before + "|" + body + " |" + _remove_markers(body) + after + "|"
            )
            continue
        # First time through: the body with its first ending; each later ending
        # (``|N2...``) is preceded by the body up to the first ending.
        out = before + "|" + re.sub(r"N\d", "", body) + after
        head = re.search(r"([^N]+)N\d", body)
        if head is None:
            raise ValueError(f"Repeat with an ending but no body: {body!r}")
        replay = "|" + _remove_markers(head.group(1))
        while re.search(r"\|\s*N(\d)", out) is not None:
            out = re.sub(r"\|\s*N(\d)", lambda _: replay, out)
        return out
    return chord_string


def _fill_codas(chord_string: str) -> str:
    """Write out a D.C./D.S. al Coda (two ``Q``s); a single ``Q`` is just dropped."""
    qs = chord_string.count("Q")
    if qs > 2:
        raise ValueError(f"Could not parse codas: expected 0, 1 or 2 Qs, not {qs}")
    if qs == 1:
        return chord_string.replace("Q", "")
    if qs == 2:
        q1 = chord_string.index("Q")
        q2 = chord_string.index("Q", q1 + 1)
        segno = chord_string.find("S")  # from after it, else after the first character
        repeat = chord_string[segno + 1 if segno >= 0 else 1 : q1]
        out = chord_string[:q2] + repeat + " |" + chord_string[q2 + 1 :]
        return re.sub(r"[QS]", "", out)
    return chord_string


def _fill_repeat_signs(bars: list[list[str]]) -> list[list[str]]:
    """Replace ``x`` (previous bar) and ``r`` (previous two bars); drop them with nothing to repeat."""
    out: list[list[str]] = []
    for bar in bars:
        if bar == ["x"]:
            out += out[-1:]
        elif bar == ["r"]:
            out += out[-2:] if len(out) >= 2 else []
        else:
            out.append(bar)
    return out


def _bar_tokens(bar: str) -> list[str]:
    """A bar's chords and signs: split at the source's separators, then before each root
    (``A``-``G``, or ``W``, not after a ``/``) and around each ``p``."""
    return [
        piece
        for token in bar.split()
        for piece in re.split(r"(?<!/)(?=[A-GW])|(?=p)|(?<=p)", token)
        if piece
    ]


def _fill_slashes(bars: list[list[str]]) -> list[list[str]]:
    """Write out ``p`` (the previous chord again) and ``W`` (an invisible root: the previous
    chord, with the bass that follows the ``W``); drop them when there is no previous chord."""
    out: list[list[str]] = []
    last = ""  # the last chord so far
    for bar in bars:
        chords: list[str] = []
        for token in bar:
            if token == "p":
                token = last
            elif token.startswith("W"):
                token = (last.split("/")[0] + token[1:] if token[1:] else last) if last else ""
            if token[:1] in _ROOTS:
                last = token
            chords += [token] if token else []
        out.append(chords)
    return out


def flatten_measures(chord_string: str) -> list[list[str]]:
    """The bars of an (unscrambled) chord string, each a list of its chords, with repeats,
    codas and signs written out (a ``p`` repeats the previous chord on its beat).

    >>> flatten_measures("{C^7 p|A-7 D7 |N1D-7,G7 }|N2G-7 C7 F7 |F^7 Z")
    [['C^7', 'C^7'], ['A-7', 'D7'], ['D-7', 'G7'], ['C^7', 'C^7'], ['A-7', 'D7'], ['G-7', 'C7', 'F7'], ['F^7']]
    """
    chord_string = cleanup_chord_string(chord_string)
    chord_string = _remove_annotations(chord_string)
    chord_string = _remove_markers(_fill_codas(_fill_long_repeats(chord_string)))
    bars = [_bar_tokens(bar) for bar in re.split(r"\||LZ|K|Z|{|}|\[|\]", chord_string)]
    return _fill_slashes(_fill_repeat_signs([bar for bar in bars if bar]))


def time_signature(chord_string: str) -> tuple[int, int]:
    """The first time signature (``T44``, ``T34``, ``T12`` = 12/8, ...), else 4/4."""
    match = re.search(r"T(\d)(\d)", chord_string)
    if match is None:
        return (4, 4)
    ts = (int(match.group(1)), int(match.group(2)))
    return TIME_SIGNATURE_EXCEPTIONS.get(ts, ts)


def _tune(music: str, **fields) -> IrealTune:
    chord_string = cleanup_chord_string(music)
    return IrealTune(
        **fields,
        chord_string=chord_string,
        time_signature=time_signature(chord_string),
        measures=flatten_measures(chord_string),
    )


def _scrambled_songs(fields: list[str]):
    """``(music, metadata)`` for each song: its fields are placed around its music field."""

    def at(i: int) -> str:
        return fields[i] if 0 <= i < len(fields) else ""

    previous = -1
    for m, music in enumerate(fields):
        if not music.startswith(SCRAMBLE_PREFIX):
            continue
        # A song starts right after the previous one, or at the standard offset when a
        # ``===`` separator (two empty fields) comes just before that offset.
        start, standard = previous + 1, m - _FIELDS_BEFORE_MUSIC
        if standard > start and at(standard - 1) == at(standard - 2) == "":
            start = standard
        previous = m
        before = fields[start:m]
        if len(before) >= _FIELDS_BEFORE_MUSIC:  # title, composer, ..., style, key, transpose
            meta = dict(title=at(start), composer=at(start + 1), style=at(m + _STYLE))
            meta.update(key=at(m + _KEY), transpose=at(m - 1))
        else:  # too few fields to place them: the non-empty ones, in order
            names = ("title", "composer", "style", "key")
            meta = dict(zip(names, [f for f in before if f] + [""] * len(names)))
        after = ("comp_style", "bpm", "repeats")
        meta.update({name: at(m + 1 + k) for k, name in enumerate(after)})
        yield unscramble(music[len(SCRAMBLE_PREFIX) :]), meta


def _plain_songs(fields: list[str]):
    """``(music, metadata)`` for each six-field ``irealbook`` song."""
    for s in range(0, len(fields) - PLAIN_SONG_FIELDS + 1, PLAIN_SONG_FIELDS):
        title, composer, style, key, _, music = fields[s : s + PLAIN_SONG_FIELDS]
        yield music, dict(title=title, composer=composer, style=style, key=key)


def decode_ireal_url(url: str) -> list[IrealTune]:
    """The tunes of an iReal URL (a playlist has several), skipping those that do not decode.

    The URL is percent-decoded and ends at its first ``"`` (as when cut out of an HTML
    ``href``); the ``irealb://`` / ``irealbook://`` scheme is optional. Music fields that
    start with :data:`SCRAMBLE_PREFIX` are read as ``irealb`` songs; a URL with none is
    read as ``irealbook`` six-field songs.
    """
    body = unquote(url).split('"', 1)[0]
    for scheme in ("irealbook://", "irealb://"):
        if body.startswith(scheme):
            body = body[len(scheme) :]
            break
    fields = body.split("=")
    songs = (
        _scrambled_songs(fields)
        if any(f.startswith(SCRAMBLE_PREFIX) for f in fields)
        else _plain_songs(fields)
    )
    tunes = []
    for music, meta in songs:
        try:
            tunes.append(_tune(music, **meta))
        except ValueError:
            pass  # a song whose codas or endings cannot be written out
    return tunes
