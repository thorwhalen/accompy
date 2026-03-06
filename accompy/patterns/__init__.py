"""
Pattern registry and access for accompany patterns.

This module provides access to musical patterns (drums, bass, comping) for
different styles. Includes a MutableMapping-based PatternRegistry for
runtime pattern registration.
"""

from collections.abc import MutableMapping
from typing import Iterator

from .dataclasses import (
    DrumPattern,
    BassPattern,
    CompingPattern,
    DrumHit,
    NoteEvent,
    # MIDI drum constants
    KICK,
    SNARE,
    SIDE_STICK,
    CLOSED_HIHAT,
    OPEN_HIHAT,
    PEDAL_HIHAT,
    RIDE,
    RIDE_BELL,
    CRASH,
    LOW_TOM,
    MID_TOM,
    HIGH_TOM,
    COWBELL,
    CLAVES,
    SHAKER,
)

# Import pattern collections
from .builtin import DRUM_PATTERNS, BASS_PATTERNS, COMP_PATTERNS

# Common built-in patterns (public API convenience exports)
from .builtin import (
    SWING_DRUMS_BASIC,
    SWING_BASS_WALKING,
    BOSSA_DRUMS,
    BOSSA_BASS,
    ROCK_DRUMS_BASIC,
    WALTZ_DRUMS,
)


class PatternRegistry(MutableMapping[str, dict]):
    """
    Registry of accompaniment patterns by style.

    Implements MutableMapping for intuitive access:
        registry['bossa']  # Get patterns
        registry['my_style'] = {...}  # Register custom
        del registry['my_style']  # Remove

    Example:
        >>> registry = PatternRegistry()
        >>> registry.register_builtin_patterns()
        >>> 'swing' in registry
        True
        >>> registry['swing']['drums'][0].name
        'swing_basic'
    """

    def __init__(self):
        self._patterns: dict[str, dict] = {}

    def __getitem__(self, style: str) -> dict:
        if style not in self._patterns:
            raise KeyError(f"Unknown style: {style}. Available: {list(self._patterns)}")
        return self._patterns[style]

    def __setitem__(self, style: str, patterns: dict) -> None:
        # Validate structure
        required_keys = {"drums", "bass", "comp"}
        if not required_keys.issubset(patterns.keys()):
            raise ValueError(f"Pattern dict must have keys: {required_keys}")
        self._patterns[style] = patterns

    def __delitem__(self, style: str) -> None:
        del self._patterns[style]

    def __iter__(self) -> Iterator[str]:
        return iter(self._patterns)

    def __len__(self) -> int:
        return len(self._patterns)

    def register_builtin_patterns(self) -> None:
        """Load all built-in patterns."""
        for style in DRUM_PATTERNS:
            self._patterns[style] = {
                "drums": DRUM_PATTERNS.get(style, []),
                "bass": BASS_PATTERNS.get(style, []),
                "comp": COMP_PATTERNS.get(style, []),
            }

    def available_styles(self) -> list[str]:
        """Get list of all available style names."""
        return list(self._patterns.keys())

    def get_patterns(self, style: str) -> dict:
        """
        Get patterns for a style (PatternSource protocol method).

        Args:
            style: Style name

        Returns:
            Dict with 'drums', 'bass', 'comp' keys
        """
        return self[style]


# Global registry (lazy-loaded)
_registry: PatternRegistry | None = None


def get_pattern_registry() -> PatternRegistry:
    """
    Get the global pattern registry, initializing if needed.

    Returns:
        The global PatternRegistry instance

    Example:
        >>> registry = get_pattern_registry()
        >>> 'swing' in registry
        True
    """
    global _registry
    if _registry is None:
        _registry = PatternRegistry()
        _registry.register_builtin_patterns()
    return _registry


def get_patterns(style: str) -> dict:
    """
    Get all patterns for a given style.

    Returns:
        Dict with 'drums', 'bass', 'comp' keys containing pattern lists

    Example:
        >>> patterns = get_patterns("bossa")
        >>> drums = patterns["drums"][0]
        >>> drums.name
        'bossa'
    """
    return get_pattern_registry().get_patterns(style)


def register_style(style: str, drums: list, bass: list, comp: list) -> None:
    """
    Register a custom style with the global registry.

    Args:
        style: Style name
        drums: List of DrumPattern objects
        bass: List of BassPattern objects
        comp: List of CompingPattern objects

    Example:
        >>> registry = get_pattern_registry()
        >>> register_style('my_funk', [my_drum_pattern], [my_bass_pattern], [])  # doctest: +SKIP
    """
    get_pattern_registry()[style] = {
        "drums": drums,
        "bass": bass,
        "comp": comp,
    }


__all__ = [
    # Data classes
    "DrumPattern",
    "BassPattern",
    "CompingPattern",
    "DrumHit",
    "NoteEvent",
    # Pattern registry
    "PatternRegistry",
    "get_pattern_registry",
    "get_patterns",
    "register_style",
    # MIDI drum constants
    "KICK",
    "SNARE",
    "SIDE_STICK",
    "CLOSED_HIHAT",
    "OPEN_HIHAT",
    "PEDAL_HIHAT",
    "RIDE",
    "RIDE_BELL",
    "CRASH",
    "LOW_TOM",
    "MID_TOM",
    "HIGH_TOM",
    "COWBELL",
    "CLAVES",
    "SHAKER",
    # Convenience exports for common built-in patterns
    "SWING_DRUMS_BASIC",
    "SWING_BASS_WALKING",
    "BOSSA_DRUMS",
    "BOSSA_BASS",
    "ROCK_DRUMS_BASIC",
    "WALTZ_DRUMS",
]
