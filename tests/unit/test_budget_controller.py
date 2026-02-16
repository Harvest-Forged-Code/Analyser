from __future__ import annotations

import logging

from budget_analyser.controller.budget_controller import BudgetController
from budget_analyser.features.budget_goals.models import EarningsGoal
from budget_analyser.features.budget_goals.repository import BudgetGoalsRepository
from budget_analyser.features.net_worth.repository import NetWorthRepository
from budget_analyser.features.recurring.repository import RecurringRepository


class _StubBudgetGoalsRepository(BudgetGoalsRepository):
    def __init__(self, earnings_goals):
        # Skip parent __init__ to avoid DB initialization
        self._earnings_goals = earnings_goals

    def get_all_earnings_goals(self):
        return list(self._earnings_goals)


class _StubNetWorthRepository(NetWorthRepository):
    def __init__(self):
        # Skip parent __init__ to avoid DB initialization
        pass


class _StubRecurringRepository(RecurringRepository):
    def __init__(self):
        # Skip parent __init__ to avoid DB initialization
        pass


def test_get_earnings_goal_map_prefers_month_specific_over_all() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=1000.0, year_month="ALL"),
        EarningsGoal(id=2, sub_category="salary", expected_amount=1200.0, year_month="2025-01"),
        EarningsGoal(id=3, sub_category="bonus", expected_amount=200.0, year_month="2025-01"),
    ]
    budget_goals_repo = _StubBudgetGoalsRepository(goals)
    net_worth_repo = _StubNetWorthRepository()
    recurring_repo = _StubRecurringRepository()

    controller = BudgetController(
        budget_goals_repo=budget_goals_repo,
        net_worth_repo=net_worth_repo,
        recurring_repo=recurring_repo,
        logger=logging.getLogger(__name__),
    )

    jan_map = controller.get_earnings_goal_map("2025-01")
    feb_map = controller.get_earnings_goal_map("2025-02")

    assert jan_map == {"salary": 1200.0, "bonus": 200.0}
    assert feb_map == {"salary": 1000.0}
