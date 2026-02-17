"""Backward-compatibility shim.

All budget controller functionality has been moved to feature controllers:
- Budget/earnings goals -> features.budget_goals.controller.BudgetGoalsController
- Net worth -> features.net_worth.controller.NetWorthController
- Recurring -> features.recurring.controller.RecurringController
- Savings -> features.savings.controller.SavingsController
"""

# pylint: disable=unused-import  # noqa: F401
from budget_analyser.features.budget_goals.controller import BudgetGoalsController as BudgetController  # noqa: F401,E501
from budget_analyser.features.budget_goals.models import BudgetProgress  # noqa: F401
from budget_analyser.features.savings.models import SavingsMetrics  # noqa: F401
from budget_analyser.features.net_worth.models import NetWorthSummary  # noqa: F401

__all__ = [
    "BudgetController",
    "BudgetProgress",
    "SavingsMetrics",
    "NetWorthSummary",
]
