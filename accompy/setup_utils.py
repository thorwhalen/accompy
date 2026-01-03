"""
Setup and configuration utilities for accompy.

This module provides automatic setup, verification, and troubleshooting
tools to help users get accompy configured correctly.
"""

import subprocess
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, List, Tuple


def verify_and_setup(interactive: bool = True, auto_fix: bool = False) -> Dict[str, bool]:
    """
    Verify all dependencies and optionally auto-configure.

    Args:
        interactive: If True, prompt user for permission before making changes
        auto_fix: If True and interactive=False, automatically fix issues without prompting

    Returns:
        Dict mapping dependency name to whether it's available

    Example:
        >>> from accompy.setup_utils import verify_and_setup
        >>> status = verify_and_setup(interactive=False)
        >>> if all(status.values()):
        ...     print("Ready to use!")
    """
    from .accompy import check_dependencies

    deps = check_dependencies()

    if all(deps.values()):
        return deps

    # Try to fix missing dependencies
    if not deps["fluidsynth"]:
        if interactive:
            print("\n⚠️  FluidSynth not found (required for audio rendering)")
            if _prompt_yes_no("Would you like to install FluidSynth now?"):
                deps["fluidsynth"] = _install_fluidsynth()
        elif auto_fix:
            deps["fluidsynth"] = _install_fluidsynth()

    if deps["fluidsynth"] and not deps["soundfont"]:
        if interactive:
            print("\n⚠️  SoundFont file not found (required for instrument sounds)")
            if _prompt_yes_no("Would you like to download and configure a SoundFont now?"):
                deps["soundfont"] = _setup_soundfont()
        elif auto_fix:
            deps["soundfont"] = _setup_soundfont()

    if not deps["midiutil"]:
        if interactive:
            print("\n⚠️  midiutil not found (required for MIDI generation)")
            if _prompt_yes_no("Would you like to install midiutil now?"):
                deps["midiutil"] = _install_python_package("midiutil")
        elif auto_fix:
            deps["midiutil"] = _install_python_package("midiutil")

    return deps


def diagnose_issues() -> List[Tuple[str, str, str]]:
    """
    Diagnose common setup issues and provide solutions.

    Returns:
        List of (issue, description, solution) tuples

    Example::

        from accompy.setup_utils import diagnose_issues
        for issue, desc, solution in diagnose_issues():
            print(f"{issue}: {desc}")
            print(f"Solution: {solution}")
    """
    from .accompy import check_dependencies, _default_soundfont_path, _fluidsynth_available

    issues = []
    deps = check_dependencies()

    # Check FluidSynth
    if not deps["fluidsynth"]:
        issues.append((
            "FluidSynth not installed",
            "FluidSynth is required to render MIDI files to audio",
            _get_fluidsynth_install_command()
        ))

    # Check SoundFont
    if not deps["soundfont"]:
        sf_path = _default_soundfont_path()
        issues.append((
            "SoundFont file not found",
            f"Checked: {Path.home() / '.fluidsynth' / 'default_sound_font.sf2'}",
            "Run: python -c \"from accompy.setup_utils import setup_soundfont; setup_soundfont()\""
        ))

    # Check FluidSynth version compatibility
    if deps["fluidsynth"]:
        version_issue = _check_fluidsynth_version()
        if version_issue:
            issues.append(version_issue)

    # Check SoundFont file validity
    if deps["soundfont"]:
        sf_path = _default_soundfont_path()
        if sf_path and sf_path.exists():
            if sf_path.stat().st_size < 1000:  # Less than 1KB is suspicious
                issues.append((
                    "SoundFont file appears corrupted",
                    f"File at {sf_path} is only {sf_path.stat().st_size} bytes",
                    "Delete the file and run setup again to download a valid SoundFont"
                ))

    # Check Python dependencies
    if not deps["midiutil"]:
        issues.append((
            "midiutil not installed",
            "midiutil is required for MIDI file generation",
            f"{sys.executable} -m pip install midiutil"
        ))

    if not deps["mingus"]:
        issues.append((
            "mingus not installed (optional)",
            "mingus provides better chord parsing and music theory support",
            f"{sys.executable} -m pip install mingus"
        ))

    return issues


def setup_soundfont(force: bool = False) -> bool:
    """
    Download and configure a SoundFont file.

    Args:
        force: If True, download even if a SoundFont already exists

    Returns:
        True if successful, False otherwise

    Example::

        from accompy.setup_utils import setup_soundfont
        if setup_soundfont():
            print("SoundFont configured successfully!")
    """
    from .accompy import _default_soundfont_path

    target_path = Path.home() / ".fluidsynth" / "default_sound_font.sf2"

    # Check if already exists
    if target_path.exists() and not force:
        if target_path.stat().st_size > 1000:  # At least 1KB
            print(f"✓ SoundFont already exists at {target_path}")
            return True
        else:
            print(f"⚠️  Existing SoundFont appears corrupted, will re-download")

    # Check if FluidSynth installation includes a SoundFont
    bundled_sf = _find_bundled_soundfont()
    if bundled_sf:
        print(f"Found bundled SoundFont: {bundled_sf}")
        return _link_soundfont(bundled_sf, target_path)

    # Download SoundFont
    print("Downloading SoundFont file...")
    return _download_soundfont(target_path)


