"""Recurring transactions service.

Business logic and orchestration for recurring transaction management.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.recurring.models import (
    RecurringModel,
    RecurringTransaction,
)

FREQUENCY_MONTHLY_MULTIPLIERS: dict[str, float] = {
    "weekly": 4.33,
    "monthly": 1.0,
    "quarterly": 1.0 / 3,
    "yearly": 1.0 / 12,
}


def calculate_recurring_summary(
    *,
    recurring: list[RecurringTransaction],
) -> dict[str, float]:
    """Calculate summary of recurring expenses.

    Converts each transaction to a monthly equivalent using
    frequency multipliers and sums totals.

    Args:
        recurring: List of active recurring transactions.

    Returns:
        Dictionary with monthly_total, yearly_projection, and count.

    Example:
        >>> txns = [
        ...     RecurringTransaction(
        ...         id=1, description="Netflix",
        ...         expected_amount=15.99, frequency="monthly",
        ...         category="Entertainment",
        ...         sub_category="Streaming",
        ...         last_occurrence="2024-01-15",
        ...     ),
        ... ]
        >>> calculate_recurring_summary(recurring=txns)
        {'monthly_total': 15.99, 'yearly_projection': 191.88, 'count': 1}
    """
    monthly_total = 0.0
    for rec in recurring:
        multiplier = FREQUENCY_MONTHLY_MULTIPLIERS.get(
            rec.frequency, 1.0,
        )
        monthly_total += abs(rec.expected_amount) * multiplier

    return {
        "monthly_total": monthly_total,
        "yearly_projection": monthly_total * 12,
        "count": len(recurring),
    }


def check_recurring_anomalies(
    *,
    recurring: list[RecurringTransaction],
    transactions_df: pd.DataFrame,
    tolerance_percent: float = 10.0,
) -> list[dict]:
    """Check for anomalies in recurring transactions.

    Compares most recent actual amounts against expected amounts
    to detect unusual charges.

    Args:
        recurring: Active recurring transactions to check.
        transactions_df: Historical transaction data. Must contain
            'description', 'amount', and optionally
            'transaction_date' columns.
        tolerance_percent: Percentage threshold for flagging anomalies.

    Returns:
        List of anomaly dicts with description, expected, actual,
        difference, and difference_percent.

    Example:
        >>> anomalies = check_recurring_anomalies(
        ...     recurring=txns,
        ...     transactions_df=df,
        ...     tolerance_percent=10.0,
        ... )
        >>> anomalies[0]["description"]
        'Netflix'
    """
    if not recurring or transactions_df.empty:
        return []

    anomalies = []

    for rec in recurring:
        matches = transactions_df[
            transactions_df["description"].str.contains(
                rec.description, case=False, na=False,
            )
        ]

        if matches.empty:
            continue

        if "transaction_date" in matches.columns:
            matches = matches.sort_values(
                "transaction_date", ascending=False,
            )

        recent_amount = abs(float(matches.iloc[0]["amount"]))
        expected_amount = abs(rec.expected_amount)

        if expected_amount > 0:
            diff_percent = (
                abs(recent_amount - expected_amount)
                / expected_amount * 100
            )
            if diff_percent > tolerance_percent:
                anomalies.append({
                    "description": rec.description,
                    "expected": expected_amount,
                    "actual": recent_amount,
                    "difference": recent_amount - expected_amount,
                    "difference_percent": diff_percent,
                })

    return anomalies


class RecurringService:
    """Service for recurring transaction management.

    Orchestrates persistence via RecurringModel and pure business
    logic functions for recurring transaction workflows.

    Example:
        >>> from pathlib import Path
        >>> model = RecurringModel(db_path=Path("budget.db"))
        >>> svc = RecurringService(model=model)
        >>> txn = svc.add_recurring_transaction("Netflix", 15.99)
        >>> txn.description
        'Netflix'
    """

    def __init__(self, *, model: RecurringModel) -> None:
        """Initialize the recurring service.

        Args:
            model: RecurringModel for persistence.

        Example:
            >>> svc = RecurringService(model=model)
        """
        self._model = model

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
            >>> svc.add_recurring_transaction(
            ...     "Spotify", 9.99, "monthly",
            ... )
            RecurringTransaction(id=1, description='Spotify', ...)
        """
        return self._model.add_recurring_transaction(
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
            >>> txns = svc.get_all_recurring_transactions()
            >>> len(txns)
            5
        """
        return self._model.get_all_recurring_transactions(
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
            >>> svc.deactivate_recurring_transaction(1)
            True
        """
        return self._model.deactivate_recurring_transaction(
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
            >>> svc.delete_recurring_transaction(1)
            True
        """
        return self._model.delete_recurring_transaction(
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
            >>> detected = svc.detect_recurring_transactions(
            ...     transactions_df=df,
            ...     min_occurrences=3,
            ... )
            >>> detected[0]["description"]
            'Netflix'
        """
        return self._model.detect_recurring_transactions(
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
            >>> summary = svc.get_recurring_summary(expenses_df)
            >>> summary["monthly_total"]
            125.97
        """
        recurring = self._model.get_all_recurring_transactions(
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
            >>> anomalies = svc.check_recurring_anomalies(
            ...     transactions_df=df,
            ...     tolerance_percent=10.0,
            ... )
            >>> len(anomalies)
            1
        """
        recurring = self._model.get_all_recurring_transactions(
            active_only=True,
        )
        return check_recurring_anomalies(
            recurring=recurring,
            transactions_df=transactions_df,
            tolerance_percent=tolerance_percent,
        )


# Backward-compat alias
RecurringController = RecurringService
