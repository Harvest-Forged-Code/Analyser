from __future__ import annotations

import logging

from budget_analyser.controller.budget_controller import BudgetController
from budget_analyser.infrastructure.budget_database import EarningsGoal


class _StubBudgetDB:
    def __init__(self, earnings_goals):
        self._earnings_goals = earnings_goals

    # Earnings goals
    def get_all_earnings_goals(self):
        return list(self._earnings_goals)


def test_get_earnings_goal_map_prefers_month_specific_over_all() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=1000.0, year_month="ALL"),
        EarningsGoal(id=2, sub_category="salary", expected_amount=1200.0, year_month="2025-01"),
        EarningsGoal(id=3, sub_category="bonus", expected_amount=200.0, year_month="2025-01"),
    ]
    controller = BudgetController(budget_db=_StubBudgetDB(goals), logger=logging.getLogger(__name__))

    jan_map = controller.get_earnings_goal_map("2025-01")
    feb_map = controller.get_earnings_goal_map("2025-02")

    assert jan_map == {"salary": 1200.0, "bonus": 200.0}
    assert feb_map == {"salary": 1000.0}
