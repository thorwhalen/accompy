"""
High-quality chord rendering pipeline — from chord charts to AI-enhanced audio.

Collapses the multi-step workflow of rendering MIDI audio and enhancing it via
AI music generation (e.g. Suno) into a single ``render_chords()`` call.

Pipeline::

    chords + params → ChordSequence → MIDI audio (WAV) → AI-enhanced audio (MP3)

Quick start::

    >>> from accompy.rendering import render_chords
    >>> path = render_chords("| Dm7 | G7 | C^7 |", ai_enhance=False)  # doctest: +SKIP

With AI enhancement (requires ``arioso`` and Suno API key)::

    >>> path = render_chords(  # doctest: +SKIP
    ...     "| Dm7 | G7 | C^7 |",
    ...     genre="jazz",
    ...     instruments=["piano", "upright bass", "brushes"],
    ... )

Batch rendering::

    >>> paths = render_chords_batch([  # doctest: +SKIP
    ...     dict(chords="| Dm7 | G7 | C^7 |", genre="jazz"),
    ...     dict(chords="| Dm7 | G7 | C^7 |", genre="lofi chill hop"),
    ... ], bpm=100)
"""

from __future__ import annotations

import hashlib
import tempfile
from collections.abc import MutableMapping
from pathlib import Path
from typing import Callable, Iterable, Union


# ---------------------------------------------------------------------------
# Store helpers
# ---------------------------------------------------------------------------


def _default_store(kind: str) -> MutableMapping:
    """Create a ``dol.Files``-backed store under the accompy artifacts dir."""
    from dol import Files
    from .data_access import get_artifact_dir

    rootdir = str(get_artifact_dir(kind))
    Path(rootdir).mkdir(parents=True, exist_ok=True)
    return Files(rootdir)


def _get_audio_path(store: MutableMapping, key: str) -> str:
    """Get the filesystem path for an artifact in a store.

    Uses ``store._id_of_key`` when available (dol.Files).  Falls back to
    writing the bytes to a temp file.
    """
    if hasattr(store, "_id_of_key"):
        return store._id_of_key(key)
    # Fallback: write to a temp file
    suffix = Path(key).suffix or ".wav"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(store[key])
    tmp.close()
    return tmp.name


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _compute_n_loops(
    one_pass_beats: float,
    bpm: int,
    *,
    n_loops: int | None = None,
    max_seconds: float | None = None,
) -> int:
    """Compute how many times to loop the chord progression.

    Args:
        one_pass_beats: Total beats in a single pass of the progression.
        bpm: Tempo in beats per minute.
        n_loops: Explicit loop count (takes priority).
        max_seconds: Target maximum duration. If neither ``n_loops`` nor
            ``max_seconds`` is given, defaults to 210 seconds (3.5 min).

    Returns:
        Number of loops (minimum 1).

    >>> _compute_n_loops(16, 100, n_loops=5)
    5
    >>> _compute_n_loops(16, 100, max_seconds=100)
    10
    >>> _compute_n_loops(16, 100)
    21
    """
    if n_loops is not None:
        return max(1, n_loops)
    if max_seconds is None:
        max_seconds = 210.0
    one_pass_seconds = one_pass_beats * 60.0 / bpm
    if one_pass_seconds <= 0:
        return 1
    return max(1, int(max_seconds / one_pass_seconds))


def _format_instruments(instruments: list[str]) -> str:
    """Format an instrument list with Oxford comma.

    >>> _format_instruments(["piano"])
    'piano'
    >>> _format_instruments(["piano", "bass"])
    'piano and bass'
    >>> _format_instruments(["piano", "bass", "drums"])
    'piano, bass, and drums'
    """
    if len(instruments) == 0:
        return ""
    if len(instruments) == 1:
        return instruments[0]
    if len(instruments) == 2:
        return f"{instruments[0]} and {instruments[1]}"
    return ", ".join(instruments[:-1]) + f", and {instruments[-1]}"


def _build_prompt(
    prompt_template: str,
    genre: str,
    instruments: list[str],
) -> str:
    """Format the prompt template with genre and instruments.

    >>> _build_prompt("{genre} backing track with {instruments}", "jazz", ["piano", "bass", "drums"])
    'jazz backing track with piano, bass, and drums'
    """
    return prompt_template.format(
        genre=genre,
        instruments=_format_instruments(instruments),
    )


