# accompy 🎵

Generate backing track audio from chord charts in Python — like iReal Pro, but scriptable.

```python
from accompy import generate_accompaniment

# Generate a bossa nova backing track
audio = generate_accompaniment("| Dm7 | G7 | C^7 | A7b9 |", style="bossa", tempo=140)
print(f"Generated: {audio}")  # -> /tmp/xxx.wav
```

## Features

- **Simple API**: One function to generate complete backing tracks
- **Multiple styles**: Swing, bossa nova, rock, funk, ballad, latin, waltz, blues
- **Flexible chord inputs**: Strings, `Score`, iReal URLs, or `(chord, beats)` tuples
- **Backend selector**: `backend="auto"|"mma"|"builtin"` (with backwards-compatible `use_mma`)
- **iReal Pro compatible**: Parse iReal Pro URLs directly (with optional `pyRealParser`)
- **Multi-instrument**: Drums, bass, piano with style-appropriate patterns
- **Audio output**: WAV, MP3, FLAC via FluidSynth
- **MIDI output**: Save `.mid` directly (skip audio rendering)
- **Extensible**: Add custom patterns and styles

## Quick Start

### Installation

```bash
pip install accompy  # Coming soon to PyPI

# Or install from source:
git clone https://github.com/yourname/accompy
pip install -e accompy
```

### System Dependencies

accompy requires **FluidSynth** and a **SoundFont** for audio rendering.

#### Automated Setup (Recommended)

The easiest way to get started:

```bash
# Install accompy
pip install -e .

# Run automated setup (interactive)
python -c "from accompy import verify_and_setup; verify_and_setup()"

# This will:
# - Check all dependencies
# - Offer to install missing ones (with your permission)
# - Download and configure SoundFont files
# - Verify everything works
```

#### Manual Setup

If you prefer to install manually:

```bash
# macOS
brew install fluid-synth

# Ubuntu/Debian
sudo apt-get install fluidsynth fluid-soundfont-gm

# Install Python dependencies
pip install midiutil mingus

# Verify setup
python -m accompy --check-deps
```

#### SoundFont (important for sound quality!)

FluidSynth renders MIDI using **SoundFont** sample banks (`.sf2` files).
The SoundFont determines the quality of every instrument you hear.
FluidSynth's bundled SoundFont (`VintageDreamsWaves-v2.sf2`, ~300 KB) is a
bare-minimum placeholder made of basic waveforms — **it will sound terrible**.

For good results, install a full General MIDI SoundFont with real instrument
samples:

```bash
mkdir -p ~/.fluidsynth

# MuseScore General (~200 MB, MIT license, good all-around quality)
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"
```

Other recommended SoundFonts:

- **GeneralUser GS** (~30 MB) — excellent bass and drums, free for commercial
  use. Download from <https://schristiancollins.com/generaluser.php>
- **FluidR3_GM** (~140 MB) — the classic GM SoundFont, widely used.

Browse more at <https://musical-artifacts.com/artifacts?formats=sf2>.

After downloading, place or symlink the file at
`~/.fluidsynth/default_sound_font.sf2` (accompy looks there by default).

#### Check Your Setup

```bash
# Quick check
python -c "from accompy import check_dependencies; print(check_dependencies())"

# Detailed diagnostic report
python -c "from accompy import print_diagnostic_report; print_diagnostic_report()"
```

## Usage

### Basic Usage

```python
from accompy import generate_accompaniment

# Generate with default settings
audio = generate_accompaniment("| C | Am | F | G |")

# Specify style and tempo
audio = generate_accompaniment(
    "| Dm7 | G7 | Cmaj7 | Am7 |",
    style="swing",
    tempo=160,
    repeats=4,
    output_path="my_track.wav"
)

# Generate MIDI only (skip audio rendering)
midi = generate_accompaniment(
   "| Dm7 | G7 | Cmaj7 | Am7 |",
   output_path="my_track.mid",
)
```

### Using Score Objects

For more control, create a `Score` object:

```python
from accompy import Score, generate_accompaniment

# Parse chord string
score = Score.from_string(
    "| Dm7 | G7 | Cmaj7 | % |",  # % = repeat previous chord
    title="ii-V-I in C",
    key="C",
    time_signature=(4, 4)
)

# Generate audio
audio = generate_accompaniment(score, style="swing", tempo=120)

### Flexible Chord Inputs

`generate_accompaniment(...)` accepts several common chord progression formats.

```python
from accompy import ensure_score, generate_accompaniment

# 1) iReal-style chord strings
generate_accompaniment("| C | Am | F | G |")

# 2) iReal Pro URL strings (irealbook://... or irealb://...)
generate_accompaniment("irealbook://Autumn%20Leaves=...")

# 3) List of (chord, beats) tuples (like `accompany`)
chords = [("F#m7b5", 4), ("B7", 4), ("Em", 8)]
score = ensure_score(chords, key="E")
generate_accompaniment(score)
```

### Backend Selection

Choose which generator to use:

```python
from accompy import generate_accompaniment

# Auto: use MMA if available, else builtin
generate_accompaniment("| Dm7 | G7 | Cmaj7 | Am7 |", backend="auto")

# Force builtin generator
generate_accompaniment("| Dm7 | G7 | Cmaj7 | Am7 |", backend="builtin")

# Force MMA (errors if MMA isn't installed)
generate_accompaniment("| Dm7 | G7 | Cmaj7 | Am7 |", backend="mma")
```
```

### Chord Notation

accompy supports flexible chord notation:

```python
# Jazz notation (iReal Pro style)
"| C^7 | D-7 | G7 | C^7 |"   # ^7=maj7, -7=min7

# Standard notation  
"| Cmaj7 | Dm7 | G7 | Cmaj7 |"

# Simple notation
"| C | Dm | G | C |"

# Multiple chords per bar
"| Dm7 G7 | Cmaj7 |"  # Two chords, split evenly

# Repeat symbols
"| C | G | % | F |"   # % repeats G
```

**Chord symbol reference:**

| Notation | Meaning |
|----------|---------|
| `C`, `Cmaj` | C major |
| `C-`, `Cm`, `Cmin` | C minor |
| `C7` | C dominant 7 |
| `C^7`, `Cmaj7` | C major 7 |
| `C-7`, `Cm7`, `Cmin7` | C minor 7 |
| `Co`, `Cdim` | C diminished |
| `Co7`, `Cdim7` | C diminished 7 |
| `Ch7`, `Cm7b5` | C half-diminished |
| `C+`, `Caug` | C augmented |
| `Csus`, `Csus4` | C suspended 4th |

### Styles

Available styles with characteristic patterns:

| Style | Description | Typical Tempo |
|-------|-------------|---------------|
| `swing` | Jazz swing with walking bass | 120-200 BPM |
| `bossa` | Bossa nova with syncopated feel | 100-150 BPM |
| `rock` | Straight 8ths rock beat | 100-140 BPM |
| `funk` | Syncopated funk groove | 90-120 BPM |
| `ballad` | Slow, sustained ballad | 60-90 BPM |
| `latin` | Latin/salsa with clave | 100-130 BPM |
| `waltz` | 3/4 waltz pattern | 90-150 BPM |
| `blues` | Blues shuffle | 80-120 BPM |

### iReal Pro Integration

Parse and play iReal Pro chord charts:

