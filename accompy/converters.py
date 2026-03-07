"""
Core types for the chord-to-audio pipeline.

Defines the data types that flow through the pipeline, plus a converter
registry that maps (source_type, target_type) pairs to converter functions.

The key types form a DAG::

    ChordSheet --> ChordSequence --> NoteSequence --> MidiData --> AudioData

    (Plus shortcut converters that skip intermediate steps.)

Usage::

    >>> from accompy.wips.types import converter, ChordSequence, MidiData
    >>> # Get a specific converter
    >>> to_midi = converter[ChordSequence, MidiData]
    >>> # Or convert in one call
    >>> midi = convert(chord_seq, MidiData)  # doctest: +SKIP
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    NewType,
    Sequence,
    TypeVar,
    Union,
)

import numpy as np

# ---------------------------------------------------------------------------
# Core pipeline types
# ---------------------------------------------------------------------------

# A chord sheet is raw text in some notation format (ChordPro, iReal URL, plain)
ChordSheet = NewType("ChordSheet", str)

# A chord event: (chord_symbol, duration_in_beats)
ChordEvent = tuple[str, float]


# An ordered sequence of chord events with optional metadata
@dataclass
class ChordSequence:
    """Ordered sequence of (chord_symbol, duration_beats) pairs with metadata.

    This is the canonical internal representation of a chord progression.

    >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0), ("Cmaj7", 8.0)])
    >>> len(cs)
    3
    >>> cs[0]
    ('Dm7', 4.0)
    >>> cs.total_beats
    16.0
    """

    chords: list[ChordEvent]
    title: str = ""
    key: str = "C"
    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)

    def __len__(self) -> int:
        return len(self.chords)

    def __getitem__(self, idx):
        return self.chords[idx]

    def __iter__(self):
        return iter(self.chords)

    @property
    def total_beats(self) -> float:
        return sum(dur for _, dur in self.chords)

    @property
    def symbols(self) -> list[str]:
        """Just the chord symbols, without durations."""
        return [sym for sym, _ in self.chords]

    @property
    def durations(self) -> list[float]:
        """Just the durations, without symbols."""
        return [dur for _, dur in self.chords]

    def to_score(self):
        """Convert to an accompy Score for pattern-based accompaniment.

        Example:
            >>> cs = ChordSequence([("Dm7", 4.0), ("G7", 4.0)])
            >>> score = cs.to_score()
            >>> len(score)
            2
        """
        from .base import ensure_score

        return ensure_score(
            self.chords,
            title=self.title or "Untitled",
            key=self.key,
            time_signature=self.time_signature,
        )


# A note event: (list_of_midi_notes, duration_in_beats)
NoteEvent = tuple[list[int], float]


@dataclass
class NoteSequence:
    """Ordered sequence of (midi_notes, duration_beats) with metadata.

    Represents resolved chords — chord symbols have been converted to
    concrete MIDI note numbers.

    >>> ns = NoteSequence([([60, 64, 67], 4.0), ([62, 65, 69], 4.0)])
    >>> ns[0]
    ([60, 64, 67], 4.0)
    """

    notes: list[NoteEvent]
    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)

    def __len__(self) -> int:
        return len(self.notes)

    def __getitem__(self, idx):
        return self.notes[idx]

    def __iter__(self):
        return iter(self.notes)

    @property
    def total_beats(self) -> float:
        return sum(dur for _, dur in self.notes)


@dataclass
class MidiData:
    """Container for MIDI data — either as bytes or as a pretty_midi object.

    Wraps MIDI content so converters have a uniform interface regardless
    of which MIDI library produced the data.

    >>> import io
    >>> md = MidiData(bytes_=b'MThd...', tempo=120)
    >>> md.has_bytes
    True
    """

    bytes_: bytes | None = None
    pretty_midi_obj: Any = None  # pretty_midi.PrettyMIDI, lazy import
    tempo: int = 120
    time_signature: tuple[int, int] = (4, 4)

    @property
    def has_bytes(self) -> bool:
        return self.bytes_ is not None

    @property
    def has_pretty_midi(self) -> bool:
        return self.pretty_midi_obj is not None

    def to_bytes(self) -> bytes:
        """Get MIDI as bytes, converting from pretty_midi if needed."""
        if self.bytes_ is not None:
            return self.bytes_
        if self.pretty_midi_obj is not None:
            import io

            buf = io.BytesIO()
            self.pretty_midi_obj.write(buf)
            return buf.getvalue()
        raise ValueError("MidiData has no content")

    def to_pretty_midi(self):
        """Get as pretty_midi.PrettyMIDI, converting from bytes if needed."""
        if self.pretty_midi_obj is not None:
            return self.pretty_midi_obj
        if self.bytes_ is not None:
            import io
            import pretty_midi

            return pretty_midi.PrettyMIDI(io.BytesIO(self.bytes_))
        raise ValueError("MidiData has no content")

    def write(self, path: str) -> str:
        """Write MIDI to a file. Returns the path."""
        with open(path, "wb") as f:
            f.write(self.to_bytes())
        return path


@dataclass
class AudioData:
    """Container for audio data — numpy array + sample rate.

    >>> import numpy as np
    >>> ad = AudioData(waveform=np.zeros(44100), sr=44100)
    >>> ad.duration_seconds
    1.0
    """

    waveform: np.ndarray
    sr: int = 44100

    @property
    def duration_seconds(self) -> float:
        return len(self.waveform) / self.sr

    def to_wav_bytes(self) -> bytes:
        """Convert to WAV file bytes."""
        import io
        import wave

        buf = io.BytesIO()
        # Normalize to int16
        peak = np.max(np.abs(self.waveform))
        if peak > 0:
            normalized = (self.waveform / peak * 32767).astype(np.int16)
        else:
            normalized = np.zeros(len(self.waveform), dtype=np.int16)

        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sr)
            wf.writeframes(normalized.tobytes())
        return buf.getvalue()

    def write(self, path: str) -> str:
        """Write audio to a WAV file. Returns the path."""
        wav_bytes = self.to_wav_bytes()
        with open(path, "wb") as f:
            f.write(wav_bytes)
        return path


# ---------------------------------------------------------------------------
# Converter Registry
# ---------------------------------------------------------------------------

# Type variables for generic converter signatures
S = TypeVar("S")
T = TypeVar("T")

# A converter is a callable: source -> target
Converter = Callable  # Callable[[S], T]


class ConverterRegistry:
    """Registry mapping (source_type, target_type) to named converter functions.

    Supports multiple converters for the same type pair, distinguished by name.
    The first registered converter becomes the default.

    >>> reg = ConverterRegistry()
    >>> reg.register(str, int, int, name='builtin')
    >>> reg[str, int]('42')
    42
    >>> reg.list_converters(str, int)
    ['builtin']
    """

    def __init__(self):
        # {(source_type, target_type): {name: converter_func}}
        self._converters: dict[tuple[type, type], dict[str, Converter]] = {}
        # {(source_type, target_type): default_name}
        self._defaults: dict[tuple[type, type], str] = {}

    def register(
        self,
        source_type: type,
        target_type: type,
        func: Converter,
        *,
        name: str = "",
        is_default: bool = False,
    ) -> None:
        """Register a converter function.

        Args:
            source_type: The input type
            target_type: The output type
            func: The converter function (source -> target)
            name: Name for this converter (defaults to func.__name__)
            is_default: If True, make this the default converter for this pair
        """
        name = name or getattr(func, "__name__", "unnamed")
        key = (source_type, target_type)

        if key not in self._converters:
            self._converters[key] = {}
            # First registered is default
            self._defaults[key] = name

        self._converters[key][name] = func

        if is_default:
            self._defaults[key] = name

    def __getitem__(self, key: tuple[type, type]) -> Converter:
        """Get the default converter for a (source, target) pair.

        >>> reg = ConverterRegistry()
        >>> reg.register(str, int, int, name='builtin')
        >>> reg[str, int]('42')
        42
        """
        source_type, target_type = key
        pair_key = (source_type, target_type)

        if pair_key not in self._converters:
            raise KeyError(
                f"No converter registered for {source_type.__name__} -> "
                f"{target_type.__name__}"
            )

        default_name = self._defaults[pair_key]
        return self._converters[pair_key][default_name]

    def get(
        self, source_type: type, target_type: type, name: str | None = None
    ) -> Converter:
        """Get a specific named converter, or the default if name is None."""
        key = (source_type, target_type)
        if key not in self._converters:
            raise KeyError(
                f"No converter for {source_type.__name__} -> {target_type.__name__}"
            )
        if name is None:
            name = self._defaults[key]
        if name not in self._converters[key]:
            available = list(self._converters[key].keys())
            raise KeyError(
                f"No converter named '{name}' for "
                f"{source_type.__name__} -> {target_type.__name__}. "
                f"Available: {available}"
            )
        return self._converters[key][name]

    def list_converters(self, source_type: type, target_type: type) -> list[str]:
        """List available converter names for a type pair."""
        key = (source_type, target_type)
        if key not in self._converters:
            return []
        return list(self._converters[key].keys())

    def list_pairs(self) -> list[tuple[str, str]]:
        """List all registered (source, target) type name pairs."""
        return [(s.__name__, t.__name__) for s, t in self._converters.keys()]

    def set_default(self, source_type: type, target_type: type, name: str) -> None:
        """Change the default converter for a type pair."""
        key = (source_type, target_type)
        if key not in self._converters or name not in self._converters[key]:
            raise KeyError(f"No converter named '{name}' for this pair")
        self._defaults[key] = name


# Global converter registry
converter = ConverterRegistry()


def convert(source: Any, target_type: type, *, via: str | None = None) -> Any:
    """Convert source to target_type using the registered converter.

    Args:
        source: The source data
        target_type: The desired output type
        via: Optional converter name (uses default if None)

    Returns:
        Converted data of target_type

    Example::

        >>> # After converters are registered:
        >>> # audio = convert(chord_seq, AudioData)
    """
    source_type = type(source)
    func = converter.get(source_type, target_type, via)
    return func(source)
