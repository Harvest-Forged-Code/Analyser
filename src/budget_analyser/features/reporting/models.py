"""Reporting feature DTOs.

Data transfer objects for earnings and expenses statistics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EarningsRow:
    """A row in the earnings aggregated table.

    Attributes:
        sub_category: Sub-category name.
        actual: Actual amount received.
        percent_of_total: Percentage of total earnings.
        expected: Expected amount from goals.
        diff: Difference (actual - expected).
        diff_percent: Percentage difference.

    Example:
        >>> row = EarningsRow(
        ...     sub_category="Salary",
        ...     actual=5000.0,
        ...     percent_of_total=80.0,
        ...     expected=4500.0,
        ...     diff=500.0,
        ...     diff_percent=11.11,
        ... )
        >>> row.sub_category
        'Salary'
        >>> row.diff
        500.0
    """

    sub_category: str
    actual: float
    percent_of_total: float
    expected: float
    diff: float
    diff_percent: float | None


@dataclass(frozen=True)
class EarningsMonthTrend:
    """Monthly total for trend sparklines and charts.

    Attributes:
        period: Period string (e.g., ``"2026-01"``).
        label: Human-readable label (e.g., ``"Jan 2026"``).
        total: Total earnings for the period.

    Example:
        >>> trend = EarningsMonthTrend(
        ...     period="2026-01", label="Jan 2026", total=5200.0,
        ... )
    """

    period: str
    label: str
    total: float


@dataclass(frozen=True)
class EarningsSourceTrend:
    """Per-source monthly totals for row sparklines.

    Attributes:
        sub_category: Income source name.
        months: Monthly trend data for this source.

    Example:
        >>> src = EarningsSourceTrend(
        ...     sub_category="Salary",
        ...     months=[
        ...         EarningsMonthTrend("2026-01", "Jan 2026", 4500.0),
        ...     ],
        ... )
    """

    sub_category: str
    months: list[EarningsMonthTrend]


@dataclass(frozen=True)
class EarningsDashboard:
    """Aggregated dashboard data for KPI cards.

    Attributes:
        current_month_total: Earnings total for the selected month.
        previous_month_total: Earnings total for the prior month.
        mom_change_percent: Month-over-month change percentage.
        ytd_total: Year-to-date earnings total.
        goal_total: Sum of earnings goals for the selected month.
        goal_progress_percent: Percentage of goal achieved.
        period: Selected period string (e.g., ``"2026-02"``).
        year: Calendar year of the selected period.
        sparkline: Last 6 months of totals for mini chart.

    Example:
        >>> dash = EarningsDashboard(
        ...     current_month_total=5200.0,
        ...     previous_month_total=4800.0,
        ...     mom_change_percent=8.33,
        ...     ytd_total=10000.0,
        ...     goal_total=6000.0,
        ...     goal_progress_percent=86.67,
        ...     period="2026-02",
        ...     year=2026,
        ...     sparkline=[4500.0, 4800.0, 5000.0, 4900.0, 4800.0, 5200.0],
        ... )
    """

    current_month_total: float
    previous_month_total: float
    mom_change_percent: float | None
    ytd_total: float
    goal_total: float
    goal_progress_percent: float | None
    period: str
    year: int
    sparkline: list[float]