```python
from accompy import Score, generate_accompaniment

# From iReal Pro URL (copy from app or forum)
url = "irealb://6dim=Composer%20Unknown==Medium%20Swing=C=7=1r34LbKcu7QyX%2DA6XyQ%7C%23G%7CQyXG%2F6C%7CQyXFo%7CQyXE%2F6C%7CQyXoDoXyQ%7CC44T%7BXQyXQQ%7DXyQQyXQyXQyXQyXQyQXyXQyXQyXQyXQyXXyQXyyXoB%7CQyXQyXyQXyyXQyXQyXQyXQyXyQXQyXQyXQyXQyXQQXyQXQyXQyyXQyXQXyQXXQyXQyXQyXQyXQXyQyXQyXQyXQyXQyyQXyQyXQyXQXyQXyQXyQXyQXyQ%20Z%20=Jazz%2DMedium%20Up%20Swing%202=118=21]6dim"
score = Score.from_ireal_url(url)

# Generate backing track
audio = generate_accompaniment(score, style="swing", tempo=140)
```

**Note:** `pyRealParser` is optional. If installed, `Score.from_ireal_url(...)` will use it.
If not installed, accompy uses a best-effort built-in parser.

### Advanced Configuration

Full control with `AccompanimentConfig`:

```python
from accompy import AccompanimentConfig, generate_accompaniment

config = AccompanimentConfig(
    style="swing",
    tempo=160,
    repeats=4,
    instruments={
        "drums": True,
        "bass": True,
        "piano": True,
        "guitar": False,
    },
    volumes={
        "drums": 0.7,
        "bass": 1.0,
        "piano": 0.6,
    },
    sample_rate=44100,
   output_format="mp3",  # wav, mp3, flac, midi
)

audio = generate_accompaniment(
    "| Dm7 | G7 | Cmaj7 | A7 |",
    config=config,
    output_path="backing_track.mp3"
)
```

### Rhythmic Skeletons

For simple chord renderings (no drums or bass — just restriking chords with a
rhythmic feel), use `rhythm_to_midi` or `rhythm_to_audio`:

```python
from accompy import rhythm_to_midi, rhythm_to_audio

# Tresillo feel (1.5 + 1.5 + 1 beats)
midi = rhythm_to_midi("| Dm7 | G7 | Cmaj7 |", skeleton="tresillo", tempo=120)
midi.write("tresillo.mid")

# Whole notes (one strike per measure) — the default
midi = rhythm_to_midi("| C | Am | F | G |")

# Charleston, bossa, waltz, and 25+ other built-in skeletons
midi = rhythm_to_midi("| C | Am | F | G |", skeleton="charleston")

# Or pass a raw duration tuple
midi = rhythm_to_midi("| C | Am |", skeleton=(1.5, 0.5, 1.5, 0.5))

# Render all the way to audio
audio = rhythm_to_audio("| C | Am |", skeleton="half_notes", tempo=100)
```

A rhythmic skeleton is just a tuple of durations that sum to the measure length —
e.g. `(1.5, 1.5, 1)` says "hit, hold for a dotted quarter; hit again, hold for
another dotted quarter; hit once more, hold for a quarter." No pitches, no
voicings, no velocities. The skeleton defines *when* you strike within a measure;
the chord progression defines *what* you play.

```python
from accompy import resolve_skeleton, list_skeletons, register_skeleton

# Resolve by key, name, or style
resolve_skeleton("tresillo")           # (1.5, 1.5, 1)
resolve_skeleton("Dotted half + quarter")  # (3, 1)
resolve_skeleton("reggae")             # picks first skeleton for that style

# List available skeletons
list_skeletons()                        # all keys
list_skeletons(beats_per_measure=3)     # waltz-family only
list_skeletons(style="jazz")            # jazz-associated skeletons

# Register your own
register_skeleton("my_groove", (1, 0.5, 0.5, 2), name="My Groove", styles=["custom"])
```

### Extensibility & Custom Patterns

**New in v0.2.0**: accompy now supports extensive customization through a protocol-based architecture.

#### Custom Chord Voicings

Provide your own chord-to-notes resolver:

```python
from accompy import set_chord_resolver, generate_accompaniment

def jazz_voicing_resolver(symbol: str) -> list[int]:
    """Custom jazz voicings with rootless chords, tensions, etc."""
    # Your custom chord resolution logic
    # Return list of MIDI note numbers
    return [55, 59, 62, 65, 69]  # Example: Dm9 voicing

# Set as default resolver
set_chord_resolver(jazz_voicing_resolver)

# Now all accompaniments use your custom voicings
audio = generate_accompaniment("| Dm7 | G7 | Cmaj7 |")
```

