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
        """Initialize the earnings statistics controller.

        Args:
            reports: List of monthly report objects containing
                earnings DataFrames and period metadata.
            logger: Logger instance for diagnostic messages.
            budget_controller: Optional controller exposing
                ``get_earnings_goal_map()`` for expected-earnings
                lookups. When ``None``, expected values default
                to zero.

        Example:
            >>> ctrl = EarningsStatsController(
            ...     reports=reports,
            ...     logger=logging.getLogger(__name__),
            ... )
        """
        self._reports = reports
        self._logger = logger
        self._budget_controller = budget_controller
        self._by_period: dict[pd.Period, MonthlyReports] = {
            mr.month: mr for mr in self._reports
        }
        self._month_cache: dict[pd.Period, _MonthSummary] = {}
        self._year_cache: dict[int, _YearSummary] = {}

    def available_months(self) -> list[pd.Period]:
        """Return sorted list of available months.

        Returns:
            Periods sorted in chronological order.

        Example:
            >>> months = ctrl.available_months()
            >>> months[0]
            Period('2024-01', 'M')
        """
        return sorted(self._by_period.keys())

    def available_years(self) -> list[int]:
        """Return sorted list of years that have data.

        Returns:
            Distinct years in ascending order.

        Example:
            >>> ctrl.available_years()
            [2023, 2024]
        """
        return sorted(
            {int(p.year) for p in self._by_period.keys()},
        )

    @staticmethod
    def month_label(period: pd.Period) -> str:
        """Return short month label (e.g., ``'Jan 2025'``).

        Args:
            period: A monthly pandas Period.

        Returns:
            Formatted string like ``"Jan 2025"``.

        Example:
            >>> EarningsStatsController.month_label(
            ...     pd.Period("2025-01", freq="M"),
            ... )
            'Jan 2025'
        """
        short_names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        ]
        return (
            f"{short_names[int(period.month) - 1]} "
            f"{int(period.year)}"
        )

    def total_for_month(self, period: pd.Period) -> float:
        """Return total earnings for a month.

        Args:
            period: The month to query.

        Returns:
            Sum of all earnings amounts for the period.
            Returns ``0.0`` when no data exists.

        Example:
            >>> ctrl.total_for_month(pd.Period("2024-01", "M"))
            5200.0
        """
        return self._get_month_summary(period).total

    def subcategory_totals(
        self, period: pd.Period,
    ) -> list[tuple[str, float]]:
        """Return sub-category totals for a month.

        Args:
            period: The month to query.

        Returns:
            List of ``(sub_category_name, total_amount)`` tuples
            sorted by amount descending.

        Example:
            >>> totals = ctrl.subcategory_totals(
            ...     pd.Period("2024-01", "M"),
            ... )
            >>> totals[0]
            ('Salary', 5000.0)
        """
        return list(
            self._get_month_summary(period).subcats,
        )

    def transactions(
        self,
        period: pd.Period,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return earnings transactions for a month.

        Optionally filters to a specific sub-category.

        Args:
            period: The month to query.
            sub_category: If provided, only return transactions
                matching this sub-category name.

        Returns:
            DataFrame with columns ``transaction_date``,
            ``description``, ``amount``, ``from_account``,
            and ``sub_category``. Empty DataFrame when no
            data exists.

        Example:
            >>> df = ctrl.transactions(
            ...     pd.Period("2024-01", "M"),
            ...     sub_category="Salary",
            ... )
            >>> list(df.columns)
            ['transaction_date', 'description', 'amount', ...]
        """
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
        """Return total earnings for a year.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            Sum of all monthly earnings totals for the year.

        Example:
            >>> ctrl.total_for_year(2024)
            62400.0
        """
        return self._get_year_summary(year).total

    def table_for_month(
        self, period: pd.Period,
    ) -> tuple[list[EarningsRow], float, float]:
        """Build the earnings table for a single month.

        Retrieves all earnings transactions for the given month
        and computes actual vs expected totals per sub-category.

        Args:
            period: The month to query.

        Returns:
            A 3-tuple of:
                - rows: List of EarningsRow with category,
                  actual, expected, diff, and percentages.
                - actual_total: Sum of all actual earnings.
                - expected_total: Sum of all expected earnings.

        Example:
            >>> rows, actual, expected = ctrl.table_for_month(
            ...     pd.Period("2024-01", "M"),
            ... )
            >>> len(rows)
            3
            >>> actual
            5200.0
        """
        summary = self._get_month_summary(period)
        actual_map = dict(summary.subcats)
        expected_map = self._expected_for_month(period)
        return self._build_rows(actual_map, expected_map)

    def table_for_year(
        self, year: int,
    ) -> tuple[list[EarningsRow], float, float]:
        """Build the earnings table for an entire year.

        Aggregates sub-category totals across all months in the
        year and computes actual vs expected values.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            A 3-tuple of:
                - rows: List of EarningsRow aggregated across
                  all months of the year.
                - actual_total: Sum of all actual earnings.
                - expected_total: Sum of all expected earnings.

        Example:
            >>> rows, actual, expected = ctrl.table_for_year(
            ...     2024,
            ... )
            >>> actual
            62400.0
        """
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
        """Build the earnings table for a custom date range.

        Aggregates sub-category totals for transactions falling
        within the specified date range inclusive.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            A 3-tuple of:
                - rows: List of EarningsRow for the range.
                - actual_total: Sum of all actual earnings.
                - expected_total: Sum of all expected earnings.

        Example:
            >>> from datetime import date
            >>> rows, actual, expected = ctrl.table_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ... )
        """
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
        """Return month-by-month breakdown for the given year.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            List of 3-tuples, one per month:
                - period: The pandas Period for the month.
                - total: Total earnings for that month.
                - subcats: List of ``(sub_category, amount)``
                  tuples for the month.

        Example:
            >>> breakdown = ctrl.year_breakdown(2024)
            >>> period, total, subcats = breakdown[0]
            >>> total
            5200.0
        """
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: pd.Period | None = None,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return earnings transactions for a year.

        Optionally restricts to a specific month and/or
        sub-category.

        Args:
            year: Calendar year (e.g. ``2024``).
            month: If provided, only include this month.
            sub_category: If provided, filter to this
                sub-category name.

        Returns:
            DataFrame of matching transactions. Empty
            DataFrame with standard columns when no data
            exists.

        Example:
            >>> df = ctrl.transactions_for_year(
            ...     2024, sub_category="Salary",
            ... )
            >>> len(df) > 0
            True
        """
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
        """Return total earnings for a date range.

        Sums earnings amounts across all months for
        transactions whose date falls within the range.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            Total earnings amount. Returns ``0.0`` when
            no transactions match.

        Example:
            >>> from datetime import date
            >>> ctrl.total_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ... )
            31200.0
        """
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
        """Return sub-category totals for a date range.

        Groups earnings by sub-category for transactions within
        the given date range.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            List of ``(sub_category_name, total_amount)`` tuples
            sorted by amount descending. Empty list when no
            data exists.

        Example:
            >>> from datetime import date
            >>> totals = ctrl.subcategory_totals_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ... )
            >>> totals[0]
            ('Salary', 30000.0)
        """
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
        """Return earnings transactions within a date range.

        Collects transactions across all monthly reports whose
        transaction date falls within the range, optionally
        filtered by sub-category.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).
            sub_category: If provided, filter to this
                sub-category name.

        Returns:
            DataFrame with columns ``transaction_date``,
            ``description``, ``amount``, ``from_account``,
            and ``sub_category``. Empty DataFrame when no
            data matches.

        Example:
            >>> from datetime import date
            >>> df = ctrl.transactions_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ...     sub_category="Salary",
            ... )
        """
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
        """Get expected earnings for a month from budget goals.

        Args:
            period: The month to look up.

        Returns:
            Mapping of sub-category to expected amount.
            Empty dict when no budget controller is set or
            lookup fails.
        """
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
        """Get aggregated expected earnings across periods.

        Sums expected amounts per sub-category across multiple
        months.

        Args:
            periods: Iterable of monthly periods to aggregate.

        Returns:
            Mapping of sub-category to cumulative expected
            amount. Empty dict when no budget controller is set.
        """
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
        """Build EarningsRow list from actual vs expected maps.

        Computes difference, percentage of total, and diff
        percentage for each sub-category.

        Args:
            actual_map: Sub-category to actual amount mapping.
            expected_map: Sub-category to expected amount
                mapping.

        Returns:
            A 3-tuple of:
                - rows: EarningsRow list sorted by actual
                  amount descending.
                - actual_total: Sum of actual values.
                - expected_total: Sum of expected values.
        """
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
        """Get or compute month summary from cache.

        Groups earnings by sub-category and caches the result
        for subsequent calls with the same period.

        Args:
            period: The month to summarise.

        Returns:
            Cached or freshly computed ``_MonthSummary`` with
            total and sub-category breakdown.
        """
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
        """Compute and cache yearly earnings summary.

        Iterates months for the year, accumulates totals,
        and caches the result.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            Cached or freshly computed ``_YearSummary`` with
            aggregate total and per-month breakdown.
        """
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
