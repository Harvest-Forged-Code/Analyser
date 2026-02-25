"""Dashboard router for Budget Analyser API.

Provides summary KPIs for the main dashboard view.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends

from budget_analyser.api.dependencies import (
    get_reports,
    get_budget_goals_controller,
    get_savings_controller,
)
from budget_analyser.api.serializers import DashboardSummaryResponse
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.budget_goals.service import (
    BudgetGoalsService,
)
from budget_analyser.features.savings.service import SavingsService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


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


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    *,
    reports: list[MonthlyReports] = Depends(get_reports),
    budget_goals_controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
    savings_service: SavingsService = Depends(get_savings_controller),
) -> DashboardSummaryResponse:
    """Aggregate KPIs for the dashboard summary.

    Args:
        reports: Injected reports cache.
        budget_goals_controller: Injected BudgetGoalsService.
        savings_service: Injected SavingsService.

    Returns:
        DashboardSummaryResponse with all KPIs.
    """
    if not reports:
        return DashboardSummaryResponse(has_reports=False)

    earnings_df = _all_earnings_df(reports)
    expenses_df = _all_expenses_df(reports)

    # Savings metrics
    savings_metrics = savings_service.calculate_savings_metrics(
        earnings_df=earnings_df,
        expenses_df=expenses_df,
    )

    # Budget progress (count categories over budget)
    budgets = budget_goals_controller.get_all_budgets()
    budget_categories_total = len(budgets)

    return DashboardSummaryResponse(
        total_earnings=savings_metrics.total_earnings,
        total_expenses=savings_metrics.total_expenses,
        net_savings=savings_metrics.net_savings,
        savings_rate=savings_metrics.savings_rate,
        months_of_data=savings_metrics.months_of_data,
        net_worth=0.0,
        budget_categories_over=0,
        budget_categories_total=budget_categories_total,
        recurring_active=0,
        has_reports=True,
    )
