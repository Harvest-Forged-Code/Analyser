"""Forecasting feature module.

Provides spending/income forecasts using simple methods:
historical average, weighted average, trend extrapolation, and ensemble.
"""

from budget_analyser.features.forecasting.models import (
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
)
from budget_analyser.features.forecasting.service import (
    ForecastingService,
    forecast_spending,
)

__all__ = [
    "ForecastMethod",
    "ForecastPoint",
    "ForecastResult",
    "ForecastingService",
    "forecast_spending",
]
