# User Data Folder Design for Python Packages

A design document for managing per-user persistent data in Python packages:
configuration files, bundled resources, and user-generated artifacts.

## Problem

Python packages often need to store data outside of the package installation
directory:

- **Configuration**: User preferences, API keys, default settings.
- **Resources**: Reference data that ships with the package but should be
  editable by the user (style lists, lookup tables, templates).
- **Artifacts**: Data produced at runtime — generated files, caches, logs —
  organized by kind.

Hardcoding this data inside modules (as dicts/lists at module level) makes it
invisible to the user, hard to edit, and impossible to extend without touching
source code.

## Design

### 1. Directory Layout

Follow the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/)
to choose platform-appropriate root directories:

| Kind      | XDG env var         | macOS / Linux default | Windows default        | Purpose                                    |
|-----------|---------------------|-----------------------|------------------------|--------------------------------------------|
| `config`  | `XDG_CONFIG_HOME`   | `~/.config`           | `%APPDATA%`            | User preferences, settings files           |
| `data`    | `XDG_DATA_HOME`     | `~/.local/share`      | `%LOCALAPPDATA%`       | Essential user data and application state   |
| `cache`   | `XDG_CACHE_HOME`    | `~/.cache`            | `%LOCALAPPDATA%/Temp`  | Temporary, regenerable files               |

Under each root, the package creates a subfolder named after itself:

```
~/.config/<pkg>/          # config
    defaults.json         # user-editable defaults
    ...

~/.local/share/<pkg>/     # data
    resources/            # shipped reference data (editable copies)
        short_styles.txt
        ...
    artifacts/            # runtime-generated data, organized by kind
        chord_patterns/
        midi/
        audio/
        ...
```

### 2. Seeding Resources (First-Run Initialization)

The package bundles **seed files** — the initial content for the `resources/`
directory. On first import (or whenever a resource file is missing), the system
copies these seeds into the user data folder.

#### Where to store seed files in the package

Use Python's `importlib.resources` (3.9+) to ship seed data alongside the
package code:

```
<pkg>/
    _seed_data/
        resources/
            short_styles.txt
        config/
            defaults.json
    ...
```

Declare this directory in `pyproject.toml` so that the build system includes it:

```toml
[tool.hatch.build.targets.wheel]
packages = ["<pkg>"]
# _seed_data/ is inside <pkg>/, so it is included automatically.
# If using setuptools, add:
# [tool.setuptools.package-data]
# <pkg> = ["_seed_data/**/*"]
```

#### Why `importlib.resources` over other approaches

| Approach                   | Pros                          | Cons                                       |
|----------------------------|-------------------------------|--------------------------------------------|
| `importlib.resources`      | Standard library, zip-safe    | API changed between 3.7 and 3.12           |
| `pkg_resources`            | Well-known                    | Deprecated, slow, setuptools-only          |
| `__file__`-relative paths  | Simple                        | Breaks inside zips / wheels without files   |
| `package_data` + `__file__`| Works with pip install        | Still fragile with editable installs        |

**Recommendation**: Use `importlib.resources` with a compatibility shim for
the `files()` API (available natively in 3.9+; backported via
`importlib_resources` for older Pythons).

### 3. The Seed-on-Missing Pattern

The core pattern for accessing a user-data file that may need to be created
from a bundled seed:

```python
def get_resource(name: str) -> Path:
    """Return path to a user resource file, seeding from package data if missing."""
    resource_dir = get_app_data_folder(APP_NAME) / "resources"
    target = resource_dir / name
    if not target.exists():
        _seed_file("resources", name, target)
    return target


def _seed_file(category: str, name: str, target: Path):
    """Copy a bundled seed file to the user data directory."""
    target.parent.mkdir(parents=True, exist_ok=True)
    seed_content = _read_seed(category, name)
    target.write_bytes(seed_content)


def _read_seed(category: str, name: str) -> bytes:
    """Read a seed file from the package's _seed_data directory."""
    from importlib.resources import files

    ref = files(f"{PACKAGE_NAME}._seed_data.{category}") / name
    return ref.read_bytes()
```

**Key properties**:

- **Lazy**: Seed files are only copied when first accessed, not at import time.
  This avoids slowing down `import pkg` and avoids file I/O when the resource
  isn't needed.
- **Idempotent**: If the file already exists, no action is taken. The user's
  edits are preserved.
- **Recoverable**: If a user deletes a resource file, it is silently
  re-seeded from the package data on next access.
- **User-editable**: Once seeded, the file lives in userspace. The user can
  edit, extend, or replace it.

### 4. Loading Data with Fallback to Seed

