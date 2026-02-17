"""Data transfer objects for controller-layer presentation.

Provides view-friendly DTOs that hold aggregated yearly statistics
and category breakdowns for rendering on the Home page.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class YearlyStats:
    """View-friendly yearly statistics for Home page.

    Attributes:
        total_earnings: Sum of positive amounts for the year.
        total_expenses: Sum of expenses as positive value for readability.
        earn_subcats: List of (sub_category, amount) tuples, desc sorted.
        exp_subcats: List of (sub_category, amount) tuples, desc sorted
            (amounts positive).

    Example:
        >>> stats = YearlyStats(
        ...     total_earnings=50000.0,
        ...     total_expenses=30000.0,
        ...     earn_subcats=[("salary", 50000.0)],
        ...     exp_subcats=[("rent", 12000.0)],
        ... )
        >>> stats.total_earnings
        50000.0
    """

    total_earnings: float
    total_expenses: float
    earn_subcats: List[Tuple[str, float]]
    exp_subcats: List[Tuple[str, float]]


@dataclass(frozen=True)
class CategoryNode:
    """Category -> Sub-categories node used for tree rendering.

    Attributes:
        name: Category display name.
        amount: Total amount for this category.
        children: List of (sub_category_name, amount) tuples.

    Example:
        >>> node = CategoryNode(
        ...     name="Housing",
        ...     amount=12000.0,
        ...     children=[("rent", 12000.0)],
        ... )
        >>> node.name
        'Housing'
    """

    name: str
    amount: float
    # Direct children (sub-categories only; two-level tree for UI)
    children: List[Tuple[str, float]]


@dataclass(frozen=True)
class YearlyCategoryBreakdown:
    """Yearly category breakdown for both earnings and expenses.

    Amounts for expenses are normalized to positive values for readability.

    Attributes:
        earnings: List of CategoryNode objects for income categories.
        expenses: List of CategoryNode objects for expense categories.

    Example:
        >>> breakdown = YearlyCategoryBreakdown(
        ...     earnings=[CategoryNode("Income", 50000.0, [])],
        ...     expenses=[CategoryNode("Housing", 12000.0, [])],
        ... )
    """

    earnings: List[CategoryNode]
    expenses: List[CategoryNode]
