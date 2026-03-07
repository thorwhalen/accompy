"""
Main accompaniment generation module.

Integrates all components (patterns, chord resolution, MIDI rendering,
synthesis) to provide the main accompy API.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional, Union, Literal

from .base import Score, AccompanimentConfig, ensure_score, BackendType, StyleName
from .patterns import get_pattern_registry
from .chord_resolution import get_chord_resolver
from .renderers.midi import generate_builtin_midi
from .synthesis import get_default_backend


# Default values
DFLT_STYLE: StyleName = "swing"
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

    This is the main entry point for accompy. It generates backing tracks
    with bass, drums, and piano from chord progressions.

    Args:
        chords: Chord progression (string, Score, list of tuples, iReal URL)
        style: Musical style (swing, bossa, rock, ballad, funk, latin, waltz, blues)
        tempo: Tempo in BPM
        repeats: Number of times to repeat the progression
        output_path: Where to save the file (None = temp file)
        output_format: Output format (wav, mp3, flac, midi)
        config: Full configuration object (overrides other params if provided)
        use_mma: If True and MMA available, use MMA backend
        backend: Explicitly select backend ('auto', 'mma', 'builtin')
        autoplay: If True, automatically play the generated audio

    Returns:
        Path to the generated audio/MIDI file

    Example:
        >>> from accompy import generate_accompaniment
        >>> path = generate_accompaniment("| C | Am | F | G |", style="bossa", tempo=140)  # doctest: +SKIP
        >>> print(f"Generated: {path}")  # doctest: +SKIP

    Note:
        Requires FluidSynth and a SoundFont for audio rendering.
        For MIDI-only output, use output_format="midi".
    """
    # Build config
    if config is None:
        config = AccompanimentConfig(style=style, tempo=tempo, repeats=repeats)
    else:
        # If config provided, override with explicit params if given
        if style != DFLT_STYLE:
            config.style = style
        if tempo != DFLT_TEMPO:
            config.tempo = tempo
        if repeats != DFLT_REPEATS:
            config.repeats = repeats

    # Determine output format from path or argument
    if output_path is not None:
        out_path = Path(output_path)
        suffix = out_path.suffix.lstrip(".").lower()
        if output_format is None:
            if suffix in ("wav", "mp3", "flac"):
                output_format = suffix  # type: ignore[assignment]
            elif suffix in ("mid", "midi"):
                output_format = "midi"

    if output_format is not None:
        if output_format == "mid":
            output_format = "midi"
        config.output_format = output_format  # type: ignore[assignment]

    # Ensure Score object
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

    # Normalize file extension
    known_suffixes = {".wav", ".mp3", ".flac", ".mid", ".midi"}
    if output_path.suffix.lower() not in known_suffixes:
        if config.output_format == "midi":
            output_path = output_path.with_suffix(".mid")
        else:
            output_path = output_path.with_suffix(f".{config.output_format}")

    # If MIDI requested, ensure MIDI extension
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

    # Generate MIDI
    if selected_backend == "mma":
        midi_path = _generate_via_mma(score, config)
    else:
        # Use new modular renderer
        pattern_source = config.pattern_source or get_pattern_registry()
        chord_resolver = config.chord_resolver or get_chord_resolver()

        midi_path = generate_builtin_midi(
            score,
            config,
            pattern_source=pattern_source,
            chord_resolver=chord_resolver,
        )

    # MIDI-only output
    if config.output_format == "midi":
        if midi_path != output_path:
            import shutil

            shutil.move(str(midi_path), str(output_path))

        if autoplay:
            raise ValueError(
                "autoplay=True is only supported for audio outputs, not MIDI"
            )
        return output_path

    # Render MIDI to audio
    synth_backend = config.synthesis_backend or get_default_backend()
    synth_backend.render_to_file(midi_path, output_path, sample_rate=config.sample_rate)

    # Clean up temp MIDI file
    if midi_path.exists() and midi_path != output_path:
        midi_path.unlink()

    # Auto-play if requested
    if autoplay:
        play_audio(output_path)

    return output_path


def play_audio(audio_path: Union[str, Path]) -> bool:
    """
    Play an audio file using the system's default audio player.

    Args:
        audio_path: Path to the audio file

    Returns:
        True if playback started successfully, False otherwise

    Example:
        >>> from accompy import play_audio
        >>> play_audio("/path/to/audio.wav")  # doctest: +SKIP
    """
    import platform

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
            # Try common Linux audio players
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
                "No audio player found. Install: paplay, aplay, ffplay, mpg123, or sox",
                UserWarning,
            )
            return False
        elif system == "windows":
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
        >>> 'midiutil' in deps
        True
    """
    from .synthesis.fluidsynth import FluidSynthBackend, find_default_soundfont

    return {
        "mma": _mma_available(),
        "fluidsynth": FluidSynthBackend.is_available(),
        "soundfont": find_default_soundfont() is not None,
        "midiutil": _check_import("midiutil"),
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

    if not deps["midi2audio"]:
        print("midi2audio (optional Python wrapper for FluidSynth):")
        print("  pip install midi2audio\n")


# =============================================================================
# MMA Backend (extracted from original accompy.py)
# =============================================================================


def _generate_via_mma(score: Score, config: AccompanimentConfig) -> Path:
    """Generate MIDI using MMA (Musical MIDI Accompaniment)."""
    # Create MMA file content
    mma_content = _score_to_mma(score, config)

    # Write to temp file
    mma_path = Path(tempfile.mktemp(suffix=".mma"))
    with open(mma_path, "w") as f:
        f.write(mma_content)

    # Run MMA
    midi_path = mma_path.with_suffix(".mid")

    try:
        subprocess.run(
            ["mma", str(mma_path), "-f", str(midi_path)],
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
        chords = " ".join(measure) if measure else "z"  # 'z' = rest
        lines.append(f"{i} {chords}")

    # Repeats
    if config.repeats > 1:
        lines.append("")
        lines.append(f"Repeat {config.repeats}")

    return "\n".join(lines)


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
# Helper Functions
# =============================================================================


def _mma_available() -> bool:
    """Check if MMA is available."""
    try:
        result = subprocess.run(["mma", "-v"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_import(module_name: str) -> bool:
    """Check if a Python module can be imported."""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False
