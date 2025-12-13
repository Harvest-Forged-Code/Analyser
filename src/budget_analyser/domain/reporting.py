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

import pandas as pd


class ReportService:
    """Service that creates report DataFrames from processed transactions."""

    def earnings(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return only rows where amount is positive.

        Args:
            statement: Transaction DataFrame.

        Returns:
            DataFrame containing earnings (amount > 0).
        """
        # Earnings are positive amounts.
        return statement[statement["amount"] > 0]

    def expenses(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        """Return only rows where amount is negative.

        Args:
            statement: Transaction DataFrame.

        Returns:
            DataFrame containing expenses (amount < 0).
        """
        # Expenses are negative amounts.
        return statement[statement["amount"] < 0]

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
