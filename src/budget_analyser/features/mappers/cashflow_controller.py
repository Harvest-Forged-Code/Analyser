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
    """Deduplicate while preserving insertion order.

    Args:
        items: Iterable of raw string values. Blank and
            duplicate entries (case-insensitive) are dropped.

    Returns:
        Deduplicated list in original insertion order.
    """
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
        """Initialize the cashflow mapper controller.

        Args:
            store: Persistence backend for cashflow mappings.
            logger: Logger instance for audit messages.
        """
        self._store = store
        self._logger = logger
        self._mapping: dict[str, list[str]] = {
            "Earnings": [], "Expenses": [],
        }
        self.reload()

    def earnings_categories(self) -> list[str]:
        """Return list of earnings categories.

        Returns:
            Shallow copy of the current earnings category list.

        Example:
            >>> ctrl.earnings_categories()
            ['Salary', 'Freelance']
        """
        return list(self._mapping.get("Earnings", []))

    def expense_categories(self) -> list[str]:
        """Return list of expense categories.

        Returns:
            Shallow copy of the current expense category list.

        Example:
            >>> ctrl.expense_categories()
            ['Groceries', 'Rent', 'Utilities']
        """
        return list(self._mapping.get("Expenses", []))

    def mapping(self) -> dict[str, list[str]]:
        """Return full earnings/expenses mapping.

        Returns:
            Dictionary with ``"Earnings"`` and ``"Expenses"``
            keys, each mapping to a list of category names.

        Example:
            >>> ctrl.mapping()
            {'Earnings': ['Salary'], 'Expenses': ['Rent']}
        """
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

        Replaces both sides of the mapping. Categories appearing
        in *expenses* take priority over duplicates in *earnings*.

        Args:
            earnings: Categories classified as earnings.
            expenses: Categories classified as expenses.

        Example:
            >>> ctrl.set_mapping(
            ...     earnings=["Salary"],
            ...     expenses=["Rent", "Groceries"],
            ... )
        """
        earn = _dedup_keep_order(earnings)
        exp = _dedup_keep_order(expenses)

        earn_lower = {c.lower() for c in exp}
        earn = [c for c in earn if c.lower() not in earn_lower]

        self._mapping = {"Earnings": earn, "Expenses": exp}

    def add_category(self, name: str, flow: str) -> None:
        """Add a category to earnings or expenses.

        If the category already exists in the opposite flow,
        it is removed from there first.

        Args:
            name: Category name.
            flow: Target flow (``'earnings'`` or ``'expenses'``).

        Raises:
            ValueError: If name is empty.

        Example:
            >>> ctrl.add_category("Side Hustle", "earnings")
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
        """Move categories from expenses to earnings.

        Removes the given categories from the expenses list and
        appends them to earnings (deduplicated).

        Args:
            categories: Category names to move.

        Example:
            >>> ctrl.move_to_earnings(["Freelance"])
        """
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
        """Move categories from earnings to expenses.

        Removes the given categories from the earnings list and
        appends them to expenses (deduplicated).

        Args:
            categories: Category names to move.

        Example:
            >>> ctrl.move_to_expenses(["Misc Income"])
        """
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
        """Persist current mapping to JSON file.

        Writes the earnings/expenses mapping to the underlying
        ``JsonCashflowMappingStore`` and logs a summary.

        Example:
            >>> ctrl.add_category("Bonus", "earnings")
            >>> ctrl.save()
        """
        self._store.save_cashflow(self._mapping)
        self._logger.info(
            "Cashflow mapping saved: earnings=%d expenses=%d",
            len(self._mapping.get("Earnings", [])),
            len(self._mapping.get("Expenses", [])),
        )

    def reload(self) -> None:
        """Reload mapping from JSON file.

        Replaces the in-memory mapping with fresh data from
        the ``JsonCashflowMappingStore``. Falls back to an
        empty mapping on ``DataSourceError``.

        Example:
            >>> ctrl.reload()
        """
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
