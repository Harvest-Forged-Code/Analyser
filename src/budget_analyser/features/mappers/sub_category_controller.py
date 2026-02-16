"""Sub-category mapper controller.

Manages sub-category assignments within categories.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from budget_analyser.core.errors import DataSourceError
from budget_analyser.infrastructure.json_mappings import (
    JsonCategoryMappingStore,
)


def _dedup_keep_order(items: Iterable[str]) -> list[str]:
    """Deduplicate while preserving order."""
    seen: set[str] = set()
    out: list[str] = []
    for raw in items:
        val = str(raw).strip()
        if not val:
            continue
        key = val.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(val)
    return out


class SubCategoryMapperController:
    """Controller to manage sub-category assignments.

    Keeps an in-memory copy and persists via
    ``JsonCategoryMappingStore``.
    """

    def __init__(
        self,
        store: JsonCategoryMappingStore,
        logger: logging.Logger,
    ) -> None:
        self._store = store
        self._logger = logger
        self._mapping: dict[str, list[str]] = {}
        self.reload()

    def categories(self) -> list[str]:
        """Return list of category names."""
        return list(self._mapping.keys())

    def sub_categories(self, category: str) -> list[str]:
        """Return sub-categories for a category."""
        return list(self._mapping.get(category, []))

    def mapping(self) -> dict[str, list[str]]:
        """Return full category to sub-category mapping."""
        return {
            cat: list(subs)
            for cat, subs in self._mapping.items()
        }

    def add_sub_category(
        self,
        sub_category: str,
        category: str,
    ) -> None:
        """Add a sub-category to a category.

        Args:
            sub_category: Sub-category name.
            category: Parent category name.

        Raises:
            ValueError: If names are empty.
        """
        sub = (sub_category or "").strip()
        if not sub:
            raise ValueError("Sub-category name is required")
        cat = (category or "").strip()
        if not cat:
            raise ValueError("Category name is required")

        for k, subs in self._mapping.items():
            if k.lower() == cat.lower():
                continue
            self._mapping[k] = [
                s for s in subs if s.lower() != sub.lower()
            ]

        target_list = self._mapping.setdefault(cat, [])
        if sub.lower() not in {s.lower() for s in target_list}:
            target_list.append(sub)

    def move_sub_categories(
        self,
        sub_categories: Iterable[str],
        source: str,
        target: str,
    ) -> None:
        """Move sub-categories between categories.

        Args:
            sub_categories: Sub-categories to move.
            source: Source category.
            target: Target category.
        """
        src = (source or "").strip()
        tgt = (target or "").strip()
        if not src or not tgt or src == tgt:
            return

        move_set = {
            str(s).strip().lower()
            for s in sub_categories if str(s).strip()
        }
        if not move_set:
            return

        self._mapping.setdefault(src, [])
        self._mapping.setdefault(tgt, [])

        self._mapping[src] = [
            s for s in self._mapping[src]
            if s.lower() not in move_set
        ]

        combined = (
            list(self._mapping[tgt])
            + [s for s in sub_categories if str(s).strip()]
        )
        self._mapping[tgt] = _dedup_keep_order(combined)

    def set_mapping(
        self,
        mapping: dict[str, Iterable[str]],
    ) -> None:
        """Replace the entire mapping.

        Args:
            mapping: New category to sub-category mapping.
        """
        normalized: dict[str, list[str]] = {}
        for cat, subs in (mapping or {}).items():
            c = str(cat).strip()
            if not c:
                continue
            normalized[c] = _dedup_keep_order(subs)
        self._mapping = normalized

    def save(self) -> None:
        """Persist current mapping to JSON file."""
        self._store.save_sub_to_cat(self._mapping)
        self._logger.info(
            "Sub-category mapping saved: categories=%d",
            len(self._mapping),
        )

    def reload(self) -> None:
        """Reload mapping from JSON file."""
        try:
            mapping = self._store.load_sub_to_cat()
        except DataSourceError:
            mapping = {}
        self.set_mapping(mapping)
        self._mapping = self._mapping or {}
