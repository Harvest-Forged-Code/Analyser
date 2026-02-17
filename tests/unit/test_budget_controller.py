from __future__ import annotations

import logging

from budget_analyser.features.budget_goals.controller import BudgetGoalsController
from budget_analyser.features.budget_goals.models import EarningsGoal
from budget_analyser.features.budget_goals.repository import BudgetGoalsRepository


class _StubBudgetGoalsRepository(BudgetGoalsRepository):
    def __init__(self, earnings_goals):
        # Skip parent __init__ to avoid DB initialization
        self._earnings_goals = earnings_goals

    def get_all_earnings_goals(self):
        return list(self._earnings_goals)


def test_get_earnings_goal_map_prefers_month_specific_over_all() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=1000.0, year_month="ALL"),
        EarningsGoal(id=2, sub_category="salary", expected_amount=1200.0, year_month="2025-01"),
        EarningsGoal(id=3, sub_category="bonus", expected_amount=200.0, year_month="2025-01"),
    ]
    budget_goals_repo = _StubBudgetGoalsRepository(goals)

    controller = BudgetGoalsController(
        repository=budget_goals_repo,
        logger=logging.getLogger(__name__),
    )

    jan_map = controller.get_earnings_goal_map("2025-01")
    feb_map = controller.get_earnings_goal_map("2025-02")

    assert jan_map == {"salary": 1200.0, "bonus": 200.0}
    assert feb_map == {"salary": 1000.0}


def test_shim_exports_budget_controller_alias() -> None:
    """Verify backward-compat shim exports BudgetController as alias."""
    from budget_analyser.controller.budget_controller import BudgetController
    assert BudgetController is BudgetGoalsController
