"""Recurring transactions feature DTOs.

Data transfer objects for recurring transaction tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RecurringTransaction:  # pylint: disable=too-many-instance-attributes
    """A detected or user-defined recurring transaction."""

    id: int | None
    description: str
    expected_amount: float
    frequency: str  # "monthly", "weekly", "yearly", "quarterly"
    category: str
    sub_category: str
    last_occurrence: str  # ISO date format
    is_active: bool = True
