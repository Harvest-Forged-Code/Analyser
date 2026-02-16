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
    """

    sub_category: str
    actual: float
    percent_of_total: float
    expected: float
    diff: float
    diff_percent: float | None
