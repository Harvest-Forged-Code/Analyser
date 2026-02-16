"""Shared database utilities.

Provides a connection factory used by all feature repositories that share
the same SQLite database file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a new SQLite connection with row-factory enabled.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn
