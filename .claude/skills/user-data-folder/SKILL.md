---
name: user-data-folder
description: Use when setting up per-user persistent data directories for a Python package — configuration files, bundled resources (seed-on-missing pattern), and runtime artifact folders. Triggers on XDG directories, app data folder, user config, seed data, importlib.resources, or when externalizing module-level constants to user-editable files.
---

# User Data Folder Setup for Python Packages

## When to use

- A Python package needs to persist data outside its installation directory.
- Module-level dicts/lists should be externalized to user-editable files.
- The package should ship initial "seed" data that gets copied to userspace on first access.
- Runtime artifacts (generated files) need organized storage.

## Directory layout

Use XDG Base Directory Specification for cross-platform paths:

```
~/.config/<pkg>/              # config (user preferences, settings)
~/.local/share/<pkg>/         # data
    resources/                #   shipped reference data (editable copies)
    artifacts/                #   runtime-generated data
        <kind>/               #     one subfolder per artifact kind
```

Windows equivalents: `%APPDATA%` for config, `%LOCALAPPDATA%` for data.

## Prerequisites

Add `config2py` as a dependency in `pyproject.toml` if not already present.
`config2py.AppData` handles XDG resolution, seed-on-missing via
`importlib.resources`, and artifact directory creation.

## Implementation steps

### 1. Create the seed data directory

```
<pkg>/
    _seed_data/
        __init__.py          # empty, makes it a package for importlib.resources
        resources/
            __init__.py      # empty
            styles.txt       # example seed file
        config/
            __init__.py      # empty
            defaults.json    # example seed config
```

Every subdirectory needs an `__init__.py` for `importlib.resources.files()` to
find it as a package.

### 2. Create the data access module

Create `<pkg>/data_access.py`:

```python
"""Per-user data directory management."""

from __future__ import annotations

from pathlib import Path

from config2py import AppData

_app_data = AppData("<pkg>")

# -- Delegate core access to config2py.AppData --
get_app_folder = _app_data.app_folder
get_resource = _app_data.get_resource
get_config = _app_data.get_config
get_artifact_dir = _app_data.get_artifact_dir


# -- Project-specific convenience loaders --

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
```

### 3. Declare package data in pyproject.toml

For hatchling (default for hatch-based builds), files inside the package
directory are included automatically. No extra config needed.

For setuptools:
```toml
[tool.setuptools.package-data]
"<pkg>._seed_data" = ["**/*"]
```

### 4. Migrate module-level constants to seed files

For each module-level dict/list that is a good externalization candidate:

1. **Export the data** to an appropriate format in `_seed_data/resources/`:
   - Simple lists: plain text (one item per line)
   - Structured data: JSON
   - Complex nested config: TOML

2. **Replace the in-module definition** with a lazy loader:

```python
from functools import cache

@cache
def _load_styles() -> list[str]:
    """Load style list from user resources (seeded from package data)."""
    from .data_access import get_resource
    path = get_resource("styles.txt")
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]
```

Or more simply, just call the loader function everywhere instead of using a
module-level constant.

## `config2py.AppData` API reference

```python
from config2py import AppData

app = AppData("myapp")
# If Python package name differs from app name:
app = AppData("my-app", package_name="my_app")
# Custom seed directory name (default is "_seed_data"):
app = AppData("myapp", seed_data_dir="bundled_data")

app.app_folder()                      # -> Path: ~/.local/share/myapp
app.app_folder(folder_kind="config")  # -> Path: ~/.config/myapp
app.get_resource("data.json")         # -> Path (seeded if missing)
app.get_config("settings.json")       # -> Path (seeded if missing)
app.get_artifact_dir("exports")       # -> Path (created if missing)
```

Seed-on-missing logic: `config2py.ensure_seeded(target, package_name,
seed_subpackage, filename)` — the low-level primitive if you need
direct control.

## Checklist

- [ ] Add `config2py` to dependencies in `pyproject.toml`
- [ ] Create `<pkg>/_seed_data/` with `__init__.py` files in every subdirectory
- [ ] Place seed files in `_seed_data/resources/` and `_seed_data/config/`
- [ ] Create `<pkg>/data_access.py` using `config2py.AppData`
- [ ] Add project-specific convenience loaders as needed
- [ ] Verify `pyproject.toml` includes `_seed_data` in the wheel
- [ ] Identify module-level constants to externalize
- [ ] Replace each with a lazy loader using `get_resource()`
- [ ] Test: fresh install seeds files; editing user files persists across imports

## Artifact directory conventions

Common artifact kinds and their typical contents:

| Kind              | Contents                                |
|-------------------|-----------------------------------------|
| `chord_patterns`  | Saved chord progressions (JSON/txt)     |
| `midi`            | Generated MIDI files                    |
| `midi_audio`      | Audio rendered from MIDI                |
| `audio`           | Higher-quality audio files              |
| `exports`         | User-exported bundles                   |

## Anti-patterns

- **Seed at import time**: Use lazy seeding (on first access), not eager.
- **Overwrite user edits**: Never re-seed if file exists.
- **Hardcode paths**: Always use XDG env vars or platform helper.
- **Use `__file__` for seed data**: Use `importlib.resources` instead.
- **Store large files as seeds**: Seed files should be small reference data.
