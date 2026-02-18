"""Expenses statistics service.

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


class ExpensesStatsService:  # pylint: disable=too-many-public-methods
    """Service to compute Expenses page data.

    Totals are returned as positive values for UI display.
    """

    def __init__(
        self,
        reports: list[MonthlyReports],
        logger: logging.Logger,
    ) -> None:
        """Initialize the expenses statistics service.

        Args:
            reports: List of monthly report objects containing
                expenses DataFrames and period metadata.
            logger: Logger instance for diagnostic messages.

        Example:
            >>> svc = ExpensesStatsService(
            ...     reports=reports,
            ...     logger=logging.getLogger(__name__),
            ... )
        """
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
        """Return sorted list of available months.

        Returns:
            Periods sorted in chronological order.

        Example:
            >>> months = svc.available_months()
            >>> months[0]
            Period('2024-01', 'M')
        """
        return sorted(self._by_period.keys())

    def available_years(self) -> list[int]:
        """Return sorted list of years that have data.

        Returns:
            Distinct years in ascending order.

        Example:
            >>> svc.available_years()
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
            >>> ExpensesStatsService.month_label(
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
        """Return total expenses as a positive value for a month.

        Results are cached after the first computation.

        Args:
            period: The month to query.

        Returns:
            Sum of all expense amounts (negated to positive)
            for the period. Returns ``0.0`` when no data exists.

        Example:
            >>> svc.total_for_month(pd.Period("2024-01", "M"))
            3200.0
        """
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
        """Return hierarchical category breakdown for a month.

        Computes expense totals grouped by category, each with
        its sub-category breakdown. Results are cached.

        Args:
            period: The month to query.

        Returns:
            List of 3-tuples, one per category:
                - category_name: The expense category
                  (e.g. ``"Needs"``).
                - category_total: Total expenses (positive)
                  for this category.
                - subcats: List of ``(sub_category, amount)``
                  tuples sorted by amount descending.

        Example:
            >>> breakdown = svc.category_breakdown(
            ...     pd.Period("2024-01", "M"),
            ... )
            >>> cat, total, subcats = breakdown[0]
            >>> cat
            'Needs'
            >>> subcats[0]
            ('Rent', 1500.0)
        """
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
        """Return expense transactions for a month.

        Optionally filters to a specific category and/or
        sub-category.

        Args:
            period: The month to query.
            category: If provided, only return transactions
                matching this category.
            sub_category: If provided, only return transactions
                matching this sub-category.

        Returns:
            DataFrame with columns ``transaction_date``,
            ``description``, ``amount``, ``from_account``,
            ``category``, and ``sub_category``. Empty DataFrame
            when no data exists.

        Example:
            >>> df = svc.transactions(
            ...     pd.Period("2024-01", "M"),
            ...     category="Needs",
            ... )
            >>> list(df.columns)[:3]
            ['transaction_date', 'description', 'amount']
        """
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
        """Return total expenses as a positive value for a year.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            Sum of all monthly expense totals for the year.

        Example:
            >>> svc.total_for_year(2024)
            38400.0
        """
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
        """Return month-by-month breakdown for a year.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            List of 3-tuples, one per month:
                - period: The pandas Period for the month.
                - total: Total expenses (positive) for the
                  month.
                - categories: List of category 3-tuples
                  matching the structure returned by
                  :meth:`category_breakdown`.

        Example:
            >>> breakdown = svc.year_breakdown(2024)
            >>> period, total, cats = breakdown[0]
            >>> total
            3200.0
        """
        return list(self._get_year_summary(year).months)

    def transactions_for_year(
        self,
        year: int,
        *,
        month: pd.Period | None = None,
        category: str | None = None,
        sub_category: str | None = None,
    ) -> pd.DataFrame:
        """Return expense transactions for a year.

        Optionally restricts to a specific month, category,
        and/or sub-category.

        Args:
            year: Calendar year (e.g. ``2024``).
            month: If provided, only include this month.
            category: If provided, filter to this category.
            sub_category: If provided, filter to this
                sub-category.

        Returns:
            DataFrame of matching transactions. Empty
            DataFrame with standard columns when no data
            exists.

        Example:
            >>> df = svc.transactions_for_year(
            ...     2024, category="Needs",
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
        """Return total expenses as positive for a date range.

        Sums negated expense amounts across all months for
        transactions whose date falls within the range.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            Total expenses as a positive number. Returns
            ``0.0`` when no transactions match.

        Example:
            >>> from datetime import date
            >>> svc.total_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ... )
            19200.0
        """
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
        """Return hierarchical category breakdown for a range.

        Aggregates expenses by category and sub-category for
        transactions within the specified date range.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).

        Returns:
            List of 3-tuples, one per category:
                - category_name: The expense category.
                - category_total: Total expenses (positive).
                - subcats: List of ``(sub_category, amount)``
                  tuples sorted by amount descending.
            Empty list when no data matches.

        Example:
            >>> from datetime import date
            >>> breakdown = svc.category_breakdown_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ... )
            >>> cat, total, subcats = breakdown[0]
        """
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
        """Return expense transactions within a date range.

        Collects transactions across all monthly reports whose
        transaction date falls within the range, optionally
        filtered by category and/or sub-category.

        Args:
            start_date: Start of the range (inclusive).
            end_date: End of the range (inclusive).
            category: If provided, filter to this category.
            sub_category: If provided, filter to this
                sub-category.

        Returns:
            DataFrame with columns ``transaction_date``,
            ``description``, ``amount``, ``from_account``,
            ``category``, and ``sub_category``. Empty
            DataFrame when no data matches.

        Example:
            >>> from datetime import date
            >>> df = svc.transactions_for_range(
            ...     date(2024, 1, 1), date(2024, 6, 30),
            ...     category="Needs",
            ... )
        """
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
        """Build subcategory breakdown for a single category.

        Filters the DataFrame to the given category, groups by
        sub-category, and returns positive totals sorted
        descending.

        Args:
            data: Expenses DataFrame with ``category``,
                ``sub_category``, and ``amount`` columns.
            cat_name: Category name to filter on. Use
                ``"(Uncategorized)"`` for rows with empty
                category.

        Returns:
            List of ``(sub_category, amount)`` tuples sorted
            by amount descending. Empty list when no
            sub-category data is available.
        """
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
        """Compute category nodes with sub-category detail.

        Groups the month's expenses by category, then builds
        a ``_CategoryNode`` for each containing sub-category
        breakdowns sorted by amount descending.

        Args:
            period: The month to compute nodes for.

        Returns:
            List of ``_CategoryNode`` instances sorted by
            total descending. Empty list when no expense data
            exists for the period.
        """
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
        """Compute and cache yearly expense summary.

        Iterates months for the year, accumulates totals and
        category breakdowns, and caches the result.

        Args:
            year: Calendar year (e.g. ``2024``).

        Returns:
            Cached or freshly computed ``_YearSummary`` with
            aggregate total and per-month category breakdown.
        """
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


# Backward-compat alias
ExpensesStatsController = ExpensesStatsService
