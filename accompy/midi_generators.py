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

from .converters import ChordSequence, MidiData, NoteSequence, converter


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


# ---------------------------------------------------------------------------
# Builtin accompaniment: ChordSequence -> MidiData with drums/bass/piano
# ---------------------------------------------------------------------------


def chordseq_to_midi_builtin_accompaniment(
    cs: ChordSequence,
    *,
    style: str = "swing",
    repeats: int = 1,
) -> MidiData:
    """Convert ChordSequence to multi-track MIDI using accompy's pattern engine.

    This bridges the converter pipeline to the existing pattern-based
    accompaniment engine (drums, bass, piano).

    >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
    >>> md = chordseq_to_midi_builtin_accompaniment(cs, style="swing")
    >>> md.has_bytes
    True
    """
    from .base import AccompanimentConfig, ensure_score
    from .patterns import get_pattern_registry
    from .chord_resolution import get_chord_resolver
    from .renderers.midi import generate_builtin_midi

    score = cs.to_score()
    config = AccompanimentConfig(style=style, tempo=cs.tempo, repeats=repeats)
    pattern_source = get_pattern_registry()
    chord_resolver = get_chord_resolver()

    midi_path = generate_builtin_midi(
        score, config,
        pattern_source=pattern_source,
        chord_resolver=chord_resolver,
    )
    midi_bytes = midi_path.read_bytes()
    midi_path.unlink(missing_ok=True)
    return MidiData(bytes_=midi_bytes, tempo=cs.tempo, time_signature=cs.time_signature)


converter.register(
    ChordSequence,
    MidiData,
    chordseq_to_midi_builtin_accompaniment,
    name="builtin_accompaniment",
)


# ---------------------------------------------------------------------------
# ChordSequence -> MidiData via MMA (Musical MIDI Accompaniment)
# ---------------------------------------------------------------------------


def chordseq_to_midi_mma(
    cs: ChordSequence,
    *,
    style: str = "swing",
    repeats: int = 1,
) -> MidiData:
    """Convert ChordSequence to MIDI using MMA (Musical MIDI Accompaniment).

    MMA generates sophisticated multi-instrument accompaniment patterns
    from chord symbols, similar to Band-in-a-Box.

    Requires: ``mma`` CLI on PATH.
    See https://www.mellowood.ca/mma/ for installation.

    >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
    >>> md = chordseq_to_midi_mma(cs, style="swing")  # doctest: +SKIP
    """
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    if not shutil.which("mma"):
        raise RuntimeError(
            "MMA (Musical MIDI Accompaniment) not found on PATH. "
            "Install from https://www.mellowood.ca/mma/"
        )

    from .base import AccompanimentConfig
    from .main import _score_to_mma

    score = cs.to_score()
    config = AccompanimentConfig(style=style, tempo=cs.tempo, repeats=repeats)
    mma_content = _score_to_mma(score, config)

    mma_path = Path(tempfile.mktemp(suffix=".mma"))
    midi_path = mma_path.with_suffix(".mid")
    try:
        mma_path.write_text(mma_content)
        subprocess.run(
            ["mma", str(mma_path), "-f", str(midi_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        midi_bytes = midi_path.read_bytes()
        return MidiData(
            bytes_=midi_bytes, tempo=cs.tempo, time_signature=cs.time_signature
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"MMA failed: {e.stderr}")
    finally:
        mma_path.unlink(missing_ok=True)
        midi_path.unlink(missing_ok=True)


converter.register(
    ChordSequence,
    MidiData,
    chordseq_to_midi_mma,
    name="mma",
)
