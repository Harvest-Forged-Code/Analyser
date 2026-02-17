"""Shared DTOs used across multiple feature slices.

Contains data transfer objects that cross feature boundaries,
such as MonthlyReports which is produced by ingestion/reporting
and consumed by many feature pages.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass(frozen=True)
class MonthlyReports:
    """Report tables for a single month.

    Attributes:
        month: The calendar month this report covers.
        earnings: DataFrame of positive-amount transactions (income).
        expenses: DataFrame of negative-amount transactions (spending).
        expenses_category: Expenses aggregated by top-level category.
        expenses_sub_category: Expenses aggregated by sub-category.
        transactions: Full transaction DataFrame for the month.

    Example:
        >>> report = MonthlyReports(
        ...     month=pd.Period("2025-01"),
        ...     earnings=earnings_df,
        ...     expenses=expenses_df,
        ...     expenses_category=cat_df,
        ...     expenses_sub_category=sub_df,
        ... )
        >>> report.month
        Period('2025-01', 'M')
    """

    month: pd.Period
    earnings: pd.DataFrame
    expenses: pd.DataFrame
    expenses_category: pd.DataFrame
    expenses_sub_category: pd.DataFrame
    transactions: pd.DataFrame = field(default_factory=pd.DataFrame)
