"""Simple forecasting service (domain logic).

Purpose:
    Provide spending/income forecasts using simple methods:
    - Historical average (mean of past N months)
    - Weighted average (recent months weighted more)
    - Trend-based extrapolation (linear regression)

These forecasts help users plan budgets and anticipate future expenses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np


class ForecastMethod(Enum):
    """Available forecasting methods."""

    HISTORICAL_AVERAGE = "historical_average"
    WEIGHTED_AVERAGE = "weighted_average"
    TREND_EXTRAPOLATION = "trend_extrapolation"
    ENSEMBLE = "ensemble"


@dataclass(frozen=True)
class ForecastPoint:
    """A single forecast point.

    Attributes:
        period: The forecasted period (e.g., "2024-06").
        value: The forecasted value.
        lower_bound: Lower confidence bound.
        upper_bound: Upper confidence bound.
        confidence: Confidence level (0.0-1.0).
    """

    period: str
    value: float
    lower_bound: float
    upper_bound: float
    confidence: float


@dataclass
class ForecastResult:
    """Complete forecast result.

    Attributes:
        method: The forecasting method used.
        forecasts: List of forecast points.
        historical_data: The historical data used for forecasting.
        metrics: Model performance metrics.
    """

    method: ForecastMethod
    forecasts: list[ForecastPoint] = field(default_factory=list)
    historical_data: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def next_period_forecast(self) -> ForecastPoint | None:
        """Get the forecast for the next period."""
        return self.forecasts[0] if self.forecasts else None

    def total_forecasted(self) -> float:
        """Sum of all forecasted values."""
        return sum(f.value for f in self.forecasts)


class ForecastingService:
    """Service for generating financial forecasts."""

    def __init__(
        self,
        *,
        default_periods: int = 3,
        confidence_interval: float = 0.8,
    ) -> None:
        """Initialize the forecasting service.

        Args:
            default_periods: Default number of periods to forecast.
            confidence_interval: Confidence level for bounds (0.0-1.0).
        """
        self._default_periods = default_periods
        self._confidence_interval = confidence_interval

    def forecast(
        self,
        *,
        historical_data: pd.Series | dict[str, float],
        periods: int | None = None,
        method: ForecastMethod = ForecastMethod.WEIGHTED_AVERAGE,
    ) -> ForecastResult:
        """Generate forecasts using the specified method.

        Args:
            historical_data: Historical values indexed by period.
            periods: Number of periods to forecast.
            method: Forecasting method to use.

        Returns:
            ForecastResult with predictions and metrics.
        """
        periods = periods or self._default_periods

        # Convert dict to Series if needed
        if isinstance(historical_data, dict):
            historical_data = pd.Series(historical_data)

        if historical_data.empty:
            return ForecastResult(method=method)

        # Sort by index
        historical_data = historical_data.sort_index()

        # Choose forecasting method
        method_map = {
            ForecastMethod.HISTORICAL_AVERAGE: self._forecast_historical_average,
            ForecastMethod.WEIGHTED_AVERAGE: self._forecast_weighted_average,
            ForecastMethod.TREND_EXTRAPOLATION: self._forecast_trend,
            ForecastMethod.ENSEMBLE: self._forecast_ensemble,
        }
        forecast_func = method_map.get(method, self._forecast_weighted_average)
        return forecast_func(historical_data, periods)

    def forecast_from_transactions(
        self,
        *,
        transactions: pd.DataFrame,
        periods: int | None = None,
        method: ForecastMethod = ForecastMethod.WEIGHTED_AVERAGE,
        expense_only: bool = True,
    ) -> ForecastResult:
        """Generate forecasts from transaction data.

        Args:
            transactions: DataFrame with transaction data.
            periods: Number of periods to forecast.
            method: Forecasting method to use.
            expense_only: If True, only include expenses (negative amounts).

        Returns:
            ForecastResult with predictions.
        """
        if transactions.empty or "amount" not in transactions.columns:
            return ForecastResult(method=method)

        df = transactions.copy()

        # Filter to expenses if needed
        if expense_only:
            df = df[df["amount"] < 0].copy()
            df["amount"] = df["amount"].abs()

        # Aggregate by month
        if "transaction_date" in df.columns:
            df["period"] = pd.to_datetime(df["transaction_date"]).dt.strftime("%Y-%m")
        elif "year_month" in df.columns:
            df["period"] = df["year_month"].astype(str)
        else:
            return ForecastResult(method=method)

        monthly = df.groupby("period")["amount"].sum()

        return self.forecast(
            historical_data=monthly,
            periods=periods,
            method=method,
        )

    def forecast_by_category(
        self,
        *,
        transactions: pd.DataFrame,
        periods: int | None = None,
        method: ForecastMethod = ForecastMethod.WEIGHTED_AVERAGE,
    ) -> dict[str, ForecastResult]:
        """Generate forecasts for each category.

        Args:
            transactions: DataFrame with transaction data.
            periods: Number of periods to forecast.
            method: Forecasting method to use.

        Returns:
            Dictionary mapping category -> ForecastResult.
        """
        if transactions.empty or "category" not in transactions.columns:
            return {}

        results = {}
        for category in transactions["category"].unique():
            cat_df = transactions[transactions["category"] == category]
            results[str(category)] = self.forecast_from_transactions(
                transactions=cat_df,
                periods=periods,
                method=method,
            )

        return results

    def _forecast_historical_average(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using simple historical average."""
        mean = float(data.mean())
        std = float(data.std()) if len(data) > 1 else mean * 0.1

        # Calculate confidence bounds
        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0
        margin = z_score * std

        # Generate future periods
        last_period = str(data.index[-1])
        future_periods = self._generate_future_periods(last_period, periods)

        forecasts = [
            ForecastPoint(
                period=p,
                value=mean,
                lower_bound=max(0, mean - margin),
                upper_bound=mean + margin,
                confidence=self._confidence_interval,
            )
            for p in future_periods
        ]

        # Calculate metrics
        metrics = {
            "mean": mean,
            "std": std,
            "data_points": len(data),
        }

        return ForecastResult(
            method=ForecastMethod.HISTORICAL_AVERAGE,
            forecasts=forecasts,
            historical_data=data.to_dict(),
            metrics=metrics,
        )

    def _forecast_weighted_average(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using weighted average (recent values weighted more)."""
        n = len(data)
        if n == 0:
            return ForecastResult(method=ForecastMethod.WEIGHTED_AVERAGE)

        # Create weights that emphasize recent data
        # Weights: 1, 2, 3, ..., n (linear increasing)
        weights = np.arange(1, n + 1, dtype=float)
        weights = weights / weights.sum()

        weighted_avg = float(np.average(data.values, weights=weights))

        # Calculate weighted std for confidence bounds
        weighted_var = float(np.average((data.values - weighted_avg) ** 2, weights=weights))
        weighted_std = np.sqrt(weighted_var) if weighted_var > 0 else weighted_avg * 0.1

        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0
        margin = z_score * weighted_std

        # Generate future periods
        last_period = str(data.index[-1])
        future_periods = self._generate_future_periods(last_period, periods)

        forecasts = [
            ForecastPoint(
                period=p,
                value=weighted_avg,
                lower_bound=max(0, weighted_avg - margin),
                upper_bound=weighted_avg + margin,
                confidence=self._confidence_interval,
            )
            for p in future_periods
        ]

        metrics = {
            "weighted_mean": weighted_avg,
            "weighted_std": weighted_std,
            "data_points": n,
        }

        return ForecastResult(
            method=ForecastMethod.WEIGHTED_AVERAGE,
            forecasts=forecasts,
            historical_data=data.to_dict(),
            metrics=metrics,
        )

    def _forecast_trend(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using linear trend extrapolation."""
        n = len(data)
        if n < 2:
            # Fall back to weighted average if not enough data
            return self._forecast_weighted_average(data, periods)

        # Simple linear regression
        x = np.arange(n)
        y = data.values.astype(float)

        # Calculate slope and intercept
        x_mean = x.mean()
        y_mean = y.mean()
        slope = np.sum((x - x_mean) * (y - y_mean)) / np.sum((x - x_mean) ** 2)
        intercept = y_mean - slope * x_mean

        # Calculate residual std for confidence bounds
        predictions = slope * x + intercept
        residuals = y - predictions
        residual_std = float(np.std(residuals)) if n > 2 else y_mean * 0.1

        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0

        # Generate future periods and values
        last_period = str(data.index[-1])
        future_periods = self._generate_future_periods(last_period, periods)

        forecasts = []
        for i, p in enumerate(future_periods):
            future_x = n + i
            forecast_value = float(slope * future_x + intercept)
            # Uncertainty grows with distance
            margin = z_score * residual_std * (1 + 0.1 * i)

            forecasts.append(ForecastPoint(
                period=p,
                value=max(0, forecast_value),
                lower_bound=max(0, forecast_value - margin),
                upper_bound=forecast_value + margin,
                confidence=self._confidence_interval * (1 - 0.05 * i),  # Decreasing confidence
            ))

        metrics = {
            "slope": float(slope),
            "intercept": float(intercept),
            "residual_std": residual_std,
            "data_points": n,
            "trend_direction": "increasing" if slope > 0 else "decreasing" if slope < 0 else "flat",
        }

        return ForecastResult(
            method=ForecastMethod.TREND_EXTRAPOLATION,
            forecasts=forecasts,
            historical_data=data.to_dict(),
            metrics=metrics,
        )

    def _forecast_ensemble(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using ensemble of all methods."""
        # Get forecasts from all methods
        avg_result = self._forecast_historical_average(data, periods)
        weighted_result = self._forecast_weighted_average(data, periods)
        trend_result = self._forecast_trend(data, periods)

        # Combine forecasts (simple average of the three methods)
        combined_forecasts = []
        for i in range(periods):
            values = [
                avg_result.forecasts[i].value if i < len(avg_result.forecasts) else 0,
                weighted_result.forecasts[i].value if i < len(weighted_result.forecasts) else 0,
                trend_result.forecasts[i].value if i < len(trend_result.forecasts) else 0,
            ]
            ensemble_value = sum(values) / len(values)

            bounds = [
                (avg_result.forecasts[i].lower_bound, avg_result.forecasts[i].upper_bound)
                if i < len(avg_result.forecasts) else (0, 0),
                (weighted_result.forecasts[i].lower_bound, weighted_result.forecasts[i].upper_bound)
                if i < len(weighted_result.forecasts) else (0, 0),
                (trend_result.forecasts[i].lower_bound, trend_result.forecasts[i].upper_bound)
                if i < len(trend_result.forecasts) else (0, 0),
            ]
            avg_lower = sum(b[0] for b in bounds) / len(bounds)
            avg_upper = sum(b[1] for b in bounds) / len(bounds)

            period = avg_result.forecasts[i].period if i < len(avg_result.forecasts) else ""

            combined_forecasts.append(ForecastPoint(
                period=period,
                value=ensemble_value,
                lower_bound=avg_lower,
                upper_bound=avg_upper,
                confidence=self._confidence_interval * 0.95,
            ))

        avg_first = avg_result.forecasts[0].value if avg_result.forecasts else 0
        weighted_first = weighted_result.forecasts[0].value if weighted_result.forecasts else 0
        trend_first = trend_result.forecasts[0].value if trend_result.forecasts else 0

        metrics = {
            "avg_method_value": avg_first,
            "weighted_method_value": weighted_first,
            "trend_method_value": trend_first,
            "data_points": len(data),
        }

        return ForecastResult(
            method=ForecastMethod.ENSEMBLE,
            forecasts=combined_forecasts,
            historical_data=data.to_dict(),
            metrics=metrics,
        )

    def _generate_future_periods(self, last_period: str, count: int) -> list[str]:
        """Generate future period strings from the last known period."""
        try:
            # Parse YYYY-MM format
            year, month = map(int, last_period.split("-"))
            periods = []
            for _ in range(count):
                month += 1
                if month > 12:
                    month = 1
                    year += 1
                periods.append(f"{year:04d}-{month:02d}")
            return periods
        except (ValueError, AttributeError):
            # Fallback to generic labels
            return [f"period_{i+1}" for i in range(count)]


def forecast_spending(
    *,
    transactions: pd.DataFrame,
    periods: int = 3,
) -> ForecastResult:
    """Convenience function for spending forecasts.

    Args:
        transactions: DataFrame with transaction data.
        periods: Number of months to forecast.

    Returns:
        ForecastResult using weighted average method.
    """
    service = ForecastingService()
    return service.forecast_from_transactions(
        transactions=transactions,
        periods=periods,
        method=ForecastMethod.WEIGHTED_AVERAGE,
    )
