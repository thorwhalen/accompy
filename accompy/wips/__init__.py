"""
Backward-compatibility shim — wips modules have moved to accompy top level.

Import from ``accompy.converters``, ``accompy.chord_parsers``, etc. instead.
"""

import warnings as _warnings

_warnings.warn(
    "accompy.wips is deprecated. Import from accompy directly "
    "(e.g., accompy.converters, accompy.pipeline).",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export so existing imports don't break immediately
from accompy.converters import *  # noqa: F401,F403
from accompy.converters import converter, convert  # noqa: F401
