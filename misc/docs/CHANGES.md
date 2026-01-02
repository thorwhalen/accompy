# Changes: Setup and User Experience Improvements

## Summary

Enhanced accompy with automated setup, comprehensive diagnostics, and user-friendly troubleshooting to make it easier for new users to get started.

## New Features

### 1. Automated Setup System (`setup_utils.py`)

**New module:** `accompy/setup_utils.py`

Provides automated setup and configuration with user-friendly helpers:

- `verify_and_setup(interactive=True, auto_fix=False)` - Interactive setup wizard
  - Checks all dependencies
  - Prompts user before making changes
  - Installs FluidSynth (macOS/Linux)
  - Downloads and configures SoundFont files
  - Installs Python packages

- `setup_soundfont(force=False)` - SoundFont configuration
  - Finds bundled SoundFonts (Homebrew installations)
  - Downloads SoundFont if needed
  - Creates proper symlinks
  - Validates file integrity

- `diagnose_issues()` - Comprehensive diagnostic
  - Returns list of (issue, description, solution) tuples
  - Specific actionable solutions for each problem
  - Checks file integrity (e.g., corrupted SoundFont detection)

- `print_diagnostic_report()` - User-friendly diagnostic output
  - System information
  - Dependency status with ✓/✗ indicators
  - Detailed issue descriptions and solutions

### 2. Import-Time Verification

**Modified:** `accompy/accompy.py`

Added automatic setup verification on import:

- Checks critical dependencies (FluidSynth, SoundFont, midiutil) when module is imported
- Shows helpful warning if setup is incomplete
- Provides clear instructions on how to fix issues
- Can be disabled with `ACCOMPY_SKIP_SETUP_CHECK=1` environment variable

### 3. Enhanced Documentation

**Updated:** `README.md`

Added comprehensive sections:

- **Automated Setup** - Step-by-step quick start
- **Troubleshooting** - Common issues with specific solutions:
  - "No SoundFont found" error
  - "FluidSynth not found" error
  - Corrupted SoundFont file (255 bytes issue)
  - Import warnings
  - Missing Python dependencies
- **Diagnostic Tools** - How to use diagnostic functions
- **Getting Help** - How to report issues effectively

**New:** `SETUP.md`

Complete setup guide with:
- Quick automated setup instructions
- Step-by-step manual setup
- Verification tools and how to use them
- Common setup issues and solutions
- Advanced configuration options
- Testing procedures

### 4. Updated Package Exports

**Modified:** `accompy/__init__.py`

Exported new setup utilities for easy access:
- `verify_and_setup`
- `setup_soundfont`
- `diagnose_issues`
- `print_diagnostic_report`

### 5. Test Suite

**New:** `test_setup.py`

Comprehensive test suite for setup verification:
- Tests all import paths
- Validates dependency checking
- Tests diagnostic functions
- Verifies SoundFont detection
- Tests setup utilities

### 6. Updated Examples

**Updated:** `notebooks/005_temp.ipynb`

Enhanced notebook with:
- Setup verification examples
- Diagnostic usage examples
- Quick start guide in markdown cells
- How to disable import warnings

## User Experience Improvements

### Before

Users had to:
1. Manually install FluidSynth
2. Find and download a SoundFont file
3. Figure out where to place it
4. Debug cryptic error messages
5. No clear path when things went wrong

### After

Users can now:
1. Run one command: `verify_and_setup()`
2. Follow interactive prompts
3. Get automatic SoundFont configuration
4. See clear diagnostic reports
5. Get specific, actionable solutions for every issue

## Example Usage

### Quick Start for New Users

```python
from accompy import verify_and_setup
verify_and_setup(interactive=True)
# Walks user through entire setup process
```

### Check Setup Status

```python
from accompy import check_dependencies
deps = check_dependencies()
# Returns: {'mma': False, 'fluidsynth': True, 'soundfont': True, ...}
```

### Diagnose Issues

```python
from accompy import print_diagnostic_report
print_diagnostic_report()
# Shows system info, dependency status, and specific issues with solutions
```

### Fix Specific Issues

```python
from accompy import setup_soundfont
setup_soundfont()
# Automatically finds or downloads SoundFont and configures it
```

## Technical Details

### SoundFont Detection Logic

The setup system searches for SoundFont files in this order:

1. `~/.fluidsynth/default_sound_font.sf2` (user configuration)
2. Bundled with FluidSynth installation (e.g., `/opt/homebrew/Cellar/fluid-synth/*/share/fluid-synth/sf2/*.sf2`)
3. System locations (`/usr/share/sounds/sf2/`, `/usr/share/soundfonts/`)

If no SoundFont is found, it downloads MuseScore General SoundFont (35MB, high quality).

### Import-Time Check

On import, accompy:
1. Checks critical dependencies (unless `ACCOMPY_SKIP_SETUP_CHECK=1`)
2. Shows warning with clear instructions if incomplete
3. Doesn't block import - just warns user
4. Can be disabled per-session or permanently via environment variable

### Cross-Platform Support

- **macOS**: Uses Homebrew for FluidSynth installation
- **Linux**: Uses apt-get for FluidSynth installation
- **Windows**: Provides manual instructions (no automated install)
- All platforms: Automated SoundFont download and configuration

## Files Changed/Added

**Added:**
- `accompy/setup_utils.py` - Setup automation module (360 lines)
- `SETUP.md` - Comprehensive setup guide (280 lines)
- `CHANGES.md` - This file
- `test_setup.py` - Setup test suite

**Modified:**
- `accompy/__init__.py` - Added setup utility exports
- `accompy/accompy.py` - Added import-time verification
- `README.md` - Added troubleshooting and setup sections
- `notebooks/005_temp.ipynb` - Added setup examples

## Backwards Compatibility

All changes are fully backwards compatible:

- Existing code continues to work without modification
- New setup utilities are optional - manual setup still works
- Import-time check can be disabled
- No changes to `generate_accompaniment()` API

## Future Enhancements

Potential improvements for future versions:

1. GUI setup wizard for non-technical users
2. Automatic SoundFont download selection (let user choose quality/size)
3. Better Windows support with automated installer
4. Setup configuration file (`~/.accompy/config.json`)
5. Downloadable setup script that runs outside Python
6. Integration with package managers (brew cask, apt, chocolatey)
