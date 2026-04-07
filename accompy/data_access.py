"""Per-user data directory management for accompy.

Provides cross-platform access to:
- ``~/.config/accompy/``  — user preferences and settings
- ``~/.local/share/accompy/resources/`` — editable reference data (seeded from package)
- ``~/.local/share/accompy/artifacts/<kind>/`` — runtime-generated files

Seed files ship inside ``accompy/_seed_data/`` and are copied to userspace on
first access (seed-on-missing pattern).  All XDG resolution and seeding logic
is delegated to ``config2py.AppData``.
"""

from __future__ import annotations

from pathlib import Path

from config2py import AppData

_app_data = AppData("accompy")

# ---------------------------------------------------------------------------
# Core access — delegated to config2py.AppData
# ---------------------------------------------------------------------------

get_app_folder = _app_data.app_folder
get_resource = _app_data.get_resource
get_config = _app_data.get_config
get_artifact_dir = _app_data.get_artifact_dir


# ---------------------------------------------------------------------------
# Convenience loaders
# ---------------------------------------------------------------------------

def load_resource_text(name: str) -> str:
    """Read a resource file as text."""
    return get_resource(name).read_text()


def load_resource_lines(name: str) -> list[str]:
    """Read a resource file as a list of non-empty stripped lines."""
    return [
        line.strip()
        for line in load_resource_text(name).splitlines()
        if line.strip()
    ]


def load_resource_json(name: str):
    """Read a resource file as JSON."""
    import json

    return json.loads(load_resource_text(name))
