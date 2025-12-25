from __future__ import annotations

import logging
from typing import Dict, Iterable, List

from budget_analyser.domain.errors import DataSourceError

from budget_analyser.infrastructure.json_mappings import JsonCategoryMappingStore


def _dedup_keep_order(items: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
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
    """Controller to manage sub-category assignments within categories.

    Keeps an in-memory copy of the category -> sub-category mapping and
    persists via ``JsonCategoryMappingStore``.
    """

    def __init__(self, store: JsonCategoryMappingStore, logger: logging.Logger):
        self._store = store
        self._logger = logger
        self._mapping: Dict[str, List[str]] = {}
        self.reload()

    # ---- Queries ----
    def categories(self) -> List[str]:
        return list(self._mapping.keys())

    def sub_categories(self, category: str) -> List[str]:
        return list(self._mapping.get(category, []))

    def mapping(self) -> Dict[str, List[str]]:
        return {cat: list(subs) for cat, subs in self._mapping.items()}

    # ---- Mutations ----
    def add_sub_category(self, sub_category: str, category: str) -> None:
        sub = (sub_category or "").strip()
        if not sub:
            raise ValueError("Sub-category name is required")
        cat = (category or "").strip()
        if not cat:
            raise ValueError("Category name is required")

        # Remove from any other category to avoid duplicates across groups
        for k, subs in self._mapping.items():
            if k.lower() == cat.lower():
                continue
            self._mapping[k] = [s for s in subs if s.lower() != sub.lower()]

        target_list = self._mapping.setdefault(cat, [])
        if sub.lower() not in {s.lower() for s in target_list}:
            target_list.append(sub)

    def move_sub_categories(self, sub_categories: Iterable[str], source: str, target: str) -> None:
        src = (source or "").strip()
        tgt = (target or "").strip()
        if not src or not tgt or src == tgt:
            return

        move_set = {str(s).strip().lower() for s in sub_categories if str(s).strip()}
        if not move_set:
            return

        # Ensure categories exist
        self._mapping.setdefault(src, [])
        self._mapping.setdefault(tgt, [])

        # Remove from source
        self._mapping[src] = [s for s in self._mapping[src] if s.lower() not in move_set]

        # Add to target, deduping while preserving order
        combined = list(self._mapping[tgt]) + [s for s in sub_categories if str(s).strip()]
        self._mapping[tgt] = _dedup_keep_order(combined)

    def set_mapping(self, mapping: Dict[str, Iterable[str]]) -> None:
        normalized: Dict[str, List[str]] = {}
        for cat, subs in (mapping or {}).items():
            c = str(cat).strip()
            if not c:
                continue
            normalized[c] = _dedup_keep_order(subs)
        self._mapping = normalized

    # ---- Persistence ----
    def save(self) -> None:
        self._store.save_sub_to_cat(self._mapping)
        self._logger.info(
            "Sub-category mapping saved: categories=%d",
            len(self._mapping),
        )

    def reload(self) -> None:
        try:
            mapping = self._store.load_sub_to_cat()
        except DataSourceError:
            mapping = {}
        self.set_mapping(mapping)
        # Ensure empty dict instead of None
        self._mapping = self._mapping or {}
