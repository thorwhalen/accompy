"""
MIDI and MMA rendering backends for accompy.

This module provides different backends for generating MIDI from scores:
- midi: Built-in MIDI generation using midiutil
- mma: MMA (Musical MIDI Accompaniment) backend for more realistic grooves
"""

from .midi import (
    bass_pitch,
    chord_events,
    comp_voicing,
    events_to_midi_file,
    generate_events,
    generate_midi_events,
    pitch_classes,
    resolve_pitch_offset,
    select_patterns,
)

__all__ = [
    "chord_events",
    "bass_pitch",
    "comp_voicing",
    "pitch_classes",
    "resolve_pitch_offset",
    "generate_events",
    "select_patterns",
    "generate_midi_events",
    "events_to_midi_file",
]
