"""Budget goals data transfer objects.

Contains all DTOs specific to the budget goals feature:
budget goals, earnings goals, and progress tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BudgetGoal:
    """A budget goal for a specific expense category."""

    id: int | None
    category: str
    monthly_limit: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months


@dataclass
class EarningsGoal:
    """An expected earnings goal for a specific sub-category."""

    id: int | None
    sub_category: str
    expected_amount: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months


@dataclass
class BudgetProgress:
    """Progress tracking for a budget category."""

    category: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str  # "under", "warning", "over"
