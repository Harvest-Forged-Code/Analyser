"""Mapper controller for description-to-subcategory mappings.

Manages the keyword mapping used to categorize transactions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from budget_analyser.core.models import MonthlyReports
from budget_analyser.infrastructure.json_mappings import (
    JsonCategoryMappingStore,
)


def _norm(s: str) -> str:
    return (s or "").strip().lower()


@dataclass
class MapperController:
    """Controller to manage description/sub-category/category mappings.

    Keeps an in-memory working copy of the mappings and persists
    via ``JsonCategoryMappingStore``.
    """

    reports: list[MonthlyReports]
    logger: logging.Logger
    store: JsonCategoryMappingStore
    _desc_to_sub: dict[str, list[str]] = field(
        default_factory=dict, init=False,
    )
    _sub_to_cat: dict[str, list[str]] = field(
        default_factory=dict, init=False,
    )

    def __post_init__(self) -> None:
        self.reload()

    def list_unmapped_transactions(self) -> pd.DataFrame:
        """Return unmapped transactions across all reports."""
        frames: list[pd.DataFrame] = []
        for mr in self.reports:
            df = getattr(mr, "transactions", None)
            if df is None or df.empty:
                continue
            if "sub_category" in df.columns:
                mask = (
                    df["sub_category"].astype(str).map(_norm)
                    == ""
                )
                dfi = df.loc[mask].copy()
            else:
                dfi = df.copy()
            expected_cols = [
                "transaction_date", "description",
                "amount", "from_account",
            ]
            cols = [c for c in expected_cols if c in dfi.columns]
            if not cols:
                continue
            dfi = dfi[cols]
            frames.append(dfi)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description",
                "amount", "from_account",
            ])

        out = pd.concat(frames, ignore_index=True)
        if "transaction_date" in out.columns:
            try:
                out = out.sort_values(
                    by="transaction_date",
                    ascending=False,
                    kind="mergesort",
                )
            except Exception:  # pylint: disable=broad-exception-caught
                pass
        return out

    def list_unmapped_descriptions(self) -> list[str]:
        """Return unique unmapped descriptions, sorted."""
        seen: set[str] = set()
        out: list[str] = []
        for mr in self.reports:
            df = getattr(mr, "transactions", None)
            if df is None or df.empty:
                continue
            if "description" not in df.columns:
                continue
            if "sub_category" in df.columns:
                mask = (
                    df["sub_category"].astype(str).map(_norm)
                    == ""
                )
                series = df.loc[mask, "description"].astype(str)
            else:
                series = df["description"].astype(str)
            for desc in series:
                key = desc.strip()
                if key and key not in seen:
                    seen.add(key)
                    out.append(key)
        out.sort(key=lambda s: s.lower())
        return out

    def list_sub_categories(self) -> list[str]:
        """Return sorted list of sub-categories."""
        return sorted(
            self._desc_to_sub.keys(),
            key=lambda s: s.lower(),
        )

    def list_categories(self) -> list[str]:
        """Return sorted list of categories."""
        return sorted(
            self._sub_to_cat.keys(),
            key=lambda s: s.lower(),
        )

    def add_descriptions_to_sub_category(
        self,
        sub_category: str,
        descriptions: list[str],
    ) -> None:
        """Append description keywords to a sub-category.

        Args:
            sub_category: Target sub-category.
            descriptions: Keywords to add.

        Raises:
            ValueError: If sub-category doesn't exist or
                descriptions are already mapped.
        """
        sub_category = sub_category.strip()
        if not sub_category:
            raise ValueError("Sub-category is required")
        if sub_category not in self._desc_to_sub:
            raise ValueError(
                f"Unknown sub-category: {sub_category}",
            )

        owner: dict[str, str] = {}
        for sc, keywords in self._desc_to_sub.items():
            for kw in keywords or []:
                owner[_norm(kw)] = sc

        to_add: list[str] = []
        conflicts: list[tuple[str, str]] = []
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
                + "; ".join(
                    f"'{d}' -> {sc}"
                    for d, sc in conflicts
                ),
            )

        if not to_add:
            return
        self._desc_to_sub[sub_category] = list(
            (self._desc_to_sub.get(sub_category) or [])
        ) + to_add
        try:
            self.logger.info(
                "Mapper: added %d descriptions to '%s'",
                len(to_add), sub_category,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def create_sub_category(
        self,
        sub_category: str,
        category: str,
    ) -> None:
        """Create a new sub-category and link to a category.

        Args:
            sub_category: New sub-category name.
            category: Parent category name.

        Raises:
            ValueError: If names are empty or sub-category exists.
        """
        sc = sub_category.strip()
        if not sc:
            raise ValueError("Sub-category name is required")
        if sc in self._desc_to_sub:
            raise ValueError(
                f"Sub-category already exists: {sc}",
            )

        self._desc_to_sub[sc] = []

        cat = category.strip()
        if not cat:
            raise ValueError("Category is required")
        items = list(self._sub_to_cat.get(cat, []))
        if sc not in items:
            items.append(sc)
        self._sub_to_cat[cat] = items
        try:
            self.logger.info(
                "Mapper: created sub-category '%s' under '%s'",
                sc, cat,
            )
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def save(self) -> None:
        """Persist current mappings to JSON files."""
        self.store.save_desc_to_sub(self._desc_to_sub)
        self.store.save_sub_to_cat(self._sub_to_cat)

    def reload(self) -> None:
        """Reload mappings from JSON files."""
        self._desc_to_sub = self.store.load_desc_to_sub()
        self._sub_to_cat = self.store.load_sub_to_cat()
