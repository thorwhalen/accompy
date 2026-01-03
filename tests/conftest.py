"""Pytest configuration and shared fixtures for accompy tests."""

import os
import pytest

# Disable setup check for tests
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"


@pytest.fixture
def simple_chord_string():
    """Simple chord progression for testing."""
    return "| C | Am | F | G |"


@pytest.fixture
def jazz_chord_string():
    """Jazz chord progression with iReal notation."""
    return "| Dm7 | G7 | C^7 | A7b9 |"


@pytest.fixture
def bossa_progression():
    """Bossa nova style progression."""
    return "| Dm7 | G7 | Cmaj7 | Fmaj7 |"


@pytest.fixture
def chord_tuples():
    """Chord progression as (chord, beats) tuples."""
    return [("C", 4), ("Am", 4), ("F", 4), ("G", 4)]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir
