# Accompy v0.2.0 Architecture

## Overview

Version 0.2.0 represents a major architectural refactoring of accompy, transforming it from a monolithic module into a modular, extensible system. This refactor prioritizes a clean internal architecture over strict backward compatibility.

## Key Improvements

### Before (v0.1.0)
- **Monolithic**: Single 1400-line `accompy.py` file
- **Tightly coupled**: Pattern selection, MIDI generation, and audio rendering all interwoven
- **Hard-coded**: Chord resolution, pattern selection, synthesis backends
- **File-only**: No support for streaming or real-time use

### After (v0.2.0)
- **Modular**: ~10 focused modules with clear responsibilities
- **Protocol-based**: Extensibility contracts via `typing.Protocol`
- **Pluggable**: Custom chord resolvers, patterns, synthesis backends
- **Event-based**: Iterator pattern enables both batch and real-time use
- **Registry pattern**: `MutableMapping` for runtime pattern registration

## Module Structure

```
accompy/
├── __init__.py              # Public API
├── base.py                  # Core domain models (Score, Config, MidiEvent)
├── util.py                  # Chord parsing and normalization utilities
├── patterns/
│   ├── __init__.py          # PatternRegistry (MutableMapping)
│   ├── dataclasses.py       # Pattern data structures
│   └── builtin.py           # Built-in patterns (swing, bossa, etc.)
├── chord_resolution.py      # Pluggable chord-to-notes resolution
├── protocols.py             # Protocol definitions for extensibility
├── renderers/
│   ├── __init__.py
│   ├── midi.py              # Event-based MIDI generation
│   └── mma.py               # MMA backend (future)
├── synthesis/
│   ├── __init__.py          # SynthesizerBackend ABC
│   └── fluidsynth.py        # FluidSynth implementation
├── realtime.py              # Real-time event generation foundation
├── main.py                  # Main generation logic (refactored)
├── setup_utils.py           # Dependency checking (unchanged)
└── accompy.py               # Older implementation (kept as reference)
```

## Design Patterns

### 1. Protocol-Oriented Design (PEP 544)

All major components define protocols for structural subtyping:

```python
# accompy/protocols.py
@runtime_checkable
class ChordResolver(Protocol):
    """Convert chord symbols to MIDI notes."""

    def __call__(self, symbol: str) -> list[int]: ...


@runtime_checkable
class PatternSource(Protocol):
    """Provides patterns for a given style."""

    def get_patterns(self, style: str) -> dict[str, list]: ...
    def available_styles(self) -> list[str]: ...


@runtime_checkable
class SynthesizerBackend(Protocol):
    """Audio synthesis backend."""

    def render_to_file(self, midi_path, output_path, *, sample_rate): ...
    def is_available(cls) -> bool: ...
```

**Benefits:**
- Type safety without rigid inheritance
- Easy to implement custom components
- Duck typing with runtime checks

### 2. Registry Pattern (MutableMapping)

The `PatternRegistry` implements `collections.abc.MutableMapping`:

```python
# accompy/patterns/__init__.py
class PatternRegistry(MutableMapping[str, dict]):
    """Registry of accompaniment patterns by style."""

    def __getitem__(self, style: str) -> dict: ...
    def __setitem__(self, style: str, patterns: dict): ...
    def __delitem__(self, style: str): ...

    # ... etc
```

**Usage:**
```python
registry = get_pattern_registry()
registry["custom"] = {"drums": [...], "bass": [...], "comp": [...]}
del registry["unwanted_style"]
"swing" in registry  # True
```

**Benefits:**
- Pythonic API (dict-like interface)
- Runtime extensibility
- Validation on assignment

### 3. Event-Based MIDI Generation

MIDI generation is now iterator-based, separating event creation from file I/O:

```python
# accompy/renderers/midi.py
def generate_midi_events(
    score: Score,
    config: AccompanimentConfig,
    *,
    pattern_source: PatternSource,
    chord_resolver: ChordResolver,
) -> Iterator[MidiEvent]:
    """Generate MIDI events (pure function, no side effects)."""
    for repeat in range(config.repeats):
        for measure in score.measures:
            # ... generate events
            yield MidiEvent(time, channel, note, velocity, duration)


def events_to_midi_file(events: Sequence[MidiEvent], path: Path, tempo: int):
    """Write events to file (side effect)."""
    # ... write MIDI file
```

**Benefits:**
- Separation of concerns (generation vs. I/O)
- Enables real-time streaming
- Easier to test (pure functions)
- Memory efficient (lazy evaluation)

### 4. Dependency Injection

`AccompanimentConfig` serves as a dependency injection container:

```python
@dataclass
class AccompanimentConfig:
    # Core settings
    style: str = "swing"
    tempo: int = 120
    # ...

    # DI hooks
    chord_resolver: Optional[ChordResolver] = None
    pattern_source: Optional[PatternSource] = None
    synthesis_backend: Optional[SynthesizerBackend] = None
```

**Usage:**
```python
config = AccompanimentConfig(
    chord_resolver=my_custom_resolver, synthesis_backend=MyCustomSynthBackend()
)
generate_accompaniment(chords, config=config)
```

**Benefits:**
- Testability (inject mocks)
- Flexibility (swap implementations)
- Explicit dependencies

### 5. Strategy Pattern

Chord resolution uses the strategy pattern with global and per-call customization:

```python
# Global strategy
set_chord_resolver(my_custom_resolver)

# Per-call strategy
config = AccompanimentConfig(chord_resolver=another_resolver)
```

## Data Flow

### Original (v0.1.0)
```
chord_string
  → parse
  → generate_midi (monolithic)
  → render_audio
  → output_file
```

### Refactored (v0.2.0)
```
chord_string
  → ensure_score (util.py)
  → Score
  → generate_midi_events (renderers/midi.py)
      ├─ pattern_source.get_patterns()
      └─ chord_resolver(symbol)
  → Iterator[MidiEvent]
  → events_to_midi_file()
  → MIDI file
  → synthesis_backend.render_to_file()
  → audio file
```

**Each step is:**
- Pure (no side effects except at boundaries)
- Testable (mockable dependencies)
- Replaceable (protocols define contracts)

## Compatibility

This refactor may introduce breaking changes while the architecture stabilizes.
The docs and tests are the source of truth for the current API.

## Extensibility Examples

### Custom Chord Voicing

```python
from accompy import set_chord_resolver


def jazz_voicing(symbol: str) -> list[int]:
    # Custom voicing logic (rootless, tensions, etc.)
    return [55, 59, 62, 65, 69]


set_chord_resolver(jazz_voicing)
```

### Custom Patterns

```python
from accompy import register_style, DrumPattern, BassPattern, DrumHit, NoteEvent

my_drum = DrumPattern("my_funk", 4, [DrumHit(0, KICK, 110), ...])
my_bass = BassPattern("my_funk", [NoteEvent(0, 0, 0.4, 110), ...])

register_style("my_funk", drums=[my_drum], bass=[my_bass], comp=[])
```

### Custom Synthesis Backend

```python
from accompy.protocols import SynthesizerBackend
from accompy import AccompanimentConfig, generate_accompaniment


class PyoBackend(SynthesizerBackend):
    def render_to_file(self, midi_path, output_path, *, sample_rate=44100):
        # Use hum/pyo for synthesis
        from hum.pyo_util import Synth

        # ... custom synthesis logic
        return output_path

    @classmethod
    def is_available(cls):
        try:
            import pyo

            return True
        except ImportError:
            return False


config = AccompanimentConfig(synthesis_backend=PyoBackend())
audio = generate_accompaniment("| C | G | Am | F |", config=config)
```

## Testing Strategy

### Unit Tests
- **Protocols**: Verify structural subtyping with `@runtime_checkable`
- **Pure functions**: Test `generate_midi_events()` with mock dependencies
- **Registry**: Test `PatternRegistry` as a `MutableMapping`

### Integration Tests
- **End-to-end**: Verify `generate_accompaniment()` with all backends
- **End-to-end**: Ensure the current examples work

### Property-Based Tests
- **Chord parsing**: `ensure_score()` handles all input formats
- **MIDI generation**: All events have valid time/note/velocity

## Future Enhancements

### Real-Time Synthesis (v0.3.0)

The foundation is in place:

```python
# accompy/realtime.py (already exists)
class RealtimeAccompaniment:
    def events(self) -> Iterator[MidiEvent]:
        # Already implemented
        ...

    def play(self):
        # TODO: Integrate with hum/pyo
        raise NotImplementedError()
```

**Next steps:**
1. Create `PyoBackend(SynthesizerBackend)` in `synthesis/pyo_synth.py`
2. Implement event scheduling with audio clock sync
3. Add `RealtimeAccompaniment.play()` method

### Enhanced Pattern System (v0.3.0)

- **Pattern variations**: Multiple patterns per style with selection logic
- **Fill patterns**: Automatic fills at phrase boundaries
- **Dynamic patterns**: Patterns that adapt to chord changes
- **Pattern DSL**: Text-based pattern definition language

### MCP Server Integration (v0.4.0)

Expose accompy via Model Context Protocol for AI assistants:

```python
# Potential MCP server in accompy/mcp_server.py
from mcp import MCPServer

server = MCPServer("accompy")


@server.tool()
def generate_backing_track(chords: str, style: str, tempo: int):
    return generate_accompaniment(chords, style=style, tempo=tempo)
```

## Migration Guide

### For Users
Expect occasional breaking changes until the API stabilizes.

### For Developers
If you've created custom extensions:

**Before (custom patterns):**
```python
# Had to modify builtin pattern tables directly
DRUM_PATTERNS["custom"] = [...]
```

**After (v0.2.0):**
```python
from accompy import register_style

register_style("custom", drums=[...], bass=[...], comp=[...])
```

## Related Packages

Accompy v0.2.0 is designed to integrate with the music ecosystem:

- **tonal**: Chord-to-notes resolution (default backend)
- **hum**: Real-time synthesis with Pyo (future integration)
- **sung**: Chord/lyrics datasets for testing
- **theremin**: Gesture-based control (could drive chord changes)

See `misc/docs/packages_summaries.md` for details.

## Conclusion

The v0.2.0 refactoring transforms accompy from a useful tool into an extensible framework while maintaining simplicity for basic use cases. The protocol-based architecture enables:

- **Experimentation**: Try different chord voicings, patterns, synthesis backends
- **Integration**: Embed in larger systems (DAWs, AI assistants, live coding)
- **Evolution**: Foundation for real-time features, advanced patterns, etc.

All while preserving the simple one-function API that makes accompy easy to use.
