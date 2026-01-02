#!/usr/bin/env python
"""
Test script to verify accompy setup and functionality.

This script tests:
1. Dependency checking
2. Diagnostic reporting
3. Setup utilities
"""

import os
import sys

# Suppress the import warning for this test
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"


def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Imports ===")
    try:
        from accompy import (
            generate_accompaniment,
            check_dependencies,
            print_setup_instructions,
            verify_and_setup,
            setup_soundfont,
            diagnose_issues,
            print_diagnostic_report,
        )
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_dependency_check():
    """Test dependency checking functions."""
    print("\n=== Testing Dependency Check ===")
    try:
        from accompy import check_dependencies

        deps = check_dependencies()
        print(f"Dependencies found: {deps}")

        critical_deps = ["fluidsynth", "soundfont"]
        critical_ok = all(deps.get(dep, False) for dep in critical_deps)

        if critical_ok:
            print("✓ Critical dependencies available")
        else:
            print("⚠️  Some critical dependencies missing")

        return True
    except Exception as e:
        print(f"✗ Dependency check failed: {e}")
        return False


def test_diagnostic():
    """Test diagnostic functions."""
    print("\n=== Testing Diagnostics ===")
    try:
        from accompy import diagnose_issues

        issues = diagnose_issues()
        print(f"Found {len(issues)} issues")

        for i, (issue, desc, solution) in enumerate(issues[:3], 1):  # Show max 3
            print(f"\n{i}. {issue}")
            print(f"   {desc}")
            print(f"   Solution: {solution[:80]}...")

        print("✓ Diagnostic functions working")
        return True
    except Exception as e:
        print(f"✗ Diagnostic failed: {e}")
        return False


def test_soundfont_check():
    """Test SoundFont file detection."""
    print("\n=== Testing SoundFont Detection ===")
    try:
        from accompy.accompy import _default_soundfont_path

        sf_path = _default_soundfont_path()
        if sf_path:
            size_mb = sf_path.stat().st_size / (1024 * 1024)
            print(f"✓ SoundFont found: {sf_path} ({size_mb:.1f} MB)")
            return True
        else:
            print("✗ No SoundFont found")
            return False
    except Exception as e:
        print(f"✗ SoundFont check failed: {e}")
        return False


def test_setup_utils():
    """Test setup utility functions (non-interactive)."""
    print("\n=== Testing Setup Utils ===")
    try:
        from accompy.setup_utils import _find_bundled_soundfont

        bundled = _find_bundled_soundfont()
        if bundled:
            print(f"✓ Found bundled SoundFont: {bundled}")
        else:
            print("⚠️  No bundled SoundFont found (OK if manually configured)")

        print("✓ Setup utilities working")
        return True
    except Exception as e:
        print(f"✗ Setup utils failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("accompy Setup Test Suite")
    print("=" * 60)

    tests = [
        test_imports,
        test_dependency_check,
        test_diagnostic,
        test_soundfont_check,
        test_setup_utils,
    ]

    results = [test() for test in tests]

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Passed: {sum(results)}/{len(results)}")

    if all(results):
        print("\n✓ All tests passed! accompy setup is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Run diagnostic for details:")
        print("   python -c \"from accompy import print_diagnostic_report; print_diagnostic_report()\"")
        return 1


if __name__ == "__main__":
    sys.exit(main())
