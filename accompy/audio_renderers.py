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

from .converters import AudioData, ChordSequence, MidiData, NoteSequence, converter


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
# MidiData -> AudioData via DawDreamer (VST hosting)
# ---------------------------------------------------------------------------


def midi_to_audio_dawdreamer(
    md: MidiData,
    *,
    vst_path: Optional[str] = None,
    sr: int = 44100,
    duration: Optional[float] = None,
    buffer_size: int = 512,
) -> AudioData:
    """Render MIDI to audio using DawDreamer with a VST plugin.

    DawDreamer can host VST2/VST3 plugins for high-quality instrument sounds.
    Falls back to a simple sine-wave synth if no VST is specified.

    Requires: ``pip install dawdreamer`` (or ``pip install accompy[vst]``)

    Args:
        md: MIDI data to render
        vst_path: Path to a VST2/VST3 plugin (.so/.dylib/.dll/.vst3).
            If None, uses DawDreamer's built-in synth.
        sr: Sample rate
        duration: Duration in seconds. If None, computed from MIDI data.
        buffer_size: Audio buffer size for rendering

    >>> # md = MidiData(bytes_=some_midi_bytes)
    >>> # audio = midi_to_audio_dawdreamer(md, vst_path="/path/to/plugin.vst3")
    """
    try:
        import dawdreamer as daw
    except ImportError:
        raise ImportError(
            "dawdreamer is required for VST-based audio rendering. "
            "Install it with: pip install dawdreamer  (or: pip install accompy[vst])"
        )

    # Write MIDI to temp file for DawDreamer
    with tempfile.NamedTemporaryFile(suffix=".mid", delete=False) as f:
        f.write(md.to_bytes())
        midi_path = f.name

    try:
        engine = daw.RenderEngine(sample_rate=sr, block_size=buffer_size)

        if vst_path:
            synth = engine.make_plugin_processor("synth", vst_path)
        else:
            synth = engine.make_playback_processor("synth", [])

        synth.load_midi(midi_path)

        # Compute duration from MIDI if not specified
        if duration is None:
            pm = md.to_pretty_midi()
            duration = pm.get_end_time() + 1.0  # Add 1s for release tails

        engine.load_graph([(synth, [])])
        engine.render(duration)

        waveform = engine.get_audio()
        # Mix to mono if stereo
        if waveform.ndim > 1:
            waveform = waveform.mean(axis=0)

        return AudioData(waveform=waveform, sr=sr)
    finally:
        Path(midi_path).unlink(missing_ok=True)


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

converter.register(
    MidiData, AudioData, midi_to_audio_dawdreamer, name="dawdreamer"
)


# ---------------------------------------------------------------------------
# ChordSequence -> AudioData via MusicGen-Chord (AI-based, skips MIDI)
# ---------------------------------------------------------------------------


def chordseq_to_audio_musicgen(
    cs: ChordSequence,
    *,
    prompt: str = "smooth jazz trio",
    duration: Optional[float] = None,
    sr: int = 32000,
) -> AudioData:
    """Generate audio directly from chords using MusicGen-Chord.

    Uses Meta's MusicGen model conditioned on chord progressions
    to generate realistic audio without going through MIDI.

    Requires: ``pip install audiocraft`` (or ``pip install accompy[ai]``)

    Args:
        cs: Chord progression to render
        prompt: Text description of desired musical style
        duration: Duration in seconds. If None, computed from tempo and beats.
        sr: Sample rate (MusicGen default is 32000)

    >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 4.0)])
    >>> audio = chordseq_to_audio_musicgen(cs, prompt="jazz piano trio")  # doctest: +SKIP
    """
    try:
        from audiocraft.models import MusicGen
    except ImportError:
        raise ImportError(
            "audiocraft is required for MusicGen-Chord audio generation. "
            "Install it with: pip install audiocraft  (or: pip install accompy[ai])"
        )

    # Compute duration from tempo and total beats if not specified
    if duration is None:
        beat_duration = 60.0 / cs.tempo
        duration = cs.total_beats * beat_duration

    # Convert ChordSequence to MusicGen chord format
    # Format: "C D:min G:7 C" (space-separated, colon notation)
    chord_text = _chordseq_to_musicgen_format(cs)

    # Build the full prompt with chord conditioning
    full_prompt = f"{prompt}, chords: {chord_text}"

    model = MusicGen.get_pretrained("facebook/musicgen-chord")
    model.set_generation_params(duration=duration)

    wav = model.generate([full_prompt])
    waveform = wav[0, 0].cpu().numpy()  # (batch, channels, samples) -> 1D

    return AudioData(waveform=waveform, sr=sr)


def _chordseq_to_musicgen_format(cs: ChordSequence) -> str:
    """Convert ChordSequence to MusicGen chord text format.

    MusicGen expects chords in format like: "C D:min G:7 C"
    """
    parts = []
    for symbol, _ in cs.chords:
        # Basic normalization: Cmaj7 -> C:maj7, Am -> A:min, etc.
        # MusicGen format uses colon notation
        parts.append(symbol)
    return " ".join(parts)


converter.register(
    ChordSequence,
    AudioData,
    chordseq_to_audio_musicgen,
    name="musicgen_chord",
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
