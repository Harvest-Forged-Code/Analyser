from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from budget_analyser.domain.errors import DataSourceError
from budget_analyser.domain.protocols import CategoryMappingProvider


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise DataSourceError(f"JSON mapping file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class JsonCategoryMappingProvider(CategoryMappingProvider):
    description_to_sub_category_path: Path
    sub_category_to_category_path: Path

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        return _load_json(self.description_to_sub_category_path)

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        return _load_json(self.sub_category_to_category_path)
