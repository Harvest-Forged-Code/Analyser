from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from budget_analyser.presentation.controllers import MonthlyReports
from .dtos import YearlyStats, YearlyCategoryBreakdown, CategoryNode
from .utils import month_names as _month_names


class YearlySummaryStatsController:
    """Controller to compute Home page statistics from MonthlyReports.

    Pure Python (no Qt). Returns DTOs for the view to render.
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        self._reports = reports
        self._logger = logger
        self._year_cache: Dict[int, YearlyStats] = {}
        self._year_category_cache: Dict[int, YearlyCategoryBreakdown] = {}

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

    # ---- Category hierarchy API ----
    def get_category_breakdown(self, year: int) -> YearlyCategoryBreakdown:
        cached = self._year_category_cache.get(year)
        if cached is not None:
            return cached

        # Accumulate earnings and expenses by category -> sub_category
        earn_cat_totals: Dict[str, float] = {}
        earn_children: Dict[str, Dict[str, float]] = {}

        exp_cat_totals: Dict[str, float] = {}
        exp_children: Dict[str, Dict[str, float]] = {}

        for mr in [r for r in self._reports if int(r.month.year) == year]:
            # Earnings (amounts positive)
            if getattr(mr, "earnings", None) is not None and not mr.earnings.empty:
                df = mr.earnings
                if "category" in df.columns and "sub_category" in df.columns:
                    grouped = (
                        df.groupby(["category", "sub_category"])  # type: ignore[index]
                        ["amount"].sum()
                    )
                    for (cat, sub), val in grouped.items():
                        amt = float(val)
                        if not cat:
                            cat = "(Uncategorized)"
                        if not sub:
                            sub = "(Uncategorized)"
                        earn_cat_totals[cat] = earn_cat_totals.get(cat, 0.0) + amt
                        children = earn_children.setdefault(cat, {})
                        children[sub] = children.get(sub, 0.0) + amt

            # Expenses (amounts negative -> store positive)
            if getattr(mr, "expenses", None) is not None and not mr.expenses.empty:
                df = mr.expenses
                if "category" in df.columns and "sub_category" in df.columns:
                    grouped = (
                        df.groupby(["category", "sub_category"])  # type: ignore[index]
                        ["amount"].sum()
                    )
                    for (cat, sub), val in grouped.items():
                        amt = float(-val)  # invert to positive for display
                        if not cat:
                            cat = "(Uncategorized)"
                        if not sub:
                            sub = "(Uncategorized)"
                        exp_cat_totals[cat] = exp_cat_totals.get(cat, 0.0) + amt
                        children = exp_children.setdefault(cat, {})
                        children[sub] = children.get(sub, 0.0) + amt

        # Build nodes sorted by total desc; children sorted desc
        def build_nodes(cat_totals: Dict[str, float], child_map: Dict[str, Dict[str, float]]) -> List[CategoryNode]:
            nodes: List[CategoryNode] = []
            for cat, total in cat_totals.items():
                subs_map = child_map.get(cat, {})
                subs_list: List[Tuple[str, float]] = sorted(
                    [(s, float(a)) for s, a in subs_map.items()], key=lambda x: x[1], reverse=True
                )
                nodes.append(CategoryNode(name=cat or "(Uncategorized)", amount=float(total), children=subs_list))
            nodes.sort(key=lambda n: n.amount, reverse=True)
            return nodes

        breakdown = YearlyCategoryBreakdown(
            earnings=build_nodes(earn_cat_totals, earn_children),
            expenses=build_nodes(exp_cat_totals, exp_children),
        )
        self._year_category_cache[year] = breakdown
        return breakdown
