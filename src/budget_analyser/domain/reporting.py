"""Reporting services (domain logic).

Purpose:
    Provide pure functions/use-cases that generate report tables from processed
    transaction data.

Goal:
    Keep reporting logic independent of IO and infrastructure.

Steps:
    1. Filter earnings/expenses.
    2. Pivot expenses into category/sub-category summaries.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd


class ReportService:
    """Service that creates report DataFrames from processed transactions."""

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
        earnings_categories = set(self.DEFAULT_EARNINGS_CATEGORIES)
        expense_categories = set(self.DEFAULT_EXPENSE_CATEGORIES)
        self._refund_category = refund_category or self.DEFAULT_REFUND_CATEGORY

        if cashflow_mapping:
            earnings = self._lookup_flow(cashflow_mapping, "earnings")
            expenses = self._lookup_flow(cashflow_mapping, "expenses")

            if earnings:
                earnings_categories = {
                    str(cat).strip() for cat in earnings if str(cat).strip()
                }
            if expenses:
                expense_categories = {
                    str(cat).strip() for cat in expenses if str(cat).strip()
                }

        if not earnings_categories:
            earnings_categories = set(self.DEFAULT_EARNINGS_CATEGORIES)
        if not expense_categories:
            expense_categories = set(self.DEFAULT_EXPENSE_CATEGORIES)

        self._earnings_categories = earnings_categories
        self._expense_categories = expense_categories
        self._expense_categories.add(self._refund_category)

    @staticmethod
    def _lookup_flow(mapping: Mapping[str, list[str]], key: str) -> list[str] | None:
        for k, v in mapping.items():
            try:
                if str(k).lower() == key:
                    return list(v)
            except Exception:  # pylint: disable=broad-exception-caught
                continue
        return None

    def earnings(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return earnings restricted to configured earnings categories.

        Earnings are limited to transactions whose category appears in the
        configured earnings mapping (defaults to ``Income`` and
        ``Unplanned_income``) and whose amount is positive. If the statement
        lacks a ``category`` column, it falls back to the previous sign-based
        logic.
        """
        if "category" in statement.columns:
            mask = statement["category"].fillna("").isin(self._earnings_categories)
            amount_mask = statement["amount"] > 0
            df = statement[mask & amount_mask].copy()
        else:
            df = statement[statement["amount"] > 0].copy()

        if not df.empty:
            df["amount"] = df["amount"].abs()
        return df

    def expenses(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return expenses including refunds as reductions.

        Expenses include negative amounts, any category marked as an expense in
        the cashflow mapping (by default Needs/Flexible/Luxuries/payments_made/
        payment_confirmations/Remittance/Unplanned_Spending's/Refunded_money),
        and refund rows to offset totals. Refunds remain positive while other
        expenses are normalized to negative values. If the statement lacks a
        ``category`` column, the method falls back to sign-based filtering.
        """
        if "category" in statement.columns:
            categories = statement["category"].fillna("")
            refund_mask = categories == self._refund_category
            negative_mask = statement["amount"] < 0
            expense_mask = categories.isin(self._expense_categories - self._earnings_categories)
            df = statement[negative_mask | refund_mask | expense_mask].copy()
            if not df.empty:
                refunds = df["category"].fillna("") == self._refund_category
                df.loc[~refunds, "amount"] = -df.loc[~refunds, "amount"].abs()
                df.loc[refunds, "amount"] = df.loc[refunds, "amount"].abs()
            return df

        # Fallback when category is unavailable
        df = statement[statement["amount"] < 0].copy()
        if not df.empty:
            df["amount"] = -df["amount"].abs()
        return df

    def expenses_category(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return a pivot table of expenses aggregated by category and month.

        Args:
            statement: Processed transaction DataFrame (must include category/year_month).

        Returns:
            Pivot table where rows are categories and columns are months.
        """
        # Filter to expenses only before pivoting.
        expenses = self.expenses(statement=statement)
        # Create a category x month pivot with totals.
        return expenses.pivot_table(
            index="category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )

    def expenses_sub_category(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return a pivot table of expenses aggregated by sub-category and month.

        Args:
            statement: Processed transaction DataFrame (must include sub_category/year_month).

        Returns:
            Pivot table where rows are sub-categories and columns are months.
        """
        # Filter to expenses only before pivoting.
        expenses = self.expenses(statement=statement)
        # Create a sub-category x month pivot with totals.
        return expenses.pivot_table(
            index="sub_category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )
