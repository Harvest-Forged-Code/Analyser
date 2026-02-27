"""First-launch data seeding for the standalone desktop app.

When Budget Analyser runs as a PyInstaller-frozen binary, user data lives
in the OS app data directory.  This module copies bundled seed files there
on the very first launch, then stays out of the way on subsequent launches.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

_log = logging.getLogger(__name__)


def _bundle_data_dir() -> Path | None:
    """Return the bundled seed data directory, or None in dev mode.

    Returns:
        Path to ``data/`` inside the PyInstaller ``_MEIPASS`` directory,
        or ``None`` when running from source (not frozen).
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "data"  # type: ignore[attr-defined]
    return None


def seed_data_directory(data_dir: Path) -> None:
    """Copy bundled seed files to *data_dir* on first launch.

    Only runs when the app is frozen (PyInstaller).  Existing user files
    are never overwritten.

    Args:
        data_dir: The OS app data directory (``BUDGET_ANALYSER_DATA_DIR``).
    """
    bundle = _bundle_data_dir()
    if bundle is None:
        _log.debug("Dev mode — skipping data seeding")
        return

    data_dir.mkdir(parents=True, exist_ok=True)

    for subdir in ("mappers", "config"):
        src = bundle / subdir
        dst = data_dir / subdir
        if not dst.exists() and src.exists():
            shutil.copytree(src, dst)
            _log.info("Seeded %s from bundle", dst)

    for subdir in ("statements", "logs"):
        (data_dir / subdir).mkdir(exist_ok=True)
