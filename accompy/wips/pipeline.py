"""
High-level pipeline API — one-call chord-to-audio conversion.

This module provides convenience functions that compose the registered
converters into complete pipelines. It's the simplest entry point.

Usage::

    >>> from accompy.wips.pipeline import chords_to_midi, chords_to_audio
    >>> midi_data = chords_to_midi("| Dm7 | G7 | Cmaj7 |")
    >>> midi_data.write("output.mid")  # doctest: +SKIP

    >>> audio = chords_to_audio("| C | Am | F | G |")  # doctest: +SKIP
    >>> audio.write("output.wav")  # doctest: +SKIP

    >>> # Or with explicit control over which backend to use at each step
    >>> midi_data = chords_to_midi("| C | Am |", resolver="music21", midi_gen="mido")
"""

from __future__ import annotations

from typing import Optional

from .types import (
    AudioData,
    ChordSequence,
    ChordSheet,
    MidiData,
    NoteSequence,
    converter,
)

# Ensure all converters are registered by importing the modules
from . import chord_parsers as _cp  # noqa: F401
from . import chord_resolvers as _cr  # noqa: F401
from . import midi_generators as _mg  # noqa: F401
from . import audio_renderers as _ar  # noqa: F401


def chords_to_sequence(
    chords: str,
    *,
    parser: Optional[str] = None,
    tempo: int = 120,
    title: str = "",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> ChordSequence:
    """Parse a chord string into a ChordSequence.

    Args:
        chords: Chord string in any supported format
        parser: Parser name ('auto_detect', 'plain_text', 'chordpro', 'musicgen_chord')
        tempo: BPM (default 120)
        title: Song title
        key: Key signature
        time_signature: Time signature tuple

    Returns:
        ChordSequence with parsed chords

    >>> cs = chords_to_sequence("| Dm7 | G7 | Cmaj7 |", tempo=140)
    >>> cs.symbols
    ['Dm7', 'G7', 'Cmaj7']
    >>> cs.tempo
    140
    """
    parse_fn = converter.get(str, ChordSequence, parser)
    cs = parse_fn(
        chords,
        tempo=tempo,
        title=title,
        key=key,
        time_signature=time_signature,
    )
    return cs


def chords_to_notes(
    chords: str | ChordSequence,
    *,
    resolver: Optional[str] = None,
    tempo: int = 120,
) -> NoteSequence:
    """Convert chord string or ChordSequence to resolved MIDI notes.

    Args:
        chords: Chord string or ChordSequence
        resolver: Resolver name ('pychord', 'music21', 'mingus', 'tonal')
        tempo: BPM (used if chords is a string)

    Returns:
        NoteSequence with MIDI note numbers

    >>> ns = chords_to_notes("| C | Am |")
    >>> len(ns)
    2
    >>> all(0 <= n <= 127 for notes, _ in ns for n in notes)
    True
    """
    if isinstance(chords, str):
        cs = chords_to_sequence(chords, tempo=tempo)
    else:
        cs = chords

    resolve_fn = converter.get(ChordSequence, NoteSequence, resolver)
    return resolve_fn(cs)


def chords_to_midi(
    chords: str | ChordSequence,
    *,
    resolver: Optional[str] = None,
    midi_gen: Optional[str] = None,
    tempo: int = 120,
    output_path: Optional[str] = None,
) -> MidiData:
    """Convert chord string to MIDI data.

    Args:
        chords: Chord string or ChordSequence
        resolver: Resolver name ('pychord', 'music21', 'mingus', 'tonal')
        midi_gen: MIDI generator name ('pretty_midi', 'midiutil', 'mido')
        tempo: BPM
        output_path: Optional path to write MIDI file

    Returns:
        MidiData object

    >>> md = chords_to_midi("| C | Am | F | G |")
    >>> md.to_bytes()[:4]
    b'MThd'
    """
    if isinstance(chords, str):
        cs = chords_to_sequence(chords, tempo=tempo)
    else:
        cs = chords

    ns = converter.get(ChordSequence, NoteSequence, resolver)(cs)
    md = converter.get(NoteSequence, MidiData, midi_gen)(ns)

    if output_path:
        md.write(output_path)

    return md


def chords_to_audio(
    chords: str | ChordSequence,
    *,
    resolver: Optional[str] = None,
    midi_gen: Optional[str] = None,
    audio_renderer: Optional[str] = None,
    soundfont: Optional[str] = None,
    tempo: int = 120,
    sr: int = 44100,
    output_path: Optional[str] = None,
) -> AudioData:
    """Convert chord string to audio.

    This is the complete pipeline: parse -> resolve -> MIDI -> audio.

    Args:
        chords: Chord string or ChordSequence
        resolver: Chord resolver ('pychord', 'music21', 'mingus', 'tonal')
        midi_gen: MIDI generator ('pretty_midi', 'midiutil', 'mido')
        audio_renderer: Audio renderer ('pretty_midi', 'fluidsynth', 'tonal')
        soundfont: Path to SoundFont file
        tempo: BPM
        sr: Sample rate
        output_path: Optional path to write WAV file

    Returns:
        AudioData with waveform and sample rate

    >>> audio = chords_to_audio("| C | Am | F | G |")  # doctest: +SKIP
    >>> audio.write("output.wav")  # doctest: +SKIP
    """
    md = chords_to_midi(chords, resolver=resolver, midi_gen=midi_gen, tempo=tempo)

    render_fn = converter.get(MidiData, AudioData, audio_renderer)
    kwargs = {"sr": sr}
    if soundfont:
        kwargs["soundfont"] = soundfont
    audio = render_fn(md, **kwargs)

    if output_path:
        audio.write(output_path)

    return audio


def midi_to_audio(
    midi_data: MidiData,
    *,
    audio_renderer: Optional[str] = None,
    soundfont: Optional[str] = None,
    sr: int = 44100,
    output_path: Optional[str] = None,
) -> AudioData:
    """Convert MidiData to audio.

    Args:
        midi_data: MidiData object
        audio_renderer: Audio renderer name
        soundfont: Path to SoundFont file
        sr: Sample rate
        output_path: Optional path to write WAV file

    Returns:
        AudioData

    >>> audio = midi_to_audio(some_midi_data)  # doctest: +SKIP
    """
    render_fn = converter.get(MidiData, AudioData, audio_renderer)
    kwargs = {"sr": sr}
    if soundfont:
        kwargs["soundfont"] = soundfont
    audio = render_fn(midi_data, **kwargs)

    if output_path:
        audio.write(output_path)

    return audio


def file_to_audio(
    filepath: str,
    *,
    output_path: str | None = None,
    n_repeats: int = 1,
    transpose: int = 0,
    resolver: str | None = None,
    midi_gen: str | None = None,
    audio_renderer: str | None = None,
    soundfont: str | None = None,
    tempo: int | None = None,
    sr: int = 44100,
) -> AudioData:
    """Convert an iReal Pro HTML/URL file to audio.

    Handles:
    - iReal Pro HTML files (exported from the app)
    - iReal Pro URL strings
    - Plain chord text files

    Supports repeating the progression and transposing.

    Args:
        filepath: Path to an iReal HTML file, or a chord text file
        output_path: Where to write audio. If None, uses filepath with .wav extension
        n_repeats: Number of times to repeat the progression (default 1)
        transpose: Semitones to transpose (positive=up, negative=down)
        resolver: Chord resolver backend
        midi_gen: MIDI generator backend
        audio_renderer: Audio renderer backend
        soundfont: Path to SoundFont file
        tempo: Override BPM (None = use file's tempo or 120)
        sr: Sample rate

    Returns:
        AudioData

    Example::

        >>> file_to_audio("/path/to/song.html")  # doctest: +SKIP
        >>> file_to_audio("/path/to/song.html", n_repeats=40)  # doctest: +SKIP
        >>> file_to_audio("/path/to/song.html", transpose=5)  # doctest: +SKIP
    """
    from pathlib import Path as _Path

    fp = _Path(filepath)

    # Determine output path
    if output_path is None:
        output_path = str(fp.with_suffix(".wav"))

    # Read and parse the file
    cs = _parse_file(filepath, tempo=tempo)

    # Apply transpose
    if transpose != 0:
        cs = _transpose_chord_sequence(cs, transpose)

    # Apply repeats
    if n_repeats > 1:
        cs = _repeat_chord_sequence(cs, n_repeats)

    # Override tempo if specified
    if tempo is not None:
        cs = ChordSequence(
            chords=cs.chords,
            title=cs.title,
            key=cs.key,
            tempo=tempo,
            time_signature=cs.time_signature,
        )

    return chords_to_audio(
        cs,
        resolver=resolver,
        midi_gen=midi_gen,
        audio_renderer=audio_renderer,
        soundfont=soundfont,
        tempo=cs.tempo,
        sr=sr,
        output_path=output_path,
    )


def file_to_midi(
    filepath: str,
    *,
    output_path: str | None = None,
    n_repeats: int = 1,
    transpose: int = 0,
    resolver: str | None = None,
    midi_gen: str | None = None,
    tempo: int | None = None,
) -> MidiData:
    """Convert an iReal Pro HTML/URL file to MIDI.

    Same as file_to_audio but outputs MIDI instead.

    Args:
        filepath: Path to an iReal HTML file, or a chord text file
        output_path: Where to write MIDI. If None, uses filepath with .mid extension
        n_repeats: Number of times to repeat the progression
        transpose: Semitones to transpose
        resolver: Chord resolver backend
        midi_gen: MIDI generator backend
        tempo: Override BPM

    Returns:
        MidiData
    """
    from pathlib import Path as _Path

    fp = _Path(filepath)
    if output_path is None:
        output_path = str(fp.with_suffix(".mid"))

    cs = _parse_file(filepath, tempo=tempo)

    if transpose != 0:
        cs = _transpose_chord_sequence(cs, transpose)
    if n_repeats > 1:
        cs = _repeat_chord_sequence(cs, n_repeats)
    if tempo is not None:
        cs = ChordSequence(
            chords=cs.chords, title=cs.title, key=cs.key,
            tempo=tempo, time_signature=cs.time_signature,
        )

    return chords_to_midi(
        cs, resolver=resolver, midi_gen=midi_gen,
        tempo=cs.tempo, output_path=output_path,
    )


# ---------------------------------------------------------------------------
# Helpers for file parsing, transpose, repeat
# ---------------------------------------------------------------------------


def _parse_file(filepath: str, *, tempo: int | None = None) -> ChordSequence:
    """Parse an iReal HTML file or chord text file into a ChordSequence."""
    import re as _re
    from pathlib import Path as _Path

    fp = _Path(filepath)
    content = fp.read_text(encoding="utf-8", errors="replace")

    # Try to extract iReal URL from HTML
    match = _re.search(r'href="(irealb://[^"]+)"', content)
    if match:
        return _parse_ireal_url_robust(match.group(1), tempo=tempo)

    # Check if the content itself is an iReal URL
    stripped = content.strip()
    if stripped.startswith(("irealb://", "irealbook://")):
        return _parse_ireal_url_robust(stripped, tempo=tempo)

    # Fall back to plain text chord parsing
    return chords_to_sequence(content, tempo=tempo or 120)


def _parse_ireal_url_robust(url: str, *, tempo: int | None = None) -> ChordSequence:
    """Parse an iReal Pro URL, handling edge cases pyRealParser misses.

    Falls back to manual parsing when pyRealParser fails (e.g., URLs with
    empty fields that cause == in the URL).
    """
    import re as _re
    from urllib.parse import unquote as _unquote

    # Try pyRealParser first
    try:
        from pyRealParser import Tune

        tunes = Tune.parse_ireal_url(url)
        if tunes:
            t = tunes[0]
            measures = [m for m in t.measures_as_strings if m and m.strip()]
            return ChordSequence(
                chords=[(m, 4.0) for m in measures],
                title=t.title or "",
                key=t.key or "C",
                tempo=tempo or (int(t.bpm) if t.bpm else 120),
            )
    except Exception:
        pass

    # Manual fallback: handle URLs that pyRealParser chokes on
    decoded = _unquote(url)
    if "://" in decoded:
        decoded = decoded.split("://", 1)[1]

    # Split on single = to preserve empty fields
    raw_parts = decoded.split("=")
    title = raw_parts[0] if raw_parts else "Untitled"

    # Find the chord data: look for the scramble prefix
    prefix = "1r34LbKcu7"
    chord_part = None
    chord_idx = None
    for i, part in enumerate(raw_parts):
        if prefix in part:
            chord_part = part
            chord_idx = i
            break

    if chord_part is None:
        raise ValueError(f"Could not find chord data in iReal URL")

    # Extract key: typically 2 positions before chords
    key = raw_parts[chord_idx - 2] if chord_idx >= 2 else "C"
    if len(key) > 2 or not key:  # sanity check
        key = "C"

    # Extract tempo: typically 2 positions after chords
    file_tempo = 120
    if chord_idx + 2 < len(raw_parts):
        try:
            file_tempo = int(raw_parts[chord_idx + 2])
        except (ValueError, IndexError):
            pass

    # Unscramble the chord data
    scrambled = chord_part.split(prefix, 1)[1]
    try:
        from pyRealParser import Tune

        unscrambled = Tune._unscramble_chord_string(scrambled)
        cleaned = Tune._cleanup_chord_string(unscrambled)
        measures = Tune._get_measures(cleaned)
    except Exception:
        # Bare minimum fallback if pyRealParser not available
        measures = _re.findall(r"([A-G][#b]?[^|{}\[\]]*?)(?:\s*\|)", scrambled)

    measures = [m.strip() for m in measures if m.strip()]
    return ChordSequence(
        chords=[(m, 4.0) for m in measures],
        title=title,
        key=key,
        tempo=tempo or file_tempo,
    )


def _transpose_chord_sequence(cs: ChordSequence, semitones: int) -> ChordSequence:
    """Transpose all chords in a ChordSequence by the given number of semitones.

    >>> cs = ChordSequence([("C", 4.0), ("Am", 4.0), ("F", 4.0), ("G", 4.0)])
    >>> t = _transpose_chord_sequence(cs, 2)
    >>> t.symbols
    ['D', 'Bm', 'G', 'A']
    """
    transposed = []
    for symbol, dur in cs.chords:
        new_symbol = _transpose_chord_symbol(symbol, semitones)
        transposed.append((new_symbol, dur))
    return ChordSequence(
        chords=transposed,
        title=cs.title,
        key=_transpose_note_name(cs.key, semitones),
        tempo=cs.tempo,
        time_signature=cs.time_signature,
    )


def _repeat_chord_sequence(cs: ChordSequence, n: int) -> ChordSequence:
    """Repeat the chord progression n times.

    >>> cs = ChordSequence([("C", 4.0), ("G", 4.0)])
    >>> r = _repeat_chord_sequence(cs, 3)
    >>> len(r)
    6
    >>> r.symbols
    ['C', 'G', 'C', 'G', 'C', 'G']
    """
    return ChordSequence(
        chords=cs.chords * n,
        title=cs.title,
        key=cs.key,
        tempo=cs.tempo,
        time_signature=cs.time_signature,
    )


# Note names for transposition
_SHARP_NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
_FLAT_NOTES = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
_NOTE_TO_SEMITONE = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}