def _make_artifact_key(
    chords_repr: str,
    *,
    bpm: int,
    transpose: int,
    skeleton: str | tuple,
    n_loops: int,
    genre: str = "",
    instruments: list[str] | None = None,
    suffix: str = ".wav",
) -> str:
    """Generate a deterministic, human-readable artifact key.

    >>> k = _make_artifact_key("Dm7|G7|C^7", bpm=100, transpose=0, skeleton="whole_note", n_loops=5)
    >>> k.endswith(".wav")
    True
    >>> "100bpm" in k
    True
    """
    chords_hash = hashlib.sha256(chords_repr.encode()).hexdigest()[:8]
    skel_name = skeleton if isinstance(skeleton, str) else "custom"
    parts = [chords_hash, f"{bpm}bpm", skel_name, f"{n_loops}x"]
    if transpose:
        parts.append(f"t{transpose:+d}")
    if genre:
        safe_genre = genre.replace(" ", "-").replace(",", "")[:30]
        parts.append(f"__{safe_genre}")
    if instruments:
        safe_instr = "-".join(i.replace(" ", "_") for i in instruments)[:40]
        parts.append(safe_instr)
    return "_".join(parts) + suffix


def _ensure_chord_sequence(chords, *, bpm: int = 100):
    """Coerce any supported chord input to a ChordSequence with the given bpm.

    Accepts:
    - ``str``: chord string (``"| C | Am | F | G |"``) or iReal URL
    - ``ChordSequence``: returned with bpm overridden
    - ``Score``: converted via ``to_chord_sequence``
    - ``list[tuple[str, float]]``: chord-duration pairs
    """
    from .converters import ChordSequence
    from .base import Score, ensure_score

    if isinstance(chords, ChordSequence):
        return ChordSequence(
            chords=chords.chords,
            title=chords.title,
            key=chords.key,
            tempo=bpm,
            time_signature=chords.time_signature,
        )
    if isinstance(chords, Score):
        return chords.to_chord_sequence(tempo=bpm)
    if isinstance(chords, str):
        s = chords.strip()
        if s.startswith(("irealbook://", "irealb://")):
            score = Score.from_ireal_url(s)
            return score.to_chord_sequence(tempo=bpm)
        from .pipeline import chords_to_sequence

        return chords_to_sequence(s, tempo=bpm)
    # Try as anything ensure_score can handle (tuples, lists, etc.)
    score = ensure_score(chords)
    return score.to_chord_sequence(tempo=bpm)


# ---------------------------------------------------------------------------
# AI enhancement (Suno via arioso)
# ---------------------------------------------------------------------------


def _suno_enhance(
    audio_path: str,
    prompt: str,
    *,
    suno_mode: str = "cover",
    instrumental: bool = True,
    model: str = "",
    audio_weight: float = 0.99,
    style_weight: float = 0.51,
    weirdness: float = 0.0,
    wait_for_completion: bool = True,
    poll_interval: float = 15.0,
    timeout: float = 600.0,
    **kwargs,
) -> bytes:
    """Enhance audio via Suno (arioso.platforms.sunoapi).

    Returns the audio bytes of the first completed song.
    """
    try:
        from arioso.registry import get_platform
    except ImportError:
        raise ImportError(
            "AI enhancement requires the 'arioso' package. "
            "Install it with: pip install arioso\n"
            "Then set the SUNO_API_KEY environment variable."
        )

    adapter = get_platform("sunoapi")["adapter"]

    common_kwargs = dict(
        audio_source=audio_path,
        style=prompt,
        instrumental=instrumental,
        model=model,
        audio_weight=audio_weight,
        style_weight=style_weight,
        wait_for_completion=wait_for_completion,
        poll_interval=poll_interval,
        timeout=timeout,
    )

    if suno_mode == "cover":
        songs = adapter.upload_cover(weirdness=weirdness, **common_kwargs)
    elif suno_mode == "extend":
        songs = adapter.upload_extend(**common_kwargs)
    else:
        raise ValueError(f"suno_mode must be 'cover' or 'extend', got {suno_mode!r}")

    # Take the first completed song
    for song in songs:
        if song.status == "complete":
            fetched = adapter.fetch_audio(song)
            return fetched.audio.audio_bytes

    raise RuntimeError(
        f"Suno generation completed but no audio was returned. "
        f"Songs: {[s.status for s in songs]}"
    )


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


