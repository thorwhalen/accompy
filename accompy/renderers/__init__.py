"""
MIDI and MMA rendering backends for accompy.

This module provides different backends for generating MIDI from scores:
- midi: Built-in MIDI generation using midiutil
- mma: MMA (Musical MIDI Accompaniment) backend for more realistic grooves
"""

from .midi import (
    chord_events,
    events_to_midi_file,
    generate_events,
    generate_midi_events,
    select_patterns,
)

__all__ = [
    "chord_events",
    "generate_events",
    "select_patterns",
    "generate_midi_events",
    "events_to_midi_file",
]
