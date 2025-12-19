from __future__ import annotations

from typing import List


def month_names() -> List[str]:
    """Return full month names January..December in order.

    Shared utility so all controllers/pages use the same labels.
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
