from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import pandas as pd

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.infrastructure.json_mappings import JsonCategoryMappingStore


def _norm(s: str) -> str:
    return (s or "").strip().lower()


@dataclass
class MapperController:
    """Controller to manage description/sub-category/category mappings.

    UI-only views should call these methods. This controller keeps an in-memory
    working copy of the mappings and persists via `JsonCategoryMappingStore`.
    """

    reports: List[MonthlyReports]
    logger: logging.Logger
    store: JsonCategoryMappingStore
    _desc_to_sub: Dict[str, List[str]] = field(default_factory=dict, init=False)
    _sub_to_cat: Dict[str, List[str]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.reload()

    # ----- Queries -----
    def list_unmapped_transactions(self) -> pd.DataFrame:
        """Return rows of transactions that are not yet mapped to any sub-category.

        Columns included (when available): transaction_date, description, amount, from_account.
        Rows are sorted by transaction_date descending when possible.
        """
        frames: list[pd.DataFrame] = []
        for mr in self.reports:
            df = getattr(mr, "transactions", None)
            if df is None or df.empty:
                continue
            # Determine unmapped mask
            if "sub_category" in df.columns:
                mask = df["sub_category"].astype(str).map(_norm) == ""
                dfi = df.loc[mask].copy()
            else:
                dfi = df.copy()
            # Keep only expected columns if present
            cols = [c for c in ["transaction_date", "description", "amount", "from_account"] if c in dfi.columns]
            if not cols:
                continue
            dfi = dfi[cols]
            frames.append(dfi)

        if not frames:
            return pd.DataFrame(columns=["transaction_date", "description", "amount", "from_account"])

        out = pd.concat(frames, ignore_index=True)
        # Stable sort by date desc when possible
        if "transaction_date" in out.columns:
            try:
                out = out.sort_values(by="transaction_date", ascending=False, kind="mergesort")
            except Exception:
                pass
        return out

    def list_unmapped_descriptions(self) -> List[str]:
        """Return a stable-sorted list of unique transaction descriptions that
        do not currently map to any sub-category in the processed reports.
        """
        seen: set[str] = set()
        out: List[str] = []
        for mr in self.reports:
            df = getattr(mr, "transactions", None)
            if df is None or df.empty:
                continue
            if "description" not in df.columns:
                continue
            if "sub_category" in df.columns:
                # Only descriptions with empty/NaN sub_category are considered unmapped
                mask = df["sub_category"].astype(str).map(_norm) == ""
                series = df.loc[mask, "description"].astype(str)
            else:
                # No sub_category column -> treat all as unmapped
                series = df["description"].astype(str)
            for desc in series:
                key = desc.strip()
                if key and key not in seen:
                    seen.add(key)
                    out.append(key)
        out.sort(key=lambda s: s.lower())
        return out

    def list_sub_categories(self) -> List[str]:
        return sorted(self._desc_to_sub.keys(), key=lambda s: s.lower())

    def list_categories(self) -> List[str]:
        return sorted(self._sub_to_cat.keys(), key=lambda s: s.lower())

    # ----- Edits (in-memory until save) -----
    def add_descriptions_to_sub_category(self, sub_category: str, descriptions: List[str]) -> None:
        """Append description keywords to an existing sub-category.

        - Case-insensitive duplicate prevention across ALL sub-categories.
        - If any description already exists mapped (to same or other sub-cat),
          raise ValueError listing conflicts (no partial writes).
        """
        sub_category = sub_category.strip()
        if not sub_category:
            raise ValueError("Sub-category is required")
        if sub_category not in self._desc_to_sub:
            raise ValueError(f"Unknown sub-category: {sub_category}")

        # Build reverse index for conflict detection
        owner: Dict[str, str] = {}
        for sc, keywords in self._desc_to_sub.items():
            for kw in keywords or []:
                owner[_norm(kw)] = sc

        to_add: List[str] = []
        conflicts: List[Tuple[str, str]] = []
        for d in descriptions:
            d_clean = d.strip()
            if not d_clean:
                continue
            dn = _norm(d_clean)
            exists_owner = owner.get(dn)
            if exists_owner is not None:
                conflicts.append((d_clean, exists_owner))
            else:
                to_add.append(d_clean)

        if conflicts:
            raise ValueError(
                "Some descriptions are already mapped: "
                + "; ".join([f"'{d}' -> {sc}" for d, sc in conflicts])
            )

        if not to_add:
            return
        self._desc_to_sub[sub_category] = list((self._desc_to_sub.get(sub_category) or [])) + to_add
        try:
            self.logger.info(
                "Mapper: added %d descriptions to sub-category '%s'", len(to_add), sub_category
            )
        except Exception:
            pass

    def create_sub_category(self, sub_category: str, category: str) -> None:
        """Create a new sub-category and link it to a category.

        If the category does not exist, it will be created (per requirement).
        """
        sc = sub_category.strip()
        if not sc:
            raise ValueError("Sub-category name is required")
        if sc in self._desc_to_sub:
            raise ValueError(f"Sub-category already exists: {sc}")

        self._desc_to_sub[sc] = []

        cat = category.strip()
        if not cat:
            raise ValueError("Category is required")
        items = list(self._sub_to_cat.get(cat, []))
        if sc not in items:
            items.append(sc)
        self._sub_to_cat[cat] = items
        try:
            self.logger.info("Mapper: created sub-category '%s' under category '%s'", sc, cat)
        except Exception:
            pass

    # ----- Persistence -----
    def save(self) -> None:
        self.store.save_desc_to_sub(self._desc_to_sub)
        self.store.save_sub_to_cat(self._sub_to_cat)

    def reload(self) -> None:
        self._desc_to_sub = self.store.load_desc_to_sub()
        self._sub_to_cat = self.store.load_sub_to_cat()
