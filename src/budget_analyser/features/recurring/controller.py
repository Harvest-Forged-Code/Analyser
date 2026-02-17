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

    Example:
        >>> from pathlib import Path
        >>> repo = RecurringRepository(db_path=Path("budget.db"))
        >>> ctrl = RecurringController(repository=repo)
        >>> txn = ctrl.add_recurring_transaction("Netflix", 15.99)
        >>> txn.description
        'Netflix'
    """

    def __init__(self, *, repository: RecurringRepository) -> None:
        """Initialize the recurring controller.

        Args:
            repository: Recurring repository for persistence.

        Example:
            >>> ctrl = RecurringController(repository=repo)
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

        Example:
            >>> ctrl.add_recurring_transaction(
            ...     "Spotify", 9.99, "monthly",
            ... )
            RecurringTransaction(id=1, description='Spotify', ...)
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

        Example:
            >>> txns = ctrl.get_all_recurring_transactions()
            >>> len(txns)
            5
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

        Example:
            >>> ctrl.deactivate_recurring_transaction(1)
            True
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

        Example:
            >>> ctrl.delete_recurring_transaction(1)
            True
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

        Example:
            >>> detected = ctrl.detect_recurring_transactions(
            ...     transactions_df=df,
            ...     min_occurrences=3,
            ... )
            >>> detected[0]["description"]
            'Netflix'
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

        Example:
            >>> summary = ctrl.get_recurring_summary(expenses_df)
            >>> summary["monthly_total"]
            125.97
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

        Compares actual amounts against expected to detect unusual
        charges exceeding the tolerance threshold.

        Args:
            transactions_df: Historical transaction data.
            tolerance_percent: Percentage threshold for flagging.

        Returns:
            List of anomaly dicts with description, expected,
            actual, difference, and difference_percent.

        Example:
            >>> anomalies = ctrl.check_recurring_anomalies(
            ...     transactions_df=df,
            ...     tolerance_percent=10.0,
            ... )
            >>> len(anomalies)
            1
        """
        recurring = self._repository.get_all_recurring_transactions(
            active_only=True,
        )
        return check_recurring_anomalies(
            recurring=recurring,
            transactions_df=transactions_df,
            tolerance_percent=tolerance_percent,
        )
