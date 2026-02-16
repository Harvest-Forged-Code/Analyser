"""Unit tests for budget_goals repository."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from budget_analyser.features.budget_goals.repository import BudgetGoalsRepository


@pytest.fixture()
def repo(tmp_path: Path) -> BudgetGoalsRepository:
    """Create a repository backed by a temporary database."""
    db_path = tmp_path / "test_budget.db"
    return BudgetGoalsRepository(db_path=db_path)


# ==================== Budget Goals ====================


def test_set_and_get_budget_goal(repo: BudgetGoalsRepository) -> None:
    goal = repo.set_budget_goal("Food", 500.0)
    assert goal.category == "Food"
    assert goal.monthly_limit == 500.0
    assert goal.year_month == "ALL"
    assert goal.id is not None

    fetched = repo.get_budget_goal("Food")
    assert fetched is not None
    assert fetched.id == goal.id
    assert fetched.monthly_limit == 500.0


def test_set_budget_goal_upserts(repo: BudgetGoalsRepository) -> None:
    repo.set_budget_goal("Food", 500.0)
    updated = repo.set_budget_goal("Food", 600.0)
    assert updated.monthly_limit == 600.0

    all_goals = repo.get_all_budget_goals()
    assert len(all_goals) == 1


def test_get_budget_goal_month_specific(repo: BudgetGoalsRepository) -> None:
    repo.set_budget_goal("Food", 500.0, "ALL")
    repo.set_budget_goal("Food", 600.0, "2025-01")

    specific = repo.get_budget_goal("Food", "2025-01")
    assert specific is not None
    assert specific.monthly_limit == 600.0

    fallback = repo.get_budget_goal("Food", "2025-02")
    assert fallback is not None
    assert fallback.monthly_limit == 500.0  # Falls back to ALL


def test_get_budget_goal_not_found(repo: BudgetGoalsRepository) -> None:
    result = repo.get_budget_goal("NonExistent")
    assert result is None


def test_get_all_budget_goals(repo: BudgetGoalsRepository) -> None:
    repo.set_budget_goal("Food", 500.0)
    repo.set_budget_goal("Transport", 200.0)
    goals = repo.get_all_budget_goals()
    assert len(goals) == 2
    categories = {g.category for g in goals}
    assert categories == {"Food", "Transport"}


def test_delete_budget_goal(repo: BudgetGoalsRepository) -> None:
    repo.set_budget_goal("Food", 500.0)
    assert repo.delete_budget_goal("Food") is True
    assert repo.get_budget_goal("Food") is None


def test_delete_budget_goal_not_found(repo: BudgetGoalsRepository) -> None:
    assert repo.delete_budget_goal("NonExistent") is False


def test_set_budget_goals_for_year(repo: BudgetGoalsRepository) -> None:
    goals = repo.set_budget_goals_for_year("Food", 500.0, 2025)
    assert len(goals) == 12
    months = {g.year_month for g in goals}
    assert "2025-01" in months
    assert "2025-12" in months

    all_goals = repo.get_all_budget_goals()
    assert len(all_goals) == 12


# ==================== Earnings Goals ====================


def test_set_and_get_earnings_goal(repo: BudgetGoalsRepository) -> None:
    goal = repo.set_earnings_goal("salary", 5000.0)
    assert goal.sub_category == "salary"
    assert goal.expected_amount == 5000.0
    assert goal.id is not None

    fetched = repo.get_earnings_goal("salary")
    assert fetched is not None
    assert fetched.expected_amount == 5000.0


def test_set_earnings_goal_upserts(repo: BudgetGoalsRepository) -> None:
    repo.set_earnings_goal("salary", 5000.0)
    updated = repo.set_earnings_goal("salary", 6000.0)
    assert updated.expected_amount == 6000.0

    all_goals = repo.get_all_earnings_goals()
    assert len(all_goals) == 1


def test_get_earnings_goal_month_fallback(
    repo: BudgetGoalsRepository,
) -> None:
    repo.set_earnings_goal("salary", 5000.0, "ALL")
    repo.set_earnings_goal("salary", 6000.0, "2025-01")

    specific = repo.get_earnings_goal("salary", "2025-01")
    assert specific is not None
    assert specific.expected_amount == 6000.0

    fallback = repo.get_earnings_goal("salary", "2025-02")
    assert fallback is not None
    assert fallback.expected_amount == 5000.0


def test_get_earnings_goal_not_found(repo: BudgetGoalsRepository) -> None:
    assert repo.get_earnings_goal("nonexistent") is None


def test_get_all_earnings_goals(repo: BudgetGoalsRepository) -> None:
    repo.set_earnings_goal("salary", 5000.0)
    repo.set_earnings_goal("bonus", 200.0)
    goals = repo.get_all_earnings_goals()
    assert len(goals) == 2


def test_delete_earnings_goal(repo: BudgetGoalsRepository) -> None:
    repo.set_earnings_goal("salary", 5000.0)
    assert repo.delete_earnings_goal("salary") is True
    assert repo.get_earnings_goal("salary") is None


def test_delete_earnings_goal_not_found(repo: BudgetGoalsRepository) -> None:
    assert repo.delete_earnings_goal("nonexistent") is False


def test_set_earnings_goals_for_year(repo: BudgetGoalsRepository) -> None:
    goals = repo.set_earnings_goals_for_year("salary", 5000.0, 2025)
    assert len(goals) == 12
    all_goals = repo.get_all_earnings_goals()
    assert len(all_goals) == 12
