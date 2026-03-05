"""Root conftest — collection-level ignores for doctest-modules."""

import os

# Disable setup check during CI/tests
os.environ["ACCOMPY_SKIP_SETUP_CHECK"] = "1"

# accompy/accompy.py: imports tonal which requires config2py (optional dep)
# accompy/patterns.py: name clashes with accompy/patterns/ package directory
collect_ignore_glob = [
    "accompy/accompy.py",
    "accompy/patterns.py",
]
