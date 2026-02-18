"""Tests for trend analysis service."""

import pandas as pd
import pytest

from budget_analyser.features.trends import (
    TrendAnalysisService,
    TrendAnalysisResult,
    TrendDirection,
    MonthlyTrend,
    analyze_spending_trends,
    analyze_income_trends,
)


class TestTrendDirection:
    """Tests for TrendDirection enum."""

    def test_rising_from_positive_change(self):
        direction = TrendDirection.from_change(10.0)
        assert direction == TrendDirection.RISING

    def test_falling_from_negative_change(self):
        direction = TrendDirection.from_change(-10.0)
        assert direction == TrendDirection.FALLING

    def test_stable_from_small_change(self):
        direction = TrendDirection.from_change(2.0)
        assert direction == TrendDirection.STABLE

    def test_unknown_from_nan(self):
        direction = TrendDirection.from_change(float("nan"))
        assert direction == TrendDirection.UNKNOWN

    def test_custom_threshold(self):
        direction = TrendDirection.from_change(8.0, threshold=10.0)
        assert direction == TrendDirection.STABLE


class TestTrendAnalysisResult:
    """Tests for TrendAnalysisResult dataclass."""

    def test_get_trend_found(self):
        period = pd.Period("2024-01", freq="M")
        trends = [
            MonthlyTrend(period=period, value=100.0),
        ]
        result = TrendAnalysisResult(monthly_trends=trends)

        found = result.get_trend(period)
        assert found is not None
        assert found.value == 100.0

    def test_get_trend_not_found(self):
        result = TrendAnalysisResult()
        found = result.get_trend(pd.Period("2024-01", freq="M"))
        assert found is None

    def test_recent_trends(self):
        trends = [
            MonthlyTrend(period=pd.Period("2024-01", freq="M"), value=100.0),
            MonthlyTrend(period=pd.Period("2024-02", freq="M"), value=110.0),
            MonthlyTrend(period=pd.Period("2024-03", freq="M"), value=105.0),
            MonthlyTrend(period=pd.Period("2024-04", freq="M"), value=115.0),
        ]
        result = TrendAnalysisResult(monthly_trends=trends)

        recent = result.recent_trends(2)
        assert len(recent) == 2
        assert recent[0].period == pd.Period("2024-03", freq="M")
        assert recent[1].period == pd.Period("2024-04", freq="M")


class TestTrendAnalysisService:
    """Tests for TrendAnalysisService."""

    def test_analyze_empty_data(self):
        service = TrendAnalysisService()
        result = service.analyze(data=pd.Series(dtype=float))
        assert len(result.monthly_trends) == 0

    def test_analyze_single_month(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0],
            index=[pd.Period("2024-01", freq="M")],
        )

        result = service.analyze(data=data)
        assert len(result.monthly_trends) == 1
        assert result.monthly_trends[0].value == 100.0

    def test_analyze_calculates_mom_change(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 120.0, 110.0],
            index=pd.period_range("2024-01", periods=3, freq="M"),
        )

        result = service.analyze(data=data)

        # First month has no MoM change
        assert result.monthly_trends[0].mom_change == 0.0
        # Second month: 120 - 100 = 20
        assert result.monthly_trends[1].mom_change == 20.0
        # Third month: 110 - 120 = -10
        assert result.monthly_trends[2].mom_change == -10.0

    def test_analyze_calculates_mom_change_pct(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 120.0],
            index=pd.period_range("2024-01", periods=2, freq="M"),
        )

        result = service.analyze(data=data)

        # 20% increase
        assert abs(result.monthly_trends[1].mom_change_pct - 20.0) < 0.01

    def test_analyze_calculates_moving_averages(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 110.0, 120.0, 130.0],
            index=pd.period_range("2024-01", periods=4, freq="M"),
        )

        result = service.analyze(data=data)

        # 3-month MA for last month: (110 + 120 + 130) / 3 = 120
        assert result.monthly_trends[3].moving_avg_3m is not None
        assert abs(result.monthly_trends[3].moving_avg_3m - 120.0) < 0.01

    def test_analyze_determines_direction(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 120.0],  # 20% increase
            index=pd.period_range("2024-01", periods=2, freq="M"),
        )

        result = service.analyze(data=data)
        assert result.monthly_trends[1].direction == TrendDirection.RISING

    def test_analyze_finds_highest_lowest(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 150.0, 80.0, 120.0],
            index=pd.period_range("2024-01", periods=4, freq="M"),
        )

        result = service.analyze(data=data)
        assert result.highest_month == pd.Period("2024-02", freq="M")
        assert result.lowest_month == pd.Period("2024-03", freq="M")

    def test_analyze_with_dict_input(self):
        service = TrendAnalysisService()
        data = {
            pd.Period("2024-01", freq="M"): 100.0,
            pd.Period("2024-02", freq="M"): 110.0,
        }

        result = service.analyze(data=data)
        assert len(result.monthly_trends) == 2

    def test_analyze_calculates_volatility(self):
        service = TrendAnalysisService()
        # High volatility data
        data = pd.Series(
            [100.0, 200.0, 50.0, 150.0],
            index=pd.period_range("2024-01", periods=4, freq="M"),
        )

        result = service.analyze(data=data)
        assert result.volatility > 0


