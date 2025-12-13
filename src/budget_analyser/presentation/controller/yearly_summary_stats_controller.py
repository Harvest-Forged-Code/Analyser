from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from budget_analyser.presentation.controllers import MonthlyReports
from .dtos import YearlyStats
from .utils import month_names as _month_names


class HomeStatsController:
    """Controller to compute Home page statistics from MonthlyReports.

    Pure Python (no Qt). Returns DTOs for the view to render.
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        self._reports = reports
        self._logger = logger
        self._year_cache: Dict[int, YearlyStats] = {}

    # ---- Public API ----
    def available_years(self) -> List[int]:
        if not self._reports:
            return []
        return sorted({int(mr.month.year) for mr in self._reports})

    def get_yearly_stats(self, year: int) -> YearlyStats:
        cached = self._year_cache.get(year)
        if cached is not None:
            return cached
        stats = self._compute_year_data(year)
        self._year_cache[year] = stats
        return stats

    @staticmethod
    def month_names() -> List[str]:
        return _month_names()

    # ---- Internal computations ----
    def _compute_year_data(self, year: int) -> YearlyStats:
        # Filter reports for the year
        months = [mr for mr in self._reports if int(mr.month.year) == year]

        # Monthly sums
        earnings_by_month: Dict[int, float] = {i: 0.0 for i in range(1, 13)}
        expenses_by_month: Dict[int, float] = {i: 0.0 for i in range(1, 13)}

        # Sub-category accumulators
        earn_subcats: Dict[str, float] = {}
        exp_subcats: Dict[str, float] = {}

        for mr in months:
            month_index = int(mr.month.month)

            # Earnings totals (values are positive)
            e_sum = float(mr.earnings["amount"].sum()) if not mr.earnings.empty else 0.0
            earnings_by_month[month_index] += e_sum

            # Expenses totals (values are negative) -> store as positive for UI
            x_sum = float((-mr.expenses["amount"]).sum()) if not mr.expenses.empty else 0.0
            expenses_by_month[month_index] += x_sum

            # Sub-categories
            if "sub_category" in mr.earnings.columns and not mr.earnings.empty:
                for sub, val in (
                    mr.earnings.groupby("sub_category")["amount"].sum().items()
                ):
                    earn_subcats[sub] = earn_subcats.get(sub, 0.0) + float(val)

            if "sub_category" in mr.expenses.columns and not mr.expenses.empty:
                for sub, val in (
                    mr.expenses.groupby("sub_category")["amount"].sum().items()
                ):
                    # Convert negative sums to positive values for display
                    exp_subcats[sub] = exp_subcats.get(sub, 0.0) + float(-val)

        total_earnings = sum(earnings_by_month.values())
        total_expenses = sum(expenses_by_month.values())

        # Sort sub-categories desc by amount
        earn_sub_list: List[Tuple[str, float]] = sorted(
            earn_subcats.items(), key=lambda x: x[1], reverse=True
        )
        exp_sub_list: List[Tuple[str, float]] = sorted(
            exp_subcats.items(), key=lambda x: x[1], reverse=True
        )

        # Build monthly rows with month names
        names = _month_names()
        monthly_rows: List[Tuple[str, float, float]] = [
            (names[i - 1], float(earnings_by_month[i]), float(expenses_by_month[i]))
            for i in range(1, 13)
        ]

        return YearlyStats(
            total_earnings=total_earnings,
            total_expenses=total_expenses,
            earn_subcats=earn_sub_list,
            exp_subcats=exp_sub_list,
            monthly_rows=monthly_rows,
        )
