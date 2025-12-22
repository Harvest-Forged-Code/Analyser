"""Application version management.

Provides version information and utilities for the Budget Analyser application.
Version is read from package metadata (pyproject.toml) at runtime.
"""

from __future__ import annotations

from importlib.metadata import version as _get_pkg_version
from importlib.metadata import PackageNotFoundError
from pathlib import Path

# Application metadata
APP_NAME = "Budget Analyser"
APP_IDENTIFIER = "com.budgetanalyser.app"


def get_version() -> str:
    """Get the current application version.

    Reads version from package metadata. Falls back to pyproject.toml
    parsing if package is not installed (development mode).

    Returns:
        Version string in Major.Minor.Patch format (e.g., "1.0.0").
    """
    try:
        # Try to get version from installed package metadata
        return _get_pkg_version("budget-analyser")
    except PackageNotFoundError:
        # Fallback: parse pyproject.toml directly (development mode)
        return _read_version_from_pyproject()


def _read_version_from_pyproject() -> str:
    """Read version directly from pyproject.toml file.

    Used as fallback when package is not installed.

    Returns:
        Version string or "0.0.0" if not found.
    """
    try:
        # Navigate from this file to project root
        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():
            # Try alternative path (when running from src)
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text()
            for line in content.split("\n"):
                if line.strip().startswith("version"):
                    # Parse: version = "1.0.0"
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        version_str = parts[1].strip().strip('"').strip("'")
                        return version_str
    except OSError:
        pass
    return "0.0.0"


def get_eng_ver() -> int:
    """Get the engineering version flag.

    Returns:
        1 if auto-increment is enabled (production), 0 if disabled (development).
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():
            pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"

        if pyproject_path.exists():
            content = pyproject_path.read_text()
            for line in content.split("\n"):
                if "eng_ver" in line and "=" in line:
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        return int(parts[1].strip())
    except (OSError, ValueError):
        pass
    return 1  # Default to production mode


def is_dev_mode() -> bool:
    """Check if running in developer mode (EngVer:0).

    Returns:
        True if in developer mode, False otherwise.
    """
    return get_eng_ver() == 0


def get_version_tuple() -> tuple[int, int, int]:
    """Get version as a tuple of integers.

    Returns:
        Tuple of (major, minor, patch) version numbers.
    """
    version_str = get_version()
    try:
        parts = version_str.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return (0, 0, 0)


def get_full_version_string() -> str:
    """Get full version string with app name.

    Returns:
        String like "Budget Analyser v1.0.0".
    """
    return f"{APP_NAME} v{get_version()}"


# Module-level version for easy access
__version__ = get_version()
