"""Forecasting service (business logic).

Provides spending/income forecasts using simple methods:
- Historical average (mean of past N months)
- Weighted average (recent months weighted more)
- Trend-based extrapolation (linear regression)
- Ensemble (combination of all methods)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from budget_analyser.features.forecasting.models import (
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
)


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

        Example:
            >>> service = ForecastingService()
            >>> data = {
            ...     "2024-01": 1000.0,
            ...     "2024-02": 1100.0,
            ...     "2024-03": 1050.0,
            ... }
            >>> result = service.forecast(historical_data=data)
            >>> len(result.forecasts)
            3
        """
        periods = periods or self._default_periods

        if isinstance(historical_data, dict):
            historical_data = pd.Series(historical_data)

        if historical_data.empty:
            return ForecastResult(method=method)

        historical_data = historical_data.sort_index()

        method_map = {
            ForecastMethod.HISTORICAL_AVERAGE:
                self._forecast_historical_average,
            ForecastMethod.WEIGHTED_AVERAGE:
                self._forecast_weighted_average,
            ForecastMethod.TREND_EXTRAPOLATION:
                self._forecast_trend,
            ForecastMethod.ENSEMBLE:
                self._forecast_ensemble,
        }
        forecast_func = method_map.get(
            method, self._forecast_weighted_average,
        )
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
            expense_only: If True, only include expenses.

        Returns:
            ForecastResult with predictions.

        Example:
            >>> import pandas as pd
            >>> service = ForecastingService()
            >>> df = pd.DataFrame({
            ...     "amount": [-100, -200, -150],
            ...     "transaction_date": [
            ...         "2024-01-15", "2024-02-15", "2024-03-15",
            ...     ],
            ... })
            >>> result = service.forecast_from_transactions(
            ...     transactions=df,
            ... )
            >>> result.method
            <ForecastMethod.WEIGHTED_AVERAGE: 'weighted_average'>
        """
        if transactions.empty or "amount" not in transactions.columns:
            return ForecastResult(method=method)

        df = transactions.copy()

        if expense_only:
            df = df[df["amount"] < 0].copy()
            df["amount"] = df["amount"].abs()

        if "transaction_date" in df.columns:
            df["period"] = pd.to_datetime(
                df["transaction_date"],
            ).dt.strftime("%Y-%m")
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
            Dictionary mapping category to ForecastResult.

        Example:
            >>> import pandas as pd
            >>> service = ForecastingService()
            >>> df = pd.DataFrame({
            ...     "amount": [-100, -200, -50],
            ...     "category": ["Food", "Food", "Utilities"],
            ...     "transaction_date": [
            ...         "2024-01-15", "2024-02-15", "2024-03-15",
            ...     ],
            ... })
            >>> results = service.forecast_by_category(
            ...     transactions=df,
            ... )
            >>> "Food" in results
            True
        """
        if (transactions.empty
                or "category" not in transactions.columns):
            return {}

        results = {}
        for category in transactions["category"].unique():
            cat_df = transactions[
                transactions["category"] == category
            ]
            results[str(category)] = (
                self.forecast_from_transactions(
                    transactions=cat_df,
                    periods=periods,
                    method=method,
                )
            )

        return results

    def _forecast_historical_average(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using simple historical average.

        Computes the mean and standard deviation of historical data
        to produce flat forecasts with confidence bounds.

        Args:
            data: Historical values as a sorted pandas Series.
            periods: Number of future periods to forecast.

        Returns:
            ForecastResult using HISTORICAL_AVERAGE method with
            constant forecast values equal to the historical mean.
        """
        mean = float(data.mean())
        std = (
            float(data.std()) if len(data) > 1
            else mean * 0.1
        )

        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0
        margin = z_score * std

        last_period = str(data.index[-1])
        future_periods = self._generate_future_periods(
            last_period, periods,
        )

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
        """Forecast using weighted average (recent values weighted more).

        Assigns linearly increasing weights so that more recent
        observations have greater influence on the forecast.

        Args:
            data: Historical values as a sorted pandas Series.
            periods: Number of future periods to forecast.

        Returns:
            ForecastResult using WEIGHTED_AVERAGE method with
            constant forecast values equal to the weighted mean.
        """
        n = len(data)
        if n == 0:
            return ForecastResult(method=ForecastMethod.WEIGHTED_AVERAGE)

        weights = np.arange(1, n + 1, dtype=float)
        weights /= weights.sum()

        weighted_avg = float(np.average(data.values, weights=weights))
        weighted_var = float(
            np.average((data.values - weighted_avg) ** 2, weights=weights),
        )
        weighted_std = (
            float(np.sqrt(weighted_var)) if weighted_var > 0
            else weighted_avg * 0.1
        )

        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0
        margin = z_score * weighted_std
        future_periods = self._generate_future_periods(
            str(data.index[-1]), periods,
        )

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

        return ForecastResult(
            method=ForecastMethod.WEIGHTED_AVERAGE,
            forecasts=forecasts,
            historical_data=data.to_dict(),
            metrics={
                "weighted_mean": weighted_avg,
                "weighted_std": weighted_std,
                "data_points": n,
            },
        )

    def _forecast_trend(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using linear trend extrapolation.

        Fits a linear regression to historical data and projects
        the trend forward. Confidence bounds widen for further
        periods, and confidence decreases by 5% per period.

        Args:
            data: Historical values as a sorted pandas Series.
            periods: Number of future periods to forecast.

        Returns:
            ForecastResult using TREND_EXTRAPOLATION method.
            Falls back to weighted average if fewer than 2 data
            points are available.
        """
        n = len(data)
        if n < 2:
            return self._forecast_weighted_average(data, periods)

        slope, intercept, residual_std = self._linear_regression(data)
        z_score = 1.28 if self._confidence_interval >= 0.8 else 1.0

        future_periods = self._generate_future_periods(
            str(data.index[-1]), periods,
        )
        forecasts = []
        for i, p in enumerate(future_periods):
            forecast_value = float(slope * (n + i) + intercept)
            margin = z_score * residual_std * (1 + 0.1 * i)
            forecasts.append(ForecastPoint(
                period=p,
                value=max(0, forecast_value),
                lower_bound=max(0, forecast_value - margin),
                upper_bound=forecast_value + margin,
                confidence=self._confidence_interval * (1 - 0.05 * i),
            ))

        return ForecastResult(
            method=ForecastMethod.TREND_EXTRAPOLATION,
            forecasts=forecasts,
            historical_data=data.to_dict(),
            metrics={
                "slope": float(slope),
                "intercept": float(intercept),
                "residual_std": residual_std,
                "data_points": n,
                "trend_direction": self._trend_direction(slope),
            },
        )

    @staticmethod
    def _trend_direction(slope: float) -> str:
        """Return a human-readable trend direction string."""
        if slope > 0:
            return "increasing"
        if slope < 0:
            return "decreasing"
        return "flat"

    @staticmethod
    def _linear_regression(
        data: pd.Series,
    ) -> tuple[float, float, float]:
        """Perform simple linear regression.

        Fits y = slope * x + intercept using ordinary least squares
        where x is the integer index of each data point.

        Args:
            data: Historical values as a pandas Series.

        Returns:
            Tuple of (slope, intercept, residual_std).
        """
        n = len(data)
        x = np.arange(n)
        y = data.values.astype(float)

        x_mean = x.mean()
        y_mean = y.mean()
        slope = float(
            np.sum((x - x_mean) * (y - y_mean))
            / np.sum((x - x_mean) ** 2),
        )
        intercept = float(y_mean - slope * x_mean)

        residuals = y - (slope * x + intercept)
        residual_std = (
            float(np.std(residuals)) if n > 2
            else float(y_mean * 0.1)
        )

        return slope, intercept, residual_std

    def _forecast_ensemble(
        self,
        data: pd.Series,
        periods: int,
    ) -> ForecastResult:
        """Forecast using ensemble of all methods.

        Runs historical average, weighted average, and trend
        extrapolation, then combines results by averaging each
        forecast point across all three methods.

        Args:
            data: Historical values as a sorted pandas Series.
            periods: Number of future periods to forecast.

        Returns:
            ForecastResult using ENSEMBLE method with averaged
            forecast values and per-method metrics.
        """
        results = [
            self._forecast_historical_average(data, periods),
            self._forecast_weighted_average(data, periods),
            self._forecast_trend(data, periods),
        ]

        combined = self._combine_forecasts(results, periods)

        metrics = {
            "avg_method_value": self._first_value(results[0]),
            "weighted_method_value": self._first_value(results[1]),
            "trend_method_value": self._first_value(results[2]),
            "data_points": len(data),
        }

        return ForecastResult(
            method=ForecastMethod.ENSEMBLE,
            forecasts=combined,
            historical_data=data.to_dict(),
            metrics=metrics,
        )

    def _combine_forecasts(
        self,
        results: list[ForecastResult],
        periods: int,
    ) -> list[ForecastPoint]:
        """Average forecast points across multiple methods.

        For each future period, averages the value, lower_bound,
        and upper_bound from all method results. Confidence is
        slightly reduced (95% of configured interval) to reflect
        ensemble uncertainty.

        Args:
            results: List of ForecastResult from individual methods.
            periods: Number of future periods to combine.

        Returns:
            List of averaged ForecastPoint objects.
        """
        combined: list[ForecastPoint] = []

        for i in range(periods):
            points = [
                r.forecasts[i] if i < len(r.forecasts) else None
                for r in results
            ]
            values = [p.value if p else 0.0 for p in points]
            lowers = [
                p.lower_bound if p else 0.0 for p in points
            ]
            uppers = [
                p.upper_bound if p else 0.0 for p in points
            ]
            n = len(values)

            period = ""
            for p in points:
                if p is not None:
                    period = p.period
                    break

            combined.append(ForecastPoint(
                period=period,
                value=sum(values) / n,
                lower_bound=sum(lowers) / n,
                upper_bound=sum(uppers) / n,
                confidence=self._confidence_interval * 0.95,
            ))

        return combined

    @staticmethod
    def _first_value(result: ForecastResult) -> float:
        """Return the first forecast value or 0."""
        return (
            result.forecasts[0].value if result.forecasts
            else 0.0
        )

    def _generate_future_periods(
        self,
        last_period: str,
        count: int,
    ) -> list[str]:
        """Generate future period strings from the last known period.

        Parses the last period as "YYYY-MM" and increments monthly.
        Falls back to "period_1", "period_2", etc. if parsing fails.

        Args:
            last_period: Last known period in "YYYY-MM" format.
            count: Number of future periods to generate.

        Returns:
            List of period strings in "YYYY-MM" format.
        """
        try:
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

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({
        ...     "amount": [-500, -600, -550],
        ...     "transaction_date": [
        ...         "2024-01-15", "2024-02-15", "2024-03-15",
        ...     ],
        ... })
        >>> result = forecast_spending(transactions=df)
        >>> len(result.forecasts)
        3
    """
    service = ForecastingService()
    return service.forecast_from_transactions(
        transactions=transactions,
        periods=periods,
        method=ForecastMethod.WEIGHTED_AVERAGE,
    )
