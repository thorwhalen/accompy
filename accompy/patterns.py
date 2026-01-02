"""
accompy.patterns - Musical patterns for accompaniment generation.

Contains drum grooves, bass lines, and piano voicings for different styles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

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
    """A single drum hit in a pattern."""
    beat: float      # Beat position (0-based within measure)
    drum: int        # MIDI note number
    velocity: int    # 0-127


@dataclass(frozen=True)
class NoteEvent:
    """A melodic note event."""
    beat: float
    pitch_offset: int  # Offset from root (0=root, 7=5th, etc.)
    duration: float
    velocity: int


@dataclass
class DrumPattern:
    """A drum pattern for one or more measures."""
    name: str
    beats_per_bar: int
    hits: Sequence[DrumHit]
    
    def at_tempo(self, tempo: int) -> float:
        """Return pattern duration in seconds."""
        return (60 / tempo) * self.beats_per_bar


@dataclass
class BassPattern:
    """A bass pattern template."""
    name: str
    notes: Sequence[NoteEvent]


@dataclass
class CompingPattern:
    """A piano/guitar comping pattern."""
    name: str
    hits: Sequence[tuple[float, float, int]]  # (beat, duration, velocity)


# =============================================================================
# SWING PATTERNS
# =============================================================================

SWING_DRUMS_BASIC = DrumPattern(
    name="swing_basic",
    beats_per_bar=4,
    hits=[
        # Ride cymbal - swing pattern (quarters with swing feel)
        DrumHit(0, RIDE, 90),
        DrumHit(1, RIDE, 70),
        DrumHit(2, RIDE, 85),
        DrumHit(3, RIDE, 70),
        # Hi-hat on 2 and 4
        DrumHit(1, PEDAL_HIHAT, 80),
        DrumHit(3, PEDAL_HIHAT, 80),
    ]
)

SWING_DRUMS_BRUSHES = DrumPattern(
    name="swing_brushes",
    beats_per_bar=4,
    hits=[
        DrumHit(0, SIDE_STICK, 60),
        DrumHit(0.67, CLOSED_HIHAT, 40),  # Triplet feel
        DrumHit(1, SIDE_STICK, 50),
        DrumHit(1.67, CLOSED_HIHAT, 40),
        DrumHit(2, SIDE_STICK, 60),
        DrumHit(2.67, CLOSED_HIHAT, 40),
        DrumHit(3, SIDE_STICK, 50),
        DrumHit(3.67, CLOSED_HIHAT, 40),
    ]
)

SWING_BASS_WALKING = BassPattern(
    name="walking",
    notes=[
        NoteEvent(0, 0, 0.9, 100),      # Root
        NoteEvent(1, 4, 0.9, 90),       # 3rd
        NoteEvent(2, 7, 0.9, 95),       # 5th
        NoteEvent(3, 11, 0.9, 85),      # Approach (chromatic)
    ]
)

SWING_COMP = CompingPattern(
    name="swing_comp",
    hits=[
        (1.5, 0.4, 75),   # Off-beat comping
        (3.5, 0.4, 80),
    ]
)


# =============================================================================
# BOSSA NOVA PATTERNS
# =============================================================================

BOSSA_DRUMS = DrumPattern(
    name="bossa",
    beats_per_bar=4,
    hits=[
        # Cross-stick on 1 and 3 (rim)
        DrumHit(0, SIDE_STICK, 70),
        DrumHit(2, SIDE_STICK, 65),
        # Hi-hat pattern
        DrumHit(0, CLOSED_HIHAT, 60),
        DrumHit(0.5, CLOSED_HIHAT, 40),
        DrumHit(1, CLOSED_HIHAT, 50),
        DrumHit(1.5, CLOSED_HIHAT, 40),
        DrumHit(2, CLOSED_HIHAT, 60),
        DrumHit(2.5, CLOSED_HIHAT, 40),
        DrumHit(3, CLOSED_HIHAT, 50),
        DrumHit(3.5, CLOSED_HIHAT, 40),
        # Kick drum - bossa pattern
        DrumHit(0, KICK, 80),
        DrumHit(1.5, KICK, 70),
        DrumHit(3, KICK, 75),
    ]
)

BOSSA_BASS = BassPattern(
    name="bossa",
    notes=[
        NoteEvent(0, 0, 1.3, 90),       # Root, sustained
        NoteEvent(1.5, 7, 0.8, 75),     # 5th, syncopated
        NoteEvent(2.5, 0, 1.3, 85),     # Back to root
    ]
)

BOSSA_COMP = CompingPattern(
    name="bossa_comp",
    hits=[
        (0, 0.3, 70),
        (1.5, 0.3, 65),
        (2.5, 0.3, 70),
        (3.5, 0.3, 60),
    ]
)


# =============================================================================
# ROCK PATTERNS
# =============================================================================

ROCK_DRUMS_BASIC = DrumPattern(
    name="rock_basic",
    beats_per_bar=4,
    hits=[
        # Kick on 1 and 3
        DrumHit(0, KICK, 110),
        DrumHit(2, KICK, 105),
        # Snare on 2 and 4
        DrumHit(1, SNARE, 100),
        DrumHit(3, SNARE, 100),
        # Hi-hat eighths
        DrumHit(0, CLOSED_HIHAT, 80),
        DrumHit(0.5, CLOSED_HIHAT, 60),
        DrumHit(1, CLOSED_HIHAT, 80),
        DrumHit(1.5, CLOSED_HIHAT, 60),
        DrumHit(2, CLOSED_HIHAT, 80),
        DrumHit(2.5, CLOSED_HIHAT, 60),
        DrumHit(3, CLOSED_HIHAT, 80),
        DrumHit(3.5, CLOSED_HIHAT, 60),
    ]
)

ROCK_DRUMS_HEAVY = DrumPattern(
    name="rock_heavy",
    beats_per_bar=4,
    hits=[
        DrumHit(0, KICK, 120),
        DrumHit(0.5, KICK, 90),
        DrumHit(1, SNARE, 110),
        DrumHit(2, KICK, 115),
        DrumHit(2.75, KICK, 85),
        DrumHit(3, SNARE, 110),
        DrumHit(3.5, CLOSED_HIHAT, 70),
    ]
)

ROCK_BASS = BassPattern(
    name="rock",
    notes=[
        NoteEvent(0, 0, 0.9, 100),
        NoteEvent(1, 0, 0.9, 90),
        NoteEvent(2, 0, 0.9, 100),
        NoteEvent(3, 0, 0.9, 90),
    ]
)

ROCK_BASS_DRIVING = BassPattern(
    name="rock_driving",
    notes=[
        NoteEvent(0, 0, 0.45, 100),
        NoteEvent(0.5, 0, 0.45, 80),
        NoteEvent(1, 0, 0.45, 95),
        NoteEvent(1.5, 0, 0.45, 80),
        NoteEvent(2, 0, 0.45, 100),
        NoteEvent(2.5, 0, 0.45, 80),
        NoteEvent(3, 0, 0.45, 95),
        NoteEvent(3.5, 0, 0.45, 80),
    ]
)


# =============================================================================
# FUNK PATTERNS
# =============================================================================

FUNK_DRUMS = DrumPattern(
    name="funk",
    beats_per_bar=4,
    hits=[
        # Syncopated kick
        DrumHit(0, KICK, 110),
        DrumHit(0.75, KICK, 85),
        DrumHit(1.5, KICK, 90),
        DrumHit(2.5, KICK, 100),
        DrumHit(3.25, KICK, 80),
        # Snare on 2 and 4 with ghost notes
        DrumHit(0.5, SNARE, 40),   # Ghost
        DrumHit(1, SNARE, 105),
        DrumHit(2.25, SNARE, 35),  # Ghost
        DrumHit(3, SNARE, 105),
        DrumHit(3.75, SNARE, 45),  # Ghost
        # Hi-hat 16ths
        DrumHit(0, CLOSED_HIHAT, 75),
        DrumHit(0.25, CLOSED_HIHAT, 50),
        DrumHit(0.5, CLOSED_HIHAT, 65),
        DrumHit(0.75, CLOSED_HIHAT, 50),
        DrumHit(1, OPEN_HIHAT, 80),
        DrumHit(1.25, CLOSED_HIHAT, 50),
        DrumHit(1.5, CLOSED_HIHAT, 65),
        DrumHit(1.75, CLOSED_HIHAT, 50),
        DrumHit(2, CLOSED_HIHAT, 75),
        DrumHit(2.25, CLOSED_HIHAT, 50),
        DrumHit(2.5, CLOSED_HIHAT, 65),
        DrumHit(2.75, CLOSED_HIHAT, 50),
        DrumHit(3, OPEN_HIHAT, 80),
        DrumHit(3.25, CLOSED_HIHAT, 50),
        DrumHit(3.5, CLOSED_HIHAT, 65),
        DrumHit(3.75, CLOSED_HIHAT, 50),
    ]
)

FUNK_BASS = BassPattern(
    name="funk",
    notes=[
        NoteEvent(0, 0, 0.4, 110),
        NoteEvent(0.75, 0, 0.2, 80),
        NoteEvent(1.25, 7, 0.3, 90),
        NoteEvent(1.75, 0, 0.2, 75),
        NoteEvent(2.5, 0, 0.4, 100),
        NoteEvent(3, 5, 0.3, 85),
        NoteEvent(3.5, 7, 0.3, 80),
    ]
)


# =============================================================================
# BALLAD PATTERNS
# =============================================================================

BALLAD_DRUMS = DrumPattern(
    name="ballad",
    beats_per_bar=4,
    hits=[
        DrumHit(0, KICK, 70),
        DrumHit(2, SIDE_STICK, 60),
        DrumHit(0, CLOSED_HIHAT, 50),
        DrumHit(1, CLOSED_HIHAT, 40),
        DrumHit(2, CLOSED_HIHAT, 50),
        DrumHit(3, CLOSED_HIHAT, 40),
    ]
)

BALLAD_BASS = BassPattern(
    name="ballad",
    notes=[
        NoteEvent(0, 0, 2.0, 80),       # Whole note on root
        NoteEvent(2, 7, 2.0, 70),       # 5th
    ]
)

BALLAD_COMP = CompingPattern(
    name="ballad_arp",
    hits=[
        (0, 0.8, 60),
        (0.5, 0.8, 55),
        (1, 0.8, 50),
        (1.5, 0.8, 55),
        (2, 0.8, 60),
        (2.5, 0.8, 55),
        (3, 0.8, 50),
        (3.5, 0.8, 55),
    ]
)


# =============================================================================
# LATIN PATTERNS  
# =============================================================================

LATIN_DRUMS = DrumPattern(
    name="latin",
    beats_per_bar=4,
    hits=[
        # Clave pattern (son clave 3-2)
        DrumHit(0, CLAVES, 90),
        DrumHit(0.75, CLAVES, 85),
        DrumHit(1.5, CLAVES, 80),
        DrumHit(2.5, CLAVES, 90),
        DrumHit(3.5, CLAVES, 85),
        # Kick - tumbao
        DrumHit(0, KICK, 90),
        DrumHit(2.5, KICK, 85),
        # Cowbell
        DrumHit(0, COWBELL, 70),
        DrumHit(0.5, COWBELL, 55),
        DrumHit(1, COWBELL, 65),
        DrumHit(1.5, COWBELL, 55),
        DrumHit(2, COWBELL, 70),
        DrumHit(2.5, COWBELL, 55),
        DrumHit(3, COWBELL, 65),
        DrumHit(3.5, COWBELL, 55),
    ]
)

LATIN_BASS = BassPattern(
    name="montuno",
    notes=[
        NoteEvent(0, 0, 0.4, 95),
        NoteEvent(0.5, 7, 0.4, 80),
        NoteEvent(1.5, 0, 0.4, 90),
        NoteEvent(2, 7, 0.4, 85),
        NoteEvent(2.5, 0, 0.4, 90),
        NoteEvent(3.5, 5, 0.4, 80),
    ]
)


# =============================================================================
# WALTZ PATTERNS
# =============================================================================

WALTZ_DRUMS = DrumPattern(
    name="waltz",
    beats_per_bar=3,
    hits=[
        DrumHit(0, KICK, 90),
        DrumHit(1, CLOSED_HIHAT, 60),
        DrumHit(2, CLOSED_HIHAT, 60),
    ]
)

WALTZ_BASS = BassPattern(
    name="waltz",
    notes=[
        NoteEvent(0, 0, 0.9, 95),       # Root
        NoteEvent(1, 4, 0.9, 75),       # 3rd
        NoteEvent(2, 7, 0.9, 75),       # 5th
    ]
)


# =============================================================================
# BLUES PATTERNS
# =============================================================================

BLUES_DRUMS = DrumPattern(
    name="blues_shuffle",
    beats_per_bar=4,
    hits=[
        # Shuffle feel (swung eighths)
        DrumHit(0, KICK, 95),
        DrumHit(0, CLOSED_HIHAT, 80),
        DrumHit(0.67, CLOSED_HIHAT, 60),
        DrumHit(1, CLOSED_HIHAT, 75),
        DrumHit(1, SNARE, 90),
        DrumHit(1.67, CLOSED_HIHAT, 60),
        DrumHit(2, KICK, 90),
        DrumHit(2, CLOSED_HIHAT, 80),
        DrumHit(2.67, CLOSED_HIHAT, 60),
        DrumHit(3, CLOSED_HIHAT, 75),
        DrumHit(3, SNARE, 90),
        DrumHit(3.67, CLOSED_HIHAT, 60),
    ]
)

BLUES_BASS = BassPattern(
    name="blues_shuffle",
    notes=[
        NoteEvent(0, 0, 0.6, 95),
        NoteEvent(0.67, 0, 0.3, 80),
        NoteEvent(1, 7, 0.6, 90),
        NoteEvent(1.67, 7, 0.3, 75),
        NoteEvent(2, 0, 0.6, 95),
        NoteEvent(2.67, 0, 0.3, 80),
        NoteEvent(3, 7, 0.6, 90),
        NoteEvent(3.67, 9, 0.3, 75),  # 6th for blues
    ]
)


# =============================================================================
# PATTERN COLLECTIONS
# =============================================================================

DRUM_PATTERNS = {
    "swing": [SWING_DRUMS_BASIC, SWING_DRUMS_BRUSHES],
    "bossa": [BOSSA_DRUMS],
    "rock": [ROCK_DRUMS_BASIC, ROCK_DRUMS_HEAVY],
    "funk": [FUNK_DRUMS],
    "ballad": [BALLAD_DRUMS],
    "latin": [LATIN_DRUMS],
    "waltz": [WALTZ_DRUMS],
    "blues": [BLUES_DRUMS],
}

BASS_PATTERNS = {
    "swing": [SWING_BASS_WALKING],
    "bossa": [BOSSA_BASS],
    "rock": [ROCK_BASS, ROCK_BASS_DRIVING],
    "funk": [FUNK_BASS],
    "ballad": [BALLAD_BASS],
    "latin": [LATIN_BASS],
    "waltz": [WALTZ_BASS],
    "blues": [BLUES_BASS],
}

COMP_PATTERNS = {
    "swing": [SWING_COMP],
    "bossa": [BOSSA_COMP],
    "rock": [],  # Block chords handled differently
    "funk": [],
    "ballad": [BALLAD_COMP],
    "latin": [],
    "waltz": [],
    "blues": [],
}


def get_patterns(style: str) -> dict:
    """
    Get all patterns for a given style.
    
    Returns:
        Dict with 'drums', 'bass', 'comp' keys containing pattern lists
        
    Example:
        >>> patterns = get_patterns("bossa")
        >>> drums = patterns["drums"][0]
    """
    return {
        "drums": DRUM_PATTERNS.get(style, DRUM_PATTERNS["swing"]),
        "bass": BASS_PATTERNS.get(style, BASS_PATTERNS["swing"]),
        "comp": COMP_PATTERNS.get(style, COMP_PATTERNS["swing"]),
    }