When module code needs data that might live in a user resource file, use this
pattern:

```python
def load_resource_lines(name: str) -> list[str]:
    """Load a text resource as a list of non-empty lines."""
    path = get_resource(name)
    return [line.strip() for line in path.read_text().splitlines() if line.strip()]
```

For module-level constants that currently live as dicts/lists in source code,
the migration path is:

1. Move the data to a seed file (JSON, TOML, or plain text).
2. Replace the in-module definition with a lazy loader.
3. Keep the same public name for backward compatibility.

Example migration:

```python
# BEFORE (in module)
STYLES = ["swing", "bossa", "rock", "funk", ...]

# AFTER (lazy from user data)
from functools import cache


@cache
def _load_styles():
    return load_resource_lines("short_styles.txt")


# Property-style access for backward compat at module level
# (or just call _load_styles() where needed)
```

### 5. Configuration Files

Configuration files follow the same seed-on-missing pattern, but live under
the `config` folder kind:

```python
def get_config(name: str) -> Path:
    """Return path to a config file, seeding defaults if missing."""
    config_dir = get_app_config_folder(APP_NAME)
    target = config_dir / name
    if not target.exists():
        _seed_file("config", name, target)
    return target
```

Use JSON or TOML for config files — both are human-editable and have standard
library parsers (TOML via `tomllib` in 3.11+, JSON via `json`).

### 6. Artifact Directories

Artifacts are runtime-generated data that the user may want to keep. Each kind
gets its own subdirectory under `data/artifacts/`:

```python
def get_artifact_dir(kind: str) -> Path:
    """Return (and create) an artifact directory for a given kind."""
    artifact_dir = get_app_data_folder(APP_NAME) / "artifacts" / kind
    artifact_dir.mkdir(parents=True, exist_ok=True)
    return artifact_dir
```

Typical kinds: `chord_patterns`, `midi`, `audio`, `midi_audio`, etc.

### 7. Platform-Independent Folder Resolution

Use `config2py.get_app_folder` (or equivalent logic) for cross-platform
folder resolution:

```python
import os
from pathlib import Path


def _get_xdg_dir(folder_kind: str) -> Path:
    """Resolve XDG-style directory, cross-platform."""
    if os.name == "nt":  # Windows
        defaults = {
            "config": os.environ.get("APPDATA", ""),
            "data": os.environ.get("LOCALAPPDATA", ""),
            "cache": os.path.join(os.environ.get("LOCALAPPDATA", ""), "Temp"),
        }
    else:  # macOS, Linux, etc.
        env_vars = {
            "config": "XDG_CONFIG_HOME",
            "data": "XDG_DATA_HOME",
            "cache": "XDG_CACHE_HOME",
        }
        defaults_map = {
            "config": "~/.config",
            "data": "~/.local/share",
            "cache": "~/.cache",
        }
        env_val = os.environ.get(env_vars[folder_kind])
        if env_val:
            return Path(env_val)
        return Path(defaults_map[folder_kind]).expanduser()
    return Path(defaults[folder_kind])


def get_app_folder(app_name: str, folder_kind: str = "data") -> Path:
    """Return the app-specific directory for the given folder kind, creating it."""
    folder = _get_xdg_dir(folder_kind) / app_name
    folder.mkdir(parents=True, exist_ok=True)
    return folder
```

Or simply depend on `config2py` and use:
```python
from config2py import get_app_data_folder, get_app_config_folder
```

### 8. Summary of Conventions

| Concern              | Location                              | Format           | Pattern            |
|----------------------|---------------------------------------|------------------|--------------------|
| User preferences     | `~/.config/<pkg>/`                    | JSON / TOML      | Seed-on-missing    |
| Reference data       | `~/.local/share/<pkg>/resources/`     | txt / JSON / etc | Seed-on-missing    |
| Generated artifacts  | `~/.local/share/<pkg>/artifacts/<kind>/` | varies        | mkdir-on-access    |
| Bundled seed files   | `<pkg>/_seed_data/{config,resources}/`| same as target   | importlib.resources|

### 9. Anti-Patterns to Avoid

- **Seeding at import time**: Slows down `import pkg`. Seed lazily on first access.
- **Overwriting user edits**: Never re-seed if the file already exists.
- **Hardcoding `~/.local/share`**: Always resolve via XDG env vars or a
  platform-aware helper.
- **Storing large blobs in `_seed_data`**: Seed files should be small reference
  data. Large files should be downloaded on demand or fetched from a remote.
- **Using `__file__` to find seed data**: Breaks with zip imports and some
  editable installs. Use `importlib.resources`.
