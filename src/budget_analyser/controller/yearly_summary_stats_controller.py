from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from budget_analyser.controller.controllers import MonthlyReports
from .dtos import YearlyStats, YearlyCategoryBreakdown, CategoryNode


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

    # ---- Internal computations ----
    def _compute_year_data(self, year: int) -> YearlyStats:  # pylint: disable=too-many-locals
        # Filter reports for the year
        months = [mr for mr in self._reports if int(mr.month.year) == year]

        total_earnings = 0.0
        total_expenses = 0.0

        # Sub-category accumulators
        earn_subcats: Dict[str, float] = {}
        exp_subcats: Dict[str, float] = {}

        for mr in months:

            # Earnings totals (values are positive)
            e_sum = float(mr.earnings["amount"].sum()) if not mr.earnings.empty else 0.0
            total_earnings += e_sum

            # Expenses totals (values are negative) -> store as positive for UI
            x_sum = float((-mr.expenses["amount"]).sum()) if not mr.expenses.empty else 0.0
            total_expenses += x_sum

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

        # Sort sub-categories desc by amount
        earn_sub_list: List[Tuple[str, float]] = sorted(
            earn_subcats.items(), key=lambda x: x[1], reverse=True
        )
        exp_sub_list: List[Tuple[str, float]] = sorted(
            exp_subcats.items(), key=lambda x: x[1], reverse=True
        )

        return YearlyStats(
            total_earnings=total_earnings,
            total_expenses=total_expenses,
            earn_subcats=earn_sub_list,
            exp_subcats=exp_sub_list,
        )

    # ---- Category hierarchy API ----
    def get_category_breakdown(self, year: int) -> YearlyCategoryBreakdown:  # pylint: disable=too-many-locals
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
        def build_nodes(
            cat_totals: Dict[str, float],
            child_map: Dict[str, Dict[str, float]]
        ) -> List[CategoryNode]:
            nodes: List[CategoryNode] = []
            for cat, total in cat_totals.items():
                subs_map = child_map.get(cat, {})
                subs_list: List[Tuple[str, float]] = sorted(
                    [(s, float(a)) for s, a in subs_map.items()],
                    key=lambda x: x[1],
                    reverse=True
                )
                node = CategoryNode(
                    name=cat or "(Uncategorized)",
                    amount=float(total),
                    children=subs_list
                )
                nodes.append(node)
            nodes.sort(key=lambda n: n.amount, reverse=True)
            return nodes

        breakdown = YearlyCategoryBreakdown(
            earnings=build_nodes(earn_cat_totals, earn_children),
            expenses=build_nodes(exp_cat_totals, exp_children),
        )
        self._year_category_cache[year] = breakdown
        return breakdown
