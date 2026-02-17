"""Recurring transactions feature DTOs.

Data transfer objects for recurring transaction tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecurringTransaction:  # pylint: disable=too-many-instance-attributes
    """A detected or user-defined recurring transaction.

    Attributes:
        id: Database primary key, or None for unsaved transactions.
        description: Transaction description (e.g. "Netflix").
        expected_amount: Expected charge amount in dollars.
        frequency: Recurrence period: "weekly", "monthly",
            "quarterly", or "yearly".
        category: Transaction category (e.g. "Entertainment").
        sub_category: Transaction sub-category (e.g. "Streaming").
        last_occurrence: Date of last occurrence (ISO format).
        is_active: Whether the recurring transaction is active.

    Example:
        >>> txn = RecurringTransaction(
        ...     id=1,
        ...     description="Netflix",
        ...     expected_amount=15.99,
        ...     frequency="monthly",
        ...     category="Entertainment",
        ...     sub_category="Streaming",
        ...     last_occurrence="2024-01-15",
        ... )
        >>> txn.frequency
        'monthly'
    """

    id: int | None
    description: str
    expected_amount: float
    frequency: str  # "monthly", "weekly", "yearly", "quarterly"
    category: str
    sub_category: str
    last_occurrence: str  # ISO date format
    is_active: bool = True
