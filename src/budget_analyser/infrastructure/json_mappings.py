"""JSON mapping providers (infrastructure).

Purpose:
    Load keyword mappings used for transaction categorization.

Goal:
    Keep JSON parsing and filesystem access out of domain/presentation layers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import logging
from budget_analyser.domain.errors import DataSourceError
from budget_analyser.domain.protocols import CategoryMappingProvider


def _load_json(path: Path) -> dict:
    """Load JSON content from a file.

    Args:
        path: Filesystem path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        DataSourceError: If the file does not exist.
    """
    # Validate file existence before reading.
    if not path.exists():
        raise DataSourceError(f"JSON mapping file not found: {path}")
    # Read and parse.
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class JsonCategoryMappingProvider(CategoryMappingProvider):
    """JSON-backed category mapping provider."""

    description_to_sub_category_path: Path
    sub_category_to_category_path: Path
    logger: logging.Logger | None = None

    def _log(self, level: int, msg: str, *args) -> None:
        log = self.logger or logging.getLogger("budget_analyser.gui")
        try:
            log.log(level, msg, *args)
        except Exception:
            pass

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Load mapping from description keywords to sub-category labels."""
        path = self.description_to_sub_category_path
        mapping = _load_json(path)
        try:
            size = len(mapping or {})
            self._log(
                logging.DEBUG,
                "Loaded description->sub_category mapping: path=%s keys=%d",
                str(path),
                size,
            )
            if size == 0:
                self._log(logging.WARNING, "Mapping file is empty: %s", str(path))
        except Exception:
            pass
        return mapping

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Load mapping from sub-category keywords to category labels."""
        path = self.sub_category_to_category_path
        mapping = _load_json(path)
        try:
            size = len(mapping or {})
            self._log(
                logging.DEBUG,
                "Loaded sub_category->category mapping: path=%s keys=%d",
                str(path),
                size,
            )
            if size == 0:
                self._log(logging.WARNING, "Mapping file is empty: %s", str(path))
        except Exception:
            pass
        return mapping
