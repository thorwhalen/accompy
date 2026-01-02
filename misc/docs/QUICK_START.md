# accompy Quick Start

Get up and running with accompy in under 5 minutes!

## Installation

```bash
pip install -e /path/to/accompy
```

## Setup (Choose One)

### Option 1: Automated Setup (Easiest)

```python
from accompy import verify_and_setup
verify_and_setup(interactive=True)
```

This will guide you through the entire setup process interactively.

### Option 2: Quick Manual Setup (macOS)

```bash
# Install FluidSynth (includes SoundFont)
brew install fluid-synth

# Link the bundled SoundFont
python -c "from accompy import setup_soundfont; setup_soundfont()"

# Install Python dependencies
pip install midiutil mingus
```

### Option 3: Quick Manual Setup (Linux)

```bash
# Install FluidSynth with SoundFont
sudo apt-get install fluidsynth fluid-soundfont-gm

# Install Python dependencies
pip install midiutil mingus
```

## Verify Setup

```python
from accompy import print_diagnostic_report
print_diagnostic_report()
```

You should see ✓ marks for `fluidsynth` and `soundfont` at minimum.

## First Track

```python
from accompy import generate_accompaniment

# Generate a bossa nova backing track
audio = generate_accompaniment(
    "| Dm7 | G7 | Cmaj7 | A7b9 |",
    style="bossa",
    tempo=140
)

print(f"Generated: {audio}")
```

## Troubleshooting

If you see errors:

```python
from accompy import diagnose_issues

for issue, desc, solution in diagnose_issues():
    print(f"{issue}:")
    print(f"  {solution}\n")
```

## Common Issues

**"No SoundFont found"**
```python
from accompy import setup_soundfont
setup_soundfont()
```

**"FluidSynth not found"**
```bash
# macOS
brew install fluid-synth

# Linux
sudo apt-get install fluidsynth
```

**Import warning**
```python
import os
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"  # Temporarily disable
# Then run verify_and_setup() to fix
```

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed setup instructions
- Check [README.md](README.md) for usage examples and API reference
- Explore different styles: swing, bossa, rock, funk, ballad, latin, waltz, blues

## Getting Help

1. Run diagnostic: `python -c "from accompy import print_diagnostic_report; print_diagnostic_report()"`
2. Check [SETUP.md](SETUP.md) troubleshooting section
3. File an issue with your diagnostic output
