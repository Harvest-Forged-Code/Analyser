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
        """Look up a cashflow mapping key."""
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

        Args:
            statement: Processed transaction DataFrame.

        Returns:
            DataFrame of earnings transactions.
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

        Args:
            statement: Processed transaction DataFrame.

        Returns:
            DataFrame of expense transactions.
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

        Args:
            statement: Processed transaction DataFrame.

        Returns:
            Pivot table (rows=categories, columns=months).
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

        Args:
            statement: Processed transaction DataFrame.

        Returns:
            Pivot table (rows=sub-categories, columns=months).
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
