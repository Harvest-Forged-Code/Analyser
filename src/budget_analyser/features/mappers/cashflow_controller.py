"""Cashflow mapper controller.

Manages earnings/expenses category grouping.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from budget_analyser.core.errors import DataSourceError
from budget_analyser.infrastructure.json_mappings import (
    JsonCashflowMappingStore,
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


class CashflowMapperController:
    """Controller to edit earnings/expenses category grouping.

    Keeps an in-memory copy and persists via
    ``JsonCashflowMappingStore``.
    """

    def __init__(
        self,
        store: JsonCashflowMappingStore,
        logger: logging.Logger,
    ) -> None:
        self._store = store
        self._logger = logger
        self._mapping: dict[str, list[str]] = {
            "Earnings": [], "Expenses": [],
        }
        self.reload()

    def earnings_categories(self) -> list[str]:
        """Return list of earnings categories."""
        return list(self._mapping.get("Earnings", []))

    def expense_categories(self) -> list[str]:
        """Return list of expense categories."""
        return list(self._mapping.get("Expenses", []))

    def mapping(self) -> dict[str, list[str]]:
        """Return full earnings/expenses mapping."""
        return {
            "Earnings": self.earnings_categories(),
            "Expenses": self.expense_categories(),
        }

    def set_mapping(
        self,
        earnings: Iterable[str],
        expenses: Iterable[str],
    ) -> None:
        """Set the full earnings/expenses mapping.

        Args:
            earnings: Categories classified as earnings.
            expenses: Categories classified as expenses.
        """
        earn = _dedup_keep_order(earnings)
        exp = _dedup_keep_order(expenses)

        earn_lower = {c.lower() for c in exp}
        earn = [c for c in earn if c.lower() not in earn_lower]

        self._mapping = {"Earnings": earn, "Expenses": exp}

    def add_category(self, name: str, flow: str) -> None:
        """Add a category to earnings or expenses.

        Args:
            name: Category name.
            flow: Target flow ('earnings' or 'expenses').

        Raises:
            ValueError: If name is empty.
        """
        val = (name or "").strip()
        if not val:
            raise ValueError("Category name is required")

        target = (
            "Expenses"
            if (flow or "").strip().lower().startswith("exp")
            else "Earnings"
        )
        other = (
            "Earnings" if target == "Expenses"
            else "Expenses"
        )

        other_list = [
            c for c in self._mapping.get(other, [])
            if c.lower() != val.lower()
        ]
        target_list = self._mapping.get(target, [])
        if val.lower() not in {c.lower() for c in target_list}:
            target_list = target_list + [val]

        self._mapping[target] = target_list
        self._mapping[other] = other_list

    def move_to_earnings(
        self, categories: Iterable[str],
    ) -> None:
        """Move categories from expenses to earnings."""
        current_exp = self._mapping.get("Expenses", [])
        move_set = {
            c.lower() for c in categories
            if str(c).strip()
        }
        self._mapping["Expenses"] = [
            c for c in current_exp
            if c.lower() not in move_set
        ]
        self._mapping["Earnings"] = _dedup_keep_order(
            list(self._mapping.get("Earnings", []))
            + [c for c in categories if str(c).strip()],
        )

    def move_to_expenses(
        self, categories: Iterable[str],
    ) -> None:
        """Move categories from earnings to expenses."""
        current_earn = self._mapping.get("Earnings", [])
        move_set = {
            c.lower() for c in categories
            if str(c).strip()
        }
        self._mapping["Earnings"] = [
            c for c in current_earn
            if c.lower() not in move_set
        ]
        self._mapping["Expenses"] = _dedup_keep_order(
            list(self._mapping.get("Expenses", []))
            + [c for c in categories if str(c).strip()],
        )

    def save(self) -> None:
        """Persist current mapping to JSON file."""
        self._store.save_cashflow(self._mapping)
        self._logger.info(
            "Cashflow mapping saved: earnings=%d expenses=%d",
            len(self._mapping.get("Earnings", [])),
            len(self._mapping.get("Expenses", [])),
        )

    def reload(self) -> None:
        """Reload mapping from JSON file."""
        try:
            mapping = self._store.load_cashflow()
        except DataSourceError:
            mapping = {}

        earnings = (
            mapping.get("Earnings")
            or mapping.get("earnings")
            or []
        )
        expenses = (
            mapping.get("Expenses")
            or mapping.get("expenses")
            or []
        )

        self.set_mapping(earnings, expenses)
        self._mapping.setdefault("Earnings", [])
        self._mapping.setdefault("Expenses", [])
