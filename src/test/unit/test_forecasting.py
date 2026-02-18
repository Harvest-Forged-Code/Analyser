"""Tests for forecasting service."""

import pandas as pd
import pytest

from budget_analyser.features.forecasting import (
    ForecastingService,
    ForecastMethod,
    ForecastResult,
    ForecastPoint,
    forecast_spending,
)


class TestForecastPoint:
    """Tests for ForecastPoint dataclass."""

    def test_forecast_point_attributes(self):
        point = ForecastPoint(
            period="2024-06",
            value=1000.0,
            lower_bound=800.0,
            upper_bound=1200.0,
            confidence=0.8,
        )
        assert point.period == "2024-06"
        assert point.value == 1000.0


class TestForecastResult:
    """Tests for ForecastResult dataclass."""

    def test_next_period_forecast(self):
        result = ForecastResult(
            method=ForecastMethod.HISTORICAL_AVERAGE,
            forecasts=[
                ForecastPoint("2024-06", 1000.0, 800.0, 1200.0, 0.8),
                ForecastPoint("2024-07", 1050.0, 850.0, 1250.0, 0.8),
            ],
        )
        assert result.next_period_forecast.period == "2024-06"

    def test_next_period_forecast_empty(self):
        result = ForecastResult(method=ForecastMethod.HISTORICAL_AVERAGE)
        assert result.next_period_forecast is None

    def test_total_forecasted(self):
        result = ForecastResult(
            method=ForecastMethod.HISTORICAL_AVERAGE,
            forecasts=[
                ForecastPoint("2024-06", 1000.0, 800.0, 1200.0, 0.8),
                ForecastPoint("2024-07", 1000.0, 800.0, 1200.0, 0.8),
                ForecastPoint("2024-08", 1000.0, 800.0, 1200.0, 0.8),
            ],
        )
        assert result.total_forecasted() == 3000.0


class TestHistoricalAverage:
    """Tests for historical average forecasting."""

    def test_historical_average_basic(self):
        service = ForecastingService()
        data = pd.Series(
            [1000, 1100, 900, 1000, 1000],
            index=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        )

        result = service.forecast(
            historical_data=data,
            periods=3,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )

        assert result.method == ForecastMethod.HISTORICAL_AVERAGE
        assert len(result.forecasts) == 3
        # Average is 1000
        assert result.forecasts[0].value == 1000.0

    def test_historical_average_generates_future_periods(self):
        service = ForecastingService()
        data = pd.Series(
            [1000, 1000, 1000],
            index=["2024-01", "2024-02", "2024-03"],
        )

        result = service.forecast(
            historical_data=data,
            periods=2,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )

        assert result.forecasts[0].period == "2024-04"
        assert result.forecasts[1].period == "2024-05"


class TestWeightedAverage:
    """Tests for weighted average forecasting."""

    def test_weighted_average_emphasizes_recent(self):
        service = ForecastingService()
        # Old values are 500, recent values are 1500
        data = pd.Series(
            [500, 500, 500, 1500, 1500, 1500],
            index=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"],
        )

        result = service.forecast(
            historical_data=data,
            periods=1,
            method=ForecastMethod.WEIGHTED_AVERAGE,
        )

        # Weighted average should be closer to 1500 than 1000
        assert result.forecasts[0].value > 1000

    def test_weighted_average_with_dict(self):
        service = ForecastingService()
        data = {
            "2024-01": 1000.0,
            "2024-02": 1100.0,
            "2024-03": 1200.0,
        }

        result = service.forecast(
            historical_data=data,
            periods=2,
            method=ForecastMethod.WEIGHTED_AVERAGE,
        )

        assert len(result.forecasts) == 2


class TestTrendExtrapolation:
    """Tests for trend extrapolation forecasting."""

    def test_trend_increasing(self):
        service = ForecastingService()
        # Clear upward trend
        data = pd.Series(
            [1000, 1100, 1200, 1300, 1400],
            index=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        )

        result = service.forecast(
            historical_data=data,
            periods=2,
            method=ForecastMethod.TREND_EXTRAPOLATION,
        )

        # Should predict continued increase
        assert result.forecasts[0].value > 1400
        assert result.metrics["trend_direction"] == "increasing"

    def test_trend_decreasing(self):
        service = ForecastingService()
        # Clear downward trend
        data = pd.Series(
            [1400, 1300, 1200, 1100, 1000],
            index=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        )

        result = service.forecast(
            historical_data=data,
            periods=1,
            method=ForecastMethod.TREND_EXTRAPOLATION,
        )

        # Should predict continued decrease
        assert result.forecasts[0].value < 1000
        assert result.metrics["trend_direction"] == "decreasing"

    def test_trend_confidence_decreases(self):
        service = ForecastingService()
        data = pd.Series(
            [1000, 1100, 1200],
            index=["2024-01", "2024-02", "2024-03"],
        )

        result = service.forecast(
            historical_data=data,
            periods=3,
            method=ForecastMethod.TREND_EXTRAPOLATION,
        )

        # Confidence should decrease for farther periods
        assert result.forecasts[0].confidence > result.forecasts[2].confidence


