"""Budget goals data transfer objects.

Contains all DTOs specific to the budget goals feature:
budget goals, earnings goals, and progress tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetGoal:
    """A budget goal for a specific expense category.

    Attributes:
        id: Database primary key, or None for unsaved goals.
        category: Expense category name (e.g. "Groceries").
        monthly_limit: Monthly spending limit in dollars.
        year_month: Period as "YYYY-MM" or "ALL" for every month.

    Example:
        >>> goal = BudgetGoal(
        ...     id=1,
        ...     category="Groceries",
        ...     monthly_limit=500.0,
        ...     year_month="2024-01",
        ... )
        >>> goal.category
        'Groceries'
    """

    id: int | None
    category: str
    monthly_limit: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months


@dataclass
class EarningsGoal:
    """An expected earnings goal for a specific sub-category.

    Attributes:
        id: Database primary key, or None for unsaved goals.
        sub_category: Earnings sub-category name (e.g. "Salary").
        expected_amount: Expected monthly earnings in dollars.
        year_month: Period as "YYYY-MM" or "ALL" for every month.

    Example:
        >>> goal = EarningsGoal(
        ...     id=1,
        ...     sub_category="Salary",
        ...     expected_amount=5000.0,
        ...     year_month="2024-01",
        ... )
        >>> goal.expected_amount
        5000.0
    """

    id: int | None
    sub_category: str
    expected_amount: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months


@dataclass
class BudgetProgress:
    """Progress tracking for a budget category.

    Attributes:
        category: Expense category name (e.g. "Groceries").
        budget_limit: Monthly budget ceiling in dollars.
        spent: Amount spent so far in dollars.
        remaining: Budget remaining (budget_limit - spent).
        percentage: Percentage of budget consumed (0-100+).
        status: Budget status: "under", "warning", or "over".

    Example:
        >>> progress = BudgetProgress(
        ...     category="Groceries",
        ...     budget_limit=500.0,
        ...     spent=450.0,
        ...     remaining=50.0,
        ...     percentage=90.0,
        ...     status="warning",
        ... )
        >>> progress.status
        'warning'
    """

    category: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str  # "under", "warning", "over"


@dataclass
class BudgetGoalsSummary:
    """Aggregate summary of all budget goals.

    Attributes:
        total_monthly_budget: Sum of all default (ALL) goal limits.
        categories_tracked: Count of unique categories with goals.
        month_overrides: Count of month-specific override entries.
    """

    total_monthly_budget: float
    categories_tracked: int
    month_overrides: int


@dataclass
class EarningsGoalsSummary:
    """Aggregate summary of all earnings goals.

    Attributes:
        total_expected_earnings: Sum of all default (ALL) goal amounts.
        sub_categories_tracked: Count of unique sub-categories with goals.
        month_overrides: Count of month-specific override entries.
    """

    total_expected_earnings: float
    sub_categories_tracked: int
    month_overrides: int


@dataclass
class ProgressSummary:
    """Aggregate progress summary for a single month.

    Attributes:
        on_track_count: Categories under 80% budget.
        warning_count: Categories between 80-100% budget.
        over_budget_count: Categories exceeding 100% budget.
        total_spent: Sum of all category spending.
        total_budget: Sum of all category budget limits.
    """

    on_track_count: int
    warning_count: int
    over_budget_count: int
    total_spent: float
    total_budget: float


@dataclass
class CategoryProgressPoint:
    """A single month's progress data for one category.

    Used to build historical trend charts in the drill-down view.

    Attributes:
        year_month: The month period (format: "YYYY-MM").
        budget_limit: Budget ceiling for that month.
        spent: Actual spending in that month.
        remaining: Budget remaining (budget_limit - spent).
        percentage: Percentage of budget consumed.
        status: Budget status: "under", "warning", or "over".
    """

    year_month: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str