#### Custom Patterns

Register your own accompaniment patterns:

```python
from accompy import register_style, DrumPattern, BassPattern, DrumHit, NoteEvent, KICK, SNARE, CLOSED_HIHAT

# Define custom drum pattern
my_drum = DrumPattern(
    name="my_funk",
    beats_per_bar=4,
    hits=[
        DrumHit(0, KICK, 110),
        DrumHit(0.75, KICK, 85),
        DrumHit(1, SNARE, 105),
        DrumHit(2, KICK, 110),
        DrumHit(3, SNARE, 105),
        # ... more hits
    ]
)

# Define custom bass pattern
my_bass = BassPattern(
    name="my_funk",
    notes=[
        NoteEvent(0, 0, 0.4, 110),      # Root, short
        NoteEvent(0.75, 0, 0.2, 80),    # Root, ghostNote
        NoteEvent(1.5, 7, 0.3, 90),      # 5th
        # ... more notes
    ]
)

# Register the custom style
register_style('my_funk', drums=[my_drum], bass=[my_bass], comp=[])

# Use it
audio = generate_accompaniment("| C7 | F7 | C7 | G7 |", style="my_funk")
```

#### Pattern Registry

The pattern registry is a `MutableMapping`, making it Pythonic and extensible:

```python
from accompy import get_pattern_registry

registry = get_pattern_registry()

# Check available styles
print(registry.available_styles())  # ['swing', 'bossa', 'rock', ...]

# Access patterns like a dict
swing_patterns = registry['swing']
print(swing_patterns['drums'])  # List of DrumPattern objects

# Add/modify styles at runtime
registry['custom_groove'] = {
    'drums': [custom_drum_pattern],
    'bass': [custom_bass_pattern],
    'comp': [custom_comp_pattern]
}
```

#### Real-Time Event Generation

For advanced use cases (future integration with `hum`/`pyo` for real-time synthesis):

```python
from accompy import RealtimeAccompaniment, AccompanimentConfig

# Create real-time player
config = AccompanimentConfig(tempo=120, style='swing')
player = RealtimeAccompaniment(config)

# Set chord progression
player.set_chords("| Dm7 | G7 | Cmaj7 | A7 |")

# Get event iterator (for future real-time playback)
for event in player.events():
    # event.time, event.note, event.velocity, event.duration
    # Future: send to real-time synth like hum/pyo
    pass
```

#### Protocol-Based Architecture

All major components implement protocols for maximum flexibility:

```python
from accompy.protocols import ChordResolver, PatternSource, SynthesizerBackend

# Implement custom components that satisfy these protocols
# See accompy/protocols.py for full definitions

# Example: Custom synthesis backend
class MySynthBackend(SynthesizerBackend):
    def render_to_file(self, midi_path, output_path, *, sample_rate=44100):
        # Your custom synthesis logic (e.g., using hum, pyo, etc.)
        pass

    @classmethod
    def is_available(cls):
        return True  # Check if dependencies are available

# Use with dependency injection
from accompy import AccompanimentConfig, generate_accompaniment

config = AccompanimentConfig(synthesis_backend=MySynthBackend())
audio = generate_accompaniment("| C | G | Am | F |", config=config)
```

### Command Line

```bash
# Generate backing track
python -m accompy "| C | Am | F | G |" -s bossa -t 120 -o track.wav

# Check dependencies
python -m accompy --check-deps

# Options
python -m accompy --help
```

## How It Works

1. **Parse chords**: Convert chord string → `Score` object with normalized chord symbols
2. **Generate MIDI**: Create multi-track MIDI with drums, bass, piano patterns
   - Uses **MMA** (Musical MIDI Accompaniment) if available for realistic tracks
   - Falls back to built-in pattern generator
