"""
MIDI and MMA rendering backends for accompy.

This module provides different backends for generating MIDI from scores:
- midi: Built-in MIDI generation using midiutil
- mma: MMA (Musical MIDI Accompaniment) backend for more realistic grooves
"""

from .midi import generate_midi_events, events_to_midi_file

__all__ = [
    "generate_midi_events",
    "events_to_midi_file",
]
