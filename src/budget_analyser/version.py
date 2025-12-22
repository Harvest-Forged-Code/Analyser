"""Application version management.

Provides version information and utilities for the Budget Analyser application.
Version is read from Git tags at runtime, with fallback to package metadata,
bundled VERSION file (for PyInstaller builds), or pyproject.toml.
"""

from __future__ import annotations

import sys
import subprocess
from importlib.metadata import version as _get_pkg_version
from importlib.metadata import PackageNotFoundError
from pathlib import Path

# Application metadata
APP_NAME = "Budget Analyser"
APP_IDENTIFIER = "com.budgetanalyser.app"


def _is_frozen() -> bool:
    """Check if running as a PyInstaller frozen executable."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def _get_bundle_dir() -> Path:
    """Get the directory where bundled files are located.

    For frozen apps, this is sys._MEIPASS (PyInstaller temp directory).
    For normal execution, this is the package directory.
    """
    if _is_frozen():
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).parent


def _read_version_from_bundle() -> str | None:
    """Read version from bundled VERSION file (PyInstaller builds).

    Returns:
        Version string or None if VERSION file not found.
    """
    try:
        bundle_dir = _get_bundle_dir()
        version_file = bundle_dir / "VERSION"
        if version_file.exists():
            return version_file.read_text().strip()
    except OSError:
        pass
    return None


def get_version() -> str:
    """Get the current application version.

    Priority order:
    1. Bundled VERSION file (for PyInstaller frozen builds)
    2. Git tag (when running from git repo)
    3. Package metadata (when installed as package)
    4. pyproject.toml (development fallback)

    Returns:
        Version string in Major.Minor.Patch format (e.g., "1.0.0").
    """
    # For frozen apps, read from bundled VERSION file first
    if _is_frozen():
        bundled_version = _read_version_from_bundle()
        if bundled_version:
            return bundled_version

    # Try Git tag (works in development with git repo)
    git_version = _read_version_from_git()
    if git_version:
        return git_version

    # Try package metadata (works when installed)
    try:
        return _get_pkg_version("budget-analyser")
    except PackageNotFoundError:
        pass

    # Fallback: parse pyproject.toml directly
    return _read_version_from_pyproject()


def _read_version_from_git() -> str | None:
    """Read version from the latest Git tag.

    Returns:
        Version string without 'v' prefix, or None if not in a git repo
        or no tags exist.
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        tag = result.stdout.strip()
        # Remove 'v' prefix if present
        return tag.lstrip("v") if tag else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None


def _read_version_from_pyproject() -> str:
    """Read version directly from pyproject.toml file.

    Used as fallback when package is not installed and not in git repo.

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
