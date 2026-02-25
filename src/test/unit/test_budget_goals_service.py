"""Unit tests for budget_goals service pure functions."""
from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetGoalsSummary,
    BudgetProgress,
    CategoryProgressPoint,
    EarningsGoal,
    EarningsGoalsSummary,
    ProgressSummary,
)
from budget_analyser.features.budget_goals.service import (
    _build_year_grid_budget,
    _build_year_grid_earnings,
    build_earnings_goal_map,
    calculate_budget_goals_summary,
    calculate_budget_progress,
    calculate_category_progress_history,
    calculate_earnings_goals_summary,
    calculate_progress_summary,
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


# ==================== calculate_budget_goals_summary ====================


def test_budget_summary_empty_goals() -> None:
    result = calculate_budget_goals_summary(goals=[])
    assert result.total_monthly_budget == 0.0
    assert result.categories_tracked == 0
    assert result.month_overrides == 0


def test_budget_summary_all_defaults_only() -> None:
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Transport", monthly_limit=200, year_month="ALL"),
    ]
    result = calculate_budget_goals_summary(goals=goals)
    assert result.total_monthly_budget == 700.0
    assert result.categories_tracked == 2
    assert result.month_overrides == 0


def test_budget_summary_with_overrides() -> None:
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=600, year_month="2025-12"),
        BudgetGoal(id=3, category="Transport", monthly_limit=200, year_month="ALL"),
        BudgetGoal(id=4, category="Transport", monthly_limit=250, year_month="2025-01"),
    ]
    result = calculate_budget_goals_summary(goals=goals)
    assert result.total_monthly_budget == 700.0  # Only "ALL" goals
    assert result.categories_tracked == 2
    assert result.month_overrides == 2


# ==================== calculate_earnings_goals_summary ====================


def test_earnings_summary_empty_goals() -> None:
    result = calculate_earnings_goals_summary(goals=[])
    assert result.total_expected_earnings == 0.0
    assert result.sub_categories_tracked == 0
    assert result.month_overrides == 0


def test_earnings_summary_with_overrides() -> None:
    goals = [
        EarningsGoal(id=1, sub_category="Salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="Salary", expected_amount=5500, year_month="2025-12"),
        EarningsGoal(id=3, sub_category="Bonus", expected_amount=1000, year_month="ALL"),
    ]
    result = calculate_earnings_goals_summary(goals=goals)
    assert result.total_expected_earnings == 6000.0
    assert result.sub_categories_tracked == 2
    assert result.month_overrides == 1


# ==================== calculate_progress_summary ====================


def test_progress_summary_empty() -> None:
    result = calculate_progress_summary(progress_list=[])
    assert result.on_track_count == 0
    assert result.warning_count == 0
    assert result.over_budget_count == 0
    assert result.total_spent == 0.0
    assert result.total_budget == 0.0


def test_progress_summary_mixed_statuses() -> None:
    progress_list = [
        BudgetProgress(
            category="Food", budget_limit=500, spent=200,
            remaining=300, percentage=40, status="under",
        ),
        BudgetProgress(
            category="Transport", budget_limit=200, spent=180,
            remaining=20, percentage=90, status="warning",
        ),
        BudgetProgress(
            category="Dining", budget_limit=300, spent=350,
            remaining=-50, percentage=116.7, status="over",
        ),
    ]
    result = calculate_progress_summary(progress_list=progress_list)
    assert result.on_track_count == 1
    assert result.warning_count == 1
    assert result.over_budget_count == 1
    assert result.total_spent == 730.0
    assert result.total_budget == 1000.0


# ==================== calculate_category_progress_history ====================


def test_category_history_empty_expenses() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=pd.DataFrame(),
        months=["2025-01", "2025-02"],
    )
    assert len(result) == 2
    assert result[0].year_month == "2025-01"
    assert result[0].spent == 0.0
    assert result[0].budget_limit == 500.0


def test_category_history_with_spending() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert len(result) == 2
    assert result[0].spent == 200.0
    assert result[0].status == "under"
    assert result[1].spent == 450.0
    assert result[1].status == "warning"


