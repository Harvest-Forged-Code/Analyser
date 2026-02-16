"""Unit tests for features.forecasting.service."""

from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.forecasting.models import (
    ForecastMethod,
    ForecastPoint,
    ForecastResult,
)
from budget_analyser.features.forecasting.service import (
    ForecastingService,
    forecast_spending,
)


class TestForecastModels:
    """Tests for forecast DTOs."""

    def test_forecast_result_empty(self) -> None:
        result = ForecastResult(method=ForecastMethod.ENSEMBLE)
        assert result.next_period_forecast is None
        assert result.total_forecasted() == 0.0

    def test_forecast_result_with_data(self) -> None:
        fp = ForecastPoint(
            period="2024-06", value=100.0,
            lower_bound=80.0, upper_bound=120.0,
            confidence=0.8,
        )
        result = ForecastResult(
            method=ForecastMethod.WEIGHTED_AVERAGE,
            forecasts=[fp],
        )
        assert result.next_period_forecast == fp
        assert result.total_forecasted() == pytest.approx(100.0)


class TestForecastingService:
    """Tests for ForecastingService."""

    def test_forecast_empty_series(self) -> None:
        svc = ForecastingService()
        result = svc.forecast(historical_data=pd.Series(dtype=float))
        assert result.forecasts == []

    def test_forecast_from_dict(self) -> None:
        svc = ForecastingService(default_periods=2)
        data = {"2024-01": 100.0, "2024-02": 120.0, "2024-03": 110.0}
        result = svc.forecast(
            historical_data=data,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )
        assert len(result.forecasts) == 2
        assert result.method == ForecastMethod.HISTORICAL_AVERAGE
        assert result.forecasts[0].period == "2024-04"
        assert result.forecasts[1].period == "2024-05"
        assert result.forecasts[0].value == pytest.approx(110.0)

    def test_forecast_weighted_average(self) -> None:
        svc = ForecastingService(default_periods=1)
        data = pd.Series(
            [100.0, 200.0, 300.0],
            index=["2024-01", "2024-02", "2024-03"],
        )
        result = svc.forecast(
            historical_data=data,
            method=ForecastMethod.WEIGHTED_AVERAGE,
        )
        assert len(result.forecasts) == 1
        # Weighted avg skews toward 300 (most recent)
        assert result.forecasts[0].value > 200.0

    def test_forecast_trend_extrapolation(self) -> None:
        svc = ForecastingService(default_periods=1)
        data = pd.Series(
            [100.0, 200.0, 300.0],
            index=["2024-01", "2024-02", "2024-03"],
        )
        result = svc.forecast(
            historical_data=data,
            method=ForecastMethod.TREND_EXTRAPOLATION,
        )
        assert len(result.forecasts) == 1
        # Linear trend should project ~400
        assert result.forecasts[0].value == pytest.approx(400.0, rel=0.1)

    def test_forecast_trend_single_point_fallback(self) -> None:
        svc = ForecastingService(default_periods=1)
        data = pd.Series([100.0], index=["2024-01"])
        result = svc.forecast(
            historical_data=data,
            method=ForecastMethod.TREND_EXTRAPOLATION,
        )
        # Single point falls back to weighted average
        assert len(result.forecasts) == 1
        assert result.method == ForecastMethod.WEIGHTED_AVERAGE

    def test_forecast_ensemble(self) -> None:
        svc = ForecastingService(default_periods=1)
        data = pd.Series(
            [100.0, 200.0, 300.0],
            index=["2024-01", "2024-02", "2024-03"],
        )
        result = svc.forecast(
            historical_data=data,
            method=ForecastMethod.ENSEMBLE,
        )
        assert len(result.forecasts) == 1
        assert result.method == ForecastMethod.ENSEMBLE
        # Ensemble averages 3 methods
        assert "avg_method_value" in result.metrics

    def test_forecast_from_transactions_empty(self) -> None:
        svc = ForecastingService()
        result = svc.forecast_from_transactions(
            transactions=pd.DataFrame(),
        )
        assert result.forecasts == []

    def test_forecast_from_transactions(self) -> None:
        svc = ForecastingService(default_periods=1)
        df = pd.DataFrame({
            "transaction_date": ["2024-01-15", "2024-02-15", "2024-03-15"],
            "amount": [-100.0, -200.0, -300.0],
        })
        result = svc.forecast_from_transactions(transactions=df)
        assert len(result.forecasts) == 1
        assert result.forecasts[0].value > 0

    def test_forecast_by_category_empty(self) -> None:
        svc = ForecastingService()
        result = svc.forecast_by_category(
            transactions=pd.DataFrame(),
        )
        assert result == {}

    def test_forecast_by_category(self) -> None:
        svc = ForecastingService(default_periods=1)
        df = pd.DataFrame({
            "transaction_date": [
                "2024-01-15", "2024-02-15", "2024-03-15",
                "2024-01-20", "2024-02-20", "2024-03-20",
            ],
            "amount": [-50, -60, -70, -30, -40, -50],
            "category": ["Food", "Food", "Food", "Gas", "Gas", "Gas"],
        })
        result = svc.forecast_by_category(transactions=df)
        assert "Food" in result
        assert "Gas" in result

    def test_future_period_generation(self) -> None:
        svc = ForecastingService()
        periods = svc._generate_future_periods("2024-11", 3)
        assert periods == ["2024-12", "2025-01", "2025-02"]


class TestForecastSpendingConvenience:
    """Tests for the convenience function."""

    def test_forecast_spending(self) -> None:
        df = pd.DataFrame({
            "transaction_date": ["2024-01-15", "2024-02-15"],
            "amount": [-100.0, -200.0],
        })
        result = forecast_spending(transactions=df, periods=1)
        assert result.method == ForecastMethod.WEIGHTED_AVERAGE
        assert len(result.forecasts) == 1
