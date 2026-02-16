"""Budget controller — backward-compatibility facade.

Delegates all operations to the corresponding feature repositories
and services:
- Budget/earnings goals → features.budget_goals
- Net worth/accounts → features.net_worth
- Recurring transactions → features.recurring
- Savings metrics → features.savings

New code should import from the feature modules directly.
This facade will be removed once all page consumers migrate.
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
from budget_analyser.features.net_worth.models import (
    Account,
    NetWorthSummary,
)
from budget_analyser.features.net_worth.repository import (
    NetWorthRepository,
)
from budget_analyser.features.net_worth.service import (
    calculate_net_worth_summary,
)
from budget_analyser.features.recurring.models import (
    RecurringTransaction,
)
from budget_analyser.features.recurring.repository import (
    RecurringRepository,
)
from budget_analyser.features.recurring.service import (
    calculate_recurring_summary,
    check_recurring_anomalies,
)
from budget_analyser.features.savings.models import (
    SavingsMetrics,
)
from budget_analyser.features.savings.service import (
    calculate_monthly_savings,
    calculate_savings_metrics,
)


class BudgetController:  # pylint: disable=too-many-public-methods
    """Backward-compatibility facade over feature repositories.

    All methods delegate to feature repositories and services.
    This class exists so that legacy page consumers can keep using
    the old interface. New code should import directly from
    features.budget_goals, features.net_worth, features.recurring,
    or features.savings.
    """

    def __init__(
        self,
        *,
        budget_goals_repo: BudgetGoalsRepository,
        net_worth_repo: NetWorthRepository,
        recurring_repo: RecurringRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the budget controller.

        Args:
            budget_goals_repo: Repository for budget and earnings goals.
            net_worth_repo: Repository for financial accounts.
            recurring_repo: Repository for recurring transactions.
            logger: Optional logger for diagnostics.
        """
        self._goals_repo = budget_goals_repo
        self._net_worth_repo = net_worth_repo
        self._recurring_repo = recurring_repo
        self._logger = logger or logging.getLogger(
            "budget_analyser.budget_controller"
        )

    # ==================== Budget Goals ====================

    def set_budget(
        self,
        category: str,
        monthly_limit: float,
        year_month: str = "ALL",
    ) -> BudgetGoal:
        """Set a budget limit for a category."""
        return self._goals_repo.set_budget_goal(
            category, monthly_limit, year_month,
        )

    def get_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> BudgetGoal | None:
        """Get budget for a category."""
        return self._goals_repo.get_budget_goal(
            category, year_month,
        )

    def get_all_budgets(self) -> list[BudgetGoal]:
        """Get all budget goals."""
        return self._goals_repo.get_all_budget_goals()

    def delete_budget(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete a budget goal."""
        return self._goals_repo.delete_budget_goal(
            category, year_month,
        )

    def set_budget_for_year(
        self,
        category: str,
        monthly_limit: float,
        year: int,
    ) -> list[BudgetGoal]:
        """Set budget limits for all 12 months of a year."""
        return self._goals_repo.set_budget_goals_for_year(
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
        return self._goals_repo.set_earnings_goal(
            sub_category, expected_amount, year_month,
        )

    def get_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> EarningsGoal | None:
        """Get earnings goal for a sub-category."""
        return self._goals_repo.get_earnings_goal(
            sub_category, year_month,
        )

    def get_all_earnings_goals(self) -> list[EarningsGoal]:
        """Get all earnings goals."""
        return self._goals_repo.get_all_earnings_goals()

    def delete_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete an earnings goal."""
        return self._goals_repo.delete_earnings_goal(
            sub_category, year_month,
        )

    def set_earnings_goal_for_year(
        self,
        sub_category: str,
        expected_amount: float,
        year: int,
    ) -> list[EarningsGoal]:
        """Set expected earnings for all 12 months of a year."""
        return self._goals_repo.set_earnings_goals_for_year(
            sub_category, expected_amount, year,
        )

    def get_earnings_goal_map(
        self,
        year_month: str = "ALL",
    ) -> dict[str, float]:
        """Get a mapping of sub-category to expected amount."""
        goals = self._goals_repo.get_all_earnings_goals()
        return build_earnings_goal_map(
            goals=goals, year_month=year_month,
        )

    def calculate_budget_progress(
        self,
        expenses_df: pd.DataFrame,
        year_month: str,
    ) -> list[BudgetProgress]:
        """Calculate budget progress for all categories."""
        budgets = self._goals_repo.get_all_budget_goals()
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
        progress = self.calculate_budget_progress(
            expenses_df, year_month,
        )
        return [
            p for p in progress if p.status in ("over", "warning")
        ]

    # ==================== Savings Rate ====================

    def calculate_savings_metrics(
        self,
        earnings_df: pd.DataFrame,
        expenses_df: pd.DataFrame,
        year: int | None = None,
    ) -> SavingsMetrics:
        """Calculate savings rate and related metrics."""
        return calculate_savings_metrics(
            earnings_df=earnings_df,
            expenses_df=expenses_df,
            year=year,
        )

    def calculate_monthly_savings(
        self,
        earnings_df: pd.DataFrame,
        expenses_df: pd.DataFrame,
        year: int,
    ) -> list[tuple[str, float, float, float, float]]:
        """Calculate savings for each month in a year."""
        return calculate_monthly_savings(
            earnings_df=earnings_df,
            expenses_df=expenses_df,
            year=year,
        )

    # ==================== Net Worth ====================

    def add_account(
        self,
        name: str,
        account_type: str,
        balance: float = 0,
        notes: str = "",
    ) -> Account:
        """Add a new financial account."""
        return self._net_worth_repo.add_account(
            name, account_type, balance, notes,
        )

    def update_account_balance(
        self,
        account_id: int,
        balance: float,
    ) -> bool:
        """Update an account's balance."""
        return self._net_worth_repo.update_account_balance(
            account_id, balance,
        )

    def get_all_accounts(self) -> list[Account]:
        """Get all financial accounts."""
        return self._net_worth_repo.get_all_accounts()

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account."""
        return self._net_worth_repo.delete_account(account_id)

    def get_net_worth_summary(self) -> NetWorthSummary:
        """Get comprehensive net worth summary."""
        accounts = self._net_worth_repo.get_all_accounts()
        return calculate_net_worth_summary(accounts=accounts)

    # ==================== Recurring Transactions ====================

    def add_recurring_transaction(  # pylint: disable=too-many-positional-arguments
        self,
        description: str,
        expected_amount: float,
        frequency: str = "monthly",
        category: str = "",
        sub_category: str = "",
    ) -> RecurringTransaction:
        """Add a recurring transaction."""
        return self._recurring_repo.add_recurring_transaction(
            description, expected_amount, frequency,
            category, sub_category,
        )

    def get_all_recurring_transactions(
        self,
        active_only: bool = True,
    ) -> list[RecurringTransaction]:
        """Get all recurring transactions."""
        return self._recurring_repo.get_all_recurring_transactions(
            active_only,
        )

    def deactivate_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Mark a recurring transaction as inactive."""
        return self._recurring_repo.deactivate_recurring_transaction(
            recurring_id,
        )

    def delete_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Delete a recurring transaction."""
        return self._recurring_repo.delete_recurring_transaction(
            recurring_id,
        )

    def detect_recurring_transactions(
        self,
        transactions_df: pd.DataFrame,
        min_occurrences: int = 2,
    ) -> list[dict]:
        """Detect potential recurring transactions from history."""
        return self._recurring_repo.detect_recurring_transactions(
            transactions_df, min_occurrences,
        )

    def get_recurring_summary(
        self,
        transactions_df: pd.DataFrame,  # pylint: disable=unused-argument
    ) -> dict[str, float]:
        """Get summary of recurring expenses."""
        recurring = self._recurring_repo.get_all_recurring_transactions(
            active_only=True,
        )
        return calculate_recurring_summary(recurring=recurring)

    def check_recurring_anomalies(
        self,
        transactions_df: pd.DataFrame,
        tolerance_percent: float = 10.0,
    ) -> list[dict]:
        """Check for anomalies in recurring transactions."""
        recurring = self._recurring_repo.get_all_recurring_transactions(
            active_only=True,
        )
        return check_recurring_anomalies(
            recurring=recurring,
            transactions_df=transactions_df,
            tolerance_percent=tolerance_percent,
        )


__all__ = [
    "BudgetProgress",
    "SavingsMetrics",
    "NetWorthSummary",
    "BudgetController",
]
