"""Budget goals feature module.

Vertical slice owning all layers for budget goal management:
models, repository, service, and controller.
"""

from budget_analyser.features.budget_goals.controller import (
    BudgetGoalsController,
)
from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetProgress,
    EarningsGoal,
)
from budget_analyser.features.budget_goals.repository import (
    BudgetGoalsRepository,
)

__all__ = [
    "BudgetGoalsController",
    "BudgetGoalsRepository",
    "BudgetGoal",
    "BudgetProgress",
    "EarningsGoal",
]
