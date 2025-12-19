from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd

from budget_analyser.controller.controllers import MonthlyReports
from .utils import month_names as _month_names


@dataclass(frozen=True)
class _MonthSummary:
    total: float
    subcats: List[Tuple[str, float]]  # (sub_category, amount)


@dataclass(frozen=True)
class _YearSummary:
    total: float
    months: List[Tuple[pd.Period, float, List[Tuple[str, float]]]]  # (period, total, subcats)


class EarningsStatsController:
    """Controller to compute Earnings page data from MonthlyReports.

    Pure Python (no Qt). Provides a simple API for the view to render:
      - available_months()
      - available_years()
      - month_label(period)
      - total_for_month(period)
      - subcategory_totals(period)
      - transactions(period, sub_category=None)
      - total_for_year(year)
      - year_breakdown(year) -> months with totals and subcategories
      - transactions_for_year(year, month=None, sub_category=None)
      - total_for_range(start_date, end_date)
      - subcategory_totals_for_range(start_date, end_date)
      - transactions_for_range(start_date, end_date, sub_category=None)
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
        # Cache year aggregates
        self._year_cache: Dict[int, _YearSummary] = {}

    # ---- Public API ----
    def available_months(self) -> List[pd.Period]:
        months = sorted(self._by_period.keys())
        return months

    def available_years(self) -> List[int]:
        """Return sorted list of years that have data."""
        years = sorted({int(p.year) for p in self._by_period.keys()})
        return years

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

    # ---- Yearly API ----
    def total_for_year(self, year: int) -> float:
        """Return total earnings for the given year."""
        return self._get_year_summary(year).total

    def year_breakdown(
        self, year: int
    ) -> List[Tuple[pd.Period, float, List[Tuple[str, float]]]]:
        """Return breakdown by month for the given year.

        Returns list of (period, month_total, [(sub_category, amount), ...])
        """
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: Optional[pd.Period] = None,
        sub_category: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return all transactions for a year, optionally filtered by month/sub_category."""
        frames = []
        for period in self._by_period.keys():
            if int(period.year) != year:
                continue
            if month is not None and period != month:
                continue
            mr = self._by_period.get(period)
            if mr is None or mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if sub_category and "sub_category" in df.columns:
                df = df[df["sub_category"].fillna("") == sub_category]
            frames.append(df)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    # ---- Date Range API ----
    def total_for_range(self, start_date: date, end_date: date) -> float:
        """Return total earnings for the given date range."""
        total = 0.0
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            total += float(df.loc[mask, "amount"].sum())
        return total

    def subcategory_totals_for_range(
        self, start_date: date, end_date: date
    ) -> List[Tuple[str, float]]:
        """Return sub-category totals for the given date range."""
        frames = []
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            frames.append(df.loc[mask])

        if not frames:
            return []

        combined = pd.concat(frames, ignore_index=True)
        if "sub_category" not in combined.columns or combined.empty:
            return []

        grouped = combined.groupby("sub_category")["amount"].sum().sort_values(ascending=False)
        return [
            (str(idx) if idx else "(Uncategorized)", float(val))
            for idx, val in grouped.items()
        ]

    def transactions_for_range(
        self,
        start_date: date,
        end_date: date,
        sub_category: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return all transactions within the date range, optionally filtered by sub_category."""
        frames = []
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            filtered = df.loc[mask]
            if sub_category and "sub_category" in filtered.columns:
                filtered = filtered[filtered["sub_category"].fillna("") == sub_category]
            if not filtered.empty:
                frames.append(filtered)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

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

    def _get_year_summary(self, year: int) -> _YearSummary:
        """Compute and cache yearly summary with month breakdown."""
        cached = self._year_cache.get(year)
        if cached is not None:
            return cached

        year_total = 0.0
        months_data: List[Tuple[pd.Period, float, List[Tuple[str, float]]]] = []

        # Get all periods for this year, sorted
        year_periods = sorted(
            [p for p in self._by_period.keys() if int(p.year) == year]
        )

        for period in year_periods:
            month_summary = self._get_month_summary(period)
            year_total += month_summary.total
            months_data.append((period, month_summary.total, list(month_summary.subcats)))

        summary = _YearSummary(total=year_total, months=months_data)
        self._year_cache[year] = summary
        return summary
