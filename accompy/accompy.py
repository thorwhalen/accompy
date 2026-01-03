"""
accompy - Generate accompaniment audio from chord charts.

A Python library that generates backing tracks (bass, drums, piano, etc.)
from chord progressions, similar to iReal Pro.

Example:
    >>> from accompy import generate_accompaniment
    >>> chords = "| C | Am | F | G |"
    >>> audio_path = generate_accompaniment(chords, style="bossa", tempo=120)  # doctest: +SKIP
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from urllib.parse import unquote
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal, Mapping, Optional, Union

# Type aliases
ChordSymbol = str
ChordSpec = tuple[str, int | float]  # (chord_name, beats)
StyleName = Literal[
    "swing", "bossa", "rock", "ballad", "funk", "latin", "waltz", "blues"
]
BackendType = Literal["auto", "mma", "builtin"]


@dataclass
class ChordEvent:
    """A chord at a specific position in the progression."""

    symbol: str
    beats: int = 4

    def __post_init__(self):
        self.symbol = _normalize_chord_symbol(self.symbol)


@dataclass
class Score:
    """
    A musical score containing chord events and metadata.

    Example:
        >>> score = Score.from_string("| C | Am | F | G |", time_signature=(4, 4))
        >>> list(score.measures)
        [['C'], ['A-'], ['F'], ['G']]
    """

    measures: list[list[str]]
    title: str = "Untitled"
    composer: str = ""
    key: str = "C"
    time_signature: tuple[int, int] = (4, 4)

    @classmethod
    def from_string(
        cls,
        chord_string: str,
        *,
        title: str = "Untitled",
        key: str = "C",
        time_signature: tuple[int, int] = (4, 4),
    ) -> "Score":
        """
        Parse a chord string into a Score.

        Supports formats:
        - Simple: "C Am F G" (space-separated, one chord per bar)
        - Bar lines: "| C | Am | F | G |"
        - Multi-chord bars: "| C Am | F G |" (chords split evenly)
        - iReal-style: "C-7 F7 | Bb^7 | Eh7 A7b9 |"

        Example:
            >>> Score.from_string("| Dm7 | G7 | C^7 | % |").measures  # % means repeat
            [['D-7'], ['G7'], ['C^7'], ['C^7']]
        """
        measures = _parse_chord_string(chord_string)
        return cls(
            measures=measures,
            title=title,
            key=key,
            time_signature=time_signature,
        )

    @classmethod
    def from_ireal_url(cls, url: str) -> "Score":
        """
        Parse an iReal Pro URL into a Score.

        Example::

            url = "irealb://Autumn%20Leaves=..."
            score = Score.from_ireal_url(url)
        """
        return _parse_ireal_url(url)

    def __iter__(self) -> Iterable[list[str]]:
        return iter(self.measures)

    def __len__(self) -> int:
        return len(self.measures)


def ensure_score(
    chords: Any,
    *,
    title: str = "Untitled",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> Score:
    """Coerce common chord-progression formats into a `Score`.

    Supported inputs:
    - `Score`: returned as-is
    - `str`: chord string (e.g. `"| C | Am | F | G |"`) OR iReal URL (`irealbook://...`)
    - `Iterable[tuple[str, int|float]]`: list of `(chord, beats)` like in `accompany`
    - `Iterable[str]`: chord symbols, one per bar
    - `list[list[str]]`: already-parsed measures

    Notes:
    - `Score.measures` in `accompy` does not encode per-chord durations within a bar.
      For `(chord, beats)` inputs, durations not equal to whole bars are approximated
      by grouping chords into bars.

    Examples:
        >>> ensure_score("| C | Am | F | G |", time_signature=(4, 4)).measures
        [['C'], ['A-'], ['F'], ['G']]
        >>> ensure_score([("F#m7b5", 4), ("B7", 4), ("Em", 8)], key="E").measures[:3]
        [['F#h7'], ['B7'], ['E-']]
    """

    if isinstance(chords, Score):
        return chords

    if isinstance(chords, str):
        s = chords.strip()
        if s.startswith(("irealbook://", "irealb://")):
            return Score.from_ireal_url(s)
        return Score.from_string(s, title=title, key=key, time_signature=time_signature)

    if (
        isinstance(chords, list)
        and chords
        and all(
            isinstance(x, (list, tuple)) and all(isinstance(c, str) for c in x)
            for x in chords
        )
    ):
        measures = [[_normalize_chord_symbol(c) for c in measure] for measure in chords]
        return Score(
            measures=measures, title=title, key=key, time_signature=time_signature
        )

    if isinstance(chords, Iterable):
        items = list(chords)
        if not items:
            return Score(
                measures=[], title=title, key=key, time_signature=time_signature
            )

        if all(isinstance(x, str) for x in items):
            measures = [[_normalize_chord_symbol(x)] for x in items]
            return Score(
                measures=measures, title=title, key=key, time_signature=time_signature
            )

        if all(
            isinstance(x, (list, tuple))
            and len(x) == 2
            and isinstance(x[0], str)
            and isinstance(x[1], (int, float))
            for x in items
        ):
            return _score_from_chord_specs(
                items, title=title, key=key, time_signature=time_signature
            )

    raise TypeError(
        "Unsupported chords input. Expected Score, chord string, iReal URL, "
        "list of (chord, beats) tuples, iterable of chord symbols, or measures list."
    )


@dataclass
class AccompanimentConfig:
    """
    Configuration for accompaniment generation.

    Attributes:
        style: Musical style (swing, bossa, rock, etc.)
        tempo: Beats per minute
        repeats: Number of times to play through the form
        instruments: Which instruments to include
        volumes: Relative volume for each instrument (0.0-1.0)
    """

    style: StyleName = "swing"
    tempo: int = 120
    repeats: int = 2
    instruments: dict[str, bool] = field(
        default_factory=lambda: {
            "drums": True,
            "bass": True,
            "piano": True,
            "guitar": False,
        }
    )
    volumes: dict[str, float] = field(
        default_factory=lambda: {
            "drums": 0.8,
            "bass": 0.9,
            "piano": 0.7,
        }
    )

    # Audio rendering options
    soundfont: Optional[Path] = None
    sample_rate: int = 44100
    output_format: Literal["wav", "mp3", "flac", "midi"] = "wav"


# =============================================================================
# Main API
# =============================================================================

DFLT_STYLE = "swing"
DFLT_TEMPO = 120
DFLT_REPEATS = 1
DFLT_USE_MMA = True
DFLT_AUTOPLAY = False


def generate_accompaniment(
    chords: Any,
    *,
    style: StyleName = DFLT_STYLE,
    tempo: int = DFLT_TEMPO,
    repeats: int = DFLT_REPEATS,
    output_path: Optional[Union[str, Path]] = None,
    output_format: Optional[Literal["wav", "mp3", "flac", "midi", "mid"]] = None,
    config: Optional[AccompanimentConfig] = None,
    use_mma: bool = DFLT_USE_MMA,
    backend: Optional[BackendType] = None,
    autoplay: bool = DFLT_AUTOPLAY,
) -> Path:
    """
    Generate an accompaniment audio file from a chord progression.

    Args:
        chords: Chord progression as string or Score object
        style: Musical style (swing, bossa, rock, ballad, funk, latin, waltz, blues)
        tempo: Tempo in BPM
        repeats: Number of times to repeat the form
        output_path: Where to save the audio file. If None, creates temp file.
        config: Full configuration object (overrides style/tempo/repeats if provided)
        use_mma: If True, use MMA; if False, use built-in generator
        autoplay: If True, automatically play the audio after generation

    Returns:
        Path to the generated audio file

    Example::

        path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=140)
        print(f"Generated: {path}")

        # Auto-play the generated audio
        path = generate_accompaniment("| C | Am | F | G |", autoplay=True)
    """
    # Build config
    if config is None:
        config = AccompanimentConfig(style=style, tempo=tempo, repeats=repeats)

    # Determine output format (argument > output_path suffix > config)
    if output_path is not None:
        out_path = Path(output_path)
        suffix = out_path.suffix.lstrip('.').lower()
        if output_format is None:
            if suffix in ("wav", "mp3", "flac"):
                output_format = suffix  # type: ignore[assignment]
            elif suffix in ("mid", "midi"):
                output_format = "midi"

    if output_format is not None:
        if output_format == "mid":
            output_format = "midi"
        config.output_format = output_format  # type: ignore[assignment]

    score = ensure_score(chords)

    # Determine output path
    if output_path is None:
        suffix = (
            ".mid" if config.output_format == "midi" else f".{config.output_format}"
        )
        fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        output_path = Path(tmp_path)
    else:
        output_path = Path(output_path)

    # If user gave an unknown/empty suffix, normalize to the selected format
    known_suffixes = {".wav", ".mp3", ".flac", ".mid", ".midi"}
    if output_path.suffix.lower() not in known_suffixes:
        if config.output_format == "midi":
            output_path = output_path.with_suffix(".mid")
        else:
            output_path = output_path.with_suffix(f".{config.output_format}")

    # If MIDI requested, ensure a MIDI-ish extension (better UX)
    if config.output_format == "midi" and output_path.suffix.lower() not in (
        ".mid",
        ".midi",
    ):
        output_path = output_path.with_suffix(".mid")

    # Select backend
    selected_backend: BackendType
    if backend is None:
        selected_backend = "mma" if (use_mma and _mma_available()) else "builtin"
    else:
        selected_backend = backend
        if selected_backend == "auto":
            selected_backend = "mma" if _mma_available() else "builtin"
        elif selected_backend == "mma" and not _mma_available():
            raise RuntimeError(
                "MMA backend requested but MMA is not available. "
                "Install MMA (see https://www.mellowood.ca/mma/) or use backend='builtin'."
            )

    # Generate
    if selected_backend == "mma":
        midi_path = _generate_via_mma(score, config)
    else:
        midi_path = _generate_builtin(score, config)

    # MIDI-only output
    if config.output_format == "midi":
        if midi_path != output_path:
            os.replace(midi_path, output_path)

        if autoplay:
            raise ValueError(
                "autoplay=True is only supported for audio outputs, not MIDI"
            )
        return output_path

    # Render MIDI to audio
    _render_midi_to_audio(midi_path, output_path, config)

    # Auto-play if requested
    if autoplay:
        play_audio(output_path)

    return output_path


def play_audio(audio_path: Union[str, Path]) -> bool:
    """
    Play an audio file using the system's default audio player.

    Args:
        audio_path: Path to the audio file to play

    Returns:
        True if playback started successfully, False otherwise

    Example::

        from accompy import play_audio
        play_audio("/path/to/audio.wav")
    """
    import platform
    import subprocess

    audio_path = Path(audio_path)
    if not audio_path.exists():
        import warnings

        warnings.warn(f"Audio file not found: {audio_path}", UserWarning)
        return False

    system = platform.system().lower()

    try:
        if system == "darwin":  # macOS
            subprocess.Popen(
                ["afplay", str(audio_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        elif system == "linux":
            # Try common Linux audio players in order of preference
            for player in ["paplay", "aplay", "ffplay", "mpg123", "play"]:
                try:
                    subprocess.Popen(
                        [player, str(audio_path)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except FileNotFoundError:
                    continue
            import warnings

            warnings.warn(
                "No audio player found. Install one of: paplay, aplay, ffplay, mpg123, sox",
                UserWarning,
            )
            return False
        elif system == "windows":
            # Windows uses start command
            subprocess.Popen(
                ["start", str(audio_path)],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        else:
            import warnings

            warnings.warn(f"Auto-play not supported on {system}", UserWarning)
            return False
    except Exception as e:
        import warnings

        warnings.warn(f"Failed to play audio: {e}", UserWarning)
        return False


def check_dependencies() -> dict[str, bool]:
    """
    Check which dependencies are available.

    Returns:
        Dict mapping dependency name to availability status

    Example:
        >>> deps = check_dependencies()
        >>> if not deps['fluidsynth']:
        ...     print("Install FluidSynth: brew install fluidsynth")
    """
    return {
        "mma": _mma_available(),
        "fluidsynth": _fluidsynth_available(),
        "soundfont": _default_soundfont_path() is not None,
        "midiutil": _check_import("midiutil"),
        "mingus": _check_import("mingus"),
        "midi2audio": _check_import("midi2audio"),
    }


def print_setup_instructions():
    """Print installation instructions for missing dependencies."""
    deps = check_dependencies()

    if all(deps.values()):
        print("✓ All dependencies installed!")
        return

    print("=== Missing Dependencies ===\n")

    if not deps["fluidsynth"]:
        print("FluidSynth (required for audio rendering):")
        print("  macOS:  brew install fluidsynth")
        print("  Ubuntu: sudo apt-get install fluidsynth")
        print(
            "  Windows: Download from https://github.com/FluidSynth/fluidsynth/releases\n"
        )

    if not deps["soundfont"]:
        print("SoundFont (required for instrument sounds):")
        print("  Download FluidR3_GM.sf2 from:")
        print("  https://member.keymusician.com/Member/FluidR3_GM/index.html")
        print("  Place in: ~/.fluidsynth/default_sound_font.sf2\n")

    if not deps["mma"]:
        print("MMA - Musical MIDI Accompaniment (recommended for realistic tracks):")
        print("  pip install mma  # or")
        print("  git clone https://github.com/infojunkie/mma")
        print("  (See https://www.mellowood.ca/mma/ for details)\n")

    if not deps["midiutil"]:
        print("midiutil (for MIDI generation):")
        print("  pip install midiutil\n")

    if not deps["mingus"]:
        print("mingus (for music theory/chord parsing):")
        print("  pip install mingus\n")

    if not deps["midi2audio"]:
        print("midi2audio (optional Python wrapper for FluidSynth):")
        print("  pip install midi2audio\n")


# =============================================================================
# Chord Parsing
# =============================================================================


def _normalize_chord_symbol(symbol: str) -> str:
    """
    Normalize chord symbols to a standard format.

    Handles conversions like:
    - Cm -> C-
    - Cmaj7 -> C^7
    - Cdim -> Co
    - Cm7b5 -> Ch7 (half-diminished)
    """
    symbol = symbol.strip()
    if not symbol or symbol in ('', 'n', 'N.C.', 'NC', '%', 'x'):
        return symbol

    # Common normalizations
    replacements = [
        ('maj7', '^7'),
        ('maj9', '^9'),
        ('maj', '^'),
        ('min7', '-7'),
        ('min', '-'),
        ('m7', '-7'),
        ('m9', '-9'),
        ('m', '-'),
        ('dim7', 'o7'),
        ('dim', 'o'),
        ('m7b5', 'h7'),
        ('ø7', 'h7'),
        ('ø', 'h'),
        ('sus4', 'sus'),
        ('sus2', 'sus2'),
        ('add9', 'add9'),
        ('add2', 'add2'),
    ]

    result = symbol
    for old, new in replacements:
        # Only replace if it's at the end or followed by a slash
        if result.endswith(old):
            result = result[: -len(old)] + new
        elif f'{old}/' in result:
            result = result.replace(f'{old}/', f'{new}/')

    return result


def _parse_chord_string(chord_string: str) -> list[list[str]]:
    """Parse a chord string into measures, each containing chord symbols."""
    # Clean up
    chord_string = chord_string.strip()

    # Split by bar lines if present
    if '|' in chord_string:
        parts = [p.strip() for p in chord_string.split('|') if p.strip()]
    else:
        # Space-separated, one chord per bar
        parts = [[c] for c in chord_string.split() if c.strip()]
        return [[_normalize_chord_symbol(c) for c in measure] for measure in parts]

    measures = []
    last_chord = None

    for part in parts:
        chords_in_bar = [c.strip() for c in part.split() if c.strip()]
        normalized = []

        for chord in chords_in_bar:
            if chord in ('%', 'x'):
                # Repeat previous bar
                chord = last_chord if last_chord else 'C'
            chord = _normalize_chord_symbol(chord)
            normalized.append(chord)
            last_chord = chord

        if normalized:
            measures.append(normalized)

    return measures


def _parse_ireal_url(url: str) -> Score:
    """Parse an iReal Pro URL into a Score object."""
    try:
        from pyRealParser import Tune

        tunes = Tune.parse_ireal_url(url)
        if not tunes:
            raise ValueError("No songs found in URL")

        tune = tunes[0]
        measures = [[chord] for chord in tune.measures_as_strings if chord]

        return Score(
            measures=measures,
            title=tune.title or "Untitled",
            composer=tune.composer or "",
            key=tune.key or "C",
            time_signature=_parse_time_sig(tune.time_signature),
        )
    except ImportError:
        # Best-effort fallback parser (no external deps)
        return _parse_ireal_url_fallback(url)


def _parse_time_sig(ts_str: Optional[str]) -> tuple[int, int]:
    """Parse time signature string like '4/4' into tuple."""
    if not ts_str:
        return (4, 4)
    try:
        parts = ts_str.split('/')
        return (int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        return (4, 4)


# =============================================================================
# MIDI Generation - Built-in (fallback)
# =============================================================================


def _generate_builtin(score: Score, config: AccompanimentConfig) -> Path:
    """Generate MIDI using midiutil and basic patterns."""
    try:
        from midiutil import MIDIFile
    except ImportError:
        raise ImportError("midiutil required. Install with: pip install midiutil")

    try:
        from mingus.core import chords as mingus_chords
    except ImportError:
        mingus_chords = None

    # Warn about unsupported instruments
    supported_instruments = {"drums", "bass", "piano"}
    unsupported = [
        k for k, v in config.instruments.items() if v and k not in supported_instruments
    ]
    if unsupported:
        import warnings

        warnings.warn(
            f"Instruments {unsupported} are not supported in builtin generator. "
            f"Only {supported_instruments} are supported. Install MMA for more instruments.",
            UserWarning,
        )

    # Create MIDI with multiple tracks - only count implemented instruments
    num_tracks = sum(
        1 for k, v in config.instruments.items() if v and k in supported_instruments
    )
    midi = MIDIFile(num_tracks)

    track_map = {}
    track_idx = 0

    # Set up tracks with unique channels
    if config.instruments.get("drums", True):
        track_map["drums"] = track_idx
        midi.addTrackName(track_idx, 0, "Drums")
        midi.addTempo(track_idx, 0, config.tempo)
        # Drums use channel 9 (set in _add_drum_pattern)
        track_idx += 1

    if config.instruments.get("bass", True):
        track_map["bass"] = track_idx
        midi.addTrackName(track_idx, 0, "Bass")
        midi.addTempo(track_idx, 0, config.tempo)
        midi.addProgramChange(track_idx, 0, 0, 33)  # Channel 0: Acoustic bass
        track_idx += 1

    if config.instruments.get("piano", True):
        track_map["piano"] = track_idx
        midi.addTrackName(track_idx, 0, "Piano")
        midi.addTempo(track_idx, 0, config.tempo)
        midi.addProgramChange(
            track_idx, 1, 0, 0
        )  # Channel 1: Acoustic piano (fixed channel conflict!)
        track_idx += 1

    # Get style patterns
    patterns = _get_style_patterns(config.style)

    # Generate for each repeat
    beats_per_bar = score.time_signature[0]
    current_beat = 0

    for repeat in range(config.repeats):
        for measure in score.measures:
            chords_in_bar = measure
            beats_per_chord = beats_per_bar // len(chords_in_bar)

            for chord_idx, chord_symbol in enumerate(chords_in_bar):
                chord_start = current_beat + (chord_idx * beats_per_chord)

                if chord_symbol in ('', 'n', 'N.C.', 'NC'):
                    continue

                # Get chord notes
                notes = _chord_to_notes(chord_symbol, mingus_chords)
                root = notes[0] if notes else 48  # C3 default

                # Add drums
                if "drums" in track_map:
                    _add_drum_pattern(
                        midi,
                        track_map["drums"],
                        chord_start,
                        beats_per_chord,
                        patterns["drums"],
                        config.volumes.get("drums", 0.8),
                    )

                # Add bass
                if "bass" in track_map:
                    _add_bass_pattern(
                        midi,
                        track_map["bass"],
                        chord_start,
                        beats_per_chord,
                        root,
                        notes,
                        patterns["bass"],
                        config.volumes.get("bass", 0.9),
                    )

                # Add piano/comping
                if "piano" in track_map:
                    _add_piano_pattern(
                        midi,
                        track_map["piano"],
                        chord_start,
                        beats_per_chord,
                        notes,
                        patterns["piano"],
                        config.volumes.get("piano", 0.7),
                    )

            current_beat += beats_per_bar

    # Write MIDI file
    midi_path = Path(tempfile.mktemp(suffix=".mid"))
    with open(midi_path, 'wb') as f:
        midi.writeFile(f)

    return midi_path


def _score_from_chord_specs(
    chords: Iterable[ChordSpec],
    *,
    title: str = "Untitled",
    key: str = "C",
    time_signature: tuple[int, int] = (4, 4),
) -> Score:
    """Create a `Score` from `(chord, beats)` pairs.

    Durations that are multiples of the bar length map cleanly to repeated bars.
    Other durations are approximated by grouping chords into bars.
    """
    beats_per_bar = time_signature[0]

    measures: list[list[str]] = []
    current_bar: list[str] = []
    current_beats: float = 0.0

    for chord, beats in chords:
        chord = _normalize_chord_symbol(chord)
        if chord in ("", "n", "N.C.", "NC"):
            continue

        if beats <= 0:
            continue

        beats_f = float(beats)
        full_bars = int(beats_f // beats_per_bar)
        rem = beats_f - (full_bars * beats_per_bar)

        for _ in range(full_bars):
            measures.append([chord])

        if rem:
            current_bar.append(chord)
            current_beats += rem
            if current_beats >= beats_per_bar - 1e-9:
                measures.append(current_bar)
                current_bar = []
                current_beats = 0.0

    if current_bar:
        measures.append(current_bar)

    return Score(measures=measures, title=title, key=key, time_signature=time_signature)


def _chord_to_notes(symbol: str, mingus_chords) -> list[int]:
    """Convert chord symbol to MIDI note numbers."""
    if mingus_chords:
        try:
            # Extract root and quality
            root, quality = _split_chord_symbol(symbol)
            chord_notes = mingus_chords.from_shorthand(f"{root}{quality}")
            return [_note_to_midi(n) for n in chord_notes]
        except Exception:
            pass

    # Fallback: basic parsing
    return _basic_chord_to_notes(symbol)


def _split_chord_symbol(symbol: str) -> tuple[str, str]:
    """Split chord symbol into root and quality."""
    if len(symbol) < 1:
        return "C", ""

    if len(symbol) >= 2 and symbol[1] in ('#', 'b'):
        root = symbol[:2]
        quality = symbol[2:]
    else:
        root = symbol[0]
        quality = symbol[1:]

    return root, quality


def _note_to_midi(note_name: str, octave: int = 4) -> int:
    """Convert note name to MIDI number."""
    note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

    if not note_name:
        return 60

    base = note_map.get(note_name[0].upper(), 0)

    if len(note_name) > 1:
        if note_name[1] == '#':
            base += 1
        elif note_name[1] == 'b':
            base -= 1

    return base + (octave + 1) * 12


def _basic_chord_to_notes(symbol: str) -> list[int]:
    """Basic chord parsing without mingus."""
    root, quality = _split_chord_symbol(symbol)
    root_midi = _note_to_midi(root, 3)  # Start at octave 3

    # Default intervals for common chord types
    intervals = {
        '': [0, 4, 7],  # Major triad
        '-': [0, 3, 7],  # Minor
        '-7': [0, 3, 7, 10],  # Minor 7
        '7': [0, 4, 7, 10],  # Dominant 7
        '^7': [0, 4, 7, 11],  # Major 7
        '^': [0, 4, 7],  # Major
        'o': [0, 3, 6],  # Diminished
        'o7': [0, 3, 6, 9],  # Diminished 7
        'h7': [0, 3, 6, 10],  # Half-diminished
        'sus': [0, 5, 7],  # Sus4
        'sus2': [0, 2, 7],  # Sus2
        '+': [0, 4, 8],  # Augmented
        '9': [0, 4, 7, 10, 14],  # Dominant 9
        '-9': [0, 3, 7, 10, 14],  # Minor 9
        '^9': [0, 4, 7, 11, 14],  # Major 9
    }

    # Try to match quality
    chord_intervals = intervals.get(quality, [0, 4, 7])

    return [root_midi + i for i in chord_intervals]


def _get_style_patterns(style: StyleName) -> dict:
    """Get rhythm patterns for a given style."""
    patterns = {
        "swing": {
            "drums": [(0, 42, 80), (1, 42, 60), (2, 42, 80), (3, 42, 60)],  # Hi-hat
            "bass": "walking",
            "piano": "comping",
        },
        "bossa": {
            "drums": [(0, 42, 70), (1.5, 42, 50), (3, 42, 70)],
            "bass": "bossa",
            "piano": "bossa",
        },
        "rock": {
            "drums": [(0, 36, 100), (1, 38, 90), (2, 36, 100), (3, 38, 90)],
            "bass": "root",
            "piano": "block",
        },
        "ballad": {
            "drums": [(0, 42, 50), (2, 42, 50)],
            "bass": "half",
            "piano": "arpeggiate",
        },
        "funk": {
            "drums": [
                (0, 36, 110),
                (0.5, 38, 80),
                (1, 36, 90),
                (1.5, 38, 100),
                (2, 36, 110),
                (2.5, 38, 80),
                (3, 36, 90),
                (3.5, 38, 100),
            ],
            "bass": "syncopated",
            "piano": "stabs",
        },
        "latin": {
            "drums": [
                (0, 36, 90),
                (0.5, 42, 70),
                (1, 42, 70),
                (1.5, 38, 80),
                (2, 36, 90),
                (2.5, 42, 70),
                (3, 38, 80),
                (3.5, 42, 70),
            ],
            "bass": "montuno",
            "piano": "montuno",
        },
        "waltz": {
            "drums": [(0, 36, 100), (1, 42, 60), (2, 42, 60)],
            "bass": "waltz",
            "piano": "waltz",
        },
        "blues": {
            "drums": [(0, 42, 80), (1, 42, 60), (2, 42, 80), (3, 42, 60)],
            "bass": "shuffle",
            "piano": "comping",
        },
    }

    return patterns.get(style, patterns["swing"])


def _add_drum_pattern(
    midi, track: int, start_beat: float, duration: int, pattern: list, volume: float
):
    """Add drum notes for a chord duration."""
    channel = 9  # MIDI drum channel
    for beat_offset, drum_note, velocity in pattern:
        if beat_offset < duration:
            midi.addNote(
                track,
                channel,
                drum_note,
                start_beat + beat_offset,
                0.25,
                int(velocity * volume),
            )


def _add_bass_pattern(
    midi,
    track: int,
    start_beat: float,
    duration: int,
    root: int,
    chord_notes: list,
    pattern_type: str,
    volume: float,
):
    """Add bass notes based on pattern type."""
    channel = 0
    velocity = int(100 * volume)

    # Adjust to bass range (octave 2-3)
    bass_root = (root % 12) + 36

    if pattern_type == "walking":
        # Walking bass: root, 3rd, 5th, approach note
        notes = [bass_root, bass_root + 4, bass_root + 7, bass_root + 11]
        for i, note in enumerate(notes[:duration]):
            midi.addNote(track, channel, note, start_beat + i, 0.9, velocity)

    elif pattern_type == "bossa":
        # Bossa: root on 1, 5th on 3
        midi.addNote(track, channel, bass_root, start_beat, 1.5, velocity)
        if duration > 2:
            midi.addNote(track, channel, bass_root + 7, start_beat + 2, 1.5, velocity)

    elif pattern_type == "root":
        # Rock: root on each beat
        for i in range(duration):
            midi.addNote(track, channel, bass_root, start_beat + i, 0.9, velocity)

    elif pattern_type == "half":
        # Ballad: root as half notes
        midi.addNote(track, channel, bass_root, start_beat, 2, velocity)

    else:
        # Default: whole note
        midi.addNote(track, channel, bass_root, start_beat, duration, velocity)


def _add_piano_pattern(
    midi,
    track: int,
    start_beat: float,
    duration: int,
    chord_notes: list,
    pattern_type: str,
    volume: float,
):
    """Add piano/comping notes based on pattern type."""
    channel = 1  # Channel 1 (bass uses 0, drums use 9)
    velocity = int(90 * volume)

    # Move to mid-range
    notes = [(n % 12) + 60 for n in chord_notes[:4]]

    if pattern_type == "comping":
        # Jazz comping: on 2 and 4
        if duration >= 2:
            for note in notes:
                midi.addNote(track, channel, note, start_beat + 1, 0.5, velocity)
        if duration >= 4:
            for note in notes:
                midi.addNote(track, channel, note, start_beat + 3, 0.5, velocity)

    elif pattern_type == "bossa":
        # Bossa: syncopated
        for note in notes:
            midi.addNote(track, channel, note, start_beat, 0.4, velocity)
        if duration > 1:
            for note in notes:
                midi.addNote(
                    track, channel, note, start_beat + 1.5, 0.4, int(velocity * 0.8)
                )

    elif pattern_type == "block":
        # Rock: on each beat
        for i in range(min(duration, 4)):
            for note in notes:
                midi.addNote(track, channel, note, start_beat + i, 0.9, velocity)

    elif pattern_type == "arpeggiate":
        # Ballad: arpeggiated
        for i, note in enumerate(notes):
            midi.addNote(track, channel, note, start_beat + (i * 0.5), 1.5, velocity)

    else:
        # Default: whole chord on beat 1
        for note in notes:
            midi.addNote(track, channel, note, start_beat, duration * 0.9, velocity)


# =============================================================================
# MIDI Generation - MMA
# =============================================================================


def _generate_via_mma(score: Score, config: AccompanimentConfig) -> Path:
    """Generate MIDI using MMA (Musical MIDI Accompaniment)."""
    # Create MMA file content
    mma_content = _score_to_mma(score, config)

    # Write to temp file
    mma_path = Path(tempfile.mktemp(suffix=".mma"))
    with open(mma_path, 'w') as f:
        f.write(mma_content)

    # Run MMA
    midi_path = mma_path.with_suffix('.mid')

    try:
        result = subprocess.run(
            ['mma', str(mma_path), '-f', str(midi_path)],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"MMA failed: {e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("MMA not found. Install from https://www.mellowood.ca/mma/")

    return midi_path


def _score_to_mma(score: Score, config: AccompanimentConfig) -> str:
    """Convert Score to MMA format."""
    lines = [
        f"// Generated by accompy",
        f"// {score.title}",
        "",
        f"Tempo {config.tempo}",
        f"TimeSig {score.time_signature[0]}/{score.time_signature[1]}",
        f"KeySig {score.key}",
        "",
        f"Groove {_style_to_groove(config.style)}",
        "",
    ]

    # Volume adjustments
    for inst, vol in config.volumes.items():
        if config.instruments.get(inst, False):
            lines.append(f"{inst.capitalize()}Volume {int(vol * 100)}")

    lines.append("")

    # Add measures
    for i, measure in enumerate(score.measures, 1):
        chords = ' '.join(measure) if measure else 'z'  # 'z' = rest
        lines.append(f"{i} {chords}")

    # Repeats
    if config.repeats > 1:
        lines.append("")
        lines.append(f"Repeat {config.repeats}")

    return '\n'.join(lines)


def _style_to_groove(style: StyleName) -> str:
    """Map style name to MMA groove name."""
    groove_map = {
        "swing": "Swing",
        "bossa": "BossaNova",
        "rock": "Rock",
        "ballad": "Ballad",
        "funk": "Funk",
        "latin": "Latin",
        "waltz": "Waltz",
        "blues": "Blues",
    }
    return groove_map.get(style, "Swing")


# =============================================================================
# Audio Rendering
# =============================================================================


def _render_midi_to_audio(
    midi_path: Path, output_path: Path, config: AccompanimentConfig
):
    """Render MIDI to audio using FluidSynth."""
    soundfont = config.soundfont or _default_soundfont_path()

    if soundfont is None:
        raise RuntimeError(
            "No SoundFont found. Download FluidR3_GM.sf2 and place in "
            "~/.fluidsynth/default_sound_font.sf2"
        )

    # Render to WAV first
    wav_path = (
        output_path.with_suffix('.wav') if output_path.suffix != '.wav' else output_path
    )

    # Prefer midi2audio (if installed), otherwise shell out to fluidsynth.
    try:
        from midi2audio import FluidSynth  # type: ignore

        fs = FluidSynth(sound_font=str(soundfont), sample_rate=config.sample_rate)
        fs.midi_to_audio(str(midi_path), str(wav_path))
    except Exception:
        try:
            # FluidSynth 2.x syntax: options must come BEFORE soundfont and MIDI file
            subprocess.run(
                [
                    'fluidsynth',
                    '-ni',  # No interactive shell
                    '-F',
                    str(wav_path),  # Output file
                    '-r',
                    str(config.sample_rate),  # Sample rate
                    str(soundfont),  # Soundfont file
                    str(midi_path),  # MIDI input file
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "FluidSynth not found. Install with: brew install fluidsynth"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"FluidSynth failed: {e.stderr}")

    # Convert to final format if needed
    if output_path.suffix.lower() in ('.mp3', '.flac') and wav_path != output_path:
        _convert_audio(wav_path, output_path)
        wav_path.unlink()  # Clean up temp WAV


def _convert_audio(input_path: Path, output_path: Path):
    """Convert audio between formats using ffmpeg or pydub."""
    try:
        subprocess.run(
            ['ffmpeg', '-y', '-i', str(input_path), str(output_path)],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_wav(str(input_path))
            audio.export(str(output_path), format=output_path.suffix[1:])
        except ImportError:
            raise RuntimeError(
                "Neither ffmpeg nor pydub available for audio conversion. "
                "Install with: brew install ffmpeg OR pip install pydub"
            )


# =============================================================================
# Dependency Checking
# =============================================================================


def _mma_available() -> bool:
    """Check if MMA is available."""
    try:
        result = subprocess.run(['mma', '-v'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _fluidsynth_available() -> bool:
    """Check if FluidSynth is available."""
    try:
        result = subprocess.run(['fluidsynth', '--version'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _default_soundfont_path() -> Optional[Path]:
    """Find the default SoundFont file."""
    candidates = [
        Path.home() / ".fluidsynth" / "default_sound_font.sf2",
        Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
        Path("/usr/share/soundfonts/FluidR3_GM.sf2"),
        Path("/usr/local/share/fluidsynth/FluidR3_GM.sf2"),
        Path("/opt/homebrew/share/soundfonts/FluidR3_GM.sf2"),
        Path("/opt/homebrew/share/soundfonts/default.sf2"),
        Path("/usr/local/share/soundfonts/FluidR3_GM.sf2"),
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def _parse_ireal_url_fallback(url: str) -> Score:
    """Best-effort iReal Pro URL parser (no external dependencies).

    This is intentionally conservative: it extracts a usable chord progression but
    does not attempt to perfectly replicate iReal Pro's full encoding.
    """
    raw = url
    if raw.startswith("irealbook://") or raw.startswith("irealb://"):
        raw = raw.split("://", 1)[1]

    raw = unquote(raw)
    parts = raw.split("=")

    title = parts[0] if len(parts) > 0 and parts[0] else "Untitled"
    composer = parts[1] if len(parts) > 1 else ""
    key = parts[3] if len(parts) > 3 and parts[3] else "C"

    if len(parts) < 6:
        raise ValueError("Invalid iReal Pro URL format")

    chord_data = parts[5]

    # Clean up structural markers
    for marker in ["{", "}", "[", "]", "Z", "*", "Y", "Q", "S", "T"]:
        chord_data = chord_data.replace(marker, " ")

    # Remove section markers like *A, *B, N1, N2
    chord_data = re.sub(r"\*[A-Za-z]", " ", chord_data)
    chord_data = re.sub(r"N\d", " ", chord_data)
    chord_data = re.sub(r"<[^>]*>", " ", chord_data)

    # Split by barlines/whitespace
    tokens = re.split(r"[|\s]+", chord_data)

    chords: list[ChordSpec] = []
    for token in tokens:
        token = token.strip()
        if not token or token in ("n", "x", "r", "%", "p", "s", "l"):
            continue

        match = re.match(r"^([A-G][#b]?)(.*)", token)
        if not match:
            continue

        root = match.group(1)
        suffix = match.group(2)

        # Convert iReal notation to more standard symbols
        suffix = suffix.replace("^", "maj")
        suffix = suffix.replace("-", "m")
        suffix = suffix.replace("h", "m7b5")
        suffix = suffix.replace("o", "dim")
        suffix = suffix.replace("+", "aug")

        # Handle slash chords (ignore bass note)
        if "/" in suffix:
            suffix = suffix.split("/")[0]

        # Handle commas (multiple chords per bar) - take first
        if "," in suffix:
            suffix = suffix.split(",")[0]

        chord = root + suffix
        if chord:
            chords.append((chord, 4))

    score = ensure_score(chords, title=title, key=key)
    score.composer = composer
    return score


def _check_import(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False


# =============================================================================
# CLI Entry Point
# =============================================================================


def _main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate accompaniment audio from chord progressions"
    )
    parser.add_argument(
        'chords', nargs='?', help='Chord progression (e.g., "| C | Am | F | G |")'
    )
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument(
        '-s',
        '--style',
        default='swing',
        choices=['swing', 'bossa', 'rock', 'ballad', 'funk', 'latin', 'waltz', 'blues'],
        help='Musical style',
    )
    parser.add_argument('-t', '--tempo', type=int, default=120, help='Tempo in BPM')
    parser.add_argument(
        '-r', '--repeats', type=int, default=2, help='Number of repeats'
    )
    parser.add_argument(
        '--check-deps', action='store_true', help='Check and print dependency status'
    )

    args = parser.parse_args()

    if args.check_deps:
        print_setup_instructions()
        return

    if not args.chords:
        parser.error("Please provide chord progression or use --check-deps")

    output = generate_accompaniment(
        args.chords,
        style=args.style,
        tempo=args.tempo,
        repeats=args.repeats,
        output_path=args.output,
    )

    print(f"Generated: {output}")


def _check_setup_on_import():
    """
    Verify dependencies on import and warn user if setup is incomplete.

    Set ACCOMPY_SKIP_SETUP_CHECK=1 to disable this check.
    """
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


if __name__ == "__main__":
    _main()
