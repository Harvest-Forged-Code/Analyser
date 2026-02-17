"""Trend analysis service (business logic).

Provides time-series trend metrics for financial data:
- Month-over-month change (absolute and percentage)
- Moving averages (3-month, 6-month, 12-month)
- Year-over-year comparison
- Trend direction indicators
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.trends.models import (
    MonthlyTrend,
    TrendAnalysisResult,
    TrendDirection,
)


class TrendAnalysisService:
    """Service for analyzing time-series trends in financial data."""

    def __init__(
        self,
        *,
        stable_threshold_pct: float = 5.0,
    ) -> None:
        """Initialize the trend analysis service.

        Args:
            stable_threshold_pct: Percentage threshold for
                stable vs rising/falling.
        """
        self._stable_threshold = stable_threshold_pct

    def analyze(
        self,
        *,
        data: pd.Series | dict[pd.Period, float],
    ) -> TrendAnalysisResult:
        """Analyze trends in monthly data.

        Args:
            data: Monthly data as pandas Series or dict.

        Returns:
            TrendAnalysisResult with all computed metrics.

        Example:
            >>> import pandas as pd
            >>> service = TrendAnalysisService()
            >>> data = pd.Series(
            ...     [100.0, 120.0, 110.0],
            ...     index=[
            ...         pd.Period("2024-01", "M"),
            ...         pd.Period("2024-02", "M"),
            ...         pd.Period("2024-03", "M"),
            ...     ],
            ... )
            >>> result = service.analyze(data=data)
            >>> len(result.monthly_trends)
            3
        """
        if isinstance(data, dict):
            data = pd.Series(data)

        if data.empty:
            return TrendAnalysisResult()

        data = data.sort_index()

        mom_changes = data.diff()
        mom_changes_pct = data.pct_change() * 100

        moving_averages = {
            3: data.rolling(window=3, min_periods=1).mean(),
            6: data.rolling(window=6, min_periods=1).mean(),
            12: data.rolling(window=12, min_periods=1).mean(),
        }

        yoy_changes, yoy_changes_pct = self._compute_yoy(data)

        monthly_trends = self._build_monthly_trends(
            data=data,
            mom_changes=mom_changes,
            mom_changes_pct=mom_changes_pct,
            moving_averages=moving_averages,
            yoy_changes=yoy_changes,
            yoy_changes_pct=yoy_changes_pct,
        )

        valid_mom_pct = mom_changes_pct.dropna()
        average_mom_pct = (
            float(valid_mom_pct.mean())
            if not valid_mom_pct.empty else 0.0
        )
        volatility = (
            float(data.std()) if len(data) > 1 else 0.0
        )

        return TrendAnalysisResult(
            monthly_trends=monthly_trends,
            overall_direction=self._determine_overall_direction(
                mom_changes_pct,
            ),
            average_mom_change_pct=average_mom_pct,
            volatility=volatility,
            highest_month=data.idxmax(),
            lowest_month=data.idxmin(),
        )

    @staticmethod
    def _compute_yoy(
        data: pd.Series,
    ) -> tuple[dict, dict]:
        """Compute year-over-year changes.

        Compares each period's value with the same period 12 months
        prior to calculate absolute and percentage YoY changes.

        Args:
            data: Monthly values indexed by pandas Period.

        Returns:
            Tuple of (yoy_changes, yoy_changes_pct) dicts mapping
            period to absolute change and percentage change.
        """
        yoy_changes: dict = {}
        yoy_changes_pct: dict = {}
        for period in data.index:
            try:
                yoy_period = period - 12
                if yoy_period not in data.index:
                    continue
                prev_value = data[yoy_period]
                yoy_change = data[period] - prev_value
                yoy_changes[period] = yoy_change
                if prev_value != 0:
                    yoy_changes_pct[period] = (
                        (yoy_change / abs(prev_value)) * 100
                    )
                else:
                    yoy_changes_pct[period] = None
            except (TypeError, ValueError):
                continue
        return yoy_changes, yoy_changes_pct

    def _build_monthly_trends(  # pylint: disable=too-many-arguments
        self,
        *,
        data: pd.Series,
        mom_changes: pd.Series,
        mom_changes_pct: pd.Series,
        moving_averages: dict[int, pd.Series],
        yoy_changes: dict,
        yoy_changes_pct: dict,
    ) -> list[MonthlyTrend]:
        """Build MonthlyTrend objects for each period.

        Assembles all computed metrics (MoM, YoY, moving averages,
        direction) into a MonthlyTrend for each period in the data.

        Args:
            data: Original monthly values.
            mom_changes: Month-over-month absolute changes.
            mom_changes_pct: Month-over-month percentage changes.
            moving_averages: Dict mapping window size to rolling
                mean Series (keys: 3, 6, 12).
            yoy_changes: Year-over-year absolute changes by period.
            yoy_changes_pct: Year-over-year percentage changes.

        Returns:
            List of MonthlyTrend objects ordered by period.
        """
        trends: list[MonthlyTrend] = []

        for period in data.index:
            mom_change = mom_changes.get(period, 0.0)
            mom_pct = mom_changes_pct.get(period, 0.0)
            if pd.isna(mom_change):
                mom_change = 0.0
            if pd.isna(mom_pct):
                mom_pct = 0.0

            trends.append(MonthlyTrend(
                period=period,
                value=float(data[period]),
                mom_change=float(mom_change),
                mom_change_pct=float(mom_pct),
                yoy_change=yoy_changes.get(period),
                yoy_change_pct=yoy_changes_pct.get(period),
                moving_avg_3m=self._safe_float(
                    moving_averages[3], period,
                ),
                moving_avg_6m=self._safe_float(
                    moving_averages[6], period,
                ),
                moving_avg_12m=self._safe_float(
                    moving_averages[12], period,
                ),
                direction=TrendDirection.from_change(
                    mom_pct, self._stable_threshold,
                ),
            ))

        return trends

    @staticmethod
    def _safe_float(
        series: pd.Series,
        period: pd.Period,
    ) -> float | None:
        """Extract float from Series, returning None for NaN."""
        val = series[period]
        return float(val) if not pd.isna(val) else None

    def analyze_dataframe(
        self,
        *,
        df: pd.DataFrame,
        value_column: str = "amount",
        period_column: str = "year_month",
        aggregate_func: str = "sum",
    ) -> TrendAnalysisResult:
        """Analyze trends from a transaction DataFrame.

        Args:
            df: Transaction DataFrame.
            value_column: Column containing values to analyze.
            period_column: Column containing period information.
            aggregate_func: Aggregation function (sum, mean, count).

        Returns:
            TrendAnalysisResult with all computed metrics.

        Example:
            >>> import pandas as pd
            >>> service = TrendAnalysisService()
            >>> df = pd.DataFrame({
            ...     "amount": [100.0, 200.0, 150.0],
            ...     "transaction_date": [
            ...         "2024-01-15", "2024-02-15", "2024-03-15",
            ...     ],
            ... })
            >>> result = service.analyze_dataframe(df=df)
            >>> result.overall_direction
            <TrendDirection.UNKNOWN: 'unknown'>
        """
        if df.empty or value_column not in df.columns:
            return TrendAnalysisResult()

        if (period_column not in df.columns
                and "transaction_date" in df.columns):
            df = df.copy()
            df[period_column] = pd.to_datetime(
                df["transaction_date"],
            ).dt.to_period("M")

        if period_column not in df.columns:
            return TrendAnalysisResult()

        agg_map = {
            "sum": "sum", "mean": "mean", "count": "count",
        }
        func = agg_map.get(aggregate_func, "sum")
        monthly_data = (
            df.groupby(period_column)[value_column].agg(func)
        )

        return self.analyze(data=monthly_data)

    def compare_periods(
        self,
        *,
        current_period: pd.Period,
        data: pd.Series,
        comparison_type: str = "mom",
    ) -> dict:
        """Compare a period with a previous period.

        Args:
            current_period: The period to compare.
            data: Monthly data series.
            comparison_type: 'mom' or 'yoy'.

        Returns:
            Dictionary with comparison metrics.

        Example:
            >>> import pandas as pd
            >>> service = TrendAnalysisService()
            >>> data = pd.Series(
            ...     [100.0, 120.0],
            ...     index=[
            ...         pd.Period("2024-01", "M"),
            ...         pd.Period("2024-02", "M"),
            ...     ],
            ... )
            >>> result = service.compare_periods(
            ...     current_period=pd.Period("2024-02", "M"),
            ...     data=data,
            ... )
            >>> result["absolute_change"]
            20.0
        """
        if current_period not in data.index:
            return {"error": "Period not found"}

        current_value = data[current_period]

        if comparison_type == "yoy":
            prev_period = current_period - 12
        else:
            prev_period = current_period - 1

        if prev_period not in data.index:
            return {
                "current_value": float(current_value),
                "previous_value": None,
                "absolute_change": None,
                "percent_change": None,
                "direction": TrendDirection.UNKNOWN.value,
            }

        prev_value = data[prev_period]
        absolute_change = current_value - prev_value
        percent_change = (
            (current_value - prev_value) / abs(prev_value) * 100
            if prev_value != 0
            else None
        )

        direction = TrendDirection.from_change(
            percent_change if percent_change is not None else 0,
            self._stable_threshold,
        )

        return {
            "current_value": float(current_value),
            "previous_value": float(prev_value),
            "absolute_change": float(absolute_change),
            "percent_change": (
                float(percent_change)
                if percent_change is not None else None
            ),
            "direction": direction.value,
        }

    def _determine_overall_direction(
        self,
        mom_changes_pct: pd.Series,
    ) -> TrendDirection:
        """Determine overall trend direction from MoM changes.

        Uses the average of the last 3 month-over-month percentage
        changes to classify the overall direction.

        Args:
            mom_changes_pct: Series of month-over-month percentage
                changes.

        Returns:
            TrendDirection based on the recent average change.
        """
        if mom_changes_pct.empty:
            return TrendDirection.UNKNOWN

        recent = mom_changes_pct.tail(3).dropna()
        if recent.empty:
            return TrendDirection.UNKNOWN

        avg_change = recent.mean()
        return TrendDirection.from_change(
            avg_change, self._stable_threshold,
        )


def analyze_spending_trends(
    *,
    transactions: pd.DataFrame,
    category: str | None = None,
) -> TrendAnalysisResult:
    """Convenience function to analyze spending trends.

    Args:
        transactions: Transaction DataFrame.
        category: Optional category to filter by.

    Returns:
        TrendAnalysisResult for the (filtered) transactions.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "amount": [-100, -200, -150],
        ...     "transaction_date": [
        ...         "2024-01-15", "2024-02-15", "2024-03-15",
        ...     ],
        ... })
        >>> result = analyze_spending_trends(transactions=df)
        >>> isinstance(result, TrendAnalysisResult)
        True
    """
    df = transactions.copy()

    if category and "category" in df.columns:
        df = df[df["category"] == category]

    if "amount" in df.columns:
        df = df[df["amount"] < 0].copy()
        df["amount"] = df["amount"].abs()

    service = TrendAnalysisService()
    return service.analyze_dataframe(df=df)


def analyze_income_trends(
    *,
    transactions: pd.DataFrame,
) -> TrendAnalysisResult:
    """Convenience function to analyze income trends.

    Args:
        transactions: Transaction DataFrame.

    Returns:
        TrendAnalysisResult for income transactions.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "amount": [3000, 3100, 3050],
        ...     "transaction_date": [
        ...         "2024-01-01", "2024-02-01", "2024-03-01",
        ...     ],
        ... })
        >>> result = analyze_income_trends(transactions=df)
        >>> isinstance(result, TrendAnalysisResult)
        True
    """
    df = transactions.copy()

    if "amount" in df.columns:
        df = df[df["amount"] > 0]

    service = TrendAnalysisService()
    return service.analyze_dataframe(df=df)
