"""
MIDI event generation (stateless, iterator-based).

This module provides event-based MIDI generation that separates event creation
from file writing, enabling both batch file creation and future real-time streaming.

Key functions:
- generate_midi_events: Pure function that yields MIDI events
- events_to_midi_file: Side-effect function that writes events to a file
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Iterator, Sequence, Optional, Iterable

from ..base import Score, AccompanimentConfig, MidiEvent
from ..patterns.dataclasses import DrumPattern, BassPattern, CompingPattern


def generate_midi_events(
    score: Score,
    config: AccompanimentConfig,
    *,
    pattern_source,  # PatternSource protocol
    chord_resolver,  # ChordResolver protocol
) -> Iterator[MidiEvent]:
    """
    Generate MIDI events from score.

    Yields events in time order. Does NOT write files.
    This enables real-time streaming or batch file creation.

    Args:
        score: Musical score with chord progression
        config: Accompaniment configuration
        pattern_source: Source providing patterns (must have get_patterns method)
        chord_resolver: Function to convert chord symbols to MIDI notes

    Yields:
        MidiEvent objects in chronological order

    Example:
        >>> from accompy.base import Score, AccompanimentConfig
        >>> from accompy.patterns import get_patterns
        >>> from accompy.chord_resolution import chord_to_notes
        >>> score = Score.from_string("| C | Am | F | G |")
        >>> config = AccompanimentConfig()
        >>> events = generate_midi_events(score, config,
        ...     pattern_source=type('PS', (), {'get_patterns': get_patterns})(),
        ...     chord_resolver=chord_to_notes)
        >>> first_event = next(events)  # doctest: +SKIP
    """
    # Get patterns for the style
    try:
        patterns_dict = pattern_source.get_patterns(config.style)
    except AttributeError:
        # Fallback for simple dict/function interface
        patterns_dict = pattern_source(config.style) if callable(pattern_source) else pattern_source.get(config.style, {})

    # Select specific patterns (first of each type)
    drum_patterns: list = patterns_dict.get("drums", [])
    bass_patterns: list = patterns_dict.get("bass", [])
    comp_patterns: list = patterns_dict.get("comp", [])

    beats_per_bar = score.time_signature[0]

    # Select patterns based on time signature
    drum_pattern = _select_pattern(drum_patterns, beats_per_bar)
    bass_pattern = bass_patterns[0] if bass_patterns else None
    comp_pattern = comp_patterns[0] if comp_patterns else None

    # Generate events for each repeat
    for repeat in range(config.repeats):
        current_beat = repeat * len(score.measures) * beats_per_bar

        for measure in score.measures:
            chords_in_bar = measure
            beats_per_chord = beats_per_bar // len(chords_in_bar) if chords_in_bar else beats_per_bar

            for chord_idx, chord_symbol in enumerate(chords_in_bar):
                chord_start = current_beat + (chord_idx * beats_per_chord)

                if chord_symbol in ('', 'n', 'N.C.', 'NC'):
                    continue

                # Get chord notes
                try:
                    notes = chord_resolver(chord_symbol)
                except Exception:
                    # Fallback for simple chords
                    notes = [48, 52, 55]  # C minor default

                root = notes[0] if notes else 48

                # Yield drum events
                if config.instruments.get("drums", True) and drum_pattern:
                    yield from _drum_events(
                        drum_pattern,
                        chord_start,
                        beats_per_chord,
                        config.volumes.get("drums", 0.8)
                    )

                # Yield bass events
                if config.instruments.get("bass", True) and bass_pattern:
                    yield from _bass_events(
                        bass_pattern,
                        chord_start,
                        beats_per_chord,
                        root,
                        notes,
                        config.volumes.get("bass", 0.9)
                    )

                # Yield comping events
                if config.instruments.get("piano", True):
                    yield from _comp_events(
                        comp_pattern,
                        chord_start,
                        beats_per_chord,
                        notes,
                        config.volumes.get("piano", 0.7)
                    )

            current_beat += beats_per_bar


def _select_pattern(patterns: list, beats_per_bar: int):
    """Select a pattern matching the time signature, or use the first one."""
    if not patterns:
        return None
    # Try to find a matching pattern
    for pattern in patterns:
        if hasattr(pattern, 'beats_per_bar') and pattern.beats_per_bar == beats_per_bar:
            return pattern
    # Default to first pattern
    return patterns[0]


def _drum_events(
    pattern: DrumPattern,
    start_beat: float,
    duration: float,
    volume: float
) -> Iterator[MidiEvent]:
    """Generate drum MIDI events."""
    channel = 9  # MIDI drum channel
    for hit in pattern.hits:
        if hit.beat < duration:
            yield MidiEvent(
                time=start_beat + hit.beat,
                channel=channel,
                note=hit.drum,
                velocity=int(hit.velocity * volume),
                duration=0.25  # Short drum hits
            )


def _bass_events(
    pattern: BassPattern,
    start_beat: float,
    duration: float,
    root: int,
    chord_notes: list[int],
    volume: float
) -> Iterator[MidiEvent]:
    """Generate bass MIDI events."""
    channel = 0  # Bass channel

    # Adjust to bass range (octave 2-3)
    bass_root = (root % 12) + 36
    root_pc = bass_root % 12
    chord_pcs = _pitch_classes(chord_notes)

    for note in pattern.notes:
        if note.beat >= duration:
            continue

        resolved = _resolve_pitch_offset(
            root_pc=root_pc,
            chord_pcs=chord_pcs,
            target_offset=note.pitch_offset
        )
        pitch = bass_root + resolved
        vel = int(note.velocity * volume)
        dur = min(note.duration, max(0.0, duration - note.beat))
        if dur <= 0:
            continue

        yield MidiEvent(
            time=start_beat + note.beat,
            channel=channel,
            note=pitch,
            velocity=vel,
            duration=dur
        )


def _comp_events(
    pattern: Optional[CompingPattern],
    start_beat: float,
    duration: float,
    chord_notes: list[int],
    volume: float
) -> Iterator[MidiEvent]:
    """Generate piano/comping MIDI events."""
    channel = 1  # Piano channel

    # Move to mid-range
    notes = [(n % 12) + 60 for n in chord_notes[:4]] if chord_notes else [60, 64, 67]

    if pattern is None or not pattern.hits:
        # Default: block chords on each beat
        velocity = int(90 * volume)
        for i in range(min(int(duration), 4)):
            for note in notes:
                yield MidiEvent(
                    time=start_beat + i,
                    channel=channel,
                    note=note,
                    velocity=velocity,
                    duration=0.9
                )
        return

    # Use pattern
    for hit_beat, hit_duration, hit_velocity in pattern.hits:
        if hit_beat >= duration:
            continue
        dur = min(hit_duration, max(0.0, duration - hit_beat))
        if dur <= 0:
            continue

        velocity = int(hit_velocity * volume)
        for note in notes:
            yield MidiEvent(
                time=start_beat + hit_beat,
                channel=channel,
                note=note,
                velocity=velocity,
                duration=dur
            )


def _pitch_classes(notes: Iterable[int]) -> tuple[int, ...]:
    """Return unique pitch classes (0-11) as a tuple."""
    return tuple(sorted({n % 12 for n in notes}))


def _resolve_pitch_offset(
    *, root_pc: int, chord_pcs: tuple[int, ...], target_offset: int
) -> int:
    """
    Resolve a pitch offset against a chord.

    The patterns use semitone offsets (0=root, 7=5th, etc.). When an offset
    represents a chord tone which varies by quality (e.g. 3rd), we prefer a
    matching chord tone from `chord_pcs`.

    Examples:
        For a minor chord, a pattern might request offset 4 ("3rd"); this
        function will choose 3 if the chord contains a minor 3rd.
    """
    if not chord_pcs:
        return target_offset

    chord_intervals = tuple(sorted(((pc - root_pc) % 12) for pc in chord_pcs))
    if target_offset in chord_intervals:
        return target_offset

    # Special case: major vs minor 3rd
    if target_offset in (3, 4):
        if 3 in chord_intervals:
            return 3
        if 4 in chord_intervals:
            return 4

    # Special case: perfect 5th
    if target_offset == 7 and chord_intervals:
        if 7 in chord_intervals:
            return 7

    return target_offset


def events_to_midi_file(
    events: Sequence[MidiEvent],
    path: Path,
    tempo: int,
    time_signature: tuple[int, int] = (4, 4)
) -> Path:
    """
    Write MIDI events to a MIDI file.

    Args:
        events: Sequence of MIDI events (must be subscriptable, not just iterable)
        path: Output file path
        tempo: Tempo in BPM
        time_signature: Time signature (numerator, denominator)

    Returns:
        Path to the created MIDI file

    Note:
        Requires midiutil: pip install midiutil
    """
    from midiutil import MIDIFile

    # Determine number of tracks
    channels_used = {event.channel for event in events}
    num_tracks = len(channels_used)

    if num_tracks == 0:
        # Create empty MIDI file
        num_tracks = 1

    midi = MIDIFile(num_tracks)

    # Create channel to track mapping
    channel_to_track = {ch: idx for idx, ch in enumerate(sorted(channels_used))}

    # Set up tracks
    for channel, track in channel_to_track.items():
        midi.addTempo(track, 0, tempo)
        midi.addTimeSignature(track, 0, time_signature[0], time_signature[1], 24)

        # Set program (instrument) for the track
        if channel == 9:
            # Drums (channel 9) - no program change needed
            midi.addTrackName(track, 0, "Drums")
        elif channel == 0:
            midi.addTrackName(track, 0, "Bass")
            midi.addProgramChange(track, channel, 0, 33)  # Acoustic Bass
        elif channel == 1:
            midi.addTrackName(track, 0, "Piano")
            midi.addProgramChange(track, channel, 0, 0)  # Acoustic Grand Piano
        else:
            midi.addTrackName(track, 0, f"Track {channel}")

    # Add all events
    for event in events:
        track = channel_to_track.get(event.channel, 0)
        midi.addNote(
            track,
            event.channel,
            event.note,
            event.time,
            event.duration,
            event.velocity
        )

    # Write to file
    with open(path, 'wb') as f:
        midi.writeFile(f)

    return path


def generate_builtin_midi(
    score: Score,
    config: AccompanimentConfig,
    *,
    pattern_source,
    chord_resolver,
) -> Path:
    """
    Generate a MIDI file using the built-in renderer.

    This is a convenience function that combines event generation and file writing.

    Args:
        score: Musical score
        config: Configuration
        pattern_source: Pattern provider
        chord_resolver: Chord resolution function

    Returns:
        Path to the generated MIDI file
    """
    # Generate events
    events = list(generate_midi_events(
        score,
        config,
        pattern_source=pattern_source,
        chord_resolver=chord_resolver
    ))

    # Write to temp file
    midi_path = Path(tempfile.mktemp(suffix=".mid"))
    events_to_midi_file(events, midi_path, config.tempo, score.time_signature)

    return midi_path
