"""Savings service.

Pure business logic for savings rate calculations.
No PySide6 or infrastructure dependencies.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.savings.models import SavingsMetrics

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November",
    "December",
)


def calculate_savings_metrics(
    *,
    earnings_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    year: int | None = None,
) -> SavingsMetrics:
    """Calculate savings rate and related metrics.

    Args:
        earnings_df: DataFrame with earnings transactions.
        expenses_df: DataFrame with expense transactions.
        year: Optional year to filter by. If None, uses all data.

    Returns:
        SavingsMetrics with savings rate and related data.
    """
    earnings_df = _filter_by_year(earnings_df, year)
    expenses_df = _filter_by_year(expenses_df, year)

    total_earnings = (
        float(earnings_df["amount"].sum())
        if not earnings_df.empty else 0.0
    )
    total_expenses = (
        float(abs(expenses_df["amount"].sum()))
        if not expenses_df.empty else 0.0
    )

    net_savings = total_earnings - total_expenses
    savings_rate = (
        (net_savings / total_earnings) * 100
    ) if total_earnings > 0 else 0.0

    months_set: set = set()
    for df in [earnings_df, expenses_df]:
        if not df.empty and "transaction_date" in df.columns:
            dates = pd.to_datetime(
                df["transaction_date"], errors="coerce",
            )
            months_set.update(
                dates.dt.to_period("M").dropna().unique(),
            )

    months_of_data = len(months_set) if months_set else 1
    monthly_average_savings = (
        net_savings / months_of_data if months_of_data > 0 else 0.0
    )

    return SavingsMetrics(
        total_earnings=total_earnings,
        total_expenses=total_expenses,
        net_savings=net_savings,
        savings_rate=savings_rate,
        monthly_average_savings=monthly_average_savings,
        months_of_data=months_of_data,
    )


def calculate_monthly_savings(
    *,
    earnings_df: pd.DataFrame,
    expenses_df: pd.DataFrame,
    year: int,
) -> list[tuple[str, float, float, float, float]]:
    """Calculate savings for each month in a year.

    Args:
        earnings_df: DataFrame with earnings transactions.
        expenses_df: DataFrame with expense transactions.
        year: Year to calculate monthly savings for.

    Returns:
        List of 12 tuples: (month_name, earnings, expenses,
        savings, savings_rate).
    """
    results: list[tuple[str, float, float, float, float]] = []

    for month_idx in range(1, 13):
        year_month = f"{year}-{month_idx:02d}"

        month_earnings = _sum_for_month(earnings_df, year_month)
        month_expenses = abs(_sum_for_month(expenses_df, year_month))

        savings = month_earnings - month_expenses
        savings_rate = (
            (savings / month_earnings * 100)
            if month_earnings > 0 else 0.0
        )

        results.append((
            MONTH_NAMES[month_idx - 1],
            month_earnings,
            month_expenses,
            savings,
            savings_rate,
        ))

    return results


def _filter_by_year(
    df: pd.DataFrame,
    year: int | None,
) -> pd.DataFrame:
    """Filter DataFrame by year if specified.

    Args:
        df: Transaction DataFrame.
        year: Year to filter by, or None to skip filtering.

    Returns:
        Filtered (or original) DataFrame.
    """
    if year is None or df.empty:
        return df
    if "transaction_date" not in df.columns:
        return df
    return df[
        pd.to_datetime(
            df["transaction_date"], errors="coerce",
        ).dt.year == year
    ]


def _sum_for_month(
    df: pd.DataFrame,
    year_month: str,
) -> float:
    """Sum amounts for a specific month.

    Args:
        df: Transaction DataFrame with transaction_date and amount.
        year_month: Month string in "YYYY-MM" format.

    Returns:
        Sum of amounts for the month, or 0.0 if no data.
    """
    if df.empty or "transaction_date" not in df.columns:
        return 0.0

    working = df.copy()
    working["_ym"] = (
        pd.to_datetime(working["transaction_date"], errors="coerce")
        .dt.strftime("%Y-%m")
    )
    month_data = working[working["_ym"] == year_month]
    return float(month_data["amount"].sum()) if not month_data.empty else 0.0
