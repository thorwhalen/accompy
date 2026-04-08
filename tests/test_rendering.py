"""Tests for accompy.rendering — chord rendering pipeline."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from accompy.rendering import (
    _build_prompt,
    _compute_n_loops,
    _ensure_chord_sequence,
    _format_instruments,
    _make_artifact_key,
    _get_audio_path,
    _default_store,
    render_chords,
    render_chords_batch,
)
from accompy.converters import ChordSequence


# ---------------------------------------------------------------------------
# _compute_n_loops
# ---------------------------------------------------------------------------


class TestComputeNLoops:
    def test_explicit_n_loops(self):
        assert _compute_n_loops(16, 100, n_loops=5) == 5

    def test_explicit_n_loops_minimum_one(self):
        assert _compute_n_loops(16, 100, n_loops=0) == 1

    def test_max_seconds(self):
        # 16 beats at 100 bpm = 9.6s per pass → 100/9.6 = 10.4 → 10
        assert _compute_n_loops(16, 100, max_seconds=100) == 10

    def test_default_max_seconds(self):
        # 16 beats at 100 bpm = 9.6s per pass → 210/9.6 = 21.875 → 21
        assert _compute_n_loops(16, 100) == 21

    def test_minimum_one_loop(self):
        # max_seconds very small, but minimum is 1
        assert _compute_n_loops(16, 100, max_seconds=1) == 1

    def test_short_progression(self):
        # 4 beats at 120 bpm = 2s per pass → 210/2 = 105
        assert _compute_n_loops(4, 120) == 105

    def test_zero_beats(self):
        assert _compute_n_loops(0, 100) == 1


# ---------------------------------------------------------------------------
# _format_instruments / _build_prompt
# ---------------------------------------------------------------------------


class TestFormatInstruments:
    def test_empty(self):
        assert _format_instruments([]) == ""

    def test_single(self):
        assert _format_instruments(["piano"]) == "piano"

    def test_two(self):
        assert _format_instruments(["piano", "bass"]) == "piano and bass"

    def test_three(self):
        assert (
            _format_instruments(["piano", "bass", "drums"])
            == "piano, bass, and drums"
        )

    def test_four(self):
        assert (
            _format_instruments(["piano", "bass", "drums", "guitar"])
            == "piano, bass, drums, and guitar"
        )


class TestBuildPrompt:
    def test_default_template(self):
        result = _build_prompt(
            "{genre} backing track with {instruments}",
            "jazz",
            ["piano", "bass", "drums"],
        )
        assert result == "jazz backing track with piano, bass, and drums"

    def test_custom_template(self):
        result = _build_prompt(
            "A {genre} song featuring {instruments}",
            "funk",
            ["guitar", "bass"],
        )
        assert result == "A funk song featuring guitar and bass"


# ---------------------------------------------------------------------------
# _make_artifact_key
# ---------------------------------------------------------------------------


class TestMakeArtifactKey:
    def test_deterministic(self):
        k1 = _make_artifact_key(
            "Dm7|G7", bpm=100, transpose=0, skeleton="whole_note", n_loops=5
        )
        k2 = _make_artifact_key(
            "Dm7|G7", bpm=100, transpose=0, skeleton="whole_note", n_loops=5
        )
        assert k1 == k2

    def test_different_bpm(self):
        k1 = _make_artifact_key(
            "C|Am", bpm=100, transpose=0, skeleton="whole_note", n_loops=1
        )
        k2 = _make_artifact_key(
            "C|Am", bpm=120, transpose=0, skeleton="whole_note", n_loops=1
        )
        assert k1 != k2

    def test_suffix(self):
        k = _make_artifact_key(
            "C|Am", bpm=100, transpose=0, skeleton="whole_note", n_loops=1
        )
        assert k.endswith(".wav")

    def test_mp3_suffix(self):
        k = _make_artifact_key(
            "C|Am",
            bpm=100,
            transpose=0,
            skeleton="whole_note",
            n_loops=1,
            genre="jazz",
            suffix=".mp3",
        )
        assert k.endswith(".mp3")

    def test_contains_bpm(self):
        k = _make_artifact_key(
            "C|Am", bpm=100, transpose=0, skeleton="whole_note", n_loops=1
        )
        assert "100bpm" in k

    def test_transpose_in_key(self):
        k = _make_artifact_key(
            "C|Am", bpm=100, transpose=5, skeleton="whole_note", n_loops=1
        )
        assert "t+5" in k

    def test_filesystem_safe(self):
        k = _make_artifact_key(
            "C#m7|Gb7", bpm=100, transpose=-3, skeleton="tresillo", n_loops=2,
            genre="lofi chill hop", instruments=["upright bass", "drums"],
        )
        # No characters that would break a filename
        assert "/" not in k
        assert "\\" not in k
        assert ":" not in k


# ---------------------------------------------------------------------------
# _ensure_chord_sequence
# ---------------------------------------------------------------------------


class TestEnsureChordSequence:
    def test_from_string(self):
        cs = _ensure_chord_sequence("| C | Am | F | G |", bpm=120)
        assert isinstance(cs, ChordSequence)
        assert cs.tempo == 120
        assert len(cs) >= 4

    def test_from_chord_sequence(self):
        original = ChordSequence([("Dm7", 4.0), ("G7", 4.0)], tempo=80)
        cs = _ensure_chord_sequence(original, bpm=140)
        assert cs.tempo == 140
        assert cs.chords == original.chords

    def test_from_score(self):
        from accompy.base import Score

        score = Score.from_string("| Dm7 | G7 | C^7 |")
        cs = _ensure_chord_sequence(score, bpm=160)
        assert isinstance(cs, ChordSequence)
        assert cs.tempo == 160

    def test_from_tuples(self):
        cs = _ensure_chord_sequence(
            [("C", 4.0), ("Am", 4.0), ("F", 4.0)], bpm=100
        )
        assert isinstance(cs, ChordSequence)


# ---------------------------------------------------------------------------
# _get_audio_path
# ---------------------------------------------------------------------------


class TestGetAudioPath:
    def test_with_dol_files(self):
        from dol import Files

        with tempfile.TemporaryDirectory() as d:
            store = Files(d)
            store["test.wav"] = b"audio data"
            path = _get_audio_path(store, "test.wav")
            assert path.endswith("test.wav")
            assert Path(path).exists()

    def test_with_plain_dict(self):
        store = {"test.wav": b"audio data"}
        path = _get_audio_path(store, "test.wav")
        assert Path(path).exists()
        assert Path(path).read_bytes() == b"audio data"


# ---------------------------------------------------------------------------
# _default_store
# ---------------------------------------------------------------------------


class TestDefaultStore:
    def test_creates_store(self):
        store = _default_store("test_rendering")
        assert hasattr(store, "__getitem__")
        assert hasattr(store, "__setitem__")

    def test_write_and_read(self):
        store = _default_store("test_rendering")
        key = "_test_artifact.wav"
        try:
            store[key] = b"test data"
            assert store[key] == b"test data"
            assert key in store
        finally:
            if key in store:
                del store[key]


# ---------------------------------------------------------------------------
# Helpers for mocking audio rendering
# ---------------------------------------------------------------------------


def _fake_chords_to_midi_audio(cs, *, bpm=120, **kwargs):
    """Return a minimal AudioData without needing FluidSynth."""
    import numpy as np
    from accompy.converters import AudioData

    sr = 44100
    duration = cs.total_beats * 60.0 / bpm
    samples = int(sr * duration)
    # Generate a simple sine wave so the WAV bytes are valid
    t = np.linspace(0, duration, samples, dtype=np.float32)
    waveform = 0.5 * np.sin(2 * np.pi * 440 * t)
    return AudioData(waveform=waveform, sr=sr)


# ---------------------------------------------------------------------------
# render_chords (without AI)
# ---------------------------------------------------------------------------


class TestRenderChordsNoAI:
    def test_basic(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            path = render_chords(
                "| C | Am | F | G |",
                ai_enhance=False,
                bpm=120,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0

    def test_with_skeleton(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            path = render_chords(
                "| C | Am | F | G |",
                ai_enhance=False,
                rhythmic_skeleton="half_notes",
                bpm=120,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert Path(path).exists()

    def test_with_transpose(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            path = render_chords(
                "| C | Am | F | G |",
                ai_enhance=False,
                transpose=5,
                bpm=120,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert Path(path).exists()

    def test_caches_result(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            kwargs = dict(
                ai_enhance=False,
                bpm=120,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            path1 = render_chords("| C | Am |", **kwargs)
            keys_before = list(store)
            path2 = render_chords("| C | Am |", **kwargs)
            keys_after = list(store)
            assert path1 == path2
            assert keys_before == keys_after

    def test_persists_midi(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            from dol import Files

            audio_store = Files(d1)
            midi_store = Files(d2)
            render_chords(
                "| C | Am |",
                ai_enhance=False,
                bpm=120,
                n_loops=1,
                midi_audio_store=audio_store,
                midi_store=midi_store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            midi_keys = list(midi_store)
            assert len(midi_keys) == 1
            assert midi_keys[0].endswith(".mid")
            # Verify it's valid MIDI (starts with MThd)
            assert midi_store[midi_keys[0]][:4] == b"MThd"


# ---------------------------------------------------------------------------
# render_chords (with mocked AI)
# ---------------------------------------------------------------------------


class TestRenderChordsWithAI:
    def test_custom_enhance_callable(self):
        fake_audio = b"fake enhanced mp3 bytes"

        def fake_enhance(audio_path, prompt, **kwargs):
            assert Path(audio_path).exists()
            assert "jazz" in prompt
            return fake_audio

        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            from dol import Files

            path = render_chords(
                "| C | Am |",
                ai_enhance=fake_enhance,
                bpm=120,
                n_loops=1,
                midi_audio_store=Files(d1),
                enhanced_audio_store=Files(d2),
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert Path(path).exists()
            assert Path(path).read_bytes() == fake_audio

    def test_arioso_not_installed(self):
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            from dol import Files

            with patch.dict("sys.modules", {"arioso": None, "arioso.registry": None}):
                with pytest.raises(ImportError, match="arioso"):
                    render_chords(
                        "| C | Am |",
                        ai_enhance=True,
                        bpm=120,
                        n_loops=1,
                        midi_audio_store=Files(d1),
                        enhanced_audio_store=Files(d2),
                        chords_to_midi_audio=_fake_chords_to_midi_audio,
                    )


# ---------------------------------------------------------------------------
# render_chords_batch
# ---------------------------------------------------------------------------


class TestRenderChordsBatch:
    def test_basic(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            configs = [
                dict(chords="| C | Am |"),
                dict(chords="| Dm7 | G7 |"),
            ]
            paths = render_chords_batch(
                configs,
                ai_enhance=False,
                bpm=120,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert len(paths) == 2
            assert all(Path(p).exists() for p in paths)

    def test_shared_kwargs_overridden(self):
        with tempfile.TemporaryDirectory() as d:
            from dol import Files

            store = Files(d)
            configs = [
                dict(chords="| C | Am |", bpm=100),
                dict(chords="| C | Am |", bpm=120),
            ]
            paths = render_chords_batch(
                configs,
                ai_enhance=False,
                bpm=80,
                n_loops=1,
                midi_audio_store=store,
                chords_to_midi_audio=_fake_chords_to_midi_audio,
            )
            assert len(paths) == 2
            assert paths[0] != paths[1]

    def test_missing_chords_raises(self):
        with pytest.raises(ValueError, match="missing.*chords"):
            render_chords_batch([dict(bpm=100)], ai_enhance=False)
