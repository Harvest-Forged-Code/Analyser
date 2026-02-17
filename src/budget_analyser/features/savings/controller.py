"""Savings controller.

Thin facade that delegates to service for business logic.
This feature has no repository since savings metrics are computed
from transaction data, not stored in a dedicated table.
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.savings.models import SavingsMetrics
from budget_analyser.features.savings.service import (
    calculate_monthly_savings,
    calculate_savings_metrics,
)


class SavingsController:
    """Controller for savings rate tracking.

    Provides the same API surface as the legacy BudgetController
    savings methods, but delegates to the feature service. This
    feature has no repository since savings metrics are computed
    from transaction data, not stored in a dedicated table.

    Example:
        >>> ctrl = SavingsController()
        >>> metrics = ctrl.calculate_savings_metrics(
        ...     earnings_df=earnings,
        ...     expenses_df=expenses,
        ... )
        >>> metrics.savings_rate
        30.0
    """

    def calculate_savings_metrics(
        self,
        earnings_df: pd.DataFrame,
        expenses_df: pd.DataFrame,
        year: int | None = None,
    ) -> SavingsMetrics:
        """Calculate savings rate and related metrics.

        Args:
            earnings_df: DataFrame with earnings transactions.
            expenses_df: DataFrame with expense transactions.
            year: Optional year to filter by.

        Returns:
            SavingsMetrics with savings rate and related data.

        Example:
            >>> metrics = ctrl.calculate_savings_metrics(
            ...     earnings_df=earnings,
            ...     expenses_df=expenses,
            ...     year=2024,
            ... )
            >>> metrics.savings_rate
            30.0
        """
        return calculate_savings_metrics(
            earnings_df=earnings_df,
            expenses_df=expenses_df,
            year=year,
        )

    def calculate_monthly_savings(
        self,
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

        Example:
            >>> monthly = ctrl.calculate_monthly_savings(
            ...     earnings_df=earnings,
            ...     expenses_df=expenses,
            ...     year=2024,
            ... )
            >>> monthly[0][0]
            'January'
        """
        return calculate_monthly_savings(
            earnings_df=earnings_df,
            expenses_df=expenses_df,
            year=year,
        )
