"""Budget goals router for Budget Analyser API.

Provides endpoints for budget and earnings goal management.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException

from budget_analyser.api.dependencies import (
    get_budget_goals_controller,
    get_reports,
    get_expenses_stats_controller,
)
from budget_analyser.api.serializers import (
    BudgetGoalSchema,
    EarningsGoalSchema,
    BudgetProgressSchema,
    SetBudgetRequest,
    SetBudgetYearRequest,
    SetEarningsGoalRequest,
)
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.budget_goals.controller import (
    BudgetGoalsController,
)
from budget_analyser.features.reporting.expenses_controller import (
    ExpensesStatsController,
)

router = APIRouter(prefix="/api/budget-goals", tags=["budget-goals"])


@router.get("", response_model=list[BudgetGoalSchema])
def get_all_budgets(
    *, controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> list[BudgetGoalSchema]:
    """List all budget goals.

    Args:
        controller: Injected BudgetGoalsController.

    Returns:
        List of BudgetGoalSchema.
    """
    budgets = controller.get_all_budgets()
    return [
        BudgetGoalSchema(
            id=b.id,
            category=b.category,
            monthly_limit=b.monthly_limit,
            year_month=b.year_month,
        )
        for b in budgets
    ]


@router.post("")
def set_budget(
    *,
    body: SetBudgetRequest,
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set or update a budget goal.

    Args:
        body: SetBudgetRequest with category, monthly_limit, year_month.
        controller: Injected BudgetGoalsController.

    Returns:
        Success message.
    """
    controller.set_budget(
        category=body.category,
        monthly_limit=body.monthly_limit,
        year_month=body.year_month,
    )
    return {"message": "Budget goal set successfully"}


@router.delete("")
def delete_budget(
    *,
    category: str = Query(...),
    year_month: str = Query("ALL"),
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Delete a budget goal.

    Args:
        category: Budget category.
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsController.

    Returns:
        Success message.
    """
    controller.delete_budget(category=category, year_month=year_month)
    return {"message": "Budget goal deleted successfully"}


@router.post("/year")
def set_budget_for_year(
    *,
    body: SetBudgetYearRequest,
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set budget goal for all months in a year.

    Args:
        body: SetBudgetYearRequest with category, monthly_limit, year.
        controller: Injected BudgetGoalsController.

    Returns:
        Success message.
    """
    controller.set_budget_for_year(
        category=body.category,
        monthly_limit=body.monthly_limit,
        year=body.year,
    )
    return {"message": "Budget goal set for all months in year"}


@router.get("/progress/{year_month}", response_model=list[BudgetProgressSchema])
def get_budget_progress(
    *,
    year_month: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    expenses_controller: ExpensesStatsController = Depends(
        get_expenses_stats_controller,
    ),
    budget_controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> list[BudgetProgressSchema]:
    """Calculate budget progress for a specific month.

    Args:
        year_month: Year-month string (e.g., "2024-01").
        reports: Injected reports cache.
        expenses_controller: Injected ExpensesStatsController.
        budget_controller: Injected BudgetGoalsController.

    Returns:
        List of BudgetProgressSchema.

    Raises:
        HTTPException: If month not found.
    """
    # Find the report for the requested month
    import pandas as pd
    period = pd.Period(year_month)
    report = next((r for r in reports if r.month == period), None)

    if not report or report.expenses.empty:
        raise HTTPException(
            status_code=404, detail=f"No expense data for {year_month}",
        )

    progress_list = budget_controller.calculate_budget_progress(
        expenses_df=report.expenses,
        year_month=year_month,
    )

    return [
        BudgetProgressSchema(
            category=p.category,
            budget_limit=p.budget_limit,
            spent=p.spent,
            remaining=p.remaining,
            percentage=p.percentage,
            status=p.status.value,
        )
        for p in progress_list
    ]


@router.get("/earnings", response_model=list[EarningsGoalSchema])
def get_all_earnings_goals(
    *, controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> list[EarningsGoalSchema]:
    """List all earnings goals.

    Args:
        controller: Injected BudgetGoalsController.

    Returns:
        List of EarningsGoalSchema.
    """
    goals = controller.get_all_earnings_goals()
    return [
        EarningsGoalSchema(
            id=g.id,
            sub_category=g.sub_category,
            expected_amount=g.expected_amount,
            year_month=g.year_month,
        )
        for g in goals
    ]


@router.post("/earnings")
def set_earnings_goal(
    *,
    body: SetEarningsGoalRequest,
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set or update an earnings goal.

    Args:
        body: SetEarningsGoalRequest with sub_category, expected_amount, year_month.
        controller: Injected BudgetGoalsController.

    Returns:
        Success message.
    """
    controller.set_earnings_goal(
        sub_category=body.sub_category,
        expected_amount=body.expected_amount,
        year_month=body.year_month,
    )
    return {"message": "Earnings goal set successfully"}


@router.delete("/earnings")
def delete_earnings_goal(
    *,
    sub_category: str = Query(...),
    year_month: str = Query("ALL"),
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Delete an earnings goal.

    Args:
        sub_category: Earnings sub-category.
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsController.

    Returns:
        Success message.
    """
    controller.delete_earnings_goal(
        sub_category=sub_category, year_month=year_month,
    )
    return {"message": "Earnings goal deleted successfully"}


@router.get("/earnings/map")
def get_earnings_goal_map(
    *,
    year_month: str = Query("ALL"),
    controller: BudgetGoalsController = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, float]:
    """Get earnings goal mapping (sub_category -> expected amount).

    Args:
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsController.

    Returns:
        Dict mapping sub-category to expected amount.
    """
    return controller.get_earnings_goal_map(year_month=year_month)
