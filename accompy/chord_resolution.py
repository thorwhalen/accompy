"""
Chord symbol to MIDI notes resolution.

Provides pluggable chord resolution with multiple backends (tonal, music21).
Implements dependency injection pattern for flexibility.
"""

from __future__ import annotations

from typing import Callable

# Type alias for chord resolvers
# A ChordResolver takes a chord symbol and returns a list of MIDI note numbers
ChordResolver = Callable[[str], list[int]]

# Default transpose setting (tonal library anchors to C4=60, we prefer C3=48)
DFLT_CHORD_TRANSPOSE_SEMITONES = -12


def tonal_resolver(
    symbol: str, *, transpose: int = DFLT_CHORD_TRANSPOSE_SEMITONES
) -> list[int]:
    """
    Resolve chord symbol to MIDI notes using the tonal package (default).

    The tonal package is lightweight and designed for music theory operations.
    It anchors chord roots around C4=60. We apply a default -12 semitone transpose
    to voice chords closer to C3=48 for better bass/piano range.

    Args:
        symbol: Chord symbol (e.g., "Dm7", "G7", "Cmaj7")
        transpose: Semitone offset to apply (default: -12)

    Returns:
        List of MIDI note numbers

    Example:
        >>> notes = tonal_resolver("Cmaj7")
        >>> len(notes) > 0
        True

    Note:
        Requires: pip install tonal
        See: https://github.com/thorwhalen/tonal
    """
    from tonal.chords import chord_to_notes

    notes = list(chord_to_notes(symbol))
    if transpose:
        notes = [n + transpose for n in notes]
    return notes


def music21_resolver(
    symbol: str, *, transpose: int = DFLT_CHORD_TRANSPOSE_SEMITONES
) -> list[int]:
    """
    Resolve chord symbol using music21 library (alternative).

    Music21 is a comprehensive music analysis library. It provides more
    sophisticated chord parsing but has heavier dependencies.

    Args:
        symbol: Chord symbol
        transpose: Semitone offset to apply (default: -12)

    Returns:
        List of MIDI note numbers

    Note:
        Requires: pip install music21
        This is provided as an alternative for advanced use cases.
        Consider using tonal_resolver for standard accompaniment generation.
    """
    from music21 import harmony

    ch = harmony.ChordSymbol(symbol)
    notes = [p.midi for p in ch.pitches]
    if transpose:
        notes = [n + transpose for n in notes]
    return notes


# Global default resolver (can be customized)
_default_resolver: ChordResolver = tonal_resolver


def get_chord_resolver() -> ChordResolver:
    """
    Get the current default chord resolver.

    Returns:
        The active chord resolution function

    Example:
        >>> resolver = get_chord_resolver()
        >>> notes = resolver("C")
        >>> len(notes) > 0
        True
    """
    return _default_resolver


def set_chord_resolver(resolver: ChordResolver) -> None:
    """
    Set the default chord resolver.

    This enables global customization of chord-to-notes resolution.

    Args:
        resolver: A function that takes a chord symbol (str) and returns MIDI notes (list[int])

    Example:
        >>> def my_resolver(symbol: str) -> list[int]:
        ...     # Custom chord voicing logic
        ...     return [60, 64, 67]  # C major triad
        >>> set_chord_resolver(my_resolver)
    """
    global _default_resolver
    _default_resolver = resolver


def chord_to_notes(symbol: str) -> list[int]:
    """
    Convert chord symbol to MIDI notes using the current default resolver.

    This is the main entry point for chord resolution in accompy.

    Args:
        symbol: Chord symbol (e.g., "Dm7", "G7")

    Returns:
        List of MIDI note numbers

    Example:
        >>> notes = chord_to_notes("C")
        >>> len(notes) > 0
        True
    """
    return _default_resolver(symbol)


# Backward-compatible alias used in tests
_basic_chord_to_notes = tonal_resolver
