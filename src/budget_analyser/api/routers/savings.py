"""Savings router for Budget Analyser API.

Provides endpoints for savings metrics and monthly tracking.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, Query

from budget_analyser.api.dependencies import (
    get_savings_controller,
    get_reports,
)
from budget_analyser.api.serializers import SavingsMetricsSchema
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.savings.controller import SavingsController

router = APIRouter(prefix="/api/savings", tags=["savings"])


def _all_earnings_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all earnings DataFrames from reports."""
    frames = []
    for r in reports:
        if r.earnings is not None and not r.earnings.empty:
            frames.append(r.earnings)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _all_expenses_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all expenses DataFrames from reports."""
    frames = []
    for r in reports:
        if r.expenses is not None and not r.expenses.empty:
            frames.append(r.expenses)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@router.get("/metrics", response_model=SavingsMetricsSchema)
def get_savings_metrics(
    *,
    year: int | None = Query(None),
    reports: list[MonthlyReports] = Depends(get_reports),
    controller: SavingsController = Depends(get_savings_controller),
) -> SavingsMetricsSchema:
    """Calculate savings metrics.

    Args:
        year: Optional year filter.
        reports: Injected reports cache.
        controller: Injected SavingsController.

    Returns:
        SavingsMetricsSchema with totals and rates.
    """
    # Filter reports by year if specified
    filtered_reports = reports
    if year is not None:
        filtered_reports = [r for r in reports if r.month.year == year]

    earnings_df = _all_earnings_df(filtered_reports)
    expenses_df = _all_expenses_df(filtered_reports)

    metrics = controller.calculate_savings_metrics(
        earnings_df=earnings_df,
        expenses_df=expenses_df,
    )

    return SavingsMetricsSchema(
        total_earnings=metrics.total_earnings,
        total_expenses=metrics.total_expenses,
        net_savings=metrics.net_savings,
        savings_rate=metrics.savings_rate,
        monthly_average_savings=metrics.monthly_average_savings,
        months_of_data=metrics.months_of_data,
    )


@router.get("/monthly/{year}")
def get_monthly_savings(
    *,
    year: int,
    reports: list[MonthlyReports] = Depends(get_reports),
    controller: SavingsController = Depends(get_savings_controller),
) -> list[dict[str, float | str]]:
    """Calculate monthly savings breakdown for a year.

    Args:
        year: Year as integer.
        reports: Injected reports cache.
        controller: Injected SavingsController.

    Returns:
        List of monthly savings records.
    """
    # Get all earnings/expenses for the year
    year_reports = [r for r in reports if r.month.year == year]
    earnings_df = _all_earnings_df(year_reports)
    expenses_df = _all_expenses_df(year_reports)

    monthly_savings = controller.calculate_monthly_savings(
        earnings_df=earnings_df,
        expenses_df=expenses_df,
        year=year,
    )

    return [
        {
            "month": ms.month,
            "earnings": ms.earnings,
            "expenses": ms.expenses,
            "savings": ms.savings,
            "savings_rate": ms.savings_rate,
        }
        for ms in monthly_savings
    ]
