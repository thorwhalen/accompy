"""
Pattern data structures for accompaniment generation.

Contains the core pattern dataclasses: DrumHit, NoteEvent, DrumPattern,
BassPattern, and CompingPattern.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

# MIDI drum note numbers (General MIDI standard)
KICK = 36
SNARE = 38
SIDE_STICK = 37
CLOSED_HIHAT = 42
OPEN_HIHAT = 46
PEDAL_HIHAT = 44
RIDE = 51
RIDE_BELL = 53
CRASH = 49
LOW_TOM = 45
MID_TOM = 47
HIGH_TOM = 50
COWBELL = 56
CLAVES = 75
SHAKER = 70


@dataclass(frozen=True)
class DrumHit:
    """
    A single drum hit in a pattern.

    Attributes:
        beat: Beat position (0-based within measure)
        drum: MIDI note number for the drum sound
        velocity: Hit velocity (0-127)
    """
    beat: float
    drum: int
    velocity: int


@dataclass(frozen=True)
class NoteEvent:
    """
    A melodic note event for bass or other instruments.

    Attributes:
        beat: Beat position within measure
        pitch_offset: Offset from chord root in semitones (0=root, 7=5th, etc.)
        duration: Note duration in beats
        velocity: Note velocity (0-127)
    """
    beat: float
    pitch_offset: int
    duration: float
    velocity: int


@dataclass
class DrumPattern:
    """
    A drum pattern for one or more measures.

    Example:
        >>> pattern = DrumPattern("rock", 4, [DrumHit(0, KICK, 100)])
        >>> pattern.beats_per_bar
        4
    """
    name: str
    beats_per_bar: int
    hits: Sequence[DrumHit]

    def at_tempo(self, tempo: int) -> float:
        """Return pattern duration in seconds at a given tempo."""
        return (60 / tempo) * self.beats_per_bar


@dataclass
class BassPattern:
    """
    A bass pattern template.

    Uses pitch_offset in NoteEvent to specify intervals from the chord root.
    The actual pitches are determined when the pattern is applied to specific chords.
    """
    name: str
    notes: Sequence[NoteEvent]


@dataclass
class CompingPattern:
    """
    A piano/guitar comping (accompaniment) pattern.

    Attributes:
        name: Pattern identifier
        hits: Sequence of (beat, duration, velocity) tuples
    """
    name: str
    hits: Sequence[tuple[float, float, int]]
