from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

import pandas as pd

from budget_analyser.controller.controllers import MonthlyReports
from .utils import month_names as _month_names


@dataclass(frozen=True)
class _CategoryNode:
    name: str
    total: float
    subcats: List[Tuple[str, float]]  # (sub_category, total)


@dataclass(frozen=True)
class _YearSummary:
    total: float
    # (period, month_total, category_breakdown)
    months: List[Tuple[pd.Period, float, List[Tuple[str, float, List[Tuple[str, float]]]]]]


class ExpensesStatsController:
    """Controller to compute Expenses page data from MonthlyReports.

    Pure Python (no Qt). Provides a simple API for the view to render:
      - available_months()
      - available_years()
      - month_label(period)
      - total_for_month(period)
      - category_breakdown(period) -> List[(category, total, [(sub_category, total)])]
      - transactions(period, category=None, sub_category=None)
      - total_for_year(year)
      - year_breakdown(year) -> months with totals and category breakdowns
      - transactions_for_year(year, month=None, category=None, sub_category=None)
      - total_for_range(start_date, end_date)
      - category_breakdown_for_range(start_date, end_date)
      - transactions_for_range(start_date, end_date, category=None, sub_category=None)

    Notes:
      - Totals are returned as positive values for UI display, even though the
        underlying expenses amounts are negative in the data model.
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        self._reports = reports
        self._logger = logger
        # Map Period("YYYY-MM") -> MonthlyReports for fast lookup
        self._by_period: Dict[pd.Period, MonthlyReports] = {mr.month: mr for mr in self._reports}
        # Cache month aggregates
        self._month_total_cache: Dict[pd.Period, float] = {}
        self._category_cache: Dict[pd.Period, List[_CategoryNode]] = {}
        # Cache year aggregates
        self._year_cache: Dict[int, _YearSummary] = {}

    # ---- Public API ----
    def available_months(self) -> List[pd.Period]:
        return sorted(self._by_period.keys())

    def available_years(self) -> List[int]:
        """Return sorted list of years that have data."""
        years = sorted({int(p.year) for p in self._by_period.keys()})
        return years

    @staticmethod
    def month_label(period: pd.Period) -> str:
        names = _month_names()
        return f"{names[int(period.month) - 1]} {int(period.year)}"

    def total_for_month(self, period: pd.Period) -> float:
        cached = self._month_total_cache.get(period)
        if cached is not None:
            return cached
        mr = self._by_period.get(period)
        if mr is None or mr.expenses is None or mr.expenses.empty:
            self._month_total_cache[period] = 0.0
            return 0.0
        # Sum expenses as positive value for display
        total = float((-mr.expenses["amount"]).sum()) if "amount" in mr.expenses.columns else 0.0
        self._month_total_cache[period] = total
        return total

    def category_breakdown(
        self, period: pd.Period
    ) -> List[Tuple[str, float, List[Tuple[str, float]]]]:
        cached = self._category_cache.get(period)
        if cached is None:
            cached = self._compute_category_nodes(period)
            self._category_cache[period] = cached
        # Convert dataclass to tuple structure for consumers
        return [(n.name, n.total, list(n.subcats)) for n in cached]

    def transactions(
        self,
        period: pd.Period,
        *,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return transactions for selected month filtered by category/sub-category.

        Returns a copy of the underlying DataFrame. Amounts remain negative (raw data).
        """
        mr = self._by_period.get(period)
        if mr is None:
            return pd.DataFrame()
        df = mr.expenses
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "transaction_date",
                "description",
                "amount",
                "from_account",
                "category",
                "sub_category",
            ])
        out = df
        if category:
            if "category" in out.columns:
                out = out[out["category"].fillna("") == category]
            else:
                return pd.DataFrame(columns=df.columns)
        if sub_category:
            if "sub_category" in out.columns:
                out = out[out["sub_category"].fillna("") == sub_category]
            else:
                return pd.DataFrame(columns=df.columns)
        return out.copy()

    # ---- Yearly API ----
    def total_for_year(self, year: int) -> float:
        """Return total expenses for the given year (as positive value)."""
        return self._get_year_summary(year).total

    def year_breakdown(
        self, year: int
    ) -> List[Tuple[pd.Period, float, List[Tuple[str, float, List[Tuple[str, float]]]]]]:
        """Return breakdown by month for the given year.

        Returns list of (period, month_total, [(category, cat_total, [(sub_cat, sub_total)])])
        """
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: Optional[pd.Period] = None,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return all transactions for a year, optionally filtered."""
        frames = []
        for period in self._by_period.keys():
            if int(period.year) != year:
                continue
            if month is not None and period != month:
                continue
            mr = self._by_period.get(period)
            if mr is None or mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if category and "category" in df.columns:
                df = df[df["category"].fillna("") == category]
            if sub_category and "sub_category" in df.columns:
                df = df[df["sub_category"].fillna("") == sub_category]
            if not df.empty:
                frames.append(df)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "category", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    # ---- Date Range API ----
    def total_for_range(self, start_date: date, end_date: date) -> float:
        """Return total expenses for the given date range (as positive value)."""
        total = 0.0
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            # Convert to positive for display
            total += float((-df.loc[mask, "amount"]).sum())
        return total

    def category_breakdown_for_range(
        self, start_date: date, end_date: date
    ) -> List[Tuple[str, float, List[Tuple[str, float]]]]:
        """Return category breakdown for the given date range."""
        frames = []
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            frames.append(df.loc[mask])

        if not frames:
            return []

        combined = pd.concat(frames, ignore_index=True)
        if combined.empty:
            return []

        # Build category breakdown (same logic as _compute_category_nodes but for combined data)
        result: List[Tuple[str, float, List[Tuple[str, float]]]] = []

        if "category" in combined.columns:
            cat_series = combined.groupby("category")["amount"].sum().sort_values()
            cat_items = [
                (str(cat) if cat else "(Uncategorized)", float(-total))
                for cat, total in cat_series.items()
            ]
            cat_items.sort(key=lambda x: x[1], reverse=True)
        else:
            fallback_total = (
                float((-combined["amount"]).sum()) if "amount" in combined.columns else 0.0
            )
            cat_items = [("(Uncategorized)", fallback_total)]

        for cat_name, cat_total in cat_items:
            subcats_list = self._build_subcats_for_category(combined, cat_name)
            result.append((cat_name, cat_total, subcats_list))

        return result

    def transactions_for_range(
        self,
        start_date: date,
        end_date: date,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
    ) -> pd.DataFrame:
        """Return all transactions within the date range, optionally filtered."""
        frames = []
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (df["transaction_date"].dt.date >= start_date) & (
                df["transaction_date"].dt.date <= end_date
            )
            filtered = df.loc[mask]
            if category and "category" in filtered.columns:
                filtered = filtered[filtered["category"].fillna("") == category]
            if sub_category and "sub_category" in filtered.columns:
                filtered = filtered[filtered["sub_category"].fillna("") == sub_category]
            if not filtered.empty:
                frames.append(filtered)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "category", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    # ---- Internals ----
    def _build_subcats_for_category(
        self, data: pd.DataFrame, cat_name: str
    ) -> List[Tuple[str, float]]:
        """Build subcategory breakdown for a given category from DataFrame."""
        dcat = data
        if "category" in data.columns:
            cat_filter = "" if cat_name == "(Uncategorized)" else cat_name
            dcat = data[data["category"].fillna("") == cat_filter]

        if "sub_category" not in dcat.columns or dcat.empty:
            return []

        sub_series = dcat.groupby("sub_category")["amount"].sum().sort_values()
        subcats_list = [
            (str(sub) if sub else "(Uncategorized)", float(-val))
            for sub, val in sub_series.items()
        ]
        subcats_list.sort(key=lambda x: x[1], reverse=True)
        return subcats_list

    def _compute_category_nodes(self, period: pd.Period) -> List[_CategoryNode]:
        mr = self._by_period.get(period)
        if mr is None or mr.expenses is None or mr.expenses.empty:
            return []
        df = mr.expenses
        # Build category totals (positive for display)
        if "category" in df.columns and not df.empty:
            cat_series = df.groupby("category")["amount"].sum().sort_values()
            # sort_values ascending since amounts negative; but we convert to positive for display
            # We'll sort by positive totals descending for UI
            cat_items = [
                (str(cat) if cat else "(Uncategorized)", float(-total))
                for cat, total in cat_series.items()
            ]
            cat_items.sort(key=lambda x: x[1], reverse=True)
        else:
            # No category column
            fallback_total = (
                float((-df["amount"]).sum()) if "amount" in df.columns else 0.0
            )
            cat_items = [("(Uncategorized)", fallback_total)]

        nodes: list[_CategoryNode] = []
        for cat_name, cat_total in cat_items:
            # Build sub-category totals for this category
            subcats_list: List[Tuple[str, float]] = []
            dcat = df
            if "category" in df.columns:
                cat_filter = "" if cat_name == "(Uncategorized)" else cat_name
                dcat = df[df["category"].fillna("") == cat_filter]

            if "sub_category" in dcat.columns and not dcat.empty:
                sub_series = dcat.groupby("sub_category")["amount"].sum().sort_values()
                subcats_list = [
                    (str(sub) if sub else "(Uncategorized)", float(-val))
                    for sub, val in sub_series.items()
                ]
                subcats_list.sort(key=lambda x: x[1], reverse=True)

            nodes.append(_CategoryNode(name=cat_name, total=float(cat_total), subcats=subcats_list))

        return nodes

    def _get_year_summary(self, year: int) -> _YearSummary:
        """Compute and cache yearly summary with month breakdown."""
        cached = self._year_cache.get(year)
        if cached is not None:
            return cached

        year_total = 0.0
        # Type: List of (period, month_total, category_breakdown)
        months_data: List[
            Tuple[pd.Period, float, List[Tuple[str, float, List[Tuple[str, float]]]]]
        ] = []

        # Get all periods for this year, sorted
        year_periods = sorted(
            [p for p in self._by_period.keys() if int(p.year) == year]
        )

        for period in year_periods:
            month_total = self.total_for_month(period)
            year_total += month_total
            # Get category breakdown for this month
            cat_breakdown = self.category_breakdown(period)
            months_data.append((period, month_total, cat_breakdown))

        summary = _YearSummary(total=year_total, months=months_data)
        self._year_cache[year] = summary
        return summary
