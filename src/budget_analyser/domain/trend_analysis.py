"""Time-series trend analysis (domain logic).

Purpose:
    Provide trend analysis metrics for financial data:
    - Month-over-month change (absolute and percentage)
    - Moving averages (3-month, 6-month, 12-month)
    - Year-over-year comparison
    - Trend direction indicators

These metrics help users understand spending patterns over time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

import pandas as pd


class TrendDirection(Enum):
    """Trend direction indicator."""

    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    UNKNOWN = "unknown"

    @classmethod
    def from_change(cls, change_pct: float, threshold: float = 5.0) -> TrendDirection:
        """Determine trend direction from percentage change.

        Args:
            change_pct: Percentage change value.
            threshold: Minimum change to consider non-stable.

        Returns:
            TrendDirection based on the change.
        """
        if pd.isna(change_pct):
            return cls.UNKNOWN
        if change_pct > threshold:
            return cls.RISING
        if change_pct < -threshold:
            return cls.FALLING
        return cls.STABLE


@dataclass(frozen=True)
class MonthlyTrend:
    """Trend data for a single month.

    Attributes:
        period: The month (as pandas Period).
        value: The actual value for the month.
        mom_change: Month-over-month absolute change.
        mom_change_pct: Month-over-month percentage change.
        yoy_change: Year-over-year absolute change.
        yoy_change_pct: Year-over-year percentage change.
        moving_avg_3m: 3-month moving average.
        moving_avg_6m: 6-month moving average.
        moving_avg_12m: 12-month moving average.
        direction: Trend direction based on recent movement.
    """

    period: pd.Period
    value: float
    mom_change: float = 0.0
    mom_change_pct: float = 0.0
    yoy_change: float | None = None
    yoy_change_pct: float | None = None
    moving_avg_3m: float | None = None
    moving_avg_6m: float | None = None
    moving_avg_12m: float | None = None
    direction: TrendDirection = TrendDirection.UNKNOWN


@dataclass
class TrendAnalysisResult:
    """Complete trend analysis result.

    Attributes:
        monthly_trends: List of MonthlyTrend objects for each period.
        overall_direction: Overall trend direction.
        average_mom_change_pct: Average month-over-month change.
        volatility: Standard deviation of monthly values.
        highest_month: Period with highest value.
        lowest_month: Period with lowest value.
    """

    monthly_trends: list[MonthlyTrend] = field(default_factory=list)
    overall_direction: TrendDirection = TrendDirection.UNKNOWN
    average_mom_change_pct: float = 0.0
    volatility: float = 0.0
    highest_month: pd.Period | None = None
    lowest_month: pd.Period | None = None

    def get_trend(self, period: pd.Period) -> MonthlyTrend | None:
        """Get trend data for a specific period."""
        for trend in self.monthly_trends:
            if trend.period == period:
                return trend
        return None

    def recent_trends(self, n: int = 3) -> list[MonthlyTrend]:
        """Get the most recent N trends."""
        return self.monthly_trends[-n:] if self.monthly_trends else []


class TrendAnalysisService:
    """Service for analyzing time-series trends in financial data.

    Calculates various trend metrics from monthly aggregated data.
    """

    def __init__(
        self,
        *,
        stable_threshold_pct: float = 5.0,
    ) -> None:
        """Initialize the trend analysis service.

        Args:
            stable_threshold_pct: Percentage threshold for stable vs rising/falling.
        """
        self._stable_threshold = stable_threshold_pct

    def analyze(
        self,
        *,
        data: pd.Series | dict[pd.Period, float],
    ) -> TrendAnalysisResult:
        """Analyze trends in monthly data.

        Args:
            data: Monthly data as pandas Series (index=Period) or dict.

        Returns:
            TrendAnalysisResult with all computed metrics.
        """
        # Convert dict to Series if needed
        if isinstance(data, dict):
            data = pd.Series(data)

        if data.empty:
            return TrendAnalysisResult()

        # Ensure sorted by period
        data = data.sort_index()

        # Calculate all metrics
        mom_changes = data.diff()
        mom_changes_pct = data.pct_change() * 100

        # Moving averages
        ma_3m = data.rolling(window=3, min_periods=1).mean()
        ma_6m = data.rolling(window=6, min_periods=1).mean()
        ma_12m = data.rolling(window=12, min_periods=1).mean()

        # Year-over-year (shift by 12 periods)
        yoy_changes = {}
        yoy_changes_pct = {}
        for period in data.index:
            try:
                yoy_period = period - 12
                if yoy_period in data.index:
                    prev_value = data[yoy_period]
                    curr_value = data[period]
                    yoy_changes[period] = curr_value - prev_value
                    if prev_value != 0:
                        yoy_changes_pct[period] = ((curr_value - prev_value) / abs(prev_value)) * 100
                    else:
                        yoy_changes_pct[period] = None
            except Exception:
                pass

        # Build monthly trends
        monthly_trends = []
        for period in data.index:
            mom_change = mom_changes.get(period, 0.0)
            mom_pct = mom_changes_pct.get(period, 0.0)

            if pd.isna(mom_change):
                mom_change = 0.0
            if pd.isna(mom_pct):
                mom_pct = 0.0

            direction = TrendDirection.from_change(mom_pct, self._stable_threshold)

            trend = MonthlyTrend(
                period=period,
                value=float(data[period]),
                mom_change=float(mom_change),
                mom_change_pct=float(mom_pct),
                yoy_change=yoy_changes.get(period),
                yoy_change_pct=yoy_changes_pct.get(period),
                moving_avg_3m=float(ma_3m[period]) if not pd.isna(ma_3m[period]) else None,
                moving_avg_6m=float(ma_6m[period]) if not pd.isna(ma_6m[period]) else None,
                moving_avg_12m=float(ma_12m[period]) if not pd.isna(ma_12m[period]) else None,
                direction=direction,
            )
            monthly_trends.append(trend)

        # Calculate overall metrics
        valid_mom_pct = mom_changes_pct.dropna()
        average_mom_pct = float(valid_mom_pct.mean()) if not valid_mom_pct.empty else 0.0
        volatility = float(data.std()) if len(data) > 1 else 0.0

        # Determine overall direction from recent trend
        overall_direction = self._determine_overall_direction(mom_changes_pct)

        # Find highest and lowest months
        highest_month = data.idxmax() if not data.empty else None
        lowest_month = data.idxmin() if not data.empty else None

        return TrendAnalysisResult(
            monthly_trends=monthly_trends,
            overall_direction=overall_direction,
            average_mom_change_pct=average_mom_pct,
            volatility=volatility,
            highest_month=highest_month,
            lowest_month=lowest_month,
        )

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
        """
        if df.empty or value_column not in df.columns:
            return TrendAnalysisResult()

        # Create period column if needed
        if period_column not in df.columns and "transaction_date" in df.columns:
            df = df.copy()
            df[period_column] = pd.to_datetime(df["transaction_date"]).dt.to_period("M")

        if period_column not in df.columns:
            return TrendAnalysisResult()

        # Aggregate by period
        if aggregate_func == "sum":
            monthly_data = df.groupby(period_column)[value_column].sum()
        elif aggregate_func == "mean":
            monthly_data = df.groupby(period_column)[value_column].mean()
        elif aggregate_func == "count":
            monthly_data = df.groupby(period_column)[value_column].count()
        else:
            monthly_data = df.groupby(period_column)[value_column].sum()

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
            comparison_type: 'mom' (month-over-month) or 'yoy' (year-over-year).

        Returns:
            Dictionary with comparison metrics.
        """
        if current_period not in data.index:
            return {"error": "Period not found"}

        current_value = data[current_period]

        if comparison_type == "yoy":
            prev_period = current_period - 12
        else:  # mom
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
        percent_change = ((current_value - prev_value) / abs(prev_value) * 100
                          if prev_value != 0 else None)

        direction = TrendDirection.from_change(
            percent_change if percent_change is not None else 0,
            self._stable_threshold,
        )

        return {
            "current_value": float(current_value),
            "previous_value": float(prev_value),
            "absolute_change": float(absolute_change),
            "percent_change": float(percent_change) if percent_change is not None else None,
            "direction": direction.value,
        }

    def _determine_overall_direction(
        self,
        mom_changes_pct: pd.Series,
    ) -> TrendDirection:
        """Determine overall trend direction from MoM changes."""
        if mom_changes_pct.empty:
            return TrendDirection.UNKNOWN

        # Use last 3 months to determine direction
        recent = mom_changes_pct.tail(3).dropna()
        if recent.empty:
            return TrendDirection.UNKNOWN

        avg_change = recent.mean()
        return TrendDirection.from_change(avg_change, self._stable_threshold)


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
    """
    df = transactions.copy()

    if category and "category" in df.columns:
        df = df[df["category"] == category]

    # Filter to expenses (negative amounts)
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
    """
    df = transactions.copy()

    # Filter to income (positive amounts)
    if "amount" in df.columns:
        df = df[df["amount"] > 0]

    service = TrendAnalysisService()
    return service.analyze_dataframe(df=df)
