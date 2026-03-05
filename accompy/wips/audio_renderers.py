"""
Audio renderers — convert MidiData to AudioData.

Registered converters: MidiData -> AudioData

Backends:
- fluidsynth (via midi2audio): renders MIDI using SoundFont sample banks
- pretty_midi.fluidsynth: built-in FluidSynth integration in pretty_midi
- tonal.midi_to_wav: existing tonal package converter

Also provides end-to-end shortcuts: ChordSequence -> AudioData.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Callable, Optional

import numpy as np

from .types import AudioData, ChordSequence, MidiData, NoteSequence, converter


# ---------------------------------------------------------------------------
# MidiData -> AudioData via midi2audio (FluidSynth CLI wrapper)
# ---------------------------------------------------------------------------


def midi_to_audio_fluidsynth(
    md: MidiData,
    *,
    soundfont: Optional[str] = None,
    sr: int = 44100,
) -> AudioData:
    """Render MIDI to audio using FluidSynth CLI directly.

    Calls the ``fluidsynth`` binary via subprocess for maximum compatibility
    across FluidSynth versions (midi2audio's wrapper breaks on >=2.x).

    Requires:
    - FluidSynth installed (brew install fluidsynth / apt install fluidsynth)
    - A SoundFont file (.sf2)

    >>> # md = MidiData(bytes_=some_midi_bytes)
    >>> # audio = midi_to_audio_fluidsynth(md)
    """
    import shutil
    import subprocess

    if not shutil.which("fluidsynth"):
        raise RuntimeError("fluidsynth binary not found on PATH")

    if not soundfont:
        # Try common default locations
        for sf_path in [
            Path.home() / ".fluidsynth" / "default_sound_font.sf2",
            Path("/usr/share/sounds/sf2/FluidR3_GM.sf2"),
            Path("/usr/share/soundfonts/FluidR3_GM.sf2"),
        ]:
            if sf_path.exists():
                soundfont = str(sf_path)
                break
        if not soundfont:
            raise RuntimeError("No SoundFont found. Set the soundfont parameter.")

    # Write MIDI to temp file
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        f.write(md.to_bytes())
        midi_path = f.name

    wav_path = tempfile.mktemp(suffix=".wav")
    try:
        cmd = [
            "fluidsynth",
            "-F", wav_path, "-r", str(sr),
            "-ni", soundfont, midi_path,
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=60,
        )
        if not Path(wav_path).exists():
            raise RuntimeError(
                f"FluidSynth failed to produce output.\n"
                f"stderr: {result.stderr}\nstdout: {result.stdout}"
            )
        waveform = _read_wav(wav_path)
        return AudioData(waveform=waveform, sr=sr)
    finally:
        Path(midi_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# MidiData -> AudioData via pretty_midi's built-in FluidSynth
# ---------------------------------------------------------------------------


def midi_to_audio_pretty_midi(
    md: MidiData,
    *,
    soundfont: Optional[str] = None,
    sr: int = 44100,
) -> AudioData:
    """Render MIDI to audio using pretty_midi's built-in FluidSynth binding.

    This calls pretty_midi's .fluidsynth() method which uses pyfluidsynth.
    Simpler setup than midi2audio but requires the FluidSynth C library.

    >>> # md = MidiData(pretty_midi_obj=pm)
    >>> # audio = midi_to_audio_pretty_midi(md)
    """
    pm = md.to_pretty_midi()
    if soundfont:
        waveform = pm.fluidsynth(fs=sr, sf2_path=soundfont)
    else:
        waveform = pm.fluidsynth(fs=sr)
    return AudioData(waveform=waveform, sr=sr)


# ---------------------------------------------------------------------------
# MidiData -> AudioData via tonal.midi_to_wav
# ---------------------------------------------------------------------------


def midi_to_audio_tonal(
    md: MidiData,
    *,
    soundfont: Optional[str] = None,
    sr: int = 44100,
) -> AudioData:
    """Render MIDI to audio using tonal.converters.midi_to_wav.

    Uses the tonal package's existing converter which wraps FluidSynth.

    >>> # md = MidiData(bytes_=some_midi_bytes)
    >>> # audio = midi_to_audio_tonal(md)
    """
    from tonal.converters import midi_to_wav

    # Write MIDI to temp file
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        f.write(md.to_bytes())
        midi_path = f.name

    wav_path = tempfile.mktemp(suffix=".wav")
    try:
        kwargs = {}
        if soundfont:
            kwargs["soundfont"] = soundfont
        midi_to_wav(midi_path, wav_path, **kwargs)

        waveform = _read_wav(wav_path)
        return AudioData(waveform=waveform, sr=sr)
    finally:
        Path(midi_path).unlink(missing_ok=True)
        Path(wav_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Helper: read WAV to numpy
# ---------------------------------------------------------------------------


def _read_wav(path: str) -> np.ndarray:
    """Read a WAV file into a numpy float64 array (mono)."""
    import wave

    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)

    if sampwidth == 2:
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    elif sampwidth == 4:
        samples = np.frombuffer(raw, dtype=np.int32).astype(np.float64)
    else:
        samples = np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0

    # Mix to mono if stereo
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    # Normalize to [-1, 1]
    peak = np.max(np.abs(samples))
    if peak > 0:
        samples = samples / peak

    return samples


# ---------------------------------------------------------------------------
# Register MidiData -> AudioData converters
# ---------------------------------------------------------------------------

converter.register(
    MidiData,
    AudioData,
    midi_to_audio_pretty_midi,
    name="pretty_midi",
    is_default=True,
)

converter.register(
    MidiData, AudioData, midi_to_audio_fluidsynth, name="fluidsynth"
)

converter.register(
    MidiData, AudioData, midi_to_audio_tonal, name="tonal"
)


# ---------------------------------------------------------------------------
# End-to-end shortcuts: ChordSequence -> AudioData
# ---------------------------------------------------------------------------


def _make_chordseq_to_audio(
    resolver_name: str,
    midi_gen_name: str,
    audio_renderer_name: str,
) -> Callable[[ChordSequence], AudioData]:
    """Factory for ChordSequence -> AudioData pipelines."""

    def convert_fn(cs: ChordSequence) -> AudioData:
        resolve_fn = converter.get(ChordSequence, NoteSequence, resolver_name)
        midi_fn = converter.get(NoteSequence, MidiData, midi_gen_name)
        audio_fn = converter.get(MidiData, AudioData, audio_renderer_name)
        ns = resolve_fn(cs)
        md = midi_fn(ns)
        return audio_fn(md)

    name = f"{resolver_name}+{midi_gen_name}+{audio_renderer_name}"
    convert_fn.__name__ = name
    return convert_fn


# Register the most useful end-to-end pipelines
converter.register(
    ChordSequence,
    AudioData,
    _make_chordseq_to_audio("pychord", "pretty_midi", "pretty_midi"),
    name="pychord+pretty_midi+pretty_midi",
    is_default=True,
)

converter.register(
    ChordSequence,
    AudioData,
    _make_chordseq_to_audio("tonal", "midiutil", "fluidsynth"),
    name="tonal+midiutil+fluidsynth",
)

converter.register(
    ChordSequence,
    AudioData,
    _make_chordseq_to_audio("pychord", "pretty_midi", "fluidsynth"),
    name="pychord+pretty_midi+fluidsynth",
)