3. **Render audio**: Convert MIDI → WAV using **FluidSynth** with SoundFont
4. **Convert format**: Optionally convert to MP3/FLAC via ffmpeg or pydub

### MMA (Musical MIDI Accompaniment)

For the best quality backing tracks, install [MMA](https://www.mellowood.ca/mma/):

```bash
# MMA provides 50+ professionally designed grooves
git clone https://github.com/infojunkie/mma
cd mma && python install  # Follow MMA installation instructions
```

MMA offers extensive groove libraries with realistic fills, variations, and transitions.

## Python Dependencies

Required:
- `midiutil` — MIDI file generation

Recommended:
- `mingus` — Music theory (better chord parsing)  
- `pyRealParser` — iReal Pro URL parsing
- `midi2audio` — Optional Python wrapper for FluidSynth (can improve portability)
- `pydub` — Audio format conversion (if no ffmpeg)

```bash
pip install midiutil mingus pyRealParser midi2audio pydub
```

## API Reference

### `generate_accompaniment(chords, *, style, tempo, repeats, output_path, output_format, config, use_mma, backend)`

Generate accompaniment audio from chord progression.

**Parameters:**
- `chords` (str | Score | Iterable[tuple[str, int|float]] | Iterable[str] | list[list[str]]): Chord progression
- `style` (str): "swing", "bossa", "rock", "ballad", "funk", "latin", "waltz", "blues"
- `tempo` (int): BPM (default: 120)
- `repeats` (int): Number of times through the form (default: 2)
- `output_path` (str | Path): Where to save audio (default: temp file)
- `output_format` (str | None): "wav", "mp3", "flac", "midi" (optional; inferred from `output_path`)
- `config` (AccompanimentConfig): Full config (overrides style/tempo/repeats)
- `use_mma` (bool): Backwards-compatible MMA toggle (default: True)
- `backend` (str | None): "auto", "mma", "builtin" (optional)

**Returns:** Path to generated audio file

### `Score.from_string(chord_string, *, title, key, time_signature)`

Parse chord string into Score object.

### `Score.from_ireal_url(url)`

Parse iReal Pro URL into Score object.

### `check_dependencies()`

Returns dict of available dependencies.

### `print_setup_instructions()`

Print installation instructions for missing dependencies.

## Troubleshooting

### It sounds awful!

**Problem:** The generated audio plays but sounds robotic, hollow, or like
cheap ringtones from 2003.

**Cause:** You're using a tiny placeholder SoundFont. FluidSynth ships with
`VintageDreamsWaves-v2.sf2` (~300 KB), which is made of basic sine waves — not
real instrument samples. This is the #1 reason accompy output sounds bad.

**How to check:**

```bash
ls -lh ~/.fluidsynth/default_sound_font.sf2
# If it's under 1 MB, that's your problem.
```

**Fix — install a real SoundFont:**

```bash
# Download MuseScore General (~200 MB, real sampled instruments)
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"
```

A proper SoundFont should be **30–200+ MB**. See the
[SoundFont section](#soundfont-important-for-sound-quality) above for more
options, or browse <https://musical-artifacts.com/artifacts?formats=sf2>.

> **Tip:** If you're using an AI coding agent (Claude Code, Cursor, etc.),
> just tell it: *"the accompy output sounds bad, find and install a good
> SoundFont"* — it can diagnose and fix this in seconds.

### Common Issues

#### "No SoundFont found" Error

**Problem:** `RuntimeError: No SoundFont found. Download FluidR3_GM.sf2 and place in ~/.fluidsynth/default_sound_font.sf2`

**Solutions:**

1. **Automated fix:**
   ```bash
   python -c "from accompy import setup_soundfont; setup_soundfont()"
   ```

2. **Check if FluidSynth includes a SoundFont:**
   ```bash
   # macOS with Homebrew
   find /opt/homebrew/Cellar/fluid-synth -name "*.sf2"
   ```
   If found, run the automated setup to link it.

3. **Manual download:**
   ```bash
   mkdir -p ~/.fluidsynth
   # Download MuseScore General (high quality, 35MB)
   curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
     "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"
   ```

4. **Verify the file:**
   ```bash
   ls -lh ~/.fluidsynth/default_sound_font.sf2
   # Should be several MB (not just a few bytes)
   ```

#### "FluidSynth not found" Error

**Problem:** `RuntimeError: FluidSynth not found. Install with: brew install fluidsynth`

**Solutions:**

1. **macOS:**
   ```bash
   brew install fluid-synth
   ```

2. **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install fluidsynth
   ```

3. **Windows:**
   Download from [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases) and add to PATH

4. **Verify installation:**
   ```bash
   which fluidsynth
   fluidsynth --version
   ```

#### SoundFont File is Corrupted (255 bytes)

**Problem:** Downloaded SoundFont is tiny (255 bytes) and appears to be XML

**Cause:** Download URL redirected to an error page

**Solution:**
```bash
# Remove corrupted file
rm ~/.fluidsynth/default_sound_font.sf2

# Use automated setup
python -c "from accompy import setup_soundfont; setup_soundfont(force=True)"

# Or manually download from a reliable source
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"
```

#### Import Warning About Missing Dependencies

**Problem:** Warning on import: `accompy setup incomplete - missing: fluidsynth, soundfont`

**Solutions:**

1. **Run setup:**
   ```bash
   python -c "from accompy import verify_and_setup; verify_and_setup()"
   ```

2. **Temporarily disable warning:**
   ```bash
   export ACCOMPY_SKIP_SETUP_CHECK=1
   python your_script.py
   ```

3. **Fix manually and verify:**
   ```bash
   # Install dependencies
   brew install fluid-synth  # or apt-get install fluidsynth
   pip install midiutil

   # Run diagnostic
   python -c "from accompy import print_diagnostic_report; print_diagnostic_report()"
   ```

#### "midiutil not found" Error

**Problem:** Missing Python dependency

**Solution:**
```bash
pip install midiutil mingus
```

### Diagnostic Tools

#### Run Full Diagnostic

Get a comprehensive report of your setup:

```python
from accompy import print_diagnostic_report
print_diagnostic_report()
```

This shows:
- System information
- Dependency status (✓ or ✗)
- Specific issues found
- Solutions for each issue

#### Check Specific Issues

```python
from accompy import diagnose_issues

for issue, description, solution in diagnose_issues():
    print(f"Issue: {issue}")
    print(f"Description: {description}")
    print(f"Solution: {solution}\n")
```

#### Verify Individual Dependencies

```python
from accompy import check_dependencies

deps = check_dependencies()
print(f"FluidSynth: {deps['fluidsynth']}")
print(f"SoundFont: {deps['soundfont']}")
print(f"midiutil: {deps['midiutil']}")
print(f"mingus: {deps['mingus']}")
print(f"MMA: {deps['mma']}")
```

### Getting Help

If you're still having issues:

1. Run diagnostic report and save output:
   ```bash
   python -c "from accompy import print_diagnostic_report; print_diagnostic_report()" > diagnostic.txt
   ```

2. Check existing issues: [GitHub Issues](https://github.com/yourname/accompy/issues)

3. Create a new issue with:
   - Your diagnostic report
   - What you tried
   - Full error message

## Contributing

Contributions welcome! Areas of interest:

- Additional styles/grooves
- Better drum fills and variations
- Improved chord voicings
- More instrument parts (guitar, strings, horns)
- Web interface
- Better cross-platform setup automation

## License

MIT

## Acknowledgments

- [MMA - Musical MIDI Accompaniment](https://www.mellowood.ca/mma/) by Bob van der Poel
- [FluidSynth](https://www.fluidsynth.org/) team
- [pyRealParser](https://github.com/drs251/pyRealParser) for iReal Pro format parsing
- [iReal Pro](https://www.irealpro.com/) for inspiration
