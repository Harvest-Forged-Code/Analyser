"""Budget goals business logic.

Pure calculation functions for budget progress tracking.
No PySide6 or infrastructure dependencies.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetGoalsSummary,
    BudgetProgress,
    CategoryProgressPoint,
    EarningsGoal,
    EarningsGoalsSummary,
    ProgressSummary,
)


def calculate_budget_progress(
    *,
    budgets: list[BudgetGoal],
    expenses_df: pd.DataFrame,
    year_month: str,
) -> list[BudgetProgress]:
    """Calculate budget progress for all categories in a given month.

    Args:
        budgets: All budget goals to evaluate.
        expenses_df: DataFrame with expense transactions.
            Must contain 'transaction_date', 'category', and
            'amount' columns.
        year_month: Month to calculate for (format: "YYYY-MM").

    Returns:
        List of BudgetProgress sorted by percentage descending.

    Example:
        >>> import pandas as pd
        >>> budgets = [
        ...     BudgetGoal(
        ...         id=1, category="Groceries",
        ...         monthly_limit=500.0, year_month="ALL",
        ...     ),
        ... ]
        >>> expenses = pd.DataFrame({
        ...     "transaction_date": ["2024-01-15"],
        ...     "category": ["Groceries"],
        ...     "amount": [-200.0],
        ... })
        >>> progress = calculate_budget_progress(
        ...     budgets=budgets,
        ...     expenses_df=expenses,
        ...     year_month="2024-01",
        ... )
        >>> progress[0].percentage
        40.0
    """
    if not budgets:
        return []

    if expenses_df.empty:
        month_expenses = pd.DataFrame()
    else:
        df = expenses_df.copy()
        if "transaction_date" in df.columns:
            df["year_month"] = pd.to_datetime(
                df["transaction_date"], errors="coerce"
            ).dt.strftime("%Y-%m")
            month_expenses = df[df["year_month"] == year_month]
        else:
            month_expenses = pd.DataFrame()

    spending_by_category: dict[str, float] = {}
    if not month_expenses.empty and "category" in month_expenses.columns:
        grouped = month_expenses.groupby("category")["amount"].sum()
        for cat, amount in grouped.items():
            spending_by_category[cat] = abs(float(amount))

    progress_list: list[BudgetProgress] = []
    for budget in budgets:
        if budget.year_month not in {"ALL", year_month}:
            continue

        spent = spending_by_category.get(budget.category, 0.0)
        remaining = budget.monthly_limit - spent
        percentage = (
            spent / budget.monthly_limit * 100
        ) if budget.monthly_limit > 0 else 0

        if percentage >= 100:
            status = "over"
        elif percentage >= 80:
            status = "warning"
        else:
            status = "under"

        progress_list.append(BudgetProgress(
            category=budget.category,
            budget_limit=budget.monthly_limit,
            spent=spent,
            remaining=remaining,
            percentage=percentage,
            status=status,
        ))

    progress_list.sort(key=lambda p: p.percentage, reverse=True)
    return progress_list


def calculate_budget_goals_summary(
    *,
    goals: list[BudgetGoal],
) -> BudgetGoalsSummary:
    """Compute aggregate summary statistics for budget goals.

    Args:
        goals: All budget goals from the repository.

    Returns:
        BudgetGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_categories = {g.category for g in goals}

    return BudgetGoalsSummary(
        total_monthly_budget=sum(g.monthly_limit for g in default_goals),
        categories_tracked=len(unique_categories),
        month_overrides=len(override_goals),
    )


