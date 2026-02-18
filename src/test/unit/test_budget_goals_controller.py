"""Unit tests for budget_goals controller."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.budget_goals.models import BudgetGoalsModel
from budget_analyser.features.budget_goals.service import BudgetGoalsService


@pytest.fixture()
def controller(tmp_path: Path) -> BudgetGoalsService:
    """Create a service backed by a temporary database."""
    model = BudgetGoalsModel(db_path=tmp_path / "test.db")
    return BudgetGoalsService(model=model)


def test_set_and_get_budget(controller: BudgetGoalsService) -> None:
    goal = controller.set_budget("Food", 500.0)
    assert goal.category == "Food"

    fetched = controller.get_budget("Food")
    assert fetched is not None
    assert fetched.monthly_limit == 500.0


def test_get_all_budgets(controller: BudgetGoalsService) -> None:
    controller.set_budget("Food", 500.0)
    controller.set_budget("Transport", 200.0)
    assert len(controller.get_all_budgets()) == 2


def test_delete_budget(controller: BudgetGoalsService) -> None:
    controller.set_budget("Food", 500.0)
    assert controller.delete_budget("Food") is True
    assert controller.get_budget("Food") is None


def test_set_budget_for_year(controller: BudgetGoalsService) -> None:
    goals = controller.set_budget_for_year("Food", 500.0, 2025)
    assert len(goals) == 12


def test_earnings_goal_map(controller: BudgetGoalsService) -> None:
    controller.set_earnings_goal("salary", 5000.0, "ALL")
    controller.set_earnings_goal("salary", 6000.0, "2025-01")
    controller.set_earnings_goal("bonus", 200.0, "2025-01")

    jan_map = controller.get_earnings_goal_map("2025-01")
    feb_map = controller.get_earnings_goal_map("2025-02")

    assert jan_map == {"salary": 6000.0, "bonus": 200.0}
    assert feb_map == {"salary": 5000.0}


def test_calculate_budget_progress(
    controller: BudgetGoalsService,
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
    controller: BudgetGoalsService,
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


# ==================== Summary and History Methods ====================


def test_get_budget_goals_summary(tmp_path: Path) -> None:
    """Summary returns correct totals and counts."""
    model = BudgetGoalsModel(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsService(model=model)
    ctrl.set_budget("Food", 500, "ALL")
    ctrl.set_budget("Transport", 200, "ALL")
    ctrl.set_budget("Food", 600, "2025-12")

    summary = ctrl.get_budget_goals_summary()
    assert summary.total_monthly_budget == 700.0
    assert summary.categories_tracked == 2
    assert summary.month_overrides == 1


def test_get_earnings_goals_summary(tmp_path: Path) -> None:
    """Summary returns correct totals and counts."""
    model = BudgetGoalsModel(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsService(model=model)
    ctrl.set_earnings_goal("Salary", 5000, "ALL")
    ctrl.set_earnings_goal("Bonus", 1000, "ALL")
    ctrl.set_earnings_goal("Salary", 5500, "2025-12")

    summary = ctrl.get_earnings_goals_summary()
    assert summary.total_expected_earnings == 6000.0
    assert summary.sub_categories_tracked == 2
    assert summary.month_overrides == 1


def test_get_progress_summary(tmp_path: Path) -> None:
    """Progress summary returns correct status counts."""
    model = BudgetGoalsModel(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsService(model=model)
    ctrl.set_budget("Food", 500, "ALL")
    ctrl.set_budget("Transport", 200, "ALL")

    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-01-15"],
        "amount": [-200, -180],
        "category": ["Food", "Transport"],
    })
    summary = ctrl.get_progress_summary(
        expenses_df=expenses, year_month="2025-01",
    )
    assert summary.on_track_count == 1  # Food at 40%
    assert summary.warning_count == 1   # Transport at 90%
    assert summary.over_budget_count == 0


def test_get_category_progress_history(tmp_path: Path) -> None:
    """History returns progress for each month."""
    model = BudgetGoalsModel(db_path=tmp_path / "test.db")
    ctrl = BudgetGoalsService(model=model)
    ctrl.set_budget("Food", 500, "ALL")

    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    history = ctrl.get_category_progress_history(
        category="Food",
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert len(history) == 2
    assert history[0].spent == 200.0
    assert history[1].spent == 450.0
