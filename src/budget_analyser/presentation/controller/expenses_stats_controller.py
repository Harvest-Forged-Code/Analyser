from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from budget_analyser.presentation.controllers import MonthlyReports
from .utils import month_names as _month_names


@dataclass(frozen=True)
class _CategoryNode:
    name: str
    total: float
    subcats: List[Tuple[str, float]]  # (sub_category, total)


class ExpensesStatsController:
    """Controller to compute Expenses page data from MonthlyReports.

    Pure Python (no Qt). Provides a simple API for the view to render:
      - available_months()
      - month_label(period)
      - total_for_month(period)
      - category_breakdown(period) -> List[(category, total, [(sub_category, total)])]
      - transactions(period, category=None, sub_category=None)

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

    # ---- Public API ----
    def available_months(self) -> List[pd.Period]:
        return sorted(self._by_period.keys())

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

    def category_breakdown(self, period: pd.Period) -> List[Tuple[str, float, List[Tuple[str, float]]]]:
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

    # ---- Internals ----
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
                (str(cat) if cat else "(Uncategorized)", float(-total)) for cat, total in cat_series.items()
            ]
            cat_items.sort(key=lambda x: x[1], reverse=True)
        else:
            # No category column
            cat_items = [("(Uncategorized)", float((-df["amount"]).sum()) if "amount" in df.columns else 0.0)]

        nodes: list[_CategoryNode] = []
        for cat_name, cat_total in cat_items:
            # Build sub-category totals for this category
            subcats_list: List[Tuple[str, float]] = []
            dcat = df
            if "category" in df.columns:
                dcat = df[df["category"].fillna("") == ("" if cat_name == "(Uncategorized)" else cat_name)]

            if "sub_category" in dcat.columns and not dcat.empty:
                sub_series = dcat.groupby("sub_category")["amount"].sum().sort_values()
                subcats_list = [
                    (str(sub) if sub else "(Uncategorized)", float(-val)) for sub, val in sub_series.items()
                ]
                subcats_list.sort(key=lambda x: x[1], reverse=True)

            nodes.append(_CategoryNode(name=cat_name, total=float(cat_total), subcats=subcats_list))

        return nodes
