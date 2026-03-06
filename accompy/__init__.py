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

Converter Pipeline:
    >>> from accompy import converter, ChordSequence, MidiData, convert
    >>> # List available converters for a given step
    >>> converter.list_converters(ChordSequence, MidiData)  # doctest: +SKIP
    >>> # Convert using the default or a named converter
    >>> midi = convert(chord_seq, MidiData)  # doctest: +SKIP
    >>> midi = convert(chord_seq, MidiData, via="midiutil")  # doctest: +SKIP

Advanced Usage (Extensibility):
    >>> # Register custom patterns
    >>> from accompy import get_pattern_registry
    >>> registry = get_pattern_registry()
    >>> # registry['my_style'] = {'drums': [...], 'bass': [...], 'comp': [...]}
    >>>
    >>> # Use custom chord resolver
    >>> from accompy import set_chord_resolver
    >>> # set_chord_resolver(my_custom_resolver)
    >>>
    >>> # Access protocol definitions for custom implementations
    >>> from accompy.protocols import ChordResolver, PatternSource, SynthesizerBackend
"""

__version__ = "0.3.0"

# =============================================================================
# Main API — pattern-based accompaniment
# =============================================================================

from .main import (
    generate_accompaniment,
    play_audio,
    check_dependencies,
    print_setup_instructions,
)

from .base import (
    Score,
    ChordEvent,
    AccompanimentConfig,
    MidiEvent,
    ensure_score,
    BackendType,
    StyleName,
)

from .patterns import (
    DrumPattern,
    BassPattern,
    CompingPattern,
    DrumHit,
    NoteEvent,
    get_patterns,
    get_pattern_registry,
    register_style,
)

from .setup_utils import (
    verify_and_setup,
    setup_soundfont,
    diagnose_issues,
    print_diagnostic_report,
)

# =============================================================================
# Converter pipeline — types, registry, and high-level functions
# =============================================================================

from .converters import (
    ChordSequence,
    NoteSequence,
    MidiData,
    AudioData,
    ChordSheet,
    ConverterRegistry,
    converter,
    convert,
)

from .pipeline import (
    chords_to_sequence,
    chords_to_notes,
    chords_to_midi,
    chords_to_audio,
    midi_to_audio,
    list_available_converters,
)

# Import converter registration modules so converters are registered on import
import accompy.chord_parsers as _chord_parsers  # noqa: F401
import accompy.chord_resolvers as _chord_resolvers  # noqa: F401
import accompy.midi_generators as _midi_generators  # noqa: F401
import accompy.audio_renderers as _audio_renderers  # noqa: F401

# =============================================================================
# Advanced/Extensibility API
# =============================================================================

from .chord_resolution import (
    chord_to_notes,
    get_chord_resolver,
    set_chord_resolver,
    tonal_resolver,
)

from .protocols import (
    ChordResolver,
    PatternSource,
    SynthesizerBackend,
)

from .realtime import RealtimeAccompaniment


__all__ = [
    # Main API
    "generate_accompaniment",
    "ensure_score",
    "play_audio",
    "check_dependencies",
    "print_setup_instructions",
    # Data structures — original
    "Score",
    "ChordEvent",
    "AccompanimentConfig",
    "MidiEvent",
    "BackendType",
    "StyleName",
    # Data structures — converter pipeline
    "ChordSequence",
    "NoteSequence",
    "MidiData",
    "AudioData",
    "ChordSheet",
    # Converter registry
    "ConverterRegistry",
    "converter",
    "convert",
    # High-level pipeline functions
    "chords_to_sequence",
    "chords_to_notes",
    "chords_to_midi",
    "chords_to_audio",
    "midi_to_audio",
    "list_available_converters",
    # Pattern types and registry
    "DrumPattern",
    "BassPattern",
    "CompingPattern",
    "DrumHit",
    "NoteEvent",
    "get_patterns",
    "get_pattern_registry",
    "register_style",
    # Setup utilities
    "verify_and_setup",
    "setup_soundfont",
    "diagnose_issues",
    "print_diagnostic_report",
    # Advanced/Extensibility API
    "chord_to_notes",
    "get_chord_resolver",
    "set_chord_resolver",
    "tonal_resolver",
    "ChordResolver",
    "PatternSource",
    "SynthesizerBackend",
    "RealtimeAccompaniment",
]


# =============================================================================
# Import-time dependency check (can be disabled)
# =============================================================================


def _check_setup_on_import():
    """
    Verify dependencies on import and warn user if setup is incomplete.

    Set ACCOMPY_SKIP_SETUP_CHECK=1 to disable this check.
    """
    import os

    if os.environ.get("ACCOMPY_SKIP_SETUP_CHECK"):
        return

    deps = check_dependencies()

    # Check critical dependencies
    critical_missing = []
    if not deps["fluidsynth"]:
        critical_missing.append("fluidsynth")
    if not deps["soundfont"]:
        critical_missing.append("soundfont")
    if not deps["midiutil"]:
        critical_missing.append("midiutil")

    if critical_missing:
        import warnings

        warnings.warn(
            f"\naccompy setup incomplete - missing: {', '.join(critical_missing)}\n"
            f"Run: python -c \"from accompy.setup_utils import verify_and_setup; verify_and_setup()\"\n"
            f"Or: python -m accompy --check-deps\n"
            f"To disable this warning: export ACCOMPY_SKIP_SETUP_CHECK=1",
            category=UserWarning,
            stacklevel=2,
        )


# Check dependencies on import (can be disabled via env var)
_check_setup_on_import()
