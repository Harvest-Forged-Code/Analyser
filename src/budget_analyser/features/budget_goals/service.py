"""Budget goals business logic.

Pure calculation functions for budget progress tracking.
No PySide6 or infrastructure dependencies.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetProgress,
    EarningsGoal,
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
        year_month: Month to calculate for (format: "YYYY-MM").

    Returns:
        List of BudgetProgress sorted by percentage descending.
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
