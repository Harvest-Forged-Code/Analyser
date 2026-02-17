"""Controller utility functions.

Shared helpers used across multiple controllers for consistent
label generation and formatting.
"""
from __future__ import annotations

from typing import List


def month_names() -> List[str]:
    """Return full month names January..December in order.

    Shared utility so all controllers/pages use the same labels.

    Returns:
        List of 12 month name strings in calendar order.

    Example:
        >>> month_names()[0]
        'January'
        >>> len(month_names())
        12
    """
    return [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
