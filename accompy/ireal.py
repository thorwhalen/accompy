"""Decode iReal Pro URLs (``irealb://`` and ``irealbook://``) into tunes and bars.

accompy owns this decoding; the TypeScript twin (``ts/src/ireal.ts``) is its exact
counterpart. The unscrambling and the chord-string cleanup started as a copy of the parts
of pyRealParser (https://github.com/drs251/pyRealParser, MIT licence, notice below) that
accompy used. Changes from it:

- ``T12`` is 12/8; every other time-signature code ``T<a><b>`` is a/b;
- the chart is read bar by bar in one linear pass: every ``{...}`` repeat is written out
  with its own endings (``}N2``, ``}`` then ``N2``, three endings), a ``}`` with no ``{``
  repeats from the last ``[``, the previous ``}`` or the top, a ``{`` inside an open
  repeat restarts it (iReal has no nesting), and the ``}`` stays a barline;
- a D.C./D.S. al Coda replays from the segno ``S`` (or the top) to the first ``Q``, as
  whole bars, then plays the coda;
- ``r`` (repeat the previous two bars) makes two bars and keeps the bar after it;
- ``p`` (the previous chord again) and ``W`` (an invisible root) with no chord before
  them are dropped; ``x`` or ``r`` with nothing to repeat is dropped;
- backslashes in chord text are literal text;
- song fields are read by position, so an empty field (an empty composer) shifts nothing;
- each bar is a list of its chords (pyRealParser glued them into one string per bar), and
  end, segno and coda marks are left out of the chords;
- the ``l`` (large print) mark is removed without eating the ``l`` of ``alt``;
- ``Z`` (final double bar) is a barline.

Regex digit and word classes follow Python's Unicode tables; the twin's JavaScript ones can
be a version newer (characters added in Unicode 15.1/16 differ; iReal uses none of them).

The URL layout. ``irealb://`` holds songs joined by ``===``, then an optional playlist
name; a song is ten ``=``-separated fields, ``title=composer=(unused)=style=key=transpose=
music=comp_style=bpm=repeats``, whose music starts with :data:`SCRAMBLE_PREFIX` and is
scrambled. Empty fields can make ``===`` inside a song, so songs are found by their music
field, not by splitting on ``===``. ``irealbook://`` (the older format) holds six-field
songs, ``title=composer=style=key=n=music``, with the music in plain text.

>>> [t.measures for t in decode_ireal_url("irealbook://Blues=Me=Swing=F=n=[T34F7 |Bb7 p|r| |C7 Z")]
[[['F7'], ['Bb7', 'Bb7'], ['F7'], ['Bb7', 'Bb7'], ['C7']]]
"""

# Parts of this module derive from pyRealParser, under this licence:
#
# MIT License
#
# Copyright (c) 2018 Daniel Stephan
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import unquote

#: The start of a scrambled (``irealb://``) music field.
SCRAMBLE_PREFIX = "1r34LbKcu7"

#: Time-signature codes that are not ``T<numerator><denominator>``.
TIME_SIGNATURE_EXCEPTIONS = {(1, 2): (12, 8)}

#: The most endings (``N1`` ... ``N9``) a repeat can have.
_MAX_ENDINGS = 9

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

    @property
    def tempo(self) -> int | None:
        """The tempo in BPM, or None when unset (empty, not a number, or not above 0)."""
        bpm = self.bpm.strip()
        return int(bpm) if bpm.isdecimal() and int(bpm) > 0 else None

    def chord_specs(self, *, beats_per_bar: float | None = None) -> list[tuple[str, float]]:
        """``(chord, beats)`` pairs: each bar shared evenly by its chords. Bars last
        ``beats_per_bar`` beats, by default the time signature's numerator.

        >>> IrealTune(measures=[["C"], ["D-7", "G7"]], time_signature=(3, 4)).chord_specs()
        [('C', 3.0), ('D-7', 1.5), ('G7', 1.5)]
        """
        beats = float(beats_per_bar or self.time_signature[0])
        return [(chord, beats / len(bar)) for bar in self.measures for chord in bar]


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
    """Unify bar lines (``Z``, the final double bar, is one too) and repeat signs; drop
    spacers and empty bars."""
    for pattern, repl in (
        (r"LZ|K|Z", "|"),
        (r"cl", "x"),
        (r"\*\s*\*", ""),
        (r"Y+", ""),
        (r"XyQ|,", " "),
        (r"\|\s*\|", "|"),
        (r"\|\s+", "|"),
        (r"\s+", " "),
    ):
        chord_string = re.sub(pattern, repl, chord_string)
    return chord_string.rstrip()


def _drop_spans(text: str, start: str, end: str, *, stop: str = "") -> str:
    """Remove each ``start...end`` span (no ``stop`` inside), in one left-to-right pass.

    The linear equivalent of ``re.sub(f"{start}[^{stop}]*?{end}", "", text)``: a regex
    retries from every unclosed ``start``, which is quadratic on text like ``<<<<...``.
    """
    out, i = [], 0
    while (j := text.find(start, i)) >= 0 and (k := text.find(end, j + 1)) >= 0:
        cut = text.find(stop, j + 1, k) if stop else -1
        if cut >= 0:  # no span starts before the stop character
            out.append(text[i : cut + 1])
            i = cut + 1
        else:
            out.append(text[i:j])
            i = k + 1
    return "".join(out) + text[i:]


