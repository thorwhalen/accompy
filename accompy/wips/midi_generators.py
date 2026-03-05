"""
MIDI generators — convert NoteSequence to MidiData.

Registered converters: NoteSequence -> MidiData

Multiple backends:
- pretty_midi: most Pythonic API, good for programmatic construction
- midiutil: accompy's existing dependency, simpler
- mido: lowest-level, message-based

Also provides ChordSequence -> MidiData shortcut converters that
combine chord resolution + MIDI generation in one step.
"""

from __future__ import annotations

import io
from typing import Callable

from .types import ChordSequence, MidiData, NoteSequence, converter


# ---------------------------------------------------------------------------
# NoteSequence -> MidiData via pretty_midi
# ---------------------------------------------------------------------------


def noteseq_to_midi_pretty_midi(
    ns: NoteSequence,
    *,
    program: int = 0,
    instrument_name: str = "Piano",
) -> MidiData:
    """Convert NoteSequence to MidiData using pretty_midi.

    Renders each chord as a block of simultaneous notes.

    >>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
    >>> md = noteseq_to_midi_pretty_midi(ns)
    >>> md.has_pretty_midi
    True
    """
    import pretty_midi

    pm = pretty_midi.PrettyMIDI(initial_tempo=ns.tempo)
    inst = pretty_midi.Instrument(program=program, name=instrument_name)

    # Convert beats to seconds
    beat_duration = 60.0 / ns.tempo
    current_beat = 0.0

    for midi_notes, duration_beats in ns.notes:
        start_sec = current_beat * beat_duration
        end_sec = (current_beat + duration_beats) * beat_duration
        for pitch in midi_notes:
            note = pretty_midi.Note(
                velocity=90,
                pitch=pitch,
                start=start_sec,
                end=end_sec,
            )
            inst.notes.append(note)
        current_beat += duration_beats

    pm.instruments.append(inst)
    return MidiData(
        pretty_midi_obj=pm,
        tempo=ns.tempo,
        time_signature=ns.time_signature,
    )


# ---------------------------------------------------------------------------
# NoteSequence -> MidiData via midiutil
# ---------------------------------------------------------------------------


def noteseq_to_midi_midiutil(ns: NoteSequence) -> MidiData:
    """Convert NoteSequence to MidiData using midiutil (MIDIFile).

    >>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
    >>> md = noteseq_to_midi_midiutil(ns)
    >>> md.has_bytes
    True
    """
    from midiutil import MIDIFile

    midi = MIDIFile(1)
    track = 0
    channel = 0
    midi.addTempo(track, 0, ns.tempo)
    midi.addTimeSignature(
        track, 0, ns.time_signature[0], ns.time_signature[1], 24
    )
    midi.addProgramChange(track, channel, 0, 0)  # Piano

    current_beat = 0.0
    for midi_notes, duration_beats in ns.notes:
        for pitch in midi_notes:
            midi.addNote(
                track, channel, pitch, current_beat, duration_beats, 90
            )
        current_beat += duration_beats

    buf = io.BytesIO()
    midi.writeFile(buf)
    return MidiData(
        bytes_=buf.getvalue(),
        tempo=ns.tempo,
        time_signature=ns.time_signature,
    )


# ---------------------------------------------------------------------------
# NoteSequence -> MidiData via mido
# ---------------------------------------------------------------------------


def noteseq_to_midi_mido(ns: NoteSequence) -> MidiData:
    """Convert NoteSequence to MidiData using mido.

    >>> ns = NoteSequence([([60, 64, 67], 4.0)], tempo=120)
    >>> md = noteseq_to_midi_mido(ns)
    >>> md.has_bytes
    True
    """
    import mido

    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Set tempo
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(ns.tempo)))

    # Convert notes
    ticks_per_beat = 480
    current_tick = 0
    events = []  # (tick, type, note, velocity)

    beat_pos = 0.0
    for midi_notes, duration_beats in ns.notes:
        start_tick = int(beat_pos * ticks_per_beat)
        end_tick = int((beat_pos + duration_beats) * ticks_per_beat)
        for pitch in midi_notes:
            events.append((start_tick, "note_on", pitch, 90))
            events.append((end_tick, "note_off", pitch, 0))
        beat_pos += duration_beats

    # Sort by tick, then note_off before note_on at same tick
    events.sort(key=lambda e: (e[0], 0 if e[1] == "note_off" else 1))

    prev_tick = 0
    for tick, msg_type, pitch, vel in events:
        delta = tick - prev_tick
        track.append(mido.Message(msg_type, note=pitch, velocity=vel, time=delta))
        prev_tick = tick

    buf = io.BytesIO()
    mid.save(file=buf)
    return MidiData(
        bytes_=buf.getvalue(),
        tempo=ns.tempo,
        time_signature=ns.time_signature,
    )


# ---------------------------------------------------------------------------
# Register NoteSequence -> MidiData converters
# ---------------------------------------------------------------------------

converter.register(
    NoteSequence,
    MidiData,
    noteseq_to_midi_pretty_midi,
    name="pretty_midi",
    is_default=True,
)

converter.register(
    NoteSequence, MidiData, noteseq_to_midi_midiutil, name="midiutil"
)

converter.register(
    NoteSequence, MidiData, noteseq_to_midi_mido, name="mido"
)


# ---------------------------------------------------------------------------
# Shortcut: ChordSequence -> MidiData (combining resolution + MIDI gen)
# ---------------------------------------------------------------------------


def _make_chordseq_to_midi(
    resolver_name: str, midi_gen_name: str
) -> Callable[[ChordSequence], MidiData]:
    """Factory for ChordSequence -> MidiData shortcuts."""

    def convert_fn(cs: ChordSequence) -> MidiData:
        resolve_fn = converter.get(ChordSequence, NoteSequence, resolver_name)
        midi_fn = converter.get(NoteSequence, MidiData, midi_gen_name)
        ns = resolve_fn(cs)
        return midi_fn(ns)

    name = f"{resolver_name}+{midi_gen_name}"
    convert_fn.__name__ = name
    return convert_fn


# Register the most useful shortcuts
converter.register(
    ChordSequence,
    MidiData,
    _make_chordseq_to_midi("pychord", "pretty_midi"),
    name="pychord+pretty_midi",
    is_default=True,
)

converter.register(
    ChordSequence,
    MidiData,
    _make_chordseq_to_midi("tonal", "midiutil"),
    name="tonal+midiutil",
)

converter.register(
    ChordSequence,
    MidiData,
    _make_chordseq_to_midi("music21", "pretty_midi"),
    name="music21+pretty_midi",
)