def render_chords(
    chords,
    *,
    # Rhythm and tempo
    rhythmic_skeleton: str | tuple[float, ...] = "whole_note",
    bpm: int = 100,
    transpose: int = 0,
    # Duration control
    n_loops: int | None = None,
    max_seconds: float | None = None,
    # AI enhancement
    ai_enhance: Union[bool, Callable, None] = True,
    suno_mode: str = "cover",
    prompt_template: str = "{genre} backing track with {instruments}",
    genre: str = "jazz",
    instruments: list[str] | None = None,
    # Suno kwargs (passed through when using default enhancer)
    audio_weight: float = 0.99,
    style_weight: float = 0.51,
    weirdness: float = 0.0,
    model: str = "",
    instrumental: bool = True,
    wait_for_completion: bool = True,
    poll_interval: float = 15.0,
    timeout: float = 600.0,
    # Pipeline step overrides
    chords_to_midi_audio: Callable | None = None,
    audio_to_enhanced_audio: Callable | None = None,
    # Storage (MutableMapping, default=dol.Files-backed)
    midi_store: MutableMapping | None = None,
    midi_audio_store: MutableMapping | None = None,
    enhanced_audio_store: MutableMapping | None = None,
    # Accompy pipeline passthrough
    resolver: str | None = None,
    midi_gen: str | None = None,
    audio_renderer: str | None = None,
    soundfont: str | None = None,
    sr: int = 44100,
) -> str:
    """Render chords to a high-quality audio file, optionally AI-enhanced.

    Args:
        chords: Chord input — string (``"| Dm7 | G7 | C^7 |"``), iReal URL,
            :class:`~accompy.converters.ChordSequence`, :class:`~accompy.base.Score`,
            or list of ``(chord, beats)`` tuples.
        rhythmic_skeleton: Restrike pattern within each measure.
        bpm: Tempo in beats per minute.
        transpose: Semitones to transpose (positive=up, negative=down).
        n_loops: Explicit number of loops. Mutually exclusive with *max_seconds*.
        max_seconds: Target maximum duration; computes loop count automatically.
            Defaults to 210 (3.5 min) when neither *n_loops* nor *max_seconds*
            is given.
        ai_enhance: ``True`` for default Suno enhancement, ``False``/``None``
            to skip, or a callable ``(audio_path, prompt, **kw) → bytes``.
        suno_mode: ``"cover"`` (default, re-generates in style) or ``"extend"``.
        prompt_template: Template with ``{genre}`` and ``{instruments}`` placeholders.
        genre: Genre/style tags for the AI prompt.
        instruments: Instrument list for the AI prompt. Defaults to
            ``["piano", "bass", "drums"]``.
        audio_weight: How much the source audio influences AI output (0–1).
        style_weight: How much the style prompt influences AI output (0–1).
        weirdness: Creative deviation for cover mode (0–1).
        model: Suno model version (e.g. ``"V4_5"``).
        instrumental: If True, generate without vocals.
        wait_for_completion: If True, poll until AI generation is ready.
        poll_interval: Seconds between AI status checks.
        timeout: Max seconds to wait for AI completion.
        chords_to_midi_audio: Override for the MIDI audio rendering step.
            Callable: ``(ChordSequence, **kw) → AudioData``.
        audio_to_enhanced_audio: Override for the AI enhancement step.
            Callable: ``(audio_path, prompt, **kw) → bytes``.
        midi_store: Optional store for MIDI files. ``None`` = don't persist MIDI.
        midi_audio_store: Store for rendered MIDI audio. ``None`` = default
            file store under ``~/.local/share/accompy/artifacts/midi_audio/``.
        enhanced_audio_store: Store for AI-enhanced audio. ``None`` = default
            file store under ``~/.local/share/accompy/artifacts/enhanced_audio/``.
        resolver: Chord resolver backend name.
        midi_gen: MIDI generator backend name.
        audio_renderer: Audio renderer backend name.
        soundfont: Path to a SoundFont file.
        sr: Sample rate for MIDI audio rendering.

    Returns:
        Filesystem path to the final audio file.
    """
    from .pipeline import (
        chords_to_audio,
        _transpose_chord_sequence,
        _repeat_chord_sequence,
    )
    from .rhythmic_skeletons import apply_skeleton

    # --- Defaults ---
    if instruments is None:
        instruments = ["piano", "bass", "drums"]

    # --- 1. Coerce input to ChordSequence ---
    cs = _ensure_chord_sequence(chords, bpm=bpm)

    # --- 2. Transpose ---
    if transpose != 0:
        cs = _transpose_chord_sequence(cs, transpose)

    # --- 3. Compute loop count ---
    effective_n_loops = _compute_n_loops(
        cs.total_beats, bpm, n_loops=n_loops, max_seconds=max_seconds
    )

    # --- 4. Build chords representation for keying ---
    chords_repr = "|".join(sym for sym, _ in cs.chords)

    # --- 5. Initialize stores ---
    if midi_audio_store is None:
        midi_audio_store = _default_store("midi_audio")
    if enhanced_audio_store is None:
        enhanced_audio_store = _default_store("enhanced_audio")

    # --- 6. MIDI audio rendering (with caching) ---
    midi_audio_key = _make_artifact_key(
        chords_repr,
        bpm=bpm,
        transpose=transpose,
        skeleton=rhythmic_skeleton,
        n_loops=effective_n_loops,
    )

    if midi_audio_key not in midi_audio_store:
        # Apply skeleton to one pass, then repeat
        expanded = apply_skeleton(cs, rhythmic_skeleton)
        if effective_n_loops > 1:
            repeated = _repeat_chord_sequence(expanded, effective_n_loops)
        else:
            repeated = expanded

        # Render to audio
        if chords_to_midi_audio is not None:
            audio_data = chords_to_midi_audio(repeated, bpm=bpm)
        else:
            audio_data = chords_to_audio(
                repeated,
                resolver=resolver,
                midi_gen=midi_gen,
                audio_renderer=audio_renderer,
                soundfont=soundfont,
                tempo=bpm,
                sr=sr,
            )

        midi_audio_store[midi_audio_key] = audio_data.to_wav_bytes()

        # Optionally persist MIDI
        if midi_store is not None:
            from .pipeline import chords_to_midi as _chords_to_midi

            midi_key = midi_audio_key.replace(".wav", ".mid")
            midi_data = _chords_to_midi(
                repeated,
                resolver=resolver,
                midi_gen=midi_gen,
                tempo=bpm,
            )
            midi_store[midi_key] = midi_data.to_bytes()

    # --- 7. AI enhancement (with caching) ---
    if not ai_enhance:
        return _get_audio_path(midi_audio_store, midi_audio_key)

    prompt = _build_prompt(prompt_template, genre, instruments)

    enhanced_key = _make_artifact_key(
        chords_repr,
        bpm=bpm,
        transpose=transpose,
        skeleton=rhythmic_skeleton,
        n_loops=effective_n_loops,
        genre=genre,
        instruments=instruments,
        suffix=".mp3",
    )

    if enhanced_key not in enhanced_audio_store:
        midi_audio_path = _get_audio_path(midi_audio_store, midi_audio_key)

        # Determine enhancement function
        if audio_to_enhanced_audio is not None:
            enhance_fn = audio_to_enhanced_audio
        elif callable(ai_enhance):
            enhance_fn = ai_enhance
        else:
            enhance_fn = _suno_enhance

        audio_bytes = enhance_fn(
            midi_audio_path,
            prompt,
            suno_mode=suno_mode,
            instrumental=instrumental,
            model=model,
            audio_weight=audio_weight,
            style_weight=style_weight,
            weirdness=weirdness,
            wait_for_completion=wait_for_completion,
            poll_interval=poll_interval,
            timeout=timeout,
        )

        enhanced_audio_store[enhanced_key] = audio_bytes

    return _get_audio_path(enhanced_audio_store, enhanced_key)


