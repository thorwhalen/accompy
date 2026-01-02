# accompy Setup Guide

This guide will help you get accompy up and running with all necessary dependencies.

## Quick Setup (Recommended)

For most users, the automated setup is the easiest way to get started:

```python
from accompy import verify_and_setup
verify_and_setup(interactive=True)
```

This interactive setup will:
1. Check all required dependencies
2. Prompt you before installing anything
3. Install FluidSynth if missing (via Homebrew on macOS, apt on Linux)
4. Download and configure a SoundFont file
5. Install Python packages (midiutil, mingus)
6. Verify everything works

## Step-by-Step Manual Setup

If you prefer to install dependencies manually, follow these steps:

### 1. Install FluidSynth

FluidSynth is required for converting MIDI to audio.

**macOS:**
```bash
brew install fluid-synth
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install fluidsynth
```

**Windows:**
1. Download from [FluidSynth Releases](https://github.com/FluidSynth/fluidsynth/releases)
2. Extract and add to your PATH

**Verify:**
```bash
fluidsynth --version
# Should show version 2.0 or higher
```

### 2. Configure SoundFont File

A SoundFont file provides the instrument sounds for audio rendering.

**Option A: Use bundled SoundFont (macOS with Homebrew)**

If you installed FluidSynth via Homebrew, it comes with a SoundFont:

```python
from accompy import setup_soundfont
setup_soundfont()
```

This will automatically find and link the bundled SoundFont.

**Option B: Download SoundFont manually**

```bash
# Create directory
mkdir -p ~/.fluidsynth

# Download MuseScore General SoundFont (35MB, high quality)
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"

# Verify download (should be ~35MB)
ls -lh ~/.fluidsynth/default_sound_font.sf2
```

**Alternative SoundFonts:**
- FluidR3_GM.sf2 (older but reliable)
- GeneralUser GS (good quality)
- Any General MIDI compatible .sf2 file

### 3. Install Python Dependencies

```bash
# Required
pip install midiutil

# Recommended (better chord parsing)
pip install mingus

# Optional (for iReal Pro support)
pip install pyRealParser
```

### 4. Verify Installation

```python
from accompy import print_diagnostic_report
print_diagnostic_report()
```

You should see:
```
✓ fluidsynth: available
✓ soundfont: available
✓ midiutil: available
✓ mingus: available
```

## Verification Tools

accompy provides several tools to check your setup:

### Quick Check

```python
from accompy import check_dependencies

deps = check_dependencies()
print(deps)
# {'mma': False, 'fluidsynth': True, 'soundfont': True, 'midiutil': True, 'mingus': True}
```

### Detailed Diagnostic

```python
from accompy import print_diagnostic_report
print_diagnostic_report()
```

Shows:
- System information
- All dependencies with ✓/✗ status
- Specific issues found
- Solutions for each issue

### Find Specific Issues

```python
from accompy import diagnose_issues

for issue, description, solution in diagnose_issues():
    print(f"Issue: {issue}")
    print(f"Fix: {solution}\n")
```

### Check SoundFont Specifically

```python
from accompy.accompy import _default_soundfont_path

sf_path = _default_soundfont_path()
if sf_path:
    size_mb = sf_path.stat().st_size / (1024 * 1024)
    print(f"SoundFont: {sf_path} ({size_mb:.1f} MB)")
else:
    print("No SoundFont found")
```

## Common Setup Issues

### Issue: "No SoundFont found"

**Quick fix:**
```python
from accompy import setup_soundfont
setup_soundfont()
```

**Manual fix:**
```bash
# Check if FluidSynth includes a bundled SoundFont
find /opt/homebrew/Cellar/fluid-synth -name "*.sf2"  # macOS
find /usr/share -name "*.sf2"  # Linux

# If found, create symlink
ln -s /path/to/found/soundfont.sf2 ~/.fluidsynth/default_sound_font.sf2

# Otherwise, download one
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"
```

### Issue: "FluidSynth not found"

**macOS:**
```bash
brew install fluid-synth
```

**Ubuntu/Debian:**
```bash
sudo apt-get install fluidsynth
```

**Verify:**
```bash
which fluidsynth
# Should show path like /usr/local/bin/fluidsynth or /opt/homebrew/bin/fluidsynth
```

### Issue: SoundFont file is corrupted (255 bytes)

This happens when a download URL redirects to an error page.

**Fix:**
```bash
# Remove corrupted file
rm ~/.fluidsynth/default_sound_font.sf2

# Re-download from reliable source
curl -L -o ~/.fluidsynth/default_sound_font.sf2 \
  "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2"

# Verify file size (should be 30+ MB)
ls -lh ~/.fluidsynth/default_sound_font.sf2
```

### Issue: Import warning about missing dependencies

If you see a warning when importing accompy:

```
UserWarning: accompy setup incomplete - missing: soundfont, midiutil
```

**Option 1: Run automated setup**
```python
from accompy import verify_and_setup
verify_and_setup()
```

**Option 2: Fix manually**
Install the missing dependencies, then verify:
```python
from accompy import print_diagnostic_report
print_diagnostic_report()
```

**Option 3: Disable warning temporarily**
```bash
export ACCOMPY_SKIP_SETUP_CHECK=1
```

Or in Python:
```python
import os
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"
from accompy import generate_accompaniment
```

## Advanced Setup

### Custom SoundFont Location

You can specify a custom SoundFont when generating audio:

```python
from accompy import generate_accompaniment, AccompanimentConfig

config = AccompanimentConfig(
    soundfont="/path/to/your/custom.sf2",
    style="swing",
    tempo=120
)

audio = generate_accompaniment("| C | Am | F | G |", config=config)
```

### Environment Variables

- `ACCOMPY_SKIP_SETUP_CHECK=1` - Disable import-time setup verification
- `ACCOMPY_SOUNDFONT=/path/to/file.sf2` - Override default SoundFont path (future)

### Installing MMA (Optional)

MMA (Musical MIDI Accompaniment) provides professional-quality backing tracks with realistic variations and fills.

```bash
# Clone repository
git clone https://github.com/infojunkie/mma
cd mma

# Install
python install.py

# Verify
mma --version
```

Once installed, accompy will automatically use MMA when available for better quality output.

## Testing Your Setup

After setup, test that everything works:

```python
from accompy import generate_accompaniment

# Generate a simple test track
audio = generate_accompaniment(
    "| C | Am | F | G |",
    style="bossa",
    tempo=120,
    output_path="/tmp/test.wav"
)

print(f"Generated: {audio}")
# Should create a WAV file at /tmp/test.wav
```

If this works without errors, you're all set!

## Getting Help

If you're still having issues after following this guide:

1. **Run diagnostic and save output:**
   ```bash
   python -c "from accompy import print_diagnostic_report; print_diagnostic_report()" > diagnostic.txt
   ```

2. **Check the troubleshooting section** in README.md

3. **Search existing issues:** https://github.com/yourname/accompy/issues

4. **Create a new issue** with:
   - Your diagnostic report
   - Operating system and version
   - What you tried
   - Full error message

## Next Steps

Once setup is complete:

1. Read the [README.md](README.md) for usage examples
2. Try the examples in `notebooks/005_temp.ipynb`
3. Explore different styles and tempos
4. Check out the [API Reference](README.md#api-reference) for advanced features
