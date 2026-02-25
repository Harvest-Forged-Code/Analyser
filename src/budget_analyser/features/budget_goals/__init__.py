"""Budget goals feature module.

Vertical slice owning all layers for budget goal management:
models, service (with BudgetGoalsModel for persistence).
"""

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
from budget_analyser.features.budget_goals.service import (
    BudgetGoalsService,
)

__all__ = [
    "BudgetGoalsModel",
    "BudgetGoalsService",
    "BudgetGoal",
    "BudgetProgress",
    "EarningsGoal",
    "BudgetGoalsSummary",
    "EarningsGoalsSummary",
    "ProgressSummary",
    "CategoryProgressPoint",
]
