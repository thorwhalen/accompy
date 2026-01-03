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
# FluidSynth 2.5+ comes with a bundled SoundFont
# The setup will automatically link it for you

# Ubuntu/Debian
sudo apt-get install fluidsynth fluid-soundfont-gm

# Install Python dependencies
pip install midiutil mingus

# Verify setup
python -m accompy --check-deps
```

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
