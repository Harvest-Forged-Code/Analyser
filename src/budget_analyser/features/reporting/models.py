"""Reporting feature DTOs.

Data transfer objects for earnings and expenses statistics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EarningsRow:
    """A row in the earnings aggregated table.

    Attributes:
        sub_category: Sub-category name.
        actual: Actual amount received.
        percent_of_total: Percentage of total earnings.
        expected: Expected amount from goals.
        diff: Difference (actual - expected).
        diff_percent: Percentage difference.

    Example:
        >>> row = EarningsRow(
        ...     sub_category="Salary",
        ...     actual=5000.0,
        ...     percent_of_total=80.0,
        ...     expected=4500.0,
        ...     diff=500.0,
        ...     diff_percent=11.11,
        ... )
        >>> row.sub_category
        'Salary'
        >>> row.diff
        500.0
    """

    sub_category: str
    actual: float
    percent_of_total: float
    expected: float
    diff: float
    diff_percent: float | None
