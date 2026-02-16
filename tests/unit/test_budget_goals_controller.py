"""Unit tests for budget_goals controller."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.budget_goals.controller import BudgetGoalsController
from budget_analyser.features.budget_goals.repository import BudgetGoalsRepository


@pytest.fixture()
def controller(tmp_path: Path) -> BudgetGoalsController:
    """Create a controller backed by a temporary database."""
    repo = BudgetGoalsRepository(db_path=tmp_path / "test.db")
    return BudgetGoalsController(repository=repo)


def test_set_and_get_budget(controller: BudgetGoalsController) -> None:
    goal = controller.set_budget("Food", 500.0)
    assert goal.category == "Food"

    fetched = controller.get_budget("Food")
    assert fetched is not None
    assert fetched.monthly_limit == 500.0


def test_get_all_budgets(controller: BudgetGoalsController) -> None:
    controller.set_budget("Food", 500.0)
    controller.set_budget("Transport", 200.0)
    assert len(controller.get_all_budgets()) == 2


def test_delete_budget(controller: BudgetGoalsController) -> None:
    controller.set_budget("Food", 500.0)
    assert controller.delete_budget("Food") is True
    assert controller.get_budget("Food") is None


def test_set_budget_for_year(controller: BudgetGoalsController) -> None:
    goals = controller.set_budget_for_year("Food", 500.0, 2025)
    assert len(goals) == 12


def test_earnings_goal_map(controller: BudgetGoalsController) -> None:
    controller.set_earnings_goal("salary", 5000.0, "ALL")
    controller.set_earnings_goal("salary", 6000.0, "2025-01")
    controller.set_earnings_goal("bonus", 200.0, "2025-01")

    jan_map = controller.get_earnings_goal_map("2025-01")
    feb_map = controller.get_earnings_goal_map("2025-02")

    assert jan_map == {"salary": 6000.0, "bonus": 200.0}
    assert feb_map == {"salary": 5000.0}


def test_calculate_budget_progress(
    controller: BudgetGoalsController,
) -> None:
    controller.set_budget("Food", 500.0)
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15"],
        "amount": [-300],
        "category": ["Food"],
    })
    progress = controller.calculate_budget_progress(expenses, "2025-01")
    assert len(progress) == 1
    assert progress[0].spent == 300.0
    assert progress[0].status == "under"


def test_get_categories_over_budget(
    controller: BudgetGoalsController,
) -> None:
    controller.set_budget("Food", 200.0)
    controller.set_budget("Transport", 500.0)
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-01-15"],
        "amount": [-250, -100],
        "category": ["Food", "Transport"],
    })
    over = controller.get_categories_over_budget(expenses, "2025-01")
    assert len(over) == 1
    assert over[0].category == "Food"
