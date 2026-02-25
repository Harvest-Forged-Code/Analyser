"""Budget goals business logic and service.

Contains:
- ``BudgetGoalsService``: stateful facade holding a ``BudgetGoalsModel``
  reference and delegating persistence + computation.
- Pure calculation functions for budget progress tracking.
"""

from __future__ import annotations

import logging

import pandas as pd

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetGoalsModel,
    BudgetGoalsSummary,
    BudgetProgress,
    CategoryProgressPoint,
    EarningsGoal,
    EarningsGoalsSummary,
    ProgressSummary,
)


# ---------------------------------------------------------------------------
# BudgetGoalsService (absorbs former BudgetGoalsController)
# ---------------------------------------------------------------------------

class BudgetGoalsService:
    """Service for budget goal management.

    Delegates persistence to BudgetGoalsModel and business logic
    to pure service functions.

    Example:
        >>> from pathlib import Path
        >>> model = BudgetGoalsModel(db_path=Path("budget.db"))
        >>> svc = BudgetGoalsService(model=model)
        >>> svc.set_budget("Groceries", 500.0)
        BudgetGoal(id=1, category='Groceries', ...)
    """

    def __init__(
        self,
        *,
        model: BudgetGoalsModel,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the budget goals service.

        Args:
            model: Budget goals model instance.
            logger: Optional logger for diagnostics.
        """
        self._model = model
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.budget_goals.service"
        )

    # ==================== Budget Goals ====================

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        year_month: str = "ALL",
    ) -> BudgetGoal:
        """Set a budget limit for a category.

        Args:
            category: Expense category name (e.g. "Groceries").
            monthly_limit: Monthly spending limit in dollars.
            year_month: Period as "YYYY-MM" or "ALL" for every month.

        Returns:
            The created or updated BudgetGoal.
        """
        return self._model.set_budget_goal(
            category, monthly_limit, year_month,
        )

    def get_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> BudgetGoal | None:
        """Get budget for a category.

        Args:
            category: Expense category name (e.g. "Groceries").
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            BudgetGoal if found, None otherwise.
        """
        return self._model.get_budget_goal(category, year_month)

    def get_all_budgets(self) -> list[BudgetGoal]:
        """Get all budget goals.

        Returns:
            List of all BudgetGoal entries.
        """
        return self._model.get_all_budget_goals()

    def delete_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete a budget goal.

        Args:
            category: Expense category name to delete.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            True if a goal was deleted.
        """
        return self._model.delete_budget_goal(category, year_month)

    def set_budget_for_year(
        self,
        category: str,
        monthly_limit: float,
        year: int,
    ) -> list[BudgetGoal]:
        """Set budget limits for all 12 months of a year.

        Args:
            category: The expense category name.
            monthly_limit: The monthly spending limit.
            year: The year to set goals for.

        Returns:
            List of 12 BudgetGoal objects.
        """
        return self._model.set_budget_goals_for_year(
            category, monthly_limit, year,
        )

    # ==================== Earnings Goals ====================

    def set_earnings_goal(
        self,
        sub_category: str,
        expected_amount: float,
        year_month: str = "ALL",
    ) -> EarningsGoal:
        """Set an expected earnings amount for a sub-category.

        Args:
            sub_category: Earnings sub-category (e.g. "Salary").
            expected_amount: Expected monthly amount in dollars.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            The created or updated EarningsGoal.
        """
        return self._model.set_earnings_goal(
            sub_category, expected_amount, year_month,
        )

    def get_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> EarningsGoal | None:
        """Get earnings goal for a sub-category.

        Args:
            sub_category: Earnings sub-category (e.g. "Salary").
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            EarningsGoal if found, None otherwise.
        """
        return self._model.get_earnings_goal(
            sub_category, year_month,
        )

    def get_all_earnings_goals(self) -> list[EarningsGoal]:
        """Get all earnings goals.

        Returns:
            List of all EarningsGoal entries.
        """
        return self._model.get_all_earnings_goals()

    def delete_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete an earnings goal.

        Args:
            sub_category: Earnings sub-category name to delete.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            True if a goal was deleted.
        """
        return self._model.delete_earnings_goal(
            sub_category, year_month,
        )

    def set_earnings_goal_for_year(
        self,
        sub_category: str,
        expected_amount: float,
        year: int,
    ) -> list[EarningsGoal]:
        """Set expected earnings for all 12 months of a year.

        Args:
            sub_category: The earnings sub-category name.
            expected_amount: The expected monthly earnings amount.
            year: The year to set goals for.

        Returns:
            List of 12 EarningsGoal objects.
        """
        return self._model.set_earnings_goals_for_year(
            sub_category, expected_amount, year,
        )

    def get_earnings_goal_map(
        self,
        year_month: str = "ALL",
    ) -> dict[str, float]:
        """Get a mapping of sub-category to expected amount.

        Args:
            year_month: Specific month "YYYY-MM" or "ALL" for defaults.

        Returns:
            Dict mapping sub_category name to expected_amount.
        """
        goals = self._model.get_all_earnings_goals()
        return build_earnings_goal_map(
            goals=goals, year_month=year_month,
        )

    def get_budget_goals_for_year(
        self, year: int,
    ) -> dict[str, dict[str, float]]:
        """Get resolved 12-month budget grid for a year.

        For each category, builds a 12-month dict resolving "ALL" fallback.
        Month-specific entries override the "ALL" default.

        Args:
            year: The year to retrieve goals for.

        Returns:
            Dict mapping category to {year_month: amount} for all 12 months.
        """
        goals = self._model.get_all_budget_goals()
        return _build_year_grid_budget(goals=goals, year=year)

    def get_earnings_goals_for_year(
        self, year: int,
    ) -> dict[str, dict[str, float]]:
        """Get resolved 12-month earnings grid for a year.

        For each sub-category, builds a 12-month dict resolving "ALL"
        fallback. Month-specific entries override the "ALL" default.

        Args:
            year: The year to retrieve goals for.

        Returns:
            Dict mapping sub_category to {year_month: amount} for all
            12 months.
        """
        goals = self._model.get_all_earnings_goals()
        return _build_year_grid_earnings(goals=goals, year=year)

    # ==================== Budget Progress ====================

    def calculate_budget_progress(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> list[BudgetProgress]:
        """Calculate budget progress for all categories in a given month.

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to calculate for (format: "YYYY-MM").

        Returns:
            List of BudgetProgress for each category with a budget.
        """
        budgets = self._model.get_all_budget_goals()
        return calculate_budget_progress(
            budgets=budgets,
            expenses_df=expenses_df,
            year_month=year_month,
        )

    # ==================== Summaries ====================

    def get_budget_goals_summary(self) -> BudgetGoalsSummary:
        """Get aggregate summary of all budget goals.

        Returns:
            BudgetGoalsSummary with totals and counts.
        """
        goals = self._model.get_all_budget_goals()
        return calculate_budget_goals_summary(goals=goals)

    def get_earnings_goals_summary(self) -> EarningsGoalsSummary:
        """Get aggregate summary of all earnings goals.

        Returns:
            EarningsGoalsSummary with totals and counts.
        """
        goals = self._model.get_all_earnings_goals()
        return calculate_earnings_goals_summary(goals=goals)

    def get_progress_summary(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> ProgressSummary:
        """Get aggregate progress summary for a month.

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to calculate for (format: "YYYY-MM").

        Returns:
            ProgressSummary with status counts and totals.
        """
        progress = self.calculate_budget_progress(
            expenses_df, year_month,
        )
        return calculate_progress_summary(progress_list=progress)

    def get_category_progress_history(
        self,
        *,
        category: str,
        expenses_df: pd.DataFrame,
        months: list[str],
    ) -> list[CategoryProgressPoint]:
        """Get historical progress for a single category.

        Args:
            category: The expense category to track.
            expenses_df: DataFrame with all expense transactions.
            months: List of year-month strings to compute history for.

        Returns:
            List of CategoryProgressPoint, one per month.
        """
        budgets = self._model.get_all_budget_goals()
        return calculate_category_progress_history(
            category=category,
            budgets=budgets,
            expenses_df=expenses_df,
            months=months,
        )

    def get_categories_over_budget(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> list[BudgetProgress]:
        """Get categories that are over or near budget limit.

        Returns only categories with status "over" or "warning"
        (at or above 80% budget utilization).

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to check (format: "YYYY-MM").

        Returns:
            List of BudgetProgress entries with warning or over status.
        """
        progress = self.calculate_budget_progress(
            expenses_df, year_month,
        )
        return [
            p for p in progress if p.status in ("over", "warning")
        ]


# Backward compatibility alias
BudgetGoalsController = BudgetGoalsService


# ---------------------------------------------------------------------------
# Pure calculation functions
# ---------------------------------------------------------------------------

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
        goals: All budget goals from the model.

    Returns:
        BudgetGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_categories = {g.category for g in goals}

    return BudgetGoalsSummary(
        total_monthly_budget=sum(
            g.monthly_limit for g in default_goals
        ),
        categories_tracked=len(unique_categories),
        month_overrides=len(override_goals),
    )


def calculate_earnings_goals_summary(
    *,
    goals: list[EarningsGoal],
) -> EarningsGoalsSummary:
    """Compute aggregate summary statistics for earnings goals.

    Args:
        goals: All earnings goals from the model.

    Returns:
        EarningsGoalsSummary with totals and counts.
    """
    default_goals = [g for g in goals if g.year_month == "ALL"]
    override_goals = [g for g in goals if g.year_month != "ALL"]
    unique_sub_categories = {g.sub_category for g in goals}

    return EarningsGoalsSummary(
        total_expected_earnings=sum(
            g.expected_amount for g in default_goals
        ),
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


def _spending_by_month(
    expenses_df: pd.DataFrame,
    category: str,
) -> dict[str, float]:
    """Return absolute spending per year-month for a single category."""
    result: dict[str, float] = {}
    if (expenses_df.empty
            or "transaction_date" not in expenses_df.columns):
        return result
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
        for ym, amount in cat_df.groupby("_ym")["amount"].sum().items():
            result[str(ym)] = abs(float(amount))
    return result


def calculate_category_progress_history(
    *,
    category: str,
    budgets: list[BudgetGoal],
    expenses_df: pd.DataFrame,
    months: list[str],
) -> list[CategoryProgressPoint]:
    """Compute historical progress for a single category across months.

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

    spending = _spending_by_month(expenses_df, category)

    result: list[CategoryProgressPoint] = []
    for ym in months:
        limit = month_limits.get(ym, default_limit)
        spent = spending.get(ym, 0.0)
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


def _build_year_grid_budget(
    *,
    goals: list[BudgetGoal],
    year: int,
) -> dict[str, dict[str, float]]:
    """Build a 12-month grid of budget goals for a given year.

    For each category found in the goals, creates an entry for every
    month in the year. Month-specific values take priority; otherwise
    falls back to the "ALL" default.

    Args:
        goals: All budget goals from the model.
        year: Year to build grid for.

    Returns:
        Dict of {category: {"YYYY-MM": amount, ...}} with 12 months each.
    """
    months = [f"{year}-{m:02d}" for m in range(1, 13)]

    defaults: dict[str, float] = {}
    overrides: dict[str, dict[str, float]] = {}

    for goal in goals:
        cat = goal.category
        if goal.year_month == "ALL":
            defaults[cat] = goal.monthly_limit
        elif goal.year_month.startswith(f"{year}-"):
            overrides.setdefault(cat, {})[goal.year_month] = (
                goal.monthly_limit
            )

    all_categories = sorted(set(defaults) | set(overrides))
    result: dict[str, dict[str, float]] = {}
    for cat in all_categories:
        default_val = defaults.get(cat, 0.0)
        cat_overrides = overrides.get(cat, {})
        result[cat] = {
            ym: cat_overrides.get(ym, default_val)
            for ym in months
        }

    return result


def _build_year_grid_earnings(
    *,
    goals: list[EarningsGoal],
    year: int,
) -> dict[str, dict[str, float]]:
    """Build a 12-month grid of earnings goals for a given year.

    For each sub-category found in the goals, creates an entry for
    every month in the year. Month-specific values take priority;
    otherwise falls back to the "ALL" default.

    Args:
        goals: All earnings goals from the model.
        year: Year to build grid for.

    Returns:
        Dict of {sub_category: {"YYYY-MM": amount, ...}} with 12
        months each.
    """
    months = [f"{year}-{m:02d}" for m in range(1, 13)]

    defaults: dict[str, float] = {}
    overrides: dict[str, dict[str, float]] = {}

    for goal in goals:
        sub = goal.sub_category
        if goal.year_month == "ALL":
            defaults[sub] = goal.expected_amount
        elif goal.year_month.startswith(f"{year}-"):
            overrides.setdefault(sub, {})[goal.year_month] = (
                goal.expected_amount
            )

    all_sub_categories = sorted(set(defaults) | set(overrides))
    result: dict[str, dict[str, float]] = {}
    for sub in all_sub_categories:
        default_val = defaults.get(sub, 0.0)
        sub_overrides = overrides.get(sub, {})
        result[sub] = {
            ym: sub_overrides.get(ym, default_val)
            for ym in months
        }

    return result
