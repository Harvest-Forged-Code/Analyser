"""Earnings statistics controller.

Computes earnings page data from MonthlyReports.
Pure Python (no Qt).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from collections.abc import Iterable

import pandas as pd

from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.reporting.models import EarningsRow


@dataclass(frozen=True)
class _MonthSummary:
    total: float
    subcats: list[tuple[str, float]]


@dataclass(frozen=True)
class _YearSummary:
    total: float
    months: list[
        tuple[pd.Period, float, list[tuple[str, float]]]
    ]


class EarningsStatsController:  # pylint: disable=too-many-public-methods
    """Controller to compute Earnings page data.

    Provides:
      - available_months(), available_years()
      - total_for_month(), subcategory_totals(), transactions()
      - total_for_year(), year_breakdown()
      - table_for_month(), table_for_year(), table_for_range()
      - date range queries
    """

    def __init__(
        self,
        reports: list[MonthlyReports],
        logger: logging.Logger,
        budget_controller: object | None = None,
    ) -> None:
        self._reports = reports
        self._logger = logger
        self._budget_controller = budget_controller
        self._by_period: dict[pd.Period, MonthlyReports] = {
            mr.month: mr for mr in self._reports
        }
        self._month_cache: dict[pd.Period, _MonthSummary] = {}
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
        """Return short month label (e.g., 'Jan 2025')."""
        short_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        return (
            f"{short_names[int(period.month) - 1]} "
            f"{int(period.year)}"
        )

    def total_for_month(self, period: pd.Period) -> float:
        """Return total earnings for a month."""
        return self._get_month_summary(period).total

    def subcategory_totals(
        self, period: pd.Period,
    ) -> list[tuple[str, float]]:
        """Return sub-category totals for a month."""
        return list(
            self._get_month_summary(period).subcats,
        )

    def transactions(
        self,
        period: pd.Period,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return transactions for a month."""
        mr = self._by_period.get(period)
        if mr is None:
            return pd.DataFrame()
        df = mr.earnings
        if df is None or df.empty:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "sub_category",
            ])
        if sub_category:
            if "sub_category" in df.columns:
                df = df[
                    df["sub_category"].fillna("")
                    == sub_category
                ]
            else:
                return pd.DataFrame(columns=df.columns)
        return df.copy()

    def total_for_year(self, year: int) -> float:
        """Return total earnings for a year."""
        return self._get_year_summary(year).total

    def table_for_month(
        self, period: pd.Period,
    ) -> tuple[list[EarningsRow], float, float]:
        """Return aggregated earnings table for a month."""
        summary = self._get_month_summary(period)
        actual_map = dict(summary.subcats)
        expected_map = self._expected_for_month(period)
        return self._build_rows(actual_map, expected_map)

    def table_for_year(
        self, year: int,
    ) -> tuple[list[EarningsRow], float, float]:
        """Return aggregated earnings table for a year."""
        year_summary = self._get_year_summary(year)
        actual_map: dict[str, float] = {}
        for _, _, subcats in year_summary.months:
            for sub, amt in subcats:
                actual_map[sub] = (
                    actual_map.get(sub, 0.0) + float(amt)
                )

        periods = [
            period for period, _, _ in year_summary.months
        ]
        expected_map = self._expected_for_periods(periods)
        return self._build_rows(actual_map, expected_map)

    def table_for_range(
        self, start_date: date, end_date: date,
    ) -> tuple[list[EarningsRow], float, float]:
        """Return aggregated earnings table for a date range."""
        actual_map = dict(
            self.subcategory_totals_for_range(
                start_date, end_date,
            ),
        )
        periods = list(
            pd.period_range(
                start=start_date, end=end_date, freq="M",
            ),
        )
        expected_map = self._expected_for_periods(periods)
        return self._build_rows(actual_map, expected_map)

    def year_breakdown(
        self, year: int,
    ) -> list[tuple[pd.Period, float, list[tuple[str, float]]]]:
        """Return breakdown by month for the given year."""
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: pd.Period | None = None,
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
            if (mr is None or mr.earnings is None
                    or mr.earnings.empty):
                continue
            df = mr.earnings
            if sub_category and "sub_category" in df.columns:
                df = df[
                    df["sub_category"].fillna("")
                    == sub_category
                ]
            frames.append(df)

        if not frames:
            return pd.DataFrame(columns=[
                "transaction_date", "description", "amount",
                "from_account", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    def total_for_range(
        self, start_date: date, end_date: date,
    ) -> float:
        """Return total earnings for a date range."""
        total = 0.0
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if "transaction_date" not in df.columns:
                continue
            mask = (
                (df["transaction_date"].dt.date >= start_date)
                & (df["transaction_date"].dt.date <= end_date)
            )
            total += float(df.loc[mask, "amount"].sum())
        return total

    def subcategory_totals_for_range(
        self, start_date: date, end_date: date,
    ) -> list[tuple[str, float]]:
        """Return sub-category totals for a date range."""
        frames = []
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
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
        if (
            "sub_category" not in combined.columns
            or combined.empty
        ):
            return []

        grouped = (
            combined.groupby("sub_category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )
        return [
            (
                str(idx) if idx else "(Uncategorized)",
                float(val),
            )
            for idx, val in grouped.items()
        ]

    def transactions_for_range(
        self,
        start_date: date,
        end_date: date,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return transactions within a date range."""
        frames = []
        for mr in self._reports:
            if mr.earnings is None or mr.earnings.empty:
                continue
            df = mr.earnings
            if "transaction_date" not in df.columns:
                continue
            mask = (
                (df["transaction_date"].dt.date >= start_date)
                & (df["transaction_date"].dt.date <= end_date)
            )
            filtered = df.loc[mask]
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
                "from_account", "sub_category",
            ])
        return pd.concat(frames, ignore_index=True)

    # ---- Expected helpers ----
    def _expected_for_month(
        self, period: pd.Period,
    ) -> dict[str, float]:
        """Get expected earnings for a month."""
        if self._budget_controller is None:
            return {}
        try:
            return dict(
                self._budget_controller.get_earnings_goal_map(
                    period.strftime("%Y-%m"),
                ),
            )
        except Exception:  # pylint: disable=broad-exception-caught
            return {}

    def _expected_for_periods(
        self, periods: Iterable[pd.Period],
    ) -> dict[str, float]:
        """Get aggregated expected earnings across periods."""
        if self._budget_controller is None:
            return {}
        expected: dict[str, float] = {}
        for period in periods:
            monthly = self._expected_for_month(period)
            for sub, amt in monthly.items():
                expected[sub] = (
                    expected.get(sub, 0.0) + float(amt)
                )
        return expected

    def _build_rows(
        self,
        actual_map: dict[str, float],
        expected_map: dict[str, float],
    ) -> tuple[list[EarningsRow], float, float]:
        """Build EarningsRow list from actual vs expected."""
        actual_total = sum(actual_map.values())
        expected_total = (
            sum(expected_map.values()) if expected_map else 0.0
        )

        rows: list[EarningsRow] = []
        for sub, actual in sorted(
            actual_map.items(),
            key=lambda kv: kv[1],
            reverse=True,
        ):
            expected = float(expected_map.get(sub, 0.0))
            diff = actual - expected
            diff_pct = (
                (diff / expected * 100)
                if expected > 0 else None
            )
            pct_total = (
                (actual / actual_total * 100)
                if actual_total > 0 else 0.0
            )
            rows.append(EarningsRow(
                sub_category=sub,
                actual=float(actual),
                percent_of_total=float(pct_total),
                expected=expected,
                diff=float(diff),
                diff_percent=(
                    float(diff_pct)
                    if diff_pct is not None else None
                ),
            ))

        return rows, float(actual_total), float(expected_total)

    # ---- Internals ----
    def _get_month_summary(
        self, period: pd.Period,
    ) -> _MonthSummary:
        """Get or compute month summary from cache."""
        cached = self._month_cache.get(period)
        if cached is not None:
            return cached

        mr = self._by_period.get(period)
        if (mr is None or mr.earnings is None
                or mr.earnings.empty):
            summary = _MonthSummary(total=0.0, subcats=[])
            self._month_cache[period] = summary
            return summary

        df = mr.earnings
        total_val = (
            float(df["amount"].sum())
            if "amount" in df.columns else 0.0
        )

        if "sub_category" in df.columns and not df.empty:
            grouped = (
                df.groupby("sub_category")["amount"]
                .sum()
                .sort_values(ascending=False)
            )
            subcats_list: list[tuple[str, float]] = [
                (
                    str(idx) if idx else "(Uncategorized)",
                    float(val),
                )
                for idx, val in grouped.items()
            ]
        else:
            subcats_list = []

        summary = _MonthSummary(
            total=total_val, subcats=subcats_list,
        )
        self._month_cache[period] = summary
        return summary

    def _get_year_summary(self, year: int) -> _YearSummary:
        """Compute and cache yearly summary."""
        cached = self._year_cache.get(year)
        if cached is not None:
            return cached

        year_total = 0.0
        months_data: list[
            tuple[pd.Period, float, list[tuple[str, float]]]
        ] = []

        year_periods = sorted(
            p for p in self._by_period
            if int(p.year) == year
        )

        for period in year_periods:
            month_summary = self._get_month_summary(period)
            year_total += month_summary.total
            months_data.append((
                period,
                month_summary.total,
                list(month_summary.subcats),
            ))

        summary = _YearSummary(
            total=year_total, months=months_data,
        )
        self._year_cache[year] = summary
        return summary
