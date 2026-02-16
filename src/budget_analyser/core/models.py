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
    """Report tables for a single month."""

    month: pd.Period
    earnings: pd.DataFrame
    expenses: pd.DataFrame
    expenses_category: pd.DataFrame
    expenses_sub_category: pd.DataFrame
    transactions: pd.DataFrame = field(default_factory=pd.DataFrame)
