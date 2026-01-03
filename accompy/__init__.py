"""
accompy - Generate accompaniment audio from chord charts.

Generate backing tracks with bass, drums, piano from chord progressions,
similar to iReal Pro.

Example:
    >>> from accompy import generate_accompaniment, Score
    >>>
    >>> # Simple usage
    >>> path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=120)  # doctest: +SKIP
    >>>
    >>> # With Score object for more control
    >>> score = Score.from_string("| Dm7 | G7 | C^7 | A7b9 |", title="ii-V-I")
    >>> path = generate_accompaniment(score, style="swing", tempo=160, repeats=4)  # doctest: +SKIP

Available styles: swing, bossa, rock, ballad, funk, latin, waltz, blues
"""

__version__ = "0.1.0"

from .accompy import (
    # Main API
    generate_accompaniment,
    ensure_score,
    play_audio,
    check_dependencies,
    print_setup_instructions,
    # Data classes
    Score,
    ChordEvent,
    AccompanimentConfig,
    BackendType,
)

from .patterns import (
    DrumPattern,
    BassPattern,
    CompingPattern,
    get_patterns,
)

from .setup_utils import (
    verify_and_setup,
    setup_soundfont,
    diagnose_issues,
    print_diagnostic_report,
)

__all__ = [
    # Core functions
    "generate_accompaniment",
    "ensure_score",
    "play_audio",
    # Data structures
    "Score",
    "ChordEvent",
    "AccompanimentConfig",
    "BackendType",
    # Pattern types
    "DrumPattern",
    "BassPattern",
    "CompingPattern",
    "get_patterns",
    # Setup utilities
    "check_dependencies",
    "print_setup_instructions",
    "verify_and_setup",
    "setup_soundfont",
    "diagnose_issues",
    "print_diagnostic_report",
]
