"""
FluidSynth synthesis backend.

Uses FluidSynth with SoundFonts to render MIDI to high-quality audio.
FluidSynth is the default and most widely-supported backend for accompy.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from . import SynthesizerBackend


class FluidSynthBackend(SynthesizerBackend):
    """
    FluidSynth-based synthesis.

    Uses SoundFont files (.sf2) to render MIDI with realistic instrument sounds.
    Supports both Python wrapper (midi2audio) and command-line FluidSynth.

    Example:
        >>> backend = FluidSynthBackend()  # doctest: +SKIP
        >>> backend.render_to_file(midi_path, output_path)  # doctest: +SKIP
    """

    def __init__(self, soundfont_path: Optional[Path] = None):
        """
        Initialize FluidSynth backend.

        Args:
            soundfont_path: Path to SoundFont file. If None, searches standard locations.
        """
        self.soundfont_path = soundfont_path or find_default_soundfont()
        if self.soundfont_path is None:
            raise RuntimeError(
                "No SoundFont found. Download FluidR3_GM.sf2 from:\n"
                "  https://member.keymusician.com/Member/FluidR3_GM/index.html\n"
                "Place in: ~/.fluidsynth/default_sound_font.sf2"
            )

    def render_to_file(
        self,
        midi_path: Path,
        output_path: Path,
        *,
        sample_rate: int = 44100,
    ) -> Path:
        """
        Render MIDI file to audio using FluidSynth.

        Tries Python wrapper (midi2audio) first, then falls back to command-line FluidSynth.

        Args:
            midi_path: Input MIDI file
            output_path: Output audio file (.wav, .mp3, .flac)
            sample_rate: Sample rate in Hz

        Returns:
            Path to created audio file
        """
        # Render to WAV first
        wav_path = (
            output_path.with_suffix(".wav")
            if output_path.suffix != ".wav"
            else output_path
        )

        # Use command-line FluidSynth directly (midi2audio has argument
        # ordering issues with FluidSynth 2.x).
        try:
            # FluidSynth 2.x syntax: options must come BEFORE soundfont and MIDI file
            subprocess.run(
                [
                    "fluidsynth",
                    "-ni",  # No interactive shell
                    "-F",
                    str(wav_path),  # Output file
                    "-r",
                    str(sample_rate),  # Sample rate
                    str(self.soundfont_path),  # SoundFont file
                    str(midi_path),  # MIDI input file
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError:
            raise RuntimeError(
                "FluidSynth not found. Install with:\n"
                "  macOS:  brew install fluidsynth\n"
                "  Ubuntu: sudo apt-get install fluidsynth"
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"FluidSynth failed: {(e.stderr or b'').decode()}"
            )

        # Convert to final format if needed
        if output_path.suffix.lower() in (".mp3", ".flac") and wav_path != output_path:
            convert_audio(wav_path, output_path)
            wav_path.unlink()  # Clean up temp WAV

        return output_path

    @classmethod
    def is_available(cls) -> bool:
        """Check if FluidSynth is available."""
        try:
            result = subprocess.run(
                ["fluidsynth", "--version"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False


def find_default_soundfont() -> Optional[Path]:
    """
    Find the default SoundFont file in standard locations.

    Returns:
        Path to SoundFont file, or None if not found
    """
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


def convert_audio(input_path: Path, output_path: Path) -> None:
    """
    Convert audio between formats using ffmpeg or pydub.

    Args:
        input_path: Input audio file
        output_path: Output audio file

    Raises:
        RuntimeError: If neither ffmpeg nor pydub is available
    """
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(input_path), str(output_path)],
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
                "Neither ffmpeg nor pydub available for audio conversion.\n"
                "Install with: brew install ffmpeg OR pip install pydub"
            )
