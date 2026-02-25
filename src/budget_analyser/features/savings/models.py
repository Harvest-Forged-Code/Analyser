"""Savings feature DTOs.

Data transfer objects for savings rate tracking.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SavingsMetrics:
    """Savings rate and related metrics.

    Attributes:
        total_earnings: Sum of all earnings in dollars.
        total_expenses: Sum of all expenses in dollars (positive).
        net_savings: Total earnings minus total expenses.
        savings_rate: Net savings as percentage of earnings (0-100).
        monthly_average_savings: Average savings per month.
        months_of_data: Number of distinct months in the dataset.

    Example:
        >>> metrics = SavingsMetrics(
        ...     total_earnings=10000.0,
        ...     total_expenses=7000.0,
        ...     net_savings=3000.0,
        ...     savings_rate=30.0,
        ...     monthly_average_savings=1500.0,
        ...     months_of_data=2,
        ... )
        >>> metrics.savings_rate
        30.0
    """

    total_earnings: float
    total_expenses: float
    net_savings: float
    savings_rate: float  # Percentage (0-100)
    monthly_average_savings: float
    months_of_data: int
