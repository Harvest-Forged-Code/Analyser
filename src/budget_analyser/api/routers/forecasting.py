"""Forecasting router for Budget Analyser API.

Provides endpoints for expense forecasting and predictions.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends

from budget_analyser.api.dependencies import get_reports
from budget_analyser.api.serializers import (
    ForecastResultSchema,
    ForecastPointSchema,
)
from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.forecasting.service import forecast_spending

router = APIRouter(prefix="/api/forecasting", tags=["forecasting"])


def _all_transactions_df(reports: list[MonthlyReports]) -> pd.DataFrame:
    """Concatenate all transactions from reports.

    Args:
        reports: List of MonthlyReports to extract transactions from.

    Returns:
        Combined DataFrame of all transactions, or empty DataFrame.
    """
    frames = []
    for r in reports:
        if r.transactions is not None and not r.transactions.empty:
            frames.append(r.transactions)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@router.get("/expenses", response_model=ForecastResultSchema)
def forecast_expenses(
    *, reports: list[MonthlyReports] = Depends(get_reports),
) -> ForecastResultSchema:
    """Forecast total spending for upcoming months.

    Args:
        reports: Injected reports cache.

    Returns:
        ForecastResultSchema with predictions.
    """
    transactions_df = _all_transactions_df(reports)
    result = forecast_spending(transactions_df)

    return ForecastResultSchema(
        method=result.method.value,
        forecasts=[
            ForecastPointSchema(
                period=fp.period,
                value=fp.value,
                lower_bound=fp.lower_bound,
                upper_bound=fp.upper_bound,
                confidence=fp.confidence,
            )
            for fp in result.forecasts
        ],
        historical_data=result.historical_data,
        metrics=result.metrics,
    )


