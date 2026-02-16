"""Budget goals controller.

Thin presentation-layer facade that delegates to the service and
repository. Keeps the same method signatures the view layer expects.
"""

from __future__ import annotations

import logging

import pandas as pd

from budget_analyser.features.budget_goals.models import (
    BudgetGoal,
    BudgetProgress,
    EarningsGoal,
)
from budget_analyser.features.budget_goals.repository import (
    BudgetGoalsRepository,
)
from budget_analyser.features.budget_goals.service import (
    build_earnings_goal_map,
    calculate_budget_progress,
)


class BudgetGoalsController:
    """Controller for budget goal management.

    Delegates persistence to BudgetGoalsRepository and business logic
    to pure service functions.
    """

    def __init__(
        self,
        *,
        repository: BudgetGoalsRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the budget goals controller.

        Args:
            repository: Budget goals repository instance.
            logger: Optional logger for diagnostics.
        """
        self._repo = repository
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.budget_goals.controller"
        )

    # ==================== Budget Goals ====================

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        year_month: str = "ALL",
    ) -> BudgetGoal:
        """Set a budget limit for a category."""
        return self._repo.set_budget_goal(
            category, monthly_limit, year_month,
        )

    def get_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> BudgetGoal | None:
        """Get budget for a category."""
        return self._repo.get_budget_goal(category, year_month)

    def get_all_budgets(self) -> list[BudgetGoal]:
        """Get all budget goals."""
        return self._repo.get_all_budget_goals()

    def delete_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete a budget goal."""
        return self._repo.delete_budget_goal(category, year_month)

    def set_budget_for_year(
        self,
        category: str,
        monthly_limit: float,
        year: int,
    ) -> list[BudgetGoal]:
        """Set budget limits for all 12 months of a year.

        Args:
            category: The expense category name.
            monthly_limit: The monthly spending limit.
            year: The year to set goals for.

        Returns:
            List of 12 BudgetGoal objects.
        """
        return self._repo.set_budget_goals_for_year(
            category, monthly_limit, year,
        )

    # ==================== Earnings Goals ====================

    def set_earnings_goal(
        self,
        sub_category: str,
        expected_amount: float,
        year_month: str = "ALL",
    ) -> EarningsGoal:
        """Set an expected earnings amount for a sub-category."""
        return self._repo.set_earnings_goal(
            sub_category, expected_amount, year_month,
        )

    def get_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> EarningsGoal | None:
        """Get earnings goal for a sub-category."""
        return self._repo.get_earnings_goal(sub_category, year_month)

    def get_all_earnings_goals(self) -> list[EarningsGoal]:
        """Get all earnings goals."""
        return self._repo.get_all_earnings_goals()

    def delete_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete an earnings goal."""
        return self._repo.delete_earnings_goal(sub_category, year_month)

    def set_earnings_goal_for_year(
        self,
        sub_category: str,
        expected_amount: float,
        year: int,
    ) -> list[EarningsGoal]:
        """Set expected earnings for all 12 months of a year.

        Args:
            sub_category: The earnings sub-category name.
            expected_amount: The expected monthly earnings amount.
            year: The year to set goals for.

        Returns:
            List of 12 EarningsGoal objects.
        """
        return self._repo.set_earnings_goals_for_year(
            sub_category, expected_amount, year,
        )

    def get_earnings_goal_map(
        self,
        year_month: str = "ALL",
    ) -> dict[str, float]:
        """Get a mapping of sub-category to expected amount.

        Args:
            year_month: Specific month "YYYY-MM" or "ALL" for defaults.

        Returns:
            Dict mapping sub_category name to expected_amount.
        """
        goals = self._repo.get_all_earnings_goals()
        return build_earnings_goal_map(
            goals=goals, year_month=year_month,
        )

    # ==================== Budget Progress ====================

    def calculate_budget_progress(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> list[BudgetProgress]:
        """Calculate budget progress for all categories in a given month.

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to calculate for (format: "YYYY-MM").

        Returns:
            List of BudgetProgress for each category with a budget.
        """
        budgets = self._repo.get_all_budget_goals()
        return calculate_budget_progress(
            budgets=budgets,
            expenses_df=expenses_df,
            year_month=year_month,
        )

    def get_categories_over_budget(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> list[BudgetProgress]:
        """Get categories that are over or near budget limit."""
        progress = self.calculate_budget_progress(expenses_df, year_month)
        return [p for p in progress if p.status in ("over", "warning")]
