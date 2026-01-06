"""
Protocols defining extensibility contracts for accompy.

These protocols (structural interfaces) enable dependency injection and
allow users to provide custom implementations of core components.

Key protocols:
- ChordResolver: Convert chord symbols to MIDI notes
- PatternSource: Provide patterns for styles
- MidiEventGenerator: Generate MIDI events from scores
- AudioRenderer: Render MIDI to audio

See PEP 544 for more on Protocol types.
"""

from __future__ import annotations

from typing import Protocol, Iterator, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Score, AccompanimentConfig, MidiEvent
    from pathlib import Path


@runtime_checkable
class ChordResolver(Protocol):
    """
    Convert chord symbols to MIDI note numbers.

    Example implementation:
        >>> def my_resolver(symbol: str) -> list[int]:
        ...     # Return MIDI notes for chord
        ...     return [60, 64, 67]  # C major
    """

    def __call__(self, symbol: str) -> list[int]:
        """
        Resolve a chord symbol to MIDI notes.

        Args:
            symbol: Chord symbol (e.g., "Dm7", "G7", "Cmaj7")

        Returns:
            List of MIDI note numbers (0-127)
        """
        ...


@runtime_checkable
class PatternSource(Protocol):
    """
    Provides musical patterns for a given style.

    Example:
        >>> class MyPatternSource:
        ...     def get_patterns(self, style: str) -> dict:
        ...         return {'drums': [...], 'bass': [...], 'comp': [...]}
        ...     def available_styles(self) -> list[str]:
        ...         return ['swing', 'bossa']
    """

    def get_patterns(self, style: str) -> dict[str, list]:
        """
        Get patterns for a style.

        Args:
            style: Style name (e.g., "swing", "bossa", "rock")

        Returns:
            Dict with 'drums', 'bass', 'comp' keys containing pattern lists
        """
        ...

    def available_styles(self) -> list[str]:
        """
        List all available style names.

        Returns:
            List of style names
        """
        ...


@runtime_checkable
class MidiEventGenerator(Protocol):
    """
    Generates MIDI events from score and patterns.

    This protocol enables alternative MIDI generation strategies
    (e.g., more sophisticated voicings, real-time adaptation).
    """

    def generate(
        self,
        score: Score,
        config: AccompanimentConfig,
        *,
        chord_resolver: ChordResolver,
        pattern_source: PatternSource,
    ) -> Iterator[MidiEvent]:
        """
        Generate MIDI events from a score.

        Args:
            score: Musical score with chord progression
            config: Accompaniment configuration
            chord_resolver: Function to resolve chords to notes
            pattern_source: Source of musical patterns

        Yields:
            MidiEvent objects in time order
        """
        ...


@runtime_checkable
class AudioRenderer(Protocol):
    """
    Renders MIDI events to audio.

    This protocol abstracts audio synthesis, enabling:
    - Different synthesis backends (FluidSynth, Pyo, etc.)
    - Real-time vs. batch rendering
    - Alternative output formats
    """

    def render(
        self,
        events: Iterator[MidiEvent],
        config: AccompanimentConfig,
    ) -> bytes:
        """
        Render MIDI events to PCM audio data.

        Args:
            events: Iterator of MIDI events
            config: Rendering configuration (tempo, sample rate, etc.)

        Returns:
            Raw PCM audio bytes
        """
        ...

    def render_to_file(
        self,
        events: Iterator[MidiEvent],
        config: AccompanimentConfig,
        output_path: Path,
    ) -> Path:
        """
        Render MIDI events directly to an audio file.

        Args:
            events: Iterator of MIDI events
            config: Rendering configuration
            output_path: Where to save the audio file

        Returns:
            Path to the created file
        """
        ...


@runtime_checkable
class SynthesizerBackend(Protocol):
    """
    Audio synthesis backend.

    Simpler protocol than AudioRenderer, focused just on synthesis.
    Used by the synthesis module.
    """

    def render_to_file(
        self,
        midi_path: Path,
        output_path: Path,
        *,
        sample_rate: int = 44100,
    ) -> Path:
        """
        Render a MIDI file to audio.

        Args:
            midi_path: Path to MIDI file
            output_path: Where to save audio
            sample_rate: Audio sample rate

        Returns:
            Path to the created audio file
        """
        ...

    def render_to_bytes(
        self,
        midi_path: Path,
        *,
        sample_rate: int = 44100,
    ) -> bytes:
        """
        Render a MIDI file to PCM bytes (for streaming).

        Args:
            midi_path: Path to MIDI file
            sample_rate: Audio sample rate

        Returns:
            Raw PCM audio bytes
        """
        ...

    @classmethod
    def is_available(cls) -> bool:
        """
        Check if this backend's dependencies are installed.

        Returns:
            True if the backend can be used
        """
        ...
