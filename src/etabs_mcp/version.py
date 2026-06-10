"""
Version comparison utilities for ETABS MCP.

Public API
----------
``MINIMUM_SUPPORTED_VERSION``
    Lowest ETABS version fully supported without behavioral caveats.

``check_version_warning(version_str) -> str | None``
    Return a warning message if *version_str* is below the minimum, else ``None``.
"""

from __future__ import annotations

from packaging.version import InvalidVersion, Version

SERVER_VERSION = "1.0.0"
MINIMUM_SUPPORTED_VERSION = Version("21.0.0")


def check_version_warning(version_str: str) -> str | None:
    """Return a warning string if *version_str* is below the minimum, else ``None``."""
    try:
        v = Version(version_str)
    except InvalidVersion:
        return f"Unable to parse version '{version_str}'. Minimum supported is {MINIMUM_SUPPORTED_VERSION}."
    if v < MINIMUM_SUPPORTED_VERSION:
        return (
            f"ETABS version {v} is below minimum supported {MINIMUM_SUPPORTED_VERSION}. "
            f"Some results may be inaccurate due to known bugs in older releases."
        )
    return None
