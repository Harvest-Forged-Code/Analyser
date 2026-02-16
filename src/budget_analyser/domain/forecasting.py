"""Simple forecasting service (domain logic).

Backward-compatibility shim: re-exports from features.forecasting.
New code should import from budget_analyser.features.forecasting directly.
"""

from budget_analyser.features.forecasting import (  # pylint: disable=unused-import  # noqa: F401
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
    ForecastingService,
    forecast_spending,
)
