"""
Audio synthesis backends for accompy.

Provides abstraction over different synthesis engines:
- FluidSynth: Default, uses SoundFonts for realistic instrument sounds
- Pyo: Real-time synthesis (future integration with hum package)

The synthesis backends are used to convert MIDI files to audio.
"""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class SynthesizerBackend(ABC):
    """
    Abstract base for audio synthesis backends.

    Subclasses implement specific synthesis engines (FluidSynth, Pyo, etc.).
    """

    @abstractmethod
    def render_to_file(
        self,
        midi_path: Path,
        output_path: Path,
        *,
        sample_rate: int = 44100,
    ) -> Path:
        """
        Render a MIDI file to an audio file.

        Args:
            midi_path: Path to input MIDI file
            output_path: Path for output audio file
            sample_rate: Audio sample rate in Hz

        Returns:
            Path to the created audio file
        """
        ...

    def render_to_bytes(
        self,
        midi_path: Path,
        *,
        sample_rate: int = 44100,
    ) -> bytes:
        """
        Render a MIDI file to PCM bytes (for streaming).

        Args:
            midi_path: Path to MIDI file
            sample_rate: Audio sample rate

        Returns:
            Raw PCM audio bytes

        Note:
            Default implementation not provided - subclasses should override
            for streaming support.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support render_to_bytes"
        )

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """
        Check if this backend's dependencies are installed.

        Returns:
            True if the backend can be used
        """
        ...


def get_default_backend() -> SynthesizerBackend:
    """
    Get the best available synthesis backend.

    Returns:
        An instance of an available SynthesizerBackend

    Raises:
        RuntimeError: If no synthesis backend is available
    """
    from .fluidsynth import FluidSynthBackend

    if FluidSynthBackend.is_available():
        return FluidSynthBackend()

    raise RuntimeError(
        "No synthesis backend available. Install FluidSynth:\n"
        "  macOS:  brew install fluidsynth\n"
        "  Ubuntu: sudo apt-get install fluidsynth\n"
        "  Windows: Download from https://github.com/FluidSynth/fluidsynth/releases"
    )


__all__ = [
    "SynthesizerBackend",
    "get_default_backend",
]
