from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple


@dataclass(frozen=True)
class YearlyStats:
    """View-friendly yearly statistics for Home page.

    - total_earnings: sum of positive amounts for the year.
    - total_expenses: sum of expenses shown as positive value for readability.
    - earn_subcats: list of (sub_category, amount) tuples, desc sorted.
    - exp_subcats: list of (sub_category, amount) tuples, desc sorted (amounts positive).
    - monthly_rows: list of (month_name, earnings, expenses) for Jan..Dec with zero padding.
    """

    total_earnings: float
    total_expenses: float
    earn_subcats: List[Tuple[str, float]]
    exp_subcats: List[Tuple[str, float]]
    monthly_rows: List[Tuple[str, float, float]]


@dataclass(frozen=True)
class CategoryNode:
    """Category -> Sub-categories node used for tree rendering."""

    name: str
    amount: float
    # Direct children (sub-categories only; two-level tree for UI)
    children: List[Tuple[str, float]]


@dataclass(frozen=True)
class YearlyCategoryBreakdown:
    """Yearly category breakdown for both earnings and expenses.

    Amounts for expenses are normalized to positive values for readability.
    """

    earnings: List[CategoryNode]
    expenses: List[CategoryNode]
