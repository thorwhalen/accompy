"""
Chord resolvers — convert chord symbols to MIDI note numbers.

Registered converters: ChordSequence -> NoteSequence

Multiple backends, each wrapping a different music theory library:
- pychord: lightweight, good coverage of standard chord types
- music21: comprehensive, heavyweight, handles edge cases well
- mingus: pure Python music theory, no C dependencies
- tonal: the existing accompy dependency (thorwhalen/tonal)

Each resolver is a function: chord_symbol (str) -> list[int] (MIDI notes).
We also provide converters that operate on whole ChordSequences.
"""

from __future__ import annotations

from typing import Callable

from .converters import ChordSequence, NoteSequence, converter

# Type alias: a single-chord resolver
ChordResolver = Callable[[str], list[int]]


# ---------------------------------------------------------------------------
# Individual chord resolvers (str -> list[int])
# ---------------------------------------------------------------------------


def resolve_with_pychord(symbol: str, *, root_octave: int = 3) -> list[int]:
    """Resolve a chord symbol to MIDI notes using pychord.

    >>> resolve_with_pychord("Cmaj7")
    [48, 52, 55, 59]
    >>> resolve_with_pychord("Am")
    [57, 60, 64]
    """
    from pychord import Chord

    c = Chord(symbol)
    note_names = c.components_with_pitch(root_pitch=root_octave)
    return [_name_to_midi(n) for n in note_names]


def resolve_with_music21(symbol: str, *, root_octave: int = 3) -> list[int]:
    """Resolve a chord symbol to MIDI notes using music21.

    Handles the widest range of chord types including altered chords.

    >>> resolve_with_music21("Cmaj7")
    [48, 52, 55, 59]
    """
    from music21 import harmony

    cs = harmony.ChordSymbol(symbol)
    return [p.midi for p in cs.pitches]


def resolve_with_mingus(symbol: str, *, root_octave: int = 3) -> list[int]:
    """Resolve a chord symbol to MIDI notes using mingus.

    >>> resolve_with_mingus("Cmaj7")
    [36, 40, 43, 47]
    """
    from mingus.core import chords as mingus_chords
    from mingus.containers import Note

    note_names = mingus_chords.from_shorthand(symbol)
    return [int(Note(name, root_octave)) for name in note_names]


def resolve_with_tonal(symbol: str, *, transpose: int = -12) -> list[int]:
    """Resolve a chord symbol to MIDI notes using the tonal package.

    This is accompy's existing default resolver.

    >>> resolve_with_tonal("Cmaj7")
    [48, 52, 55, 59]
    """
    from tonal.chords import chord_to_notes

    notes = list(chord_to_notes(symbol))
    if transpose:
        notes = [n + transpose for n in notes]
    return notes


# ---------------------------------------------------------------------------
# Helper: note name -> MIDI number
# ---------------------------------------------------------------------------

_NOTE_MAP = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11,
}


def _name_to_midi(name: str) -> int:
    """Convert a note name like 'C#3' or 'Eb4' to MIDI number.

    >>> _name_to_midi('C4')
    60
    >>> _name_to_midi('A3')
    57
    >>> _name_to_midi('Bb3')
    58
    """
    # Parse: letter + optional accidental + octave
    letter = name[0].upper()
    rest = name[1:]

    accidental = 0
    while rest and rest[0] in ("#", "b"):
        if rest[0] == "#":
            accidental += 1
        else:
            accidental -= 1
        rest = rest[1:]

    octave = int(rest) if rest else 4
    return _NOTE_MAP[letter] + accidental + (octave + 1) * 12


# ---------------------------------------------------------------------------
# Whole-sequence converters: ChordSequence -> NoteSequence
# ---------------------------------------------------------------------------


def _make_sequence_converter(
    resolver: ChordResolver, name: str
) -> Callable[[ChordSequence], NoteSequence]:
    """Factory: wrap a single-chord resolver into a ChordSequence converter."""

    def convert_sequence(cs: ChordSequence) -> NoteSequence:
        notes = []
        for symbol, duration in cs.chords:
            try:
                midi_notes = resolver(symbol)
            except Exception:
                midi_notes = [60, 64, 67]  # C major fallback
            notes.append((midi_notes, duration))
        return NoteSequence(
            notes=notes,
            tempo=cs.tempo,
            time_signature=cs.time_signature,
        )

    convert_sequence.__name__ = name
    convert_sequence.__doc__ = f"Convert ChordSequence to NoteSequence using {name}."
    return convert_sequence


# Create the sequence-level converters
chordseq_to_noteseq_pychord = _make_sequence_converter(resolve_with_pychord, "pychord")
chordseq_to_noteseq_music21 = _make_sequence_converter(resolve_with_music21, "music21")
chordseq_to_noteseq_mingus = _make_sequence_converter(resolve_with_mingus, "mingus")
chordseq_to_noteseq_tonal = _make_sequence_converter(resolve_with_tonal, "tonal")


# ---------------------------------------------------------------------------
# Register converters
# ---------------------------------------------------------------------------

converter.register(
    ChordSequence,
    NoteSequence,
    chordseq_to_noteseq_pychord,
    name="pychord",
    is_default=True,
)

converter.register(
    ChordSequence, NoteSequence, chordseq_to_noteseq_music21, name="music21"
)

converter.register(
    ChordSequence, NoteSequence, chordseq_to_noteseq_mingus, name="mingus"
)

converter.register(ChordSequence, NoteSequence, chordseq_to_noteseq_tonal, name="tonal")
