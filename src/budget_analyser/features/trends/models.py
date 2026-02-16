"""Trends feature DTOs.

Data transfer objects for trend analysis, spending patterns,
and burn rate tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

import pandas as pd


class TrendDirection(Enum):
    """Trend direction indicator."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"

    @classmethod
    def from_change(
        cls,
        change_pct: float,
        threshold: float = 5.0,
    ) -> TrendDirection:
        """Determine trend direction from percentage change.

        Args:
            change_pct: Percentage change value.
            threshold: Minimum change to consider non-stable.

        Returns:
            TrendDirection based on the change.
        """
        if pd.isna(change_pct):
            return cls.UNKNOWN
        if change_pct > threshold:
            return cls.RISING
        if change_pct < -threshold:
            return cls.FALLING
        return cls.STABLE


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class MonthlyTrend:
    """Trend data for a single month.

    Attributes:
        period: The month (as pandas Period).
        value: The actual value for the month.
        mom_change: Month-over-month absolute change.
        mom_change_pct: Month-over-month percentage change.
        yoy_change: Year-over-year absolute change.
        yoy_change_pct: Year-over-year percentage change.
        moving_avg_3m: 3-month moving average.
        moving_avg_6m: 6-month moving average.
        moving_avg_12m: 12-month moving average.
        direction: Trend direction based on recent movement.
    """

    period: pd.Period
    value: float
    mom_change: float = 0.0
    mom_change_pct: float = 0.0
    yoy_change: float | None = None
    yoy_change_pct: float | None = None
    moving_avg_3m: float | None = None
    moving_avg_6m: float | None = None
    moving_avg_12m: float | None = None
    direction: TrendDirection = TrendDirection.UNKNOWN


@dataclass
class TrendAnalysisResult:
    """Complete trend analysis result.

    Attributes:
        monthly_trends: List of MonthlyTrend objects.
        overall_direction: Overall trend direction.
        average_mom_change_pct: Average month-over-month change.
        volatility: Standard deviation of monthly values.
        highest_month: Period with highest value.
        lowest_month: Period with lowest value.
    """

    monthly_trends: list[MonthlyTrend] = field(
        default_factory=list,
    )
    overall_direction: TrendDirection = TrendDirection.UNKNOWN
    average_mom_change_pct: float = 0.0
    volatility: float = 0.0
    highest_month: pd.Period | None = None
    lowest_month: pd.Period | None = None

    def get_trend(self, period: pd.Period) -> MonthlyTrend | None:
        """Get trend data for a specific period."""
        for trend in self.monthly_trends:
            if trend.period == period:
                return trend
        return None

    def recent_trends(self, n: int = 3) -> list[MonthlyTrend]:
        """Get the most recent N trends."""
        return (
            self.monthly_trends[-n:]
            if self.monthly_trends else []
        )


# --- Spending Pattern DTOs ---

