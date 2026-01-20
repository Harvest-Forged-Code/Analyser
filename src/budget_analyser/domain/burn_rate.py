"""Budget burn rate tracking (domain logic).

Purpose:
    Track spending velocity and project budget exhaustion:
    - Daily burn rate calculation
    - Month-end spending projection
    - Days until budget exhaustion
    - Safe daily spend recommendations

Helps users understand if they're on track with their budgets.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from calendar import monthrange
from typing import Mapping

import pandas as pd


@dataclass(frozen=True)
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
        safe_daily_spend: Recommended daily spending to stay in budget.
        days_until_exhausted: Days until budget would be exhausted at current rate.
        burn_rate_status: Status indicator (on_track, warning, over_budget).
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
        total_days = (self.period_end - self.period_start).days + 1
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


class BurnRateService:
    """Service for calculating budget burn rates and projections."""

    def __init__(
        self,
        *,
        warning_threshold: float = 80.0,
    ) -> None:
        """Initialize the burn rate service.

        Args:
            warning_threshold: Percentage threshold for warning status.
        """
        self._warning_threshold = warning_threshold

    def calculate_monthly_burn_rate(
        self,
        *,
        budget_amount: float,
        spent_amount: float,
        year: int,
        month: int,
        as_of_date: date | None = None,
    ) -> BurnRateMetrics:
        """Calculate burn rate metrics for a monthly budget.

        Args:
            budget_amount: Total budget for the month.
            spent_amount: Amount spent so far.
            year: Budget year.
            month: Budget month (1-12).
            as_of_date: Date to calculate as of (defaults to today).

        Returns:
            BurnRateMetrics with all calculated values.
        """
        # Determine period boundaries
        period_start = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        period_end = date(year, month, days_in_month)

        # Determine current position in period
        if as_of_date is None:
            as_of_date = date.today()

        # Clamp as_of_date to period
        if as_of_date < period_start:
            as_of_date = period_start
        elif as_of_date > period_end:
            as_of_date = period_end

        days_elapsed = (as_of_date - period_start).days + 1
        days_remaining = (period_end - as_of_date).days

        return self._calculate_metrics(
            period_start=period_start,
            period_end=period_end,
            budget_amount=budget_amount,
            spent_amount=spent_amount,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
        )

    def calculate_from_transactions(
        self,
        *,
        transactions: pd.DataFrame,
        budget_amount: float,
        year: int,
        month: int,
        as_of_date: date | None = None,
    ) -> BurnRateMetrics:
        """Calculate burn rate from transaction data.

        Args:
            transactions: DataFrame with transaction data for the month.
            budget_amount: Total budget for the month.
            year: Budget year.
            month: Budget month (1-12).
            as_of_date: Date to calculate as of.

        Returns:
            BurnRateMetrics based on transaction totals.
        """
        # Filter to the specified month
        if transactions.empty:
            spent_amount = 0.0
        elif "amount" not in transactions.columns:
            spent_amount = 0.0
        else:
            # Sum absolute values of expenses (negative amounts)
            expenses = transactions[transactions["amount"] < 0]["amount"]
            spent_amount = float(expenses.abs().sum()) if not expenses.empty else 0.0

        return self.calculate_monthly_burn_rate(
            budget_amount=budget_amount,
            spent_amount=spent_amount,
            year=year,
            month=month,
            as_of_date=as_of_date,
        )

    def calculate_by_category(
        self,
        *,
        transactions: pd.DataFrame,
        budgets: Mapping[str, float],
        year: int,
        month: int,
        as_of_date: date | None = None,
    ) -> list[CategoryBurnRate]:
        """Calculate burn rates for multiple categories.

        Args:
            transactions: DataFrame with transaction data.
            budgets: Mapping of category -> budget amount.
            year: Budget year.
            month: Budget month.
            as_of_date: Date to calculate as of.

        Returns:
            List of CategoryBurnRate for each budgeted category.
        """
        results = []

        for category, budget_amount in budgets.items():
            # Filter transactions for this category
            if transactions.empty or "category" not in transactions.columns:
                cat_transactions = pd.DataFrame()
            else:
                cat_transactions = transactions[
                    transactions["category"] == category
                ]

            metrics = self.calculate_from_transactions(
                transactions=cat_transactions,
                budget_amount=budget_amount,
                year=year,
                month=month,
                as_of_date=as_of_date,
            )

            results.append(CategoryBurnRate(
                category=category,
                metrics=metrics,
            ))

        # Sort by burn rate percentage descending
        results.sort(key=lambda x: x.metrics.burn_rate_percentage, reverse=True)
        return results

    def _calculate_metrics(
        self,
        *,
        period_start: date,
        period_end: date,
        budget_amount: float,
        spent_amount: float,
        days_elapsed: int,
        days_remaining: int,
    ) -> BurnRateMetrics:
        """Calculate all burn rate metrics."""
        total_days = days_elapsed + days_remaining

        # Daily burn rate
        if days_elapsed > 0:
            daily_burn_rate = spent_amount / days_elapsed
        else:
            daily_burn_rate = 0.0

        # Projected total spending
        projected_total = daily_burn_rate * total_days

        # Budget remaining
        budget_remaining = budget_amount - spent_amount

        # Safe daily spend
        if days_remaining > 0 and budget_remaining > 0:
            safe_daily_spend = budget_remaining / days_remaining
        else:
            safe_daily_spend = 0.0

        # Days until budget exhausted
        if daily_burn_rate > 0 and budget_remaining > 0:
            days_until_exhausted = budget_remaining / daily_burn_rate
        elif budget_remaining <= 0:
            days_until_exhausted = 0.0
        else:
            days_until_exhausted = None  # Not spending, won't exhaust

        # Determine status
        if spent_amount > budget_amount:
            status = "over_budget"
        elif projected_total > budget_amount:
            status = "warning"
        elif (spent_amount / budget_amount * 100) >= self._warning_threshold if budget_amount > 0 else False:
            status = "warning"
        else:
            status = "on_track"

        # Projected over/under
        projected_over_under = projected_total - budget_amount

        return BurnRateMetrics(
            period_start=period_start,
            period_end=period_end,
            budget_amount=budget_amount,
            spent_amount=spent_amount,
            days_elapsed=days_elapsed,
            days_remaining=days_remaining,
            daily_burn_rate=daily_burn_rate,
            projected_total=projected_total,
            budget_remaining=budget_remaining,
            safe_daily_spend=safe_daily_spend,
            days_until_exhausted=days_until_exhausted,
            burn_rate_status=status,
            projected_over_under=projected_over_under,
        )


def calculate_burn_rate(
    *,
    budget: float,
    spent: float,
    year: int,
    month: int,
) -> BurnRateMetrics:
    """Convenience function for quick burn rate calculation.

    Args:
        budget: Monthly budget amount.
        spent: Amount spent so far.
        year: Budget year.
        month: Budget month.

    Returns:
        BurnRateMetrics for the current date.
    """
    service = BurnRateService()
    return service.calculate_monthly_burn_rate(
        budget_amount=budget,
        spent_amount=spent,
        year=year,
        month=month,
    )