def _remove_annotations(chord_string: str) -> str:
    chord_string = _drop_spans(chord_string, "<", ">", stop="\n")  # comments
    chord_string = _drop_spans(chord_string, "(", ")")  # alternate chords
    for pattern, repl in (
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


@dataclass
class _Bar:
    """A bar of the chart as written: its text (chords and marks) and the barlines around it."""

    text: str
    opener: str  # "{" (repeat start), "[" (section start) or ""
    closes: bool  # ends with a repeat sign "}"
    ending: int | None  # the ending (volta) number it starts, from ``N<digit>``


def _split_bars(chord_string: str) -> list[_Bar]:
    bars, opener, pos = [], "", 0

    def bar(text: str, closes: bool) -> _Bar:
        ending = re.search(r"N(\d)", text)
        return _Bar(text, opener, closes, int(ending.group(1)) if ending else None)

    for m in re.finditer(r"[|\[\]{}]", chord_string):
        bars.append(bar(chord_string[pos : m.start()], m.group() == "}"))
        opener, pos = (m.group() if m.group() in "{[" else ""), m.end()
    bars.append(bar(chord_string[pos:], False))
    return bars


def _expand_repeats(bars: list[_Bar]) -> list[int | str]:
    """The order bars are played in (indices; the text of a part-bar before an ending
    written mid-bar), with ``{...}`` repeats and endings written out.

    One pass, left to right. A ``}`` repeats from its ``{`` or, with none, from the last
    section start ``[``, the bar after the previous ``}``, or the top. With endings
    (``N1``, ``N2``, ...), the replay is the part before the first ending, then play goes
    on into the next ending; an ending that closes with ``}`` again is followed by one more
    replay. iReal has no nested repeats: a ``{`` inside an open repeat restarts it. Every
    bar is replayed at most once per ending, so the output stays linear in the input.
    """
    order: list[int | str] = []
    region, opened = 0, None  # where a lone "}" repeats from; the open "{"
    body: list[int | str] = []  # what a later ending's "}" replays
    last_close, replays = -1, 0
    for i, bar in enumerate(bars):
        if bar.opener:
            region, body = i, []
            opened = i if bar.opener == "{" else opened
        order.append(i)
        if not bar.closes:
            continue
        later_ending = opened is None and body and any(
            bars[j].ending is not None for j in range(last_close + 1, i + 1)
        )
        if later_ending and replays < _MAX_ENDINGS:
            order += body
            replays += 1
        elif not later_ending:
            start = opened if opened is not None else region
            first = next((j for j in range(start, i + 1) if bars[j].ending is not None), None)
            replay: list[int | str] = list(range(start, i + 1 if first is None else first))
            if first is not None:  # an ending written mid-bar: replay the bar's start too
                head = bars[first].text[: re.search(r"N\d", bars[first].text).start()]
                replay += [head] if _remove_markers(head).strip() else []
            order += replay
            body, replays = (replay, 1) if first is not None else ([], 0)
        region, opened, last_close = i + 1, None, i
    return order


def _fill_codas(bars: list[_Bar], order: list[int | str]) -> list[str]:
    """The played bars' texts, with a D.C./D.S. al Coda (two ``Q``s) written out.

    At the second ``Q`` (the coda), play goes back to the segno ``S`` (or the top) and on
    to the first ``Q``, then into the coda. One ``Q`` alone is just dropped.
    """
    texts = [bars[i].text if isinstance(i, int) else i for i in order]
    qs = sum(bar.text.count("Q") for bar in bars)
    if qs > 2:
        raise ValueError(f"Could not parse codas: expected 0, 1 or 2 Qs, not {qs}")
    q_bars = [i for i, bar in enumerate(bars) if "Q" in bar.text]
    if qs < 2 or len(q_bars) < 2:
        return texts
    p1, p2 = order.index(q_bars[0]), order.index(q_bars[1])
    if p1 >= p2:
        return texts
    segno = next((order.index(i) for i, b in enumerate(bars) if "S" in b.text), None)

    def cut(text: str, mark: str) -> tuple[str, str]:
        k = text.find(mark)
        return (text[:k], text[k + 1 :]) if k >= 0 else (text, "")

    to_coda = cut(texts[p1], "Q")[0]
    if segno is None or segno > p1:
        replay = texts[:p1] + [to_coda]
    elif segno < p1:
        replay = [cut(texts[segno], "S")[1]] + texts[segno + 1 : p1] + [to_coda]
    else:
        replay = [cut(cut(texts[p1], "S")[1], "Q")[0]]
    before, coda = cut(texts[p2], "Q")
    return texts[:p2] + [before] + replay + [coda] + texts[p2 + 1 :]


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
    endings, codas and signs written out (a ``p`` repeats the previous chord on its beat).

    >>> flatten_measures("{C^7 p|A-7 D7 |N1D-7,G7 }N2G-7 C7 F7 |F^7 Z")
    [['C^7', 'C^7'], ['A-7', 'D7'], ['D-7', 'G7'], ['C^7', 'C^7'], ['A-7', 'D7'], ['G-7', 'C7', 'F7'], ['F^7']]
    """
    bars = _split_bars(_remove_annotations(cleanup_chord_string(chord_string)))
    texts = _fill_codas(bars, _expand_repeats(bars))
    tokens = [_bar_tokens(_remove_markers(text)) for text in texts]
    return _fill_slashes(_fill_repeat_signs([bar for bar in tokens if bar]))


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

    The URL ends at its first raw ``"`` (as when cut out of an HTML ``href``; a ``%22``
    is a quote inside a title or comment) and is then percent-decoded; the ``irealb://`` / ``irealbook://`` scheme is optional. Music fields that
    start with :data:`SCRAMBLE_PREFIX` are read as ``irealb`` songs; a URL with none is
    read as ``irealbook`` six-field songs.
    """
    body = unquote(url.split('"', 1)[0])
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