def _transpose_note_name(name: str, semitones: int) -> str:
    """Transpose a single note name by semitones.

    >>> _transpose_note_name("C", 5)
    'F'
    >>> _transpose_note_name("A", -2)
    'G'
    """
    if name not in _NOTE_TO_SEMITONE:
        return name
    idx = (_NOTE_TO_SEMITONE[name] + semitones) % 12
    # Use flats for negative transposition, sharps for positive
    notes = _FLAT_NOTES if semitones < 0 else _SHARP_NOTES
    return notes[idx]


def _transpose_chord_symbol(symbol: str, semitones: int) -> str:
    """Transpose a chord symbol by semitones.

    >>> _transpose_chord_symbol("Am7", 2)
    'Bm7'
    >>> _transpose_chord_symbol("C6/E", 5)
    'F6/A'
    >>> _transpose_chord_symbol("G#o", -2)
    'Gbo'
    """
    import re as _re

    if not symbol or symbol in ("", "N.C.", "NC"):
        return symbol

    # Handle slash chords: "C6/E" -> transpose both parts
    if "/" in symbol:
        parts = symbol.split("/", 1)
        main = _transpose_chord_symbol(parts[0], semitones)
        bass = _transpose_chord_symbol(parts[1], semitones)
        return f"{main}/{bass}"

    # Extract root note (with optional # or b)
    match = _re.match(r"^([A-G][#b]?)(.*)", symbol)
    if not match:
        return symbol

    root = match.group(1)
    quality = match.group(2)
    new_root = _transpose_note_name(root, semitones)
    return new_root + quality


def list_available_converters() -> dict[str, list[str]]:
    """List all available converters organized by pipeline stage.

    Returns:
        Dict mapping stage names to lists of converter names.

    >>> info = list_available_converters()
    >>> 'parsers' in info
    True
    >>> 'resolvers' in info
    True
    """
    return {
        "parsers": converter.list_converters(str, ChordSequence),
        "resolvers": converter.list_converters(ChordSequence, NoteSequence),
        "midi_generators": converter.list_converters(NoteSequence, MidiData),
        "audio_renderers": converter.list_converters(MidiData, AudioData),
        "shortcuts_chord_to_midi": converter.list_converters(
            ChordSequence, MidiData
        ),
        "shortcuts_chord_to_audio": converter.list_converters(
            ChordSequence, AudioData
        ),
    }
