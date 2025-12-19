from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from budget_analyser.controller.controllers import MonthlyReports
from .utils import month_names as _month_names


@dataclass(frozen=True)
class _MonthSummary:
    total: float
    subcats: List[Tuple[str, float]]  # (sub_category, amount)


class EarningsStatsController:
    """Controller to compute Earnings page data from MonthlyReports.

    Pure Python (no Qt). Provides a simple API for the view to render:
      - available_months()
      - month_label(period)
      - total_for_month(period)
      - subcategory_totals(period)
      - transactions(period, sub_category=None)
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        self._reports = reports
        self._logger = logger
        # Map Period("YYYY-MM") -> MonthlyReports for fast lookup
        self._by_period: Dict[pd.Period, MonthlyReports] = {
            mr.month: mr for mr in self._reports
        }
        # Cache month aggregates
        self._month_cache: Dict[pd.Period, _MonthSummary] = {}

    # ---- Public API ----
    def available_months(self) -> List[pd.Period]:
        months = sorted(self._by_period.keys())
        return months

    @staticmethod
    def month_label(period: pd.Period) -> str:
        names = _month_names()
        return f"{names[int(period.month) - 1]} {int(period.year)}"

    def total_for_month(self, period: pd.Period) -> float:
        return self._get_month_summary(period).total

    def subcategory_totals(self, period: pd.Period) -> List[Tuple[str, float]]:
        return list(self._get_month_summary(period).subcats)

    def transactions(
        self, period: pd.Period, sub_category: Optional[str] = None
    ) -> pd.DataFrame:
        """Return transactions for selected month, optionally filtered by sub-category.

        Columns returned are those present in the underlying MonthlyReports.earnings
        (typically transaction_date, description, amount, from_account, sub_category).
        """
        mr = self._by_period.get(period)
        if mr is None:
            return pd.DataFrame()
        df = mr.earnings
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "transaction_date",
                "description",
                "amount",
                "from_account",
                "sub_category",
            ])
        if sub_category:
            if "sub_category" in df.columns:
                df = df[df["sub_category"].fillna("") == sub_category]
            else:
                # If sub_category info is missing, no rows match this filter.
                return pd.DataFrame(columns=df.columns)
        return df.copy()

    # ---- Internals ----
    def _get_month_summary(self, period: pd.Period) -> _MonthSummary:
        cached = self._month_cache.get(period)
        if cached is not None:
            return cached

        mr = self._by_period.get(period)
        if mr is None or mr.earnings is None or mr.earnings.empty:
            summary = _MonthSummary(total=0.0, subcats=[])
            self._month_cache[period] = summary
            return summary

        df = mr.earnings
        total_val = float(df["amount"].sum()) if "amount" in df.columns else 0.0

        if "sub_category" in df.columns and not df.empty:
            grouped = (
                df.groupby("sub_category")["amount"].sum().sort_values(ascending=False)
            )
            subcats_list: List[Tuple[str, float]] = [
                (str(idx) if idx else "(Uncategorized)", float(val))
                for idx, val in grouped.items()
            ]
        else:
            subcats_list = []

        summary = _MonthSummary(total=total_val, subcats=subcats_list)
        self._month_cache[period] = summary
        return summary
