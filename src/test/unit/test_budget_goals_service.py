"""Unit tests for budget_goals service pure functions."""
from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetProgress,
    EarningsGoal,
)
from budget_analyser.features.budget_goals.service import (
    build_earnings_goal_map,
    calculate_budget_progress,
)


# ==================== calculate_budget_progress ====================


def test_progress_empty_budgets_returns_empty() -> None:
    expenses = pd.DataFrame({"amount": [100], "category": ["Food"]})
    result = calculate_budget_progress(
        budgets=[], expenses_df=expenses, year_month="2025-01",
    )
    assert result == []


def test_progress_empty_expenses_all_under() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=pd.DataFrame(), year_month="2025-01",
    )
    assert len(result) == 1
    assert result[0].spent == 0.0
    assert result[0].status == "under"
    assert result[0].remaining == 500.0


def test_progress_under_budget() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15"],
        "amount": [-200],
        "category": ["Food"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert len(result) == 1
    assert result[0].spent == 200.0
    assert result[0].status == "under"
    assert result[0].percentage == 40.0


def test_progress_warning_at_80_percent() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15"],
        "amount": [-420],
        "category": ["Food"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert result[0].status == "warning"
    assert result[0].percentage == 84.0


def test_progress_over_budget() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-01-20"],
        "amount": [-300, -250],
        "category": ["Food", "Food"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert result[0].status == "over"
    assert result[0].percentage == pytest.approx(110.0)


def test_progress_filters_by_year_month() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -300],
        "category": ["Food", "Food"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert result[0].spent == 200.0


def test_progress_month_specific_budget_skips_other_months() -> None:
    budgets = [
        BudgetGoal(
            id=1, category="Food", monthly_limit=500, year_month="2025-02",
        ),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15"],
        "amount": [-200],
        "category": ["Food"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert result == []


def test_progress_sorted_by_percentage_descending() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Transport", monthly_limit=200, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-01-15"],
        "amount": [-100, -180],
        "category": ["Food", "Transport"],
    })
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=expenses, year_month="2025-01",
    )
    assert result[0].category == "Transport"
    assert result[1].category == "Food"


def test_progress_zero_limit_stays_under() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=0, year_month="ALL"),
    ]
    result = calculate_budget_progress(
        budgets=budgets, expenses_df=pd.DataFrame(), year_month="2025-01",
    )
    assert result[0].percentage == 0
    assert result[0].status == "under"


# ==================== build_earnings_goal_map ====================


def test_earnings_map_all_goals_only() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="bonus", expected_amount=200, year_month="ALL"),
    ]
    result = build_earnings_goal_map(goals=goals)
    assert result == {"salary": 5000, "bonus": 200}


def test_earnings_map_month_specific_overrides_all() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="salary", expected_amount=6000, year_month="2025-01"),
    ]
    result = build_earnings_goal_map(goals=goals, year_month="2025-01")
    assert result == {"salary": 6000}


def test_earnings_map_month_with_no_all_default() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="bonus", expected_amount=500, year_month="2025-01"),
    ]
    result = build_earnings_goal_map(goals=goals, year_month="2025-01")
    assert result == {"bonus": 500}


def test_earnings_map_unmatched_month_falls_back_to_all() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="bonus", expected_amount=500, year_month="2025-01"),
    ]
    result = build_earnings_goal_map(goals=goals, year_month="2025-02")
    assert result == {"salary": 5000}


def test_earnings_map_empty_goals() -> None:
    result = build_earnings_goal_map(goals=[])
    assert result == {}