def calculate_earnings_goals_summary(
    *,
    goals: list[EarningsGoal],
) -> EarningsGoalsSummary:
    """Compute aggregate summary statistics for earnings goals.

    Args:
        goals: All earnings goals from the repository.

    Returns:
        EarningsGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_sub_categories = {g.sub_category for g in goals}

    return EarningsGoalsSummary(
        total_expected_earnings=sum(g.expected_amount for g in default_goals),
        sub_categories_tracked=len(unique_sub_categories),
        month_overrides=len(override_goals),
    )


def calculate_progress_summary(
    *,
    progress_list: list[BudgetProgress],
) -> ProgressSummary:
    """Compute aggregate progress summary from individual category progress.

    Args:
        progress_list: List of BudgetProgress for each category.

    Returns:
        ProgressSummary with status counts and totals.
    """
    on_track = sum(1 for p in progress_list if p.status == "under")
    warning = sum(1 for p in progress_list if p.status == "warning")
    over = sum(1 for p in progress_list if p.status == "over")

    return ProgressSummary(
        on_track_count=on_track,
        warning_count=warning,
        over_budget_count=over,
        total_spent=sum(p.spent for p in progress_list),
        total_budget=sum(p.budget_limit for p in progress_list),
    )


def calculate_category_progress_history(
    *,
    category: str,
    budgets: list[BudgetGoal],
    expenses_df: pd.DataFrame,
    months: list[str],
) -> list[CategoryProgressPoint]:
    """Compute historical progress for a single category across months.

    For each month, finds the applicable budget (month-specific override
    or ALL default) and calculates spending against it.

    Args:
        category: The expense category to track.
        budgets: All budget goals (used to find applicable limits).
        expenses_df: DataFrame with all expense transactions.
        months: List of year-month strings to compute history for.

    Returns:
        List of CategoryProgressPoint, one per month, in order.
    """
    default_limit = 0.0
    month_limits: dict[str, float] = {}
    for b in budgets:
        if b.category != category:
            continue
        if b.year_month == "ALL":
            default_limit = b.monthly_limit
        else:
            month_limits[b.year_month] = b.monthly_limit

    spending_by_month: dict[str, float] = {}
    if not expenses_df.empty and "transaction_date" in expenses_df.columns:
        df = expenses_df.copy()
        df["_ym"] = pd.to_datetime(
            df["transaction_date"], errors="coerce",
        ).dt.strftime("%Y-%m")
        cat_df = (
            df[df["category"] == category]
            if "category" in df.columns
            else pd.DataFrame()
        )
        if not cat_df.empty:
            grouped = cat_df.groupby("_ym")["amount"].sum()
            for ym, amount in grouped.items():
                spending_by_month[str(ym)] = abs(float(amount))

    result: list[CategoryProgressPoint] = []
    for ym in months:
        limit = month_limits.get(ym, default_limit)
        spent = spending_by_month.get(ym, 0.0)
        remaining = limit - spent
        percentage = (spent / limit * 100) if limit > 0 else 0.0

        if percentage >= 100:
            status = "over"
        elif percentage >= 80:
            status = "warning"
        else:
            status = "under"

        result.append(CategoryProgressPoint(
            year_month=ym,
            budget_limit=limit,
            spent=spent,
            remaining=remaining,
            percentage=percentage,
            status=status,
        ))

    return result


def build_earnings_goal_map(
    *,
    goals: list[EarningsGoal],
    year_month: str = "ALL",
) -> dict[str, float]:
    """Build a mapping of sub-category to expected amount for easy lookup.

    Month-specific goals take priority over "ALL" defaults.

    Args:
        goals: All earnings goals.
        year_month: Specific month "YYYY-MM" or "ALL" for defaults.

    Returns:
        Dict mapping sub_category name to expected_amount.

    Example:
        >>> goals = [
        ...     EarningsGoal(
        ...         id=1, sub_category="Salary",
        ...         expected_amount=5000.0, year_month="ALL",
        ...     ),
        ...     EarningsGoal(
        ...         id=2, sub_category="Salary",
        ...         expected_amount=5500.0, year_month="2024-12",
        ...     ),
        ... ]
        >>> build_earnings_goal_map(goals=goals, year_month="2024-12")
        {'Salary': 5500.0}
    """
    result: dict[str, float] = {}

    for goal in goals:
        if goal.year_month == "ALL":
            result[goal.sub_category] = goal.expected_amount

    if year_month != "ALL":
        for goal in goals:
            if goal.year_month == year_month:
                result[goal.sub_category] = goal.expected_amount

    return result
