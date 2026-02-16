"""Recurring transactions service.

Pure business logic for recurring transaction analysis.
No PySide6 or infrastructure dependencies.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.recurring.models import RecurringTransaction

FREQUENCY_MONTHLY_MULTIPLIERS: dict[str, float] = {
    "weekly": 4.33,
    "monthly": 1.0,
    "quarterly": 1.0 / 3,
    "yearly": 1.0 / 12,
}


def calculate_recurring_summary(
    *,
    recurring: list[RecurringTransaction],
) -> dict[str, float]:
    """Calculate summary of recurring expenses.

    Args:
        recurring: List of active recurring transactions.

    Returns:
        Dictionary with monthly_total, yearly_projection, and count.
    """
    monthly_total = 0.0
    for rec in recurring:
        multiplier = FREQUENCY_MONTHLY_MULTIPLIERS.get(
            rec.frequency, 1.0,
        )
        monthly_total += abs(rec.expected_amount) * multiplier

    return {
        "monthly_total": monthly_total,
        "yearly_projection": monthly_total * 12,
        "count": len(recurring),
    }


def check_recurring_anomalies(
    *,
    recurring: list[RecurringTransaction],
    transactions_df: pd.DataFrame,
    tolerance_percent: float = 10.0,
) -> list[dict]:
    """Check for anomalies in recurring transactions.

    Compares most recent actual amounts against expected amounts
    to detect unusual charges.

    Args:
        recurring: Active recurring transactions to check.
        transactions_df: Historical transaction data.
        tolerance_percent: Percentage threshold for flagging anomalies.

    Returns:
        List of anomaly dicts with description, expected, actual,
        difference, and difference_percent.
    """
    if not recurring or transactions_df.empty:
        return []

    anomalies = []

    for rec in recurring:
        matches = transactions_df[
            transactions_df["description"].str.contains(
                rec.description, case=False, na=False,
            )
        ]

        if matches.empty:
            continue

        if "transaction_date" in matches.columns:
            matches = matches.sort_values(
                "transaction_date", ascending=False,
            )

        recent_amount = abs(float(matches.iloc[0]["amount"]))
        expected_amount = abs(rec.expected_amount)

        if expected_amount > 0:
            diff_percent = (
                abs(recent_amount - expected_amount)
                / expected_amount * 100
            )
            if diff_percent > tolerance_percent:
                anomalies.append({
                    "description": rec.description,
                    "expected": expected_amount,
                    "actual": recent_amount,
                    "difference": recent_amount - expected_amount,
                    "difference_percent": diff_percent,
                })

    return anomalies
