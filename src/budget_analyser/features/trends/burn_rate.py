"""Burn rate tracking service (business logic).

Tracks spending velocity and projects budget exhaustion:
- Daily burn rate calculation
- Month-end spending projection
- Days until budget exhaustion
- Safe daily spend recommendations
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date
from typing import Mapping

import pandas as pd

from budget_analyser.features.trends.models import (
    BurnRateMetrics,
    CategoryBurnRate,
)


class BurnRateService:
    """Service for calculating budget burn rates."""

    def __init__(
        self,
        *,
        warning_threshold: float = 80.0,
    ) -> None:
        """Initialize the burn rate service.

        Args:
            warning_threshold: Percentage threshold for warning.
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
            as_of_date: Date to calculate as of.

        Returns:
            BurnRateMetrics with all calculated values.
        """
        period_start = date(year, month, 1)
        _, days_in_month = monthrange(year, month)
        period_end = date(year, month, days_in_month)

        if as_of_date is None:
            as_of_date = date.today()

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
            transactions: DataFrame with transaction data.
            budget_amount: Total budget for the month.
            year: Budget year.
            month: Budget month (1-12).
            as_of_date: Date to calculate as of.

        Returns:
            BurnRateMetrics based on transaction totals.
        """
        if (transactions.empty
                or "amount" not in transactions.columns):
            spent_amount = 0.0
        else:
            expenses = transactions[
                transactions["amount"] < 0
            ]["amount"]
            spent_amount = (
                float(expenses.abs().sum())
                if not expenses.empty else 0.0
            )

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
            budgets: Mapping of category to budget amount.
            year: Budget year.
            month: Budget month.
            as_of_date: Date to calculate as of.

        Returns:
            List of CategoryBurnRate for each budgeted category.
        """
        results = []

        for category, budget_amount in budgets.items():
            if (transactions.empty
                    or "category" not in transactions.columns):
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

        results.sort(
            key=lambda x: x.metrics.burn_rate_percentage,
            reverse=True,
        )
        return results

    def _calculate_metrics(  # pylint: disable=too-many-arguments
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

        daily_burn_rate = (
            spent_amount / days_elapsed
            if days_elapsed > 0 else 0.0
        )

        projected_total = daily_burn_rate * total_days
        budget_remaining = budget_amount - spent_amount

        safe_daily_spend = (
            budget_remaining / days_remaining
            if days_remaining > 0 and budget_remaining > 0
            else 0.0
        )

        if daily_burn_rate > 0 and budget_remaining > 0:
            days_until_exhausted = (
                budget_remaining / daily_burn_rate
            )
        elif budget_remaining <= 0:
            days_until_exhausted = 0.0
        else:
            days_until_exhausted = None

        if spent_amount > budget_amount:
            status = "over_budget"
        elif projected_total > budget_amount:
            status = "warning"
        elif budget_amount > 0 and (
            spent_amount / budget_amount * 100
        ) >= self._warning_threshold:
            status = "warning"
        else:
            status = "on_track"

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
