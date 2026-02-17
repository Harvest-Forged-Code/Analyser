"""Report service (business logic).

Provides pure functions/use-cases that generate report tables
from processed transaction data.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd


class ReportService:
    """Service that creates report DataFrames from transactions."""

    DEFAULT_EARNINGS_CATEGORIES = {"Income", "Unplanned_income"}
    DEFAULT_EXPENSE_CATEGORIES = {
        "Needs",
        "Flexible",
        "Luxuries",
        "payments_made",
        "payment_confirmations",
        "Remittance",
        "Unplanned_Spending's",
        "Refunded_money",
    }
    DEFAULT_REFUND_CATEGORY = "Refunded_money"

    def __init__(
        self,
        *,
        cashflow_mapping: Mapping[str, list[str]] | None = None,
        refund_category: str | None = None,
    ) -> None:
        """Initialize the report service with cashflow configuration.

        Resolves earnings and expense category sets from the
        optional cashflow mapping. Falls back to built-in defaults
        when the mapping is absent or empty.

        Args:
            cashflow_mapping: Optional mapping with ``"earnings"``
                and ``"expenses"`` keys pointing to category lists.
                When provided, overrides the default category sets.
            refund_category: Category name for refunded
                transactions. Defaults to ``"Refunded_money"``.

        Example:
            >>> svc = ReportService(
            ...     cashflow_mapping={
            ...         "earnings": ["Income", "Bonus"],
            ...         "expenses": ["Needs", "Luxuries"],
            ...     },
            ... )
        """
        earnings_categories = set(
            self.DEFAULT_EARNINGS_CATEGORIES,
        )
        expense_categories = set(
            self.DEFAULT_EXPENSE_CATEGORIES,
        )
        self._refund_category = (
            refund_category or self.DEFAULT_REFUND_CATEGORY
        )

        if cashflow_mapping:
            earnings = self._lookup_flow(
                cashflow_mapping, "earnings",
            )
            expenses = self._lookup_flow(
                cashflow_mapping, "expenses",
            )

            if earnings:
                earnings_categories = {
                    str(cat).strip()
                    for cat in earnings if str(cat).strip()
                }
            if expenses:
                expense_categories = {
                    str(cat).strip()
                    for cat in expenses if str(cat).strip()
                }

        if not earnings_categories:
            earnings_categories = set(
                self.DEFAULT_EARNINGS_CATEGORIES,
            )
        if not expense_categories:
            expense_categories = set(
                self.DEFAULT_EXPENSE_CATEGORIES,
            )

        self._earnings_categories = earnings_categories
        self._expense_categories = expense_categories
        self._expense_categories.add(self._refund_category)

    @staticmethod
    def _lookup_flow(
        mapping: Mapping[str, list[str]],
        key: str,
    ) -> list[str] | None:
        """Look up a cashflow mapping key case-insensitively.

        Iterates the mapping entries and returns the value whose
        key matches *key* (lowercased comparison).

        Args:
            mapping: Cashflow category mapping to search.
            key: The key to look up (e.g. ``"earnings"``).

        Returns:
            The category list if found, or ``None``
            when no matching key exists.

        Example:
            >>> ReportService._lookup_flow(
            ...     {"Earnings": ["Income"]}, "earnings",
            ... )
            ['Income']
        """
        for k, v in mapping.items():
            try:
                if str(k).lower() == key:
                    return list(v)
            except (TypeError, AttributeError, ValueError):
                continue
        return None

    def earnings(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return earnings restricted to configured categories.

        Filters the statement to rows whose category is in the
        earnings set and whose amount is positive. Amounts are
        converted to their absolute value.

        Args:
            statement: Processed transaction DataFrame with at
                least an ``"amount"`` column and optionally a
                ``"category"`` column.

        Returns:
            DataFrame of earnings transactions with positive
            absolute amounts.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [1000, -50],
            ...     "category": ["Income", "Needs"],
            ... })
            >>> result = svc.earnings(statement=df)
            >>> len(result)
            1
        """
        if "category" in statement.columns:
            mask = statement["category"].fillna("").isin(
                self._earnings_categories,
            )
            amount_mask = statement["amount"] > 0
            df = statement[mask & amount_mask].copy()
        else:
            df = statement[statement["amount"] > 0].copy()

        if not df.empty:
            df["amount"] = df["amount"].abs()
        return df

    def expenses(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return expenses including refunds as reductions.

        Filters the statement to rows that belong to expense
        categories. Refunded amounts are kept positive to act
        as reductions; all other expense amounts are negated.

        Args:
            statement: Processed transaction DataFrame with at
                least an ``"amount"`` column and optionally a
                ``"category"`` column.

        Returns:
            DataFrame of expense transactions where non-refund
            amounts are negative and refund amounts are positive.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-200, 50],
            ...     "category": ["Needs", "Refunded_money"],
            ... })
            >>> result = svc.expenses(statement=df)
            >>> len(result)
            2
        """
        if "category" in statement.columns:
            categories = statement["category"].fillna("")
            refund_mask = categories == self._refund_category
            negative_mask = statement["amount"] < 0
            expense_mask = categories.isin(
                self._expense_categories
                - self._earnings_categories,
            )
            df = statement[
                negative_mask | refund_mask | expense_mask
            ].copy()
            if not df.empty:
                refunds = (
                    df["category"].fillna("")
                    == self._refund_category
                )
                df.loc[~refunds, "amount"] = (
                    -df.loc[~refunds, "amount"].abs()
                )
                df.loc[refunds, "amount"] = (
                    df.loc[refunds, "amount"].abs()
                )
            return df

        df = statement[statement["amount"] < 0].copy()
        if not df.empty:
            df["amount"] = -df["amount"].abs()
        return df

    def expenses_category(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return pivot table of expenses by category and month.

        Aggregates expense amounts by category (rows) and
        year-month (columns) with margin totals.

        Args:
            statement: Processed transaction DataFrame with
                ``"category"``, ``"year_month"``, and ``"amount"``
                columns.

        Returns:
            Pivot table DataFrame with categories as rows,
            months as columns, and a ``"Total"`` margin.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-100, -200],
            ...     "category": ["Needs", "Needs"],
            ...     "year_month": ["2024-01", "2024-02"],
            ... })
            >>> pivot = svc.expenses_category(statement=df)
            >>> "Total" in pivot.columns
            True
        """
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )

    def expenses_sub_category(
        self, *, statement: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return pivot table of expenses by sub-category and month.

        Aggregates expense amounts by sub-category (rows) and
        year-month (columns) with margin totals.

        Args:
            statement: Processed transaction DataFrame with
                ``"sub_category"``, ``"year_month"``, and
                ``"amount"`` columns.

        Returns:
            Pivot table DataFrame with sub-categories as rows,
            months as columns, and a ``"Total"`` margin.

        Example:
            >>> import pandas as pd
            >>> svc = ReportService()
            >>> df = pd.DataFrame({
            ...     "amount": [-50, -75],
            ...     "sub_category": ["Groceries", "Rent"],
            ...     "year_month": ["2024-01", "2024-01"],
            ... })
            >>> pivot = svc.expenses_sub_category(statement=df)
            >>> "Total" in pivot.columns
            True
        """
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="sub_category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )
