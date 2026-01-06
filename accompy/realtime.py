"""
Real-time accompaniment support (foundation).

This module provides the foundation for real-time accompaniment playback,
separating event scheduling from synthesis. This enables integration with
real-time audio systems like hum/pyo in the future.

NOTE: This is scaffolding for future work. Current implementation focuses on
event generation infrastructure. Real-time audio synthesis integration
with hum/pyo is planned for a future release.
"""

from __future__ import annotations

from typing import Iterator, Callable, Optional, Any

from .base import Score, AccompanimentConfig, MidiEvent, ensure_score
from .renderers.midi import generate_midi_events


class RealtimeAccompaniment:
    """
    Real-time accompaniment player (foundation for future work).

    This class separates event scheduling from synthesis, enabling integration
    with real-time audio systems. Current implementation generates events;
    future versions will integrate with hum/pyo for actual audio synthesis.

    Example (current usage):
        >>> from accompy import AccompanimentConfig
        >>> config = AccompanimentConfig(tempo=120, style='swing')
        >>> player = RealtimeAccompaniment(config)
        >>> player.set_chords([('Dm7', 4), ('G7', 4), ('Cmaj7', 8)])
        >>> events_iter = player.events()  # Get event iterator
        >>> # Future: for event in events_iter: synth.play(event.note, event.velocity)

    Future usage (with hum integration):
        >>> from hum.pyo_util import Synth  # doctest: +SKIP
        >>> def on_event(event: MidiEvent):  # doctest: +SKIP
        ...     # Send MIDI event to synth in real-time
        ...     synth.send_note(event.note, event.velocity, event.duration)
        >>> player = RealtimeAccompaniment(config, on_event=on_event)  # doctest: +SKIP
        >>> player.play()  # doctest: +SKIP
    """

    def __init__(
        self,
        config: Optional[AccompanimentConfig] = None,
        *,
        on_event: Optional[Callable[[MidiEvent], None]] = None,
    ):
        """
        Initialize real-time accompaniment player.

        Args:
            config: Accompaniment configuration (tempo, style, etc.)
            on_event: Optional callback for each MIDI event (for real-time playback)
        """
        self.config = config or AccompanimentConfig()
        self._on_event = on_event
        self._score: Optional[Score] = None

    def set_chords(self, chords: Any) -> None:
        """
        Update the chord progression.

        Args:
            chords: Chord progression in any supported format
                   (string, Score, list of tuples, etc.)

        Example:
            >>> player = RealtimeAccompaniment()
            >>> player.set_chords("| Dm7 | G7 | Cmaj7 |")
            >>> player._score is not None
            True
        """
        self._score = ensure_score(chords)

    def events(self) -> Iterator[MidiEvent]:
        """
        Generate events for current chord progression.

        Yields:
            MidiEvent objects in chronological order

        Example:
            >>> player = RealtimeAccompaniment()
            >>> player.set_chords([('C', 4)])
            >>> events = list(player.events())
            >>> len(events) > 0
            True
        """
        if self._score is None:
            return

        # Get dependencies (with defaults)
        from .patterns import get_pattern_registry
        from .chord_resolution import get_chord_resolver

        pattern_source = self.config.pattern_source or get_pattern_registry()
        chord_resolver = self.config.chord_resolver or get_chord_resolver()

        # Generate and yield events
        for event in generate_midi_events(
            self._score,
            self.config,
            pattern_source=pattern_source,
            chord_resolver=chord_resolver,
        ):
            if self._on_event:
                self._on_event(event)
            yield event

    def play(self) -> None:
        """
        Play the accompaniment (future implementation).

        This will integrate with a real-time synthesis backend (hum/pyo)
        to actually play audio. Current implementation is a placeholder.

        Raises:
            NotImplementedError: Real-time playback not yet implemented
        """
        raise NotImplementedError(
            "Real-time playback is planned for a future release.\n"
            "This will integrate with the hum package for real-time synthesis.\n"
            "For now, use generate_accompaniment() for file-based output."
        )

    def stop(self) -> None:
        """
        Stop playback (future implementation).

        Raises:
            NotImplementedError: Real-time playback not yet implemented
        """
        raise NotImplementedError(
            "Real-time playback control is planned for a future release."
        )


# Future integration points for hum/pyo:
#
# class PyoRealtimePlayer(RealtimeAccompaniment):
#     """Real-time player using Pyo synthesis (future)."""
#
#     def __init__(self, config=None):
#         super().__init__(config)
#         from hum.pyo_util import Synth
#         # Initialize synth with appropriate settings
#         self.synth = Synth(...)
#
#     def play(self):
#         """Start real-time playback using Pyo."""
#         # Schedule MIDI events in real-time
#         # Use event times to sync with audio clock
#         for event in self.events():
#             self.synth.schedule_note(
#                 event.note,
#                 event.velocity,
#                 event.duration,
#                 at_time=event.time
#             )
