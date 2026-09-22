# accompy.data_access

Per-user data directory management for accompy.

Provides cross-platform access to:

- `~/.config/accompy/`  — user preferences and settings
- `~/.local/share/accompy/resources/` — editable reference data (seeded from package)
- `~/.local/share/accompy/artifacts/<kind>/` — runtime-generated files

Seed files ship inside `accompy/_seed_data/` and are copied to userspace on
first access (seed-on-missing pattern).  All XDG resolution and seeding logic
is delegated to `config2py.AppData`.

### Functions

| [`load_resource_json`](#accompy.data_access.load_resource_json)(name)   | Read a resource file as JSON.                               |
|-----------------------------------------------------------------------------|-------------------------------------------------------------|
| [`load_resource_lines`](#accompy.data_access.load_resource_lines)(name)  | Read a resource file as a list of non-empty stripped lines. |
| [`load_resource_text`](#accompy.data_access.load_resource_text)(name)   | Read a resource file as text.                               |

### accompy.data_access.load_resource_json(name)

Read a resource file as JSON.

### accompy.data_access.load_resource_lines(name)

Read a resource file as a list of non-empty stripped lines.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### accompy.data_access.load_resource_text(name)

Read a resource file as text.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
