"""Tests for the data_access module (user data folder management).

XDG resolution and seed-on-missing primitives are tested in config2py.
These tests verify accompy's integration: that seed data ships correctly,
convenience loaders work, and main.py uses resources properly.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from accompy.data_access import (
    get_app_folder,
    get_artifact_dir,
    get_config,
    get_resource,
    load_resource_json,
    load_resource_lines,
    load_resource_text,
)


# =============================================================================
# Bundled seed data integrity
# =============================================================================


class TestSeedData:
    """Verify that accompy's _seed_data files are readable and well-formed."""

    def test_short_styles_seed(self):
        from config2py import ensure_seeded
        import tempfile

        target = Path(tempfile.mktemp(suffix=".txt"))
        try:
            ensure_seeded(target, "accompy", "resources", "short_styles.txt")
            lines = [l.strip() for l in target.read_text().splitlines() if l.strip()]
            assert len(lines) > 30
            assert "jazz club late night" in lines
        finally:
            target.unlink(missing_ok=True)

    def test_groove_map_seed(self):
        from config2py import ensure_seeded
        import tempfile

        target = Path(tempfile.mktemp(suffix=".json"))
        try:
            ensure_seeded(target, "accompy", "resources", "groove_map.json")
            data = json.loads(target.read_text())
            assert data["swing"] == "Swing"
            assert data["bossa"] == "BossaNova"
        finally:
            target.unlink(missing_ok=True)

    def test_defaults_config_seed(self):
        from config2py import ensure_seeded
        import tempfile

        target = Path(tempfile.mktemp(suffix=".json"))
        try:
            ensure_seeded(target, "accompy", "config", "defaults.json")
            data = json.loads(target.read_text())
            assert data["style"] == "swing"
            assert data["tempo"] == 120
            assert "instruments" in data
        finally:
            target.unlink(missing_ok=True)

    def test_nonexistent_seed_raises(self):
        from config2py import ensure_seeded
        import tempfile

        target = Path(tempfile.mktemp(suffix=".txt"))
        with pytest.raises(FileNotFoundError):
            ensure_seeded(target, "accompy", "resources", "no_such_file_xyz.txt")


# =============================================================================
# get_app_folder
# =============================================================================


class TestGetAppFolder:
    """Test app folder creation."""

    def test_creates_directory(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            folder = get_app_folder(folder_kind="data")
            assert folder.is_dir()
            assert folder.name == "accompy"

    def test_config_folder(self, tmp_path):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            folder = get_app_folder(folder_kind="config")
            assert folder.is_dir()
            assert folder == tmp_path / "accompy"


# =============================================================================
# Seed-on-missing pattern
# =============================================================================


class TestSeedOnMissing:
    """Test that resources are seeded when missing and preserved when present."""

    def test_get_resource_seeds_when_missing(self, tmp_path):
        """First access copies the seed file into the user data dir."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            path = get_resource("short_styles.txt")
            assert path.exists()
            assert path.parent.name == "resources"
            content = path.read_text()
            assert "jazz club late night" in content

    def test_get_resource_preserves_user_edits(self, tmp_path):
        """If the file already exists, it is NOT overwritten."""
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            # First call: seeds the file
            path = get_resource("short_styles.txt")

            # User edits the file
            path.write_text("my custom style\n")

            # Second call: should return existing file, not re-seed
            path2 = get_resource("short_styles.txt")
            assert path2 == path
            assert path2.read_text() == "my custom style\n"

    def test_get_config_seeds_when_missing(self, tmp_path):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            path = get_config("defaults.json")
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["tempo"] == 120

    def test_get_config_preserves_user_edits(self, tmp_path):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": str(tmp_path)}):
            path = get_config("defaults.json")
            # User changes tempo
            data = json.loads(path.read_text())
            data["tempo"] = 200
            path.write_text(json.dumps(data))

            path2 = get_config("defaults.json")
            assert json.loads(path2.read_text())["tempo"] == 200


# =============================================================================
# Artifact directories
# =============================================================================


class TestArtifactDirs:

    def test_creates_artifact_subdir(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            midi_dir = get_artifact_dir("midi")
            assert midi_dir.is_dir()
            assert midi_dir == tmp_path / "accompy" / "artifacts" / "midi"

    def test_multiple_kinds(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            for kind in ("midi", "audio", "midi_audio", "chord_patterns"):
                d = get_artifact_dir(kind)
                assert d.is_dir()
                assert d.name == kind


# =============================================================================
# Convenience loaders
# =============================================================================


class TestLoaders:

    def test_load_resource_text(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            text = load_resource_text("short_styles.txt")
            assert isinstance(text, str)
            assert "jazz club late night" in text

    def test_load_resource_lines_strips_and_filters(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            lines = load_resource_lines("short_styles.txt")
            assert isinstance(lines, list)
            assert all(isinstance(l, str) for l in lines)
            # No empty strings
            assert all(l for l in lines)
            # No leading/trailing whitespace
            assert all(l == l.strip() for l in lines)
            assert len(lines) == 64

    def test_load_resource_json(self, tmp_path):
        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            data = load_resource_json("groove_map.json")
            assert isinstance(data, dict)
            assert data["rock"] == "Rock"


# =============================================================================
# Integration: main.py uses data_access
# =============================================================================


class TestMainIntegration:
    """Verify that main.py correctly loads data from user resources."""

    def test_style_to_groove_uses_resource(self, tmp_path):
        from accompy.main import _style_to_groove

        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            assert _style_to_groove("swing") == "Swing"
            assert _style_to_groove("bossa") == "BossaNova"
            assert _style_to_groove("unknown") == "Swing"  # fallback

    def test_style_to_groove_reflects_user_edits(self, tmp_path):
        """If the user edits groove_map.json, _style_to_groove picks it up."""
        from accompy.main import _style_to_groove

        with patch.dict(os.environ, {"XDG_DATA_HOME": str(tmp_path)}):
            # Seed the file first
            path = get_resource("groove_map.json")
            # Add a custom mapping
            data = json.loads(path.read_text())
            data["reggae"] = "Reggae"
            path.write_text(json.dumps(data))

            assert _style_to_groove("reggae") == "Reggae"
