"""Expenses statistics controller.

Computes expenses page data from MonthlyReports.
Pure Python (no Qt).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

import pandas as pd

from budget_analyser.core.models import MonthlyReports


@dataclass(frozen=True)
class _CategoryNode:
    name: str
    total: float
    subcats: list[tuple[str, float]]


@dataclass(frozen=True)
class _YearSummary:
    total: float
    months: list[
        tuple[
            pd.Period,
            float,
            list[tuple[str, float, list[tuple[str, float]]]],
        ]
    ]


class ExpensesStatsController:  # pylint: disable=too-many-public-methods
    """Controller to compute Expenses page data.

    Totals are returned as positive values for UI display.
    """

    def __init__(
        self,
        reports: list[MonthlyReports],
        logger: logging.Logger,
    ) -> None:
        self._reports = reports
        self._logger = logger
        self._by_period: dict[pd.Period, MonthlyReports] = {
            mr.month: mr for mr in self._reports
        }
        self._month_total_cache: dict[pd.Period, float] = {}
        self._category_cache: dict[
            pd.Period, list[_CategoryNode]
        ] = {}
        self._year_cache: dict[int, _YearSummary] = {}

    def available_months(self) -> list[pd.Period]:
        """Return sorted list of available months."""
        return sorted(self._by_period.keys())

    def available_years(self) -> list[int]:
        """Return sorted list of years that have data."""
        return sorted(
            {int(p.year) for p in self._by_period.keys()},
        )

    @staticmethod
    def month_label(period: pd.Period) -> str:
        """Return short month label."""
        short_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        return (
            f"{short_names[int(period.month) - 1]} "
            f"{int(period.year)}"
        )

    def total_for_month(self, period: pd.Period) -> float:
        """Return total expenses (positive) for a month."""
        cached = self._month_total_cache.get(period)
        if cached is not None:
            return cached
        mr = self._by_period.get(period)
        if (mr is None or mr.expenses is None
                or mr.expenses.empty):
            self._month_total_cache[period] = 0.0
            return 0.0
        total = (
            float((-mr.expenses["amount"]).sum())
            if "amount" in mr.expenses.columns else 0.0
        )
        self._month_total_cache[period] = total
        return total

    def category_breakdown(
        self, period: pd.Period,
    ) -> list[tuple[str, float, list[tuple[str, float]]]]:
        """Return category breakdown for a month."""
        cached = self._category_cache.get(period)
        if cached is None:
            cached = self._compute_category_nodes(period)
            self._category_cache[period] = cached
        return [
            (n.name, n.total, list(n.subcats))
            for n in cached
        ]

    def transactions(
        self,
        period: pd.Period,
        *,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return transactions for a month."""
        mr = self._by_period.get(period)
        if mr is None:
            return pd.DataFrame()
        df = mr.expenses
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "category", "sub_category",
            ])
        out = df
        if category:
            if "category" in out.columns:
                out = out[
                    out["category"].fillna("") == category
                ]
            else:
                return pd.DataFrame(columns=df.columns)
        if sub_category:
            if "sub_category" in out.columns:
                out = out[
                    out["sub_category"].fillna("")
                    == sub_category
                ]
            else:
                return pd.DataFrame(columns=df.columns)
        return out.copy()

    def total_for_year(self, year: int) -> float:
        """Return total expenses (positive) for a year."""
        return self._get_year_summary(year).total

    def year_breakdown(
        self, year: int,
    ) -> list[
        tuple[
            pd.Period,
            float,
            list[tuple[str, float, list[tuple[str, float]]]],
        ]
    ]:
        """Return breakdown by month for a year."""
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: pd.Period | None = None,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return transactions for a year."""
        frames = []
        for period in self._by_period:
            if int(period.year) != year:
                continue
            if month is not None and period != month:
                continue
            mr = self._by_period.get(period)
            if (mr is None or mr.expenses is None
                    or mr.expenses.empty):
                continue
            df = mr.expenses
            if category and "category" in df.columns:
                df = df[
                    df["category"].fillna("") == category
                ]
            if sub_category and "sub_category" in df.columns:
                df = df[
                    df["sub_category"].fillna("")
                    == sub_category
                ]
            if not df.empty:
                frames.append(df)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "category", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    def total_for_range(
        self, start_date: date, end_date: date,
    ) -> float:
        """Return total expenses (positive) for a date range."""
        total = 0.0
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (
                (df["transaction_date"].dt.date >= start_date)
                & (df["transaction_date"].dt.date <= end_date)
            )
            total += float((-df.loc[mask, "amount"]).sum())
        return total

    def category_breakdown_for_range(
        self, start_date: date, end_date: date,
    ) -> list[tuple[str, float, list[tuple[str, float]]]]:
        """Return category breakdown for a date range."""
        frames = []
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (
                (df["transaction_date"].dt.date >= start_date)
                & (df["transaction_date"].dt.date <= end_date)
            )
            frames.append(df.loc[mask])

        if not frames:
            return []

        combined = pd.concat(frames, ignore_index=True)
        if combined.empty:
            return []

        result: list[
            tuple[str, float, list[tuple[str, float]]]
        ] = []

        if "category" in combined.columns:
            cat_series = (
                combined.groupby("category")["amount"]
                .sum()
                .sort_values()
            )
            cat_items = [
                (
                    str(cat) if cat else "(Uncategorized)",
                    float(-total),
                )
                for cat, total in cat_series.items()
            ]
            cat_items.sort(
                key=lambda x: x[1], reverse=True,
            )
        else:
            fallback_total = (
                float((-combined["amount"]).sum())
                if "amount" in combined.columns else 0.0
            )
            cat_items = [("(Uncategorized)", fallback_total)]

        for cat_name, cat_total in cat_items:
            subcats_list = self._build_subcats_for_category(
                combined, cat_name,
            )
            result.append(
                (cat_name, cat_total, subcats_list),
            )

        return result

    def transactions_for_range(
        self,
        start_date: date,
        end_date: date,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return transactions within a date range."""
        frames = []
        for mr in self._reports:
            if mr.expenses is None or mr.expenses.empty:
                continue
            df = mr.expenses
            if "transaction_date" not in df.columns:
                continue
            mask = (
                (df["transaction_date"].dt.date >= start_date)
                & (df["transaction_date"].dt.date <= end_date)
            )
            filtered = df.loc[mask]
            if category and "category" in filtered.columns:
                filtered = filtered[
                    filtered["category"].fillna("") == category
                ]
            if (sub_category
                    and "sub_category" in filtered.columns):
                filtered = filtered[
                    filtered["sub_category"].fillna("")
                    == sub_category
                ]
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
        self,
        data: pd.DataFrame,
        cat_name: str,
    ) -> list[tuple[str, float]]:
        """Build subcategory breakdown for a category."""
        dcat = data
        if "category" in data.columns:
            cat_filter = (
                "" if cat_name == "(Uncategorized)"
                else cat_name
            )
            dcat = data[
                data["category"].fillna("") == cat_filter
            ]

        if "sub_category" not in dcat.columns or dcat.empty:
            return []

        sub_series = (
            dcat.groupby("sub_category")["amount"]
            .sum()
            .sort_values()
        )
        subcats_list = [
            (
                str(sub) if sub else "(Uncategorized)",
                float(-val),
            )
            for sub, val in sub_series.items()
        ]
        subcats_list.sort(
            key=lambda x: x[1], reverse=True,
        )
        return subcats_list

    def _compute_category_nodes(
        self, period: pd.Period,
    ) -> list[_CategoryNode]:
        """Compute category nodes for a month."""
        mr = self._by_period.get(period)
        if (mr is None or mr.expenses is None
                or mr.expenses.empty):
            return []
        df = mr.expenses
        if "category" in df.columns and not df.empty:
            cat_series = (
                df.groupby("category")["amount"]
                .sum()
                .sort_values()
            )
            cat_items = [
                (
                    str(cat) if cat else "(Uncategorized)",
                    float(-total),
                )
                for cat, total in cat_series.items()
            ]
            cat_items.sort(
                key=lambda x: x[1], reverse=True,
            )
        else:
            fallback_total = (
                float((-df["amount"]).sum())
                if "amount" in df.columns else 0.0
            )
            cat_items = [("(Uncategorized)", fallback_total)]

        nodes: list[_CategoryNode] = []
        for cat_name, cat_total in cat_items:
            subcats_list = self._build_subcats_for_category(
                df, cat_name,
            )
            nodes.append(_CategoryNode(
                name=cat_name,
                total=float(cat_total),
                subcats=subcats_list,
            ))

        return nodes

    def _get_year_summary(self, year: int) -> _YearSummary:
        """Compute and cache yearly summary."""
        cached = self._year_cache.get(year)
        if cached is not None:
            return cached

        year_total = 0.0
        months_data: list[
            tuple[
                pd.Period,
                float,
                list[
                    tuple[
                        str,
                        float,
                        list[tuple[str, float]],
                    ]
                ],
            ]
        ] = []

        year_periods = sorted(
            p for p in self._by_period
            if int(p.year) == year
        )

        for period in year_periods:
            month_total = self.total_for_month(period)
            year_total += month_total
            cat_breakdown = self.category_breakdown(period)
            months_data.append(
                (period, month_total, cat_breakdown),
            )

        summary = _YearSummary(
            total=year_total, months=months_data,
        )
        self._year_cache[year] = summary
        return summary
