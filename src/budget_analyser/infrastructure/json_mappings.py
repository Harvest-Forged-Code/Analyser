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

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Load mapping from description keywords to sub-category labels."""
        return _load_json(self.description_to_sub_category_path)

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Load mapping from sub-category keywords to category labels."""
        return _load_json(self.sub_category_to_category_path)