class DayOfWeek(Enum):
    """Days of the week."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_int(cls, day: int) -> DayOfWeek:
        """Convert integer (0=Monday) to DayOfWeek."""
        return cls(day)


@dataclass(frozen=True)
class ParetoItem:
    """A single item in Pareto analysis.

    Attributes:
        category: Category name.
        amount: Total amount for this category.
        percentage: Percentage of total spending.
        cumulative_percentage: Running cumulative percentage.
        is_top_80: Whether in the top 80% of spending.
    """

    category: str
    amount: float
    percentage: float
    cumulative_percentage: float
    is_top_80: bool


@dataclass
class ParetoAnalysis:
    """Pareto (80/20) analysis result.

    Attributes:
        items: List of ParetoItem sorted by amount descending.
        total_amount: Total spending across all categories.
    """

    items: list[ParetoItem] = field(default_factory=list)
    total_amount: float = 0.0

    @property
    def top_80_count(self) -> int:
        """Number of categories in top 80%."""
        return sum(1 for item in self.items if item.is_top_80)

    @property
    def top_80_categories(self) -> list[str]:
        """Categories comprising top 80% of spending."""
        return [
            item.category for item in self.items if item.is_top_80
        ]

    @property
    def concentration_ratio(self) -> float:
        """Ratio of top 80% categories to total categories."""
        if not self.items:
            return 0.0
        return self.top_80_count / len(self.items)


@dataclass(frozen=True)
class DayPattern:
    """Spending pattern for a day of the week.

    Attributes:
        day: Day of the week.
        total_amount: Total spending on this day.
        transaction_count: Number of transactions.
        average_transaction: Average transaction amount.
        percentage_of_week: Percentage of weekly spending.
    """

    day: DayOfWeek
    total_amount: float
    transaction_count: int
    average_transaction: float
    percentage_of_week: float


@dataclass
class WeeklyPattern:
    """Weekly spending pattern analysis.

    Attributes:
        day_patterns: Spending data for each day.
    """

    day_patterns: list[DayPattern] = field(default_factory=list)

    @property
    def highest_day(self) -> DayOfWeek | None:
        """Day with highest spending."""
        if not self.day_patterns:
            return None
        return max(
            self.day_patterns, key=lambda p: p.total_amount,
        ).day

    @property
    def lowest_day(self) -> DayOfWeek | None:
        """Day with lowest spending."""
        if not self.day_patterns:
            return None
        active_days = [
            p for p in self.day_patterns if p.total_amount > 0
        ]
        if not active_days:
            return None
        return min(
            active_days, key=lambda p: p.total_amount,
        ).day

    @property
    def weekend_percentage(self) -> float:
        """Percentage of spending on weekends (Sat + Sun)."""
        total = sum(p.total_amount for p in self.day_patterns)
        if total == 0:
            return 0.0
        weekend = sum(
            p.total_amount for p in self.day_patterns
            if p.day in (DayOfWeek.SATURDAY, DayOfWeek.SUNDAY)
        )
        return (weekend / total) * 100


@dataclass(frozen=True)
class Anomaly:
    """A detected spending anomaly.

    Attributes:
        transaction_date: Date of the transaction.
        description: Transaction description.
        amount: Transaction amount.
        category: Transaction category.
        z_score: Standard deviations from mean.
        anomaly_type: Type of anomaly (high, low, unusual).
        reason: Explanation of why it's anomalous.
    """

    transaction_date: str
    description: str
    amount: float
    category: str
    z_score: float
    anomaly_type: str
    reason: str


@dataclass
class AnomalyReport:
    """Report of detected anomalies.

    Attributes:
        anomalies: List of detected anomalies.
        total_transactions: Total transactions analyzed.
    """

    anomalies: list[Anomaly] = field(default_factory=list)
    total_transactions: int = 0

    @property
    def anomaly_rate(self) -> float:
        """Percentage of transactions that are anomalies."""
        if self.total_transactions == 0:
            return 0.0
        return (
            len(self.anomalies) / self.total_transactions
        ) * 100

    def high_amount_anomalies(self) -> list[Anomaly]:
        """Get anomalies due to unusually high amounts."""
        return [
            a for a in self.anomalies
            if a.anomaly_type == "high"
        ]


@dataclass(frozen=True)
class SavingsRateTrend:
    """Savings rate for a specific period.

    Attributes:
        period: Time period (e.g., "2024-01").
        earnings: Total earnings.
        expenses: Total expenses.
        savings: Net savings (earnings - expenses).
        savings_rate: Savings as percentage of earnings.
    """

    period: str
    earnings: float
    expenses: float
    savings: float
    savings_rate: float


# --- Burn Rate DTOs ---

@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class BurnRateMetrics:
    """Burn rate metrics for a budget period.

    Attributes:
        period_start: Start of the budget period.
        period_end: End of the budget period.
        budget_amount: Total budget for the period.
        spent_amount: Amount spent so far.
        days_elapsed: Number of days elapsed in the period.
        days_remaining: Number of days remaining in the period.
        daily_burn_rate: Average daily spending rate.
        projected_total: Projected spending by end of period.
        budget_remaining: Amount remaining in budget.
        safe_daily_spend: Recommended daily spending.
        days_until_exhausted: Days until budget exhausted.
        burn_rate_status: Status (on_track, warning, over_budget).
        projected_over_under: Projected amount over/under budget.
    """

    period_start: date
    period_end: date
    budget_amount: float
    spent_amount: float
    days_elapsed: int
    days_remaining: int
    daily_burn_rate: float
    projected_total: float
    budget_remaining: float
    safe_daily_spend: float
    days_until_exhausted: float | None
    burn_rate_status: str
    projected_over_under: float

    @property
    def is_over_budget(self) -> bool:
        """Return True if already over budget."""
        return self.spent_amount > self.budget_amount

    @property
    def on_track(self) -> bool:
        """Return True if projected to stay within budget."""
        return self.projected_total <= self.budget_amount

    @property
    def burn_rate_percentage(self) -> float:
        """Return burn rate as percentage of budget."""
        if self.budget_amount <= 0:
            return 0.0
        return (self.spent_amount / self.budget_amount) * 100

    @property
    def time_percentage(self) -> float:
        """Return percentage of period elapsed."""
        total_days = (
            (self.period_end - self.period_start).days + 1
        )
        if total_days <= 0:
            return 100.0
        return (self.days_elapsed / total_days) * 100


@dataclass(frozen=True)
class CategoryBurnRate:
    """Burn rate metrics for a specific category.

    Attributes:
        category: Category name.
        metrics: BurnRateMetrics for this category.
    """

    category: str
    metrics: BurnRateMetrics