def test_category_history_month_specific_override() -> None:
    budgets = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=700, year_month="2025-02"),
    ]
    expenses = pd.DataFrame({
        "transaction_date": ["2025-01-15", "2025-02-10"],
        "amount": [-200, -450],
        "category": ["Food", "Food"],
    })
    result = calculate_category_progress_history(
        category="Food",
        budgets=budgets,
        expenses_df=expenses,
        months=["2025-01", "2025-02"],
    )
    assert result[0].budget_limit == 500.0  # ALL default
    assert result[1].budget_limit == 700.0  # Month override


# ==================== _build_year_grid_budget ====================


def test_year_grid_budget_resolves_all_fallback() -> None:
    """ALL default fills all 12 months when no month-specific entries exist."""
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
    ]
    result = _build_year_grid_budget(goals=goals, year=2026)
    assert len(result) == 1
    assert "Food" in result
    assert len(result["Food"]) == 12
    assert all(v == 500.0 for v in result["Food"].values())
    assert result["Food"]["2026-01"] == 500.0
    assert result["Food"]["2026-12"] == 500.0


def test_year_grid_budget_month_override_takes_priority() -> None:
    """Month-specific entry overrides the ALL default for that month."""
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=700, year_month="2026-12"),
    ]
    result = _build_year_grid_budget(goals=goals, year=2026)
    assert result["Food"]["2026-01"] == 500.0
    assert result["Food"]["2026-12"] == 700.0


def test_year_grid_budget_multiple_categories() -> None:
    """Multiple categories each get their own 12-month row."""
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Transport", monthly_limit=200, year_month="ALL"),
    ]
    result = _build_year_grid_budget(goals=goals, year=2026)
    assert len(result) == 2
    assert all(v == 500.0 for v in result["Food"].values())
    assert all(v == 200.0 for v in result["Transport"].values())


def test_year_grid_budget_ignores_other_years() -> None:
    """Month overrides from other years are not included."""
    goals = [
        BudgetGoal(id=1, category="Food", monthly_limit=500, year_month="ALL"),
        BudgetGoal(id=2, category="Food", monthly_limit=700, year_month="2025-12"),
    ]
    result = _build_year_grid_budget(goals=goals, year=2026)
    # 2025-12 override should not affect 2026
    assert all(v == 500.0 for v in result["Food"].values())


def test_year_grid_budget_empty_goals() -> None:
    """Empty goals list returns empty grid."""
    result = _build_year_grid_budget(goals=[], year=2026)
    assert result == {}


def test_year_grid_budget_only_month_specific_no_all_default() -> None:
    """Category with only month-specific entries uses 0 for other months."""
    goals = [
        BudgetGoal(id=1, category="Gifts", monthly_limit=300, year_month="2026-12"),
    ]
    result = _build_year_grid_budget(goals=goals, year=2026)
    assert result["Gifts"]["2026-12"] == 300.0
    assert result["Gifts"]["2026-01"] == 0.0


# ==================== _build_year_grid_earnings ====================


def test_year_grid_earnings_resolves_all_fallback() -> None:
    """ALL default fills all 12 months for earnings goals."""
    goals = [
        EarningsGoal(id=1, sub_category="Salary", expected_amount=5000, year_month="ALL"),
    ]
    result = _build_year_grid_earnings(goals=goals, year=2026)
    assert len(result) == 1
    assert "Salary" in result
    assert len(result["Salary"]) == 12
    assert all(v == 5000.0 for v in result["Salary"].values())


def test_year_grid_earnings_month_override_takes_priority() -> None:
    """Month-specific earnings entry overrides ALL default."""
    goals = [
        EarningsGoal(id=1, sub_category="Salary", expected_amount=5000, year_month="ALL"),
        EarningsGoal(id=2, sub_category="Salary", expected_amount=6000, year_month="2026-12"),
    ]
    result = _build_year_grid_earnings(goals=goals, year=2026)
    assert result["Salary"]["2026-01"] == 5000.0
    assert result["Salary"]["2026-12"] == 6000.0


def test_year_grid_earnings_empty_goals() -> None:
    """Empty earnings goals returns empty grid."""
    result = _build_year_grid_earnings(goals=[], year=2026)
    assert result == {}
