"""Budget goals router for Budget Analyser API.

Provides endpoints for budget and earnings goal management.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends, Query, HTTPException

from budget_analyser.api.dependencies import (
    get_budget_goals_controller,
    get_reports,
    get_expenses_stats_controller,
)
from budget_analyser.api.serializers import (
    BudgetGoalSchema,
    BudgetGoalsSummarySchema,
    BudgetProgressSchema,
    CategoryProgressPointSchema,
    EarningsGoalSchema,
    EarningsGoalsSummarySchema,
    ProgressSummarySchema,
    SetBudgetRequest,
    SetBudgetYearRequest,
    SetEarningsGoalRequest,
    SetEarningsYearRequest,
)
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.budget_goals.service import (
    BudgetGoalsService,
)
from budget_analyser.features.reporting.expenses_service import (
    ExpensesStatsController,
)

router = APIRouter(prefix="/api/budget-goals", tags=["budget-goals"])


@router.get("", response_model=list[BudgetGoalSchema])
def get_all_budgets(
    *, controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> list[BudgetGoalSchema]:
    """List all budget goals.

    Args:
        controller: Injected BudgetGoalsService.

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
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set or update a budget goal.

    Args:
        body: SetBudgetRequest with category, monthly_limit, year_month.
        controller: Injected BudgetGoalsService.

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
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Delete a budget goal.

    Args:
        category: Budget category.
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsService.

    Returns:
        Success message.
    """
    controller.delete_budget(category=category, year_month=year_month)
    return {"message": "Budget goal deleted successfully"}


@router.post("/year")
def set_budget_for_year(
    *,
    body: SetBudgetYearRequest,
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set budget goal for all months in a year.

    Args:
        body: SetBudgetYearRequest with category, monthly_limit, year.
        controller: Injected BudgetGoalsService.

    Returns:
        Success message.
    """
    controller.set_budget_for_year(
        category=body.category,
        monthly_limit=body.monthly_limit,
        year=body.year,
    )
    return {"message": "Budget goal set for all months in year"}


@router.get("/year/{year}")
def get_budget_goals_for_year(
    *,
    year: int,
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, dict[str, float]]:
    """Get resolved 12-month budget goal grid for a year.

    Args:
        year: Year to retrieve goals for.
        controller: Injected BudgetGoalsService.

    Returns:
        Dict mapping category to {year_month: amount}.
    """
    return controller.get_budget_goals_for_year(year)


@router.get("/earnings/year/{year}")
def get_earnings_goals_for_year(
    *,
    year: int,
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, dict[str, float]]:
    """Get resolved 12-month earnings goal grid for a year.

    Args:
        year: Year to retrieve goals for.
        controller: Injected BudgetGoalsService.

    Returns:
        Dict mapping sub_category to {year_month: amount}.
    """
    return controller.get_earnings_goals_for_year(year)


