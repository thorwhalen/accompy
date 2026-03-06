"""
Core domain models for accompy.

Contains Score, ChordEvent, AccompanimentConfig and related data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Optional
from types import MappingProxyType

# Type aliases
ChordSymbol = str
ChordSpec = tuple[str, int | float]  # (chord_name, beats)
StyleName = Literal[
    "swing", "bossa", "rock", "ballad", "funk", "latin", "waltz", "blues"
]
BackendType = Literal["auto", "mma", "builtin"]


@dataclass(frozen=True)
class MidiEvent:
    """
    A single MIDI event.

    Used for event-based MIDI generation that enables both batch file creation
    and future real-time streaming.

    Attributes:
        time: Event time in beats
        channel: MIDI channel (0-15)
        note: MIDI note number (0-127)
        velocity: Note velocity (0-127)
        duration: Note duration in beats
    """
    time: float
    channel: int
    note: int
    velocity: int
    duration: float


@dataclass
class ChordEvent:
    """
    A chord at a specific position in the progression.

    Example:
        >>> event = ChordEvent("Dm7", beats=4)
        >>> event.symbol
        'D-7'
    """
    symbol: str
    beats: int = 4

    def __post_init__(self):
        from .util import normalize_chord_symbol
        self.symbol = normalize_chord_symbol(self.symbol)


@dataclass
class Score:
    """
    A musical score containing chord events and metadata.

    This is the domain model for chord progressions. It provides a unified
    representation regardless of input format (string, iReal URL, tuples, etc.).

    Example:
        >>> score = Score.from_string("| C | Am | F | G |", time_signature=(4, 4))
        >>> list(score.measures)
        [['C'], ['A-'], ['F'], ['G']]
    """
    measures: list[list[str]]
    title: str = "Untitled"
    composer: str = ""
    key: str = "C"
    time_signature: tuple[int, int] = (4, 4)

    @classmethod
    def from_string(
        cls,
        chord_string: str,
        *,
        title: str = "Untitled",
        key: str = "C",
        time_signature: tuple[int, int] = (4, 4),
    ) -> "Score":
        """
        Parse a chord string into a Score.

        Supports formats:
        - Simple: "C Am F G" (space-separated, one chord per bar)
        - Bar lines: "| C | Am | F | G |"
        - Multi-chord bars: "| C Am | F G |" (chords split evenly)
        - iReal-style: "C-7 F7 | Bb^7 | Eh7 A7b9 |"

        Example:
            >>> Score.from_string("| Dm7 | G7 | C^7 | % |").measures  # % means repeat
            [['D-7'], ['G7'], ['C^7'], ['C^7']]
        """
        from .util import parse_chord_string
        measures = parse_chord_string(chord_string)
        return cls(
            measures=measures,
            title=title,
            key=key,
            time_signature=time_signature,
        )

    @classmethod
    def from_ireal_url(cls, url: str) -> "Score":
        """
        Parse an iReal Pro URL into a Score.

        Example::
            url = "irealb://Autumn%20Leaves=..."
            score = Score.from_ireal_url(url)
        """
        from .util import parse_ireal_url
        return parse_ireal_url(url)

    def to_chord_sequence(self, *, tempo: int = 120):
        """Convert Score to a ChordSequence (from the converter pipeline).

        Each chord gets a duration proportional to its share of the bar.

        Example:
            >>> score = Score.from_string("| Dm7 | G7 | C^7 |")
            >>> cs = score.to_chord_sequence(tempo=160)
            >>> len(cs)
            3
        """
        from .converters import ChordSequence

        beats_per_bar = self.time_signature[0]
        chords: list[tuple[str, float]] = []
        for measure in self.measures:
            if not measure:
                continue
            beats_each = beats_per_bar / len(measure)
            for sym in measure:
                chords.append((sym, float(beats_each)))
        return ChordSequence(
            chords=chords,
            title=self.title,
            key=self.key,
            tempo=tempo,
            time_signature=self.time_signature,
        )

    def __iter__(self) -> Iterable[list[str]]:
        return iter(self.measures)

    def __len__(self) -> int:
        return len(self.measures)


@dataclass
class AccompanimentConfig:
    """
    Configuration for accompaniment generation.

    This is the single source of truth for all configuration options,
    including dependency injection hooks for extensibility.

    Attributes:
        style: Musical style (swing, bossa, rock, etc.)
        tempo: Beats per minute
        repeats: Number of times to play through the form
        instruments: Which instruments to include
        volumes: Relative volume for each instrument (0.0-1.0)
        soundfont: Path to SoundFont file for synthesis
        sample_rate: Audio sample rate
        output_format: Output file format
        chord_resolver: Optional custom chord resolution function
        pattern_source: Optional custom pattern provider
        synthesis_backend: Optional custom synthesis backend
    """
    # Core settings
    style: StyleName = "swing"
    tempo: int = 120
    repeats: int = 2
    instruments: dict[str, bool] = field(
        default_factory=lambda: {
            "drums": True,
            "bass": True,
            "piano": True,
            "guitar": False,
        }
    )
    volumes: dict[str, float] = field(
        default_factory=lambda: {
            "drums": 0.8,
            "bass": 0.9,
            "piano": 0.7,
        }
    )

    # Synthesis settings
    soundfont: Optional[Path] = None
    sample_rate: int = 44100
    output_format: Literal["wav", "mp3", "flac", "midi"] = "wav"

    # Extensibility hooks (dependency injection)
    # NOTE: These are populated at runtime to avoid circular imports
    chord_resolver: Optional[Any] = None  # ChordResolver protocol
    pattern_source: Optional[Any] = None  # PatternSource protocol
    synthesis_backend: Optional[Any] = None  # SynthesizerBackend protocol

    def with_overrides(self, **kwargs) -> "AccompanimentConfig":
        """
        Create a new config with specified overrides.

        This enables immutable updates to configuration.

        Example:
            >>> config = AccompanimentConfig(tempo=120)
            >>> fast_config = config.with_overrides(tempo=180)
            >>> config.tempo, fast_config.tempo
            (120, 180)
        """
        from dataclasses import replace
        return replace(self, **kwargs)


def ensure_score(
    chords: Any,
    *,
    title: str = "Untitled",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> Score:
    """
    Coerce common chord-progression formats into a `Score`.

    Supported inputs:
    - `Score`: returned as-is
    - `str`: chord string (e.g. `"| C | Am | F | G |"`) OR iReal URL (`irealbook://...`)
    - `Iterable[tuple[str, int|float]]`: list of `(chord, beats)` like in `accompany`
    - `Iterable[str]`: chord symbols, one per bar
    - `list[list[str]]`: already-parsed measures

    Notes:
    - `Score.measures` in `accompy` does not encode per-chord durations within a bar.
      For `(chord, beats)` inputs, durations not equal to whole bars are approximated
      by grouping chords into bars.

    Examples:
        >>> ensure_score("| C | Am | F | G |", time_signature=(4, 4)).measures
        [['C'], ['A-'], ['F'], ['G']]
        >>> ensure_score([("F#m7b5", 4), ("B7", 4), ("Em", 8)], key="E").measures[:3]
        [['F#h7'], ['B7'], ['E-']]
    """
    from .util import normalize_chord_symbol, score_from_chord_specs

    if isinstance(chords, Score):
        return chords

    if isinstance(chords, str):
        s = chords.strip()
        if s.startswith(("irealbook://", "irealb://")):
            return Score.from_ireal_url(s)
        return Score.from_string(s, title=title, key=key, time_signature=time_signature)

    if (
        isinstance(chords, list)
        and chords
        and all(
            isinstance(x, (list, tuple)) and all(isinstance(c, str) for c in x)
            for x in chords
        )
    ):
        measures = [[normalize_chord_symbol(c) for c in measure] for measure in chords]
        return Score(
            measures=measures, title=title, key=key, time_signature=time_signature
        )

    if isinstance(chords, Iterable):
        items = list(chords)
        if not items:
            return Score(
                measures=[], title=title, key=key, time_signature=time_signature
            )

        if all(isinstance(x, str) for x in items):
            measures = [[normalize_chord_symbol(x)] for x in items]
            return Score(
                measures=measures, title=title, key=key, time_signature=time_signature
            )

        if all(
            isinstance(x, (list, tuple))
            and len(x) == 2
            and isinstance(x[0], str)
            and isinstance(x[1], (int, float))
            for x in items
        ):
            return score_from_chord_specs(
                items, title=title, key=key, time_signature=time_signature
            )

    raise TypeError(
        "Unsupported chords input. Expected Score, chord string, iReal URL, "
        "list of (chord, beats) tuples, iterable of chord symbols, or measures list."
    )
