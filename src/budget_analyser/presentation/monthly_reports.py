"""MonthlyReports dataclass used by presentation layer.

Single responsibility:
    Describe the set of report tables for a given month.
"""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class MonthlyReports:
    """Report tables for a single month."""

    month: pd.Period
    earnings: pd.DataFrame
    expenses: pd.DataFrame
    expenses_category: pd.DataFrame
    expenses_sub_category: pd.DataFrame
