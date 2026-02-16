"""Recurring transactions controller.

Thin facade that delegates to repository for persistence
and service for business logic.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.recurring.models import RecurringTransaction
from budget_analyser.features.recurring.repository import (
    RecurringRepository,
)
from budget_analyser.features.recurring.service import (
    calculate_recurring_summary,
    check_recurring_anomalies,
)


class RecurringController:
    """Controller for recurring transaction management.

    Provides the same API surface as the legacy BudgetController
    recurring methods, but delegates to the feature repository
    and service.
    """

    def __init__(self, *, repository: RecurringRepository) -> None:
        """Initialize the recurring controller.

        Args:
            repository: Recurring repository for persistence.
        """
        self._repository = repository

    def add_recurring_transaction(  # pylint: disable=too-many-positional-arguments
        self,
        description: str,
        expected_amount: float,
        frequency: str = "monthly",
        category: str = "",
        sub_category: str = "",
    ) -> RecurringTransaction:
        """Add a recurring transaction.

        Args:
            description: Transaction description.
            expected_amount: Expected amount.
            frequency: How often (weekly, monthly, quarterly, yearly).
            category: Transaction category.
            sub_category: Transaction sub-category.

        Returns:
            The created RecurringTransaction.
        """
        return self._repository.add_recurring_transaction(
            description, expected_amount, frequency,
            category, sub_category,
        )

    def get_all_recurring_transactions(
        self,
        active_only: bool = True,
    ) -> list[RecurringTransaction]:
        """Get all recurring transactions.

        Args:
            active_only: If True, return only active transactions.

        Returns:
            List of recurring transactions.
        """
        return self._repository.get_all_recurring_transactions(
            active_only,
        )

    def deactivate_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Mark a recurring transaction as inactive.

        Args:
            recurring_id: The recurring transaction ID.

        Returns:
            True if deactivated.
        """
        return self._repository.deactivate_recurring_transaction(
            recurring_id,
        )

    def delete_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Delete a recurring transaction.

        Args:
            recurring_id: The recurring transaction ID.

        Returns:
            True if deleted.
        """
        return self._repository.delete_recurring_transaction(
            recurring_id,
        )

    def detect_recurring_transactions(
        self,
        transactions_df: pd.DataFrame,
        min_occurrences: int = 2,
    ) -> list[dict]:
        """Detect potential recurring transactions from history.

        Args:
            transactions_df: DataFrame with transaction data.
            min_occurrences: Minimum times a transaction must appear.

        Returns:
            List of detected recurring transaction patterns.
        """
        return self._repository.detect_recurring_transactions(
            transactions_df, min_occurrences,
        )

    def get_recurring_summary(
        self,
        transactions_df: pd.DataFrame,  # pylint: disable=unused-argument
    ) -> dict[str, float]:
        """Get summary of recurring expenses.

        Args:
            transactions_df: Expenses DataFrame (unused, kept for
                API compatibility).

        Returns:
            Dictionary with monthly_total, yearly_projection, count.
        """
        recurring = self._repository.get_all_recurring_transactions(
            active_only=True,
        )
        return calculate_recurring_summary(recurring=recurring)

    def check_recurring_anomalies(
        self,
        transactions_df: pd.DataFrame,
        tolerance_percent: float = 10.0,
    ) -> list[dict]:
        """Check for anomalies in recurring transactions.

        Args:
            transactions_df: Historical transaction data.
            tolerance_percent: Percentage threshold for flagging.

        Returns:
            List of anomaly dicts.
        """
        recurring = self._repository.get_all_recurring_transactions(
            active_only=True,
        )
        return check_recurring_anomalies(
            recurring=recurring,
            transactions_df=transactions_df,
            tolerance_percent=tolerance_percent,
        )
