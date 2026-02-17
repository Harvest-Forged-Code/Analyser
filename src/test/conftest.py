from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    # src/test/ lives inside src/, so parent is src/ itself
    src_path = Path(__file__).resolve().parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
