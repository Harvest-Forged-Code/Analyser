"""Forecasting feature DTOs.

Data transfer objects for financial forecasting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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

    Example:
        >>> point = ForecastPoint(
        ...     period="2024-06",
        ...     value=1200.0,
        ...     lower_bound=900.0,
        ...     upper_bound=1500.0,
        ...     confidence=0.8,
        ... )
        >>> point.value
        1200.0
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

    Example:
        >>> point = ForecastPoint(
        ...     period="2024-06",
        ...     value=1200.0,
        ...     lower_bound=900.0,
        ...     upper_bound=1500.0,
        ...     confidence=0.8,
        ... )
        >>> result = ForecastResult(
        ...     method=ForecastMethod.WEIGHTED_AVERAGE,
        ...     forecasts=[point],
        ...     historical_data={"2024-05": 1100.0},
        ... )
        >>> result.next_period_forecast.value
        1200.0
    """

    method: ForecastMethod
    forecasts: list[ForecastPoint] = field(default_factory=list)
    historical_data: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def next_period_forecast(self) -> ForecastPoint | None:
        """Get the forecast for the next period.

        Returns:
            The first ForecastPoint in the forecast list,
            or None if no forecasts exist.
        """
        return self.forecasts[0] if self.forecasts else None

    def total_forecasted(self) -> float:
        """Sum of all forecasted values.

        Returns:
            Total of all forecast point values.
        """
        return sum(f.value for f in self.forecasts)
