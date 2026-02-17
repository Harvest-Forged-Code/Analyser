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

    Example:
        >>> from pathlib import Path
        >>> repo = BudgetGoalsRepository(db_path=Path("budget.db"))
        >>> ctrl = BudgetGoalsController(repository=repo)
        >>> ctrl.set_budget("Groceries", 500.0)
        BudgetGoal(id=1, category='Groceries', ...)
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

        Example:
            >>> ctrl = BudgetGoalsController(repository=repo)
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
        """Set a budget limit for a category.

        Args:
            category: Expense category name (e.g. "Groceries").
            monthly_limit: Monthly spending limit in dollars.
            year_month: Period as "YYYY-MM" or "ALL" for every month.

        Returns:
            The created or updated BudgetGoal.

        Example:
            >>> ctrl.set_budget("Dining", 300.0, "2024-06")
            BudgetGoal(id=1, category='Dining', ...)
        """
        return self._repo.set_budget_goal(
            category, monthly_limit, year_month,
        )

    def get_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> BudgetGoal | None:
        """Get budget for a category.

        Args:
            category: Expense category name (e.g. "Groceries").
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            BudgetGoal if found, None otherwise.

        Example:
            >>> ctrl.get_budget("Groceries", "2024-01")
            BudgetGoal(id=1, category='Groceries', ...)
        """
        return self._repo.get_budget_goal(category, year_month)

    def get_all_budgets(self) -> list[BudgetGoal]:
        """Get all budget goals.

        Returns:
            List of all BudgetGoal entries.

        Example:
            >>> budgets = ctrl.get_all_budgets()
            >>> len(budgets)
            3
        """
        return self._repo.get_all_budget_goals()

    def delete_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete a budget goal.

        Args:
            category: Expense category name to delete.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            True if a goal was deleted.

        Example:
            >>> ctrl.delete_budget("Dining", "2024-06")
            True
        """
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

        Example:
            >>> goals = ctrl.set_budget_for_year(
            ...     "Groceries", 500.0, 2024,
            ... )
            >>> len(goals)
            12
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
        """Set an expected earnings amount for a sub-category.

        Args:
            sub_category: Earnings sub-category (e.g. "Salary").
            expected_amount: Expected monthly amount in dollars.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            The created or updated EarningsGoal.

        Example:
            >>> ctrl.set_earnings_goal("Salary", 5000.0, "2024-01")
            EarningsGoal(id=1, sub_category='Salary', ...)
        """
        return self._repo.set_earnings_goal(
            sub_category, expected_amount, year_month,
        )

    def get_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> EarningsGoal | None:
        """Get earnings goal for a sub-category.

        Args:
            sub_category: Earnings sub-category (e.g. "Salary").
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            EarningsGoal if found, None otherwise.

        Example:
            >>> ctrl.get_earnings_goal("Salary", "2024-01")
            EarningsGoal(id=1, sub_category='Salary', ...)
        """
        return self._repo.get_earnings_goal(sub_category, year_month)

    def get_all_earnings_goals(self) -> list[EarningsGoal]:
        """Get all earnings goals.

        Returns:
            List of all EarningsGoal entries.

        Example:
            >>> goals = ctrl.get_all_earnings_goals()
            >>> len(goals)
            2
        """
        return self._repo.get_all_earnings_goals()

    def delete_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete an earnings goal.

        Args:
            sub_category: Earnings sub-category name to delete.
            year_month: Period as "YYYY-MM" or "ALL".

        Returns:
            True if a goal was deleted.

        Example:
            >>> ctrl.delete_earnings_goal("Freelance", "ALL")
            True
        """
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

        Example:
            >>> goals = ctrl.set_earnings_goal_for_year(
            ...     "Salary", 5000.0, 2024,
            ... )
            >>> len(goals)
            12
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

        Example:
            >>> ctrl.get_earnings_goal_map("2024-01")
            {'Salary': 5000.0, 'Freelance': 1000.0}
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

        Example:
            >>> progress = ctrl.calculate_budget_progress(
            ...     expenses_df=expenses,
            ...     year_month="2024-01",
            ... )
            >>> progress[0].status
            'under'
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
        """Get categories that are over or near budget limit.

        Returns only categories with status "over" or "warning"
        (at or above 80% budget utilization).

        Args:
            expenses_df: DataFrame with expense transactions.
            year_month: Month to check (format: "YYYY-MM").

        Returns:
            List of BudgetProgress entries with warning or over status.

        Example:
            >>> alerts = ctrl.get_categories_over_budget(
            ...     expenses_df=expenses,
            ...     year_month="2024-01",
            ... )
            >>> [a.category for a in alerts]
            ['Dining']
        """
        progress = self.calculate_budget_progress(expenses_df, year_month)
        return [p for p in progress if p.status in ("over", "warning")]