class TestEnsemble:
    """Tests for ensemble forecasting."""

    def test_ensemble_combines_methods(self):
        service = ForecastingService()
        data = pd.Series(
            [1000, 1000, 1000, 1000, 1000],
            index=["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"],
        )

        result = service.forecast(
            historical_data=data,
            periods=1,
            method=ForecastMethod.ENSEMBLE,
        )

        assert result.method == ForecastMethod.ENSEMBLE
        # With stable data, ensemble should be close to 1000
        assert 900 < result.forecasts[0].value < 1100


class TestFromTransactions:
    """Tests for forecasting from transaction data."""

    def test_forecast_from_transactions(self):
        service = ForecastingService()
        transactions = pd.DataFrame({
            "amount": [-500, -600, -700],
            "transaction_date": ["2024-01-15", "2024-02-15", "2024-03-15"],
        })

        result = service.forecast_from_transactions(
            transactions=transactions,
            periods=2,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )

        assert len(result.forecasts) == 2
        # Average of 500, 600, 700 = 600
        assert result.forecasts[0].value == 600.0

    def test_forecast_expenses_only(self):
        service = ForecastingService()
        transactions = pd.DataFrame({
            "amount": [-500, 1000, -600],  # Income of 1000 should be ignored
            "transaction_date": ["2024-01-15", "2024-01-20", "2024-02-15"],
        })

        result = service.forecast_from_transactions(
            transactions=transactions,
            periods=1,
            expense_only=True,
        )

        # Should only include 500 and 600 (from Jan and Feb)
        assert result.forecasts[0].value < 1000

    def test_forecast_empty_transactions(self):
        service = ForecastingService()
        result = service.forecast_from_transactions(
            transactions=pd.DataFrame(),
            periods=1,
        )

        assert len(result.forecasts) == 0


class TestByCategory:
    """Tests for forecasting by category."""

    def test_forecast_multiple_categories(self):
        service = ForecastingService()
        transactions = pd.DataFrame({
            "amount": [-100, -200, -150, -300, -400, -350],
            "category": ["Food", "Food", "Food", "Rent", "Rent", "Rent"],
            "transaction_date": [
                "2024-01-15", "2024-02-15", "2024-03-15",
                "2024-01-01", "2024-02-01", "2024-03-01",
            ],
        })

        results = service.forecast_by_category(transactions=transactions, periods=1)

        assert "Food" in results
        assert "Rent" in results
        assert len(results["Food"].forecasts) == 1
        assert len(results["Rent"].forecasts) == 1


class TestConvenienceFunction:
    """Tests for forecast_spending convenience function."""

    def test_convenience_function(self):
        transactions = pd.DataFrame({
            "amount": [-1000, -1100, -1200],
            "transaction_date": ["2024-01-15", "2024-02-15", "2024-03-15"],
        })

        result = forecast_spending(transactions=transactions, periods=2)

        assert isinstance(result, ForecastResult)
        assert result.method == ForecastMethod.WEIGHTED_AVERAGE
        assert len(result.forecasts) == 2


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_data_point(self):
        service = ForecastingService()
        data = pd.Series([1000], index=["2024-01"])

        result = service.forecast(
            historical_data=data,
            periods=1,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )

        assert result.forecasts[0].value == 1000.0

    def test_empty_data(self):
        service = ForecastingService()
        result = service.forecast(
            historical_data=pd.Series(dtype=float),
            periods=1,
        )

        assert len(result.forecasts) == 0

    def test_year_boundary(self):
        service = ForecastingService()
        data = pd.Series(
            [1000, 1000, 1000],
            index=["2024-10", "2024-11", "2024-12"],
        )

        result = service.forecast(
            historical_data=data,
            periods=3,
            method=ForecastMethod.HISTORICAL_AVERAGE,
        )

        # Should cross year boundary
        assert result.forecasts[0].period == "2025-01"
        assert result.forecasts[1].period == "2025-02"
        assert result.forecasts[2].period == "2025-03"

    def test_confidence_bounds_positive(self):
        service = ForecastingService()
        data = pd.Series(
            [100, 100, 100],
            index=["2024-01", "2024-02", "2024-03"],
        )

        result = service.forecast(
            historical_data=data,
            periods=1,
        )

        # Lower bound should never be negative
        assert result.forecasts[0].lower_bound >= 0