@router.post("/earnings/year")
def set_earnings_goal_for_year(
    *,
    body: SetEarningsYearRequest,
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set earnings goal for all months in a year.

    Args:
        body: SetEarningsYearRequest with sub_category,
            expected_amount, year.
        controller: Injected BudgetGoalsService.

    Returns:
        Success message.
    """
    controller.set_earnings_goal_for_year(
        sub_category=body.sub_category,
        expected_amount=body.expected_amount,
        year=body.year,
    )
    return {"message": "Earnings goal set for all months in year"}


@router.get("/summary", response_model=BudgetGoalsSummarySchema)
def get_budget_goals_summary(
    *, controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> BudgetGoalsSummarySchema:
    """Get aggregate summary of all budget goals.

    Args:
        controller: Injected BudgetGoalsService.

    Returns:
        BudgetGoalsSummarySchema with totals and counts.
    """
    s = controller.get_budget_goals_summary()
    return BudgetGoalsSummarySchema(
        total_monthly_budget=s.total_monthly_budget,
        categories_tracked=s.categories_tracked,
        month_overrides=s.month_overrides,
    )


@router.get(
    "/earnings/summary",
    response_model=EarningsGoalsSummarySchema,
)
def get_earnings_goals_summary(
    *, controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> EarningsGoalsSummarySchema:
    """Get aggregate summary of all earnings goals.

    Args:
        controller: Injected BudgetGoalsService.

    Returns:
        EarningsGoalsSummarySchema with totals and counts.
    """
    s = controller.get_earnings_goals_summary()
    return EarningsGoalsSummarySchema(
        total_expected_earnings=s.total_expected_earnings,
        sub_categories_tracked=s.sub_categories_tracked,
        month_overrides=s.month_overrides,
    )


@router.get(
    "/progress/history/{category}",
    response_model=list[CategoryProgressPointSchema],
)
def get_category_progress_history(
    *,
    category: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    budget_controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> list[CategoryProgressPointSchema]:
    """Get 12-month progress history for a single category.

    Args:
        category: Expense category name.
        reports: Injected reports cache.
        budget_controller: Injected BudgetGoalsService.

    Returns:
        List of CategoryProgressPointSchema, one per available month.
    """
    if not reports:
        return []

    all_expenses = []
    months = []
    for report in sorted(reports, key=lambda r: r.month):
        ym = str(report.month)
        months.append(ym)
        if not report.expenses.empty:
            all_expenses.append(report.expenses)

    combined_expenses = (
        pd.concat(all_expenses, ignore_index=True)
        if all_expenses else pd.DataFrame()
    )

    recent_months = months[-12:]

    history = budget_controller.get_category_progress_history(
        category=category,
        expenses_df=combined_expenses,
        months=recent_months,
    )
    return [
        CategoryProgressPointSchema(
            year_month=p.year_month,
            budget_limit=p.budget_limit,
            spent=p.spent,
            remaining=p.remaining,
            percentage=p.percentage,
            status=p.status,
        )
        for p in history
    ]


@router.get(
    "/progress/{year_month}/summary",
    response_model=ProgressSummarySchema,
)
def get_progress_summary(
    *,
    year_month: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    budget_controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> ProgressSummarySchema:
    """Get aggregate progress summary for a month.

    Args:
        year_month: Year-month string (e.g., "2024-01").
        reports: Injected reports cache.
        budget_controller: Injected BudgetGoalsService.

    Returns:
        ProgressSummarySchema with status counts and totals.

    Raises:
        HTTPException: If month not found.
    """
    period = pd.Period(year_month)
    report = next((r for r in reports if r.month == period), None)

    if not report or report.expenses.empty:
        raise HTTPException(
            status_code=404, detail=f"No expense data for {year_month}",
        )

    s = budget_controller.get_progress_summary(
        expenses_df=report.expenses, year_month=year_month,
    )
    return ProgressSummarySchema(
        on_track_count=s.on_track_count,
        warning_count=s.warning_count,
        over_budget_count=s.over_budget_count,
        total_spent=s.total_spent,
        total_budget=s.total_budget,
    )


@router.get("/progress/{year_month}", response_model=list[BudgetProgressSchema])
def get_budget_progress(
    *,
    year_month: str,
    reports: list[MonthlyReports] = Depends(get_reports),
    _expenses_controller: ExpensesStatsController = Depends(
        get_expenses_stats_controller,
    ),
    budget_controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> list[BudgetProgressSchema]:
    """Calculate budget progress for a specific month.

    Args:
        year_month: Year-month string (e.g., "2024-01").
        reports: Injected reports cache.
        _expenses_controller: Injected ExpensesStatsController (unused).
        budget_controller: Injected BudgetGoalsService.

    Returns:
        List of BudgetProgressSchema.

    Raises:
        HTTPException: If month not found.
    """
    # Find the report for the requested month
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
            status=p.status,
        )
        for p in progress_list
    ]


@router.get("/earnings", response_model=list[EarningsGoalSchema])
def get_all_earnings_goals(
    *, controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> list[EarningsGoalSchema]:
    """List all earnings goals.

    Args:
        controller: Injected BudgetGoalsService.

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
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Set or update an earnings goal.

    Args:
        body: SetEarningsGoalRequest with sub_category, expected_amount, year_month.
        controller: Injected BudgetGoalsService.

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
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, str]:
    """Delete an earnings goal.

    Args:
        sub_category: Earnings sub-category.
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsService.

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
    controller: BudgetGoalsService = Depends(
        get_budget_goals_controller,
    ),
) -> dict[str, float]:
    """Get earnings goal mapping (sub_category -> expected amount).

    Args:
        year_month: Year-month or "ALL".
        controller: Injected BudgetGoalsService.

    Returns:
        Dict mapping sub-category to expected amount.
    """
    return controller.get_earnings_goal_map(year_month=year_month)
