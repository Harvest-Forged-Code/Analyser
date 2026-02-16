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