class TestAnalyzeDataFrame:
    """Tests for analyze_dataframe method."""

    def test_analyzes_dataframe_with_amounts(self):
        service = TrendAnalysisService()
        df = pd.DataFrame({
            "year_month": pd.period_range("2024-01", periods=3, freq="M"),
            "amount": [100.0, 110.0, 120.0],
        })

        result = service.analyze_dataframe(df=df)
        assert len(result.monthly_trends) == 3

    def test_analyzes_dataframe_with_aggregation(self):
        service = TrendAnalysisService()
        df = pd.DataFrame({
            "year_month": [
                pd.Period("2024-01", freq="M"),
                pd.Period("2024-01", freq="M"),
                pd.Period("2024-02", freq="M"),
            ],
            "amount": [50.0, 50.0, 120.0],
        })

        result = service.analyze_dataframe(df=df, aggregate_func="sum")
        assert len(result.monthly_trends) == 2
        # January: 50 + 50 = 100
        assert result.monthly_trends[0].value == 100.0

    def test_empty_dataframe(self):
        service = TrendAnalysisService()
        result = service.analyze_dataframe(df=pd.DataFrame())
        assert len(result.monthly_trends) == 0


class TestComparePeriods:
    """Tests for compare_periods method."""

    def test_mom_comparison(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0, 120.0],
            index=pd.period_range("2024-01", periods=2, freq="M"),
        )

        comparison = service.compare_periods(
            current_period=pd.Period("2024-02", freq="M"),
            data=data,
            comparison_type="mom",
        )

        assert comparison["current_value"] == 120.0
        assert comparison["previous_value"] == 100.0
        assert comparison["absolute_change"] == 20.0
        assert comparison["percent_change"] == 20.0
        assert comparison["direction"] == "rising"

    def test_yoy_comparison_without_data(self):
        service = TrendAnalysisService()
        data = pd.Series(
            [100.0],
            index=[pd.Period("2024-01", freq="M")],
        )

        comparison = service.compare_periods(
            current_period=pd.Period("2024-01", freq="M"),
            data=data,
            comparison_type="yoy",
        )

        # No YoY data available
        assert comparison["previous_value"] is None

    def test_period_not_found(self):
        service = TrendAnalysisService()
        data = pd.Series([100.0], index=[pd.Period("2024-01", freq="M")])

        comparison = service.compare_periods(
            current_period=pd.Period("2024-06", freq="M"),
            data=data,
        )

        assert "error" in comparison


class TestConvenienceFunctions:
    """Tests for convenience analysis functions."""

    def test_analyze_spending_trends(self):
        df = pd.DataFrame({
            "transaction_date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "amount": [-100.0, -50.0, -75.0, -100.0, -80.0],
            "category": ["Luxury"] * 5,
        })

        result = analyze_spending_trends(transactions=df)
        # Should have aggregated to monthly
        assert len(result.monthly_trends) >= 1

    def test_analyze_spending_trends_with_category_filter(self):
        df = pd.DataFrame({
            "transaction_date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "amount": [-100.0, -50.0, -75.0, -100.0],
            "category": ["Luxury", "Needs", "Luxury", "Needs"],
        })

        result = analyze_spending_trends(transactions=df, category="Luxury")
        # Should only include Luxury expenses
        assert result is not None

    def test_analyze_income_trends(self):
        df = pd.DataFrame({
            "transaction_date": pd.date_range("2024-01-01", periods=3, freq="ME"),
            "amount": [5000.0, 5100.0, 5200.0],
        })

        result = analyze_income_trends(transactions=df)
        assert len(result.monthly_trends) >= 1


class TestYearOverYearAnalysis:
    """Tests for year-over-year comparison."""

    def test_yoy_change_calculated(self):
        service = TrendAnalysisService()
        # Data spanning more than a year
        periods = pd.period_range("2023-01", periods=14, freq="M")
        values = [100.0] * 12 + [120.0, 130.0]  # 2024-01 and 2024-02
        data = pd.Series(values, index=periods)

        result = service.analyze(data=data)

        # 2024-01 should have YoY comparison with 2023-01
        jan_2024_trend = result.get_trend(pd.Period("2024-01", freq="M"))
        assert jan_2024_trend is not None
        assert jan_2024_trend.yoy_change is not None
        assert jan_2024_trend.yoy_change == 20.0  # 120 - 100
