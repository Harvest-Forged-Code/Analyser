"""Savings feature DTOs.

Data transfer objects for savings rate tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SavingsMetrics:
    """Savings rate and related metrics."""

    total_earnings: float
    total_expenses: float
    net_savings: float
    savings_rate: float  # Percentage (0-100)
    monthly_average_savings: float
    months_of_data: int