def _find_bundled_soundfont() -> Optional[Path]:
    """Find SoundFont files bundled with FluidSynth installation."""
    search_paths = [
        Path("/opt/homebrew/Cellar/fluid-synth"),
        Path("/usr/local/Cellar/fluid-synth"),
        Path("/usr/share/sounds/sf2"),
        Path("/usr/share/soundfonts"),
    ]

    for base_path in search_paths:
        if not base_path.exists():
            continue

        # Search recursively for .sf2 files
        for sf_file in base_path.rglob("*.sf2"):
            # Skip obviously corrupt files
            if sf_file.stat().st_size < 1000:
                continue
            # Prefer files with "vintage", "dreams", "fluid" or "GM" in name
            name_lower = sf_file.name.lower()
            if any(keyword in name_lower for keyword in ["vintage", "dreams", "fluid", "gm"]):
                return sf_file

        # If no preferred file found, return any valid .sf2 file
        for sf_file in base_path.rglob("*.sf2"):
            if sf_file.stat().st_size > 1000:
                return sf_file

    return None


def _link_soundfont(source: Path, target: Path) -> bool:
    """Create a symlink to a SoundFont file."""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)

        # Remove existing file/link if it exists
        if target.exists() or target.is_symlink():
            target.unlink()

        # Create symlink
        target.symlink_to(source)

        print(f"✓ Linked SoundFont: {target} -> {source}")
        return True
    except Exception as e:
        print(f"✗ Failed to link SoundFont: {e}")
        return False


def _download_soundfont(target_path: Path, soundfont: str = "auto") -> bool:
    """
    Download a SoundFont file from the internet.

    Args:
        target_path: Where to save the soundfont
        soundfont: Which soundfont to download. Options:
            - "auto": Try multiple sources in order
            - "generaluser": GeneralUser GS (30MB, good quality, balanced)
            - "musescore": MuseScore General (35MB, good all-around)
            - Custom URL starting with http:// or https://

    Returns:
        True if successful, False otherwise
    """
    # Define available soundfonts with metadata
    soundfonts = {
        "generaluser": {
            "url": "https://schristiancollins.com/soundfonts/GeneralUser_GS_1.471.zip",
            "name": "GeneralUser GS v1.471",
            "size": "~30MB",
            "license": "GeneralUser GS License v2.0 (free for commercial use)",
            "description": "Excellent all-around soundfont with good bass and drums",
        },
        "musescore": {
            "url": "https://ftp.osuosl.org/pub/musescore/soundfont/MuseScore_General/MuseScore_General.sf2",
            "name": "MuseScore General",
            "size": "~35MB",
            "license": "MIT/public domain",
            "description": "MuseScore's default soundfont, good quality",
        },
    }

    # Determine which soundfonts to try
    if soundfont == "auto":
        urls_to_try = [
            ("generaluser", soundfonts["generaluser"]),
            ("musescore", soundfonts["musescore"]),
        ]
    elif soundfont.startswith(("http://", "https://")):
        urls_to_try = [("custom", {"url": soundfont, "name": "Custom SoundFont"})]
    elif soundfont in soundfonts:
        urls_to_try = [(soundfont, soundfonts[soundfont])]
    else:
        print(f"✗ Unknown soundfont: {soundfont}")
        print(f"Available options: {', '.join(soundfonts.keys())}")
        return False

    target_path.parent.mkdir(parents=True, exist_ok=True)

    for sf_key, sf_info in urls_to_try:
        try:
            url = sf_info["url"]
            name = sf_info["name"]
            print(f"\nAttempting to download {name}...")
            if "description" in sf_info:
                print(f"  {sf_info['description']}")

            # Check if it's a zip file
            is_zip = url.endswith(".zip")
            download_path = target_path.with_suffix(".zip") if is_zip else target_path

            # Try using curl (more likely to be available than wget)
            result = subprocess.run(
                ["curl", "-L", "-o", str(download_path), url],
                capture_output=True,
                timeout=600  # 10 minute timeout for larger files
            )

            if result.returncode == 0 and download_path.exists():
                # Handle zip files
                if is_zip:
                    print(f"  Extracting zip file...")
                    try:
                        import zipfile
                        with zipfile.ZipFile(download_path, 'r') as zip_ref:
                            # Find .sf2 file in zip
                            sf2_files = [f for f in zip_ref.namelist() if f.endswith('.sf2')]
                            if sf2_files:
                                # Extract first .sf2 file
                                zip_ref.extract(sf2_files[0], target_path.parent)
                                extracted_path = target_path.parent / sf2_files[0]
                                extracted_path.rename(target_path)
                                download_path.unlink()  # Remove zip
                            else:
                                print(f"✗ No .sf2 file found in zip")
                                download_path.unlink()
                                continue
                    except Exception as e:
                        print(f"✗ Failed to extract zip: {e}")
                        download_path.unlink()
                        continue

                # Verify file size
                if target_path.stat().st_size > 1000000:  # At least 1MB
                    print(f"✓ Downloaded {name} to {target_path}")
                    print(f"  Size: {target_path.stat().st_size / 1024 / 1024:.1f}MB")
                    return True
                else:
                    print(f"✗ Downloaded file is too small (corrupt?)")
                    target_path.unlink()

        except subprocess.TimeoutExpired:
            print(f"✗ Download timed out")
        except Exception as e:
            print(f"✗ Download failed: {e}")

    print("\n⚠️  Automatic download failed. Please manually download a SoundFont:")
    print("\nRecommended soundfonts (copyright-free, high quality):")
    print("\n1. GeneralUser GS (recommended for jazz/accompaniment):")
    print("   Download: https://schristiancollins.com/generaluser.php")
    print("   License: Free for commercial use")
    print("   Quality: Excellent bass and drums\n")
    print("2. Musyng Kite (larger, very high quality):")
    print("   Download: https://www.polyphone.io/en/soundfonts/instrument-sets/258-musyng-kite")
    print("   License: CC-BY-SA 3.0 (free, attribution required)")
    print("   Size: 339MB compressed / 990MB uncompressed\n")
    print("3. More options:")
    print("   Browse: https://musical-artifacts.com/artifacts?formats=sf2")
    print("\nAfter downloading, save as: ~/.fluidsynth/default_sound_font.sf2")
    return False


def _install_fluidsynth() -> bool:
    """Install FluidSynth using system package manager."""
    system = platform.system().lower()

    try:
        if system == "darwin":  # macOS
            print("Installing FluidSynth via Homebrew...")
            result = subprocess.run(
                ["brew", "install", "fluid-synth"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ FluidSynth installed successfully")
                return True
            else:
                print(f"✗ Installation failed: {result.stderr}")
                return False

        elif system == "linux":
            print("Installing FluidSynth via apt...")
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", "fluidsynth"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ FluidSynth installed successfully")
                return True
            else:
                print(f"✗ Installation failed: {result.stderr}")
                return False
        else:
            print(f"⚠️  Automatic installation not supported on {system}")
            print("Please install FluidSynth manually:")
            print("  Windows: https://github.com/FluidSynth/fluidsynth/releases")
            return False

    except FileNotFoundError as e:
        print(f"✗ Package manager not found: {e}")
        print(f"Please install FluidSynth manually: {_get_fluidsynth_install_command()}")
        return False


def _install_python_package(package_name: str) -> bool:
    """Install a Python package using pip."""
    try:
        print(f"Installing {package_name}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ {package_name} installed successfully")
            return True
        else:
            print(f"✗ Installation failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Installation failed: {e}")
        return False


def _get_fluidsynth_install_command() -> str:
    """Get the appropriate FluidSynth installation command for this system."""
    system = platform.system().lower()

    if system == "darwin":
        return "brew install fluid-synth"
    elif system == "linux":
        return "sudo apt-get install fluidsynth"
    elif system == "windows":
        return "Download from https://github.com/FluidSynth/fluidsynth/releases"
    else:
        return "See https://www.fluidsynth.org/ for installation instructions"


def _check_fluidsynth_version() -> Optional[Tuple[str, str, str]]:
    """Check if FluidSynth version is compatible."""
    try:
        result = subprocess.run(
            ["fluidsynth", "--version"],
            capture_output=True,
            text=True
        )
        # Version check could be added here if needed
        return None
    except Exception:
        return None


def _prompt_yes_no(question: str, default: bool = True) -> bool:
    """Prompt user for yes/no answer."""
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        response = input(f"{question} {suffix}: ").strip().lower()
        if not response:
            return default
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False
        print("Please answer 'y' or 'n'")


def print_diagnostic_report():
    """Print a comprehensive diagnostic report."""
    from .accompy import check_dependencies

    print("=" * 60)
    print("accompy Diagnostic Report")
    print("=" * 60)

    # System info
    print(f"\nSystem: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")

    # Dependency status
    print("\n--- Dependency Status ---")
    deps = check_dependencies()
    for dep, available in deps.items():
        status = "✓" if available else "✗"
        print(f"{status} {dep}: {'available' if available else 'MISSING'}")

    # Issues
    issues = diagnose_issues()
    if issues:
        print("\n--- Issues Found ---")
        for i, (issue, desc, solution) in enumerate(issues, 1):
            print(f"\n{i}. {issue}")
            print(f"   Description: {desc}")
            print(f"   Solution: {solution}")
    else:
        print("\n✓ No issues found - all dependencies are properly configured!")

    print("\n" + "=" * 60)