# ---------------------------------------------------------------------------
# Batch rendering
# ---------------------------------------------------------------------------


def render_chords_batch(
    configs: Iterable[dict],
    **shared_kwargs,
) -> list[str]:
    """Run :func:`render_chords` for each config dict.

    Each dict in *configs* is merged with *shared_kwargs* (per-config values
    take priority over shared defaults).

    Args:
        configs: Iterable of dicts, each containing keyword arguments for
            :func:`render_chords`.
        **shared_kwargs: Default arguments applied to every config.

    Returns:
        List of filesystem paths to the final audio files.

    Example::

        >>> from itertools import product
        >>> configs = [
        ...     dict(chords="| Dm7 | G7 | C^7 |", genre=g, bpm=b)
        ...     for g, b in product(["jazz", "lofi"], [100, 120])
        ... ]
        >>> paths = render_chords_batch(configs, ai_enhance=False)  # doctest: +SKIP
    """
    results = []
    for i, config in enumerate(configs):
        merged = {**shared_kwargs, **config}
        chords = merged.pop("chords", None)
        if chords is None:
            raise ValueError(
                f"Config at index {i} is missing the required 'chords' key."
            )
        try:
            path = render_chords(chords, **merged)
            results.append(path)
        except Exception as e:
            print(f"  FAILED config {i}: {e}")
            results.append("")
    return results
