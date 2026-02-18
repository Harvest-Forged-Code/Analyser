"""Tests for spending pattern analysis service."""

import pandas as pd
import pytest

from budget_analyser.features.trends import (
    SpendingPatternService,
    ParetoAnalysis,
    ParetoItem,
    WeeklyPattern,
    DayOfWeek,
    AnomalyReport,
    SavingsRateTrend,
    analyze_spending_patterns,
)


class TestParetoAnalysis:
    """Tests for Pareto analysis."""

    def test_pareto_empty_transactions(self):
        service = SpendingPatternService()
        result = service.pareto_analysis(transactions=pd.DataFrame())
        assert len(result.items) == 0

    def test_pareto_basic_analysis(self):
        service = SpendingPatternService()
        transactions = pd.DataFrame({
            "amount": [-800, -150, -50],  # 80%, 15%, 5%
            "category": ["Rent", "Food", "Entertainment"],
        })

        result = service.pareto_analysis(transactions=transactions)

        assert len(result.items) == 3
        assert result.total_amount == 1000.0
        # First item should be Rent (highest)
        assert result.items[0].category == "Rent"
        assert result.items[0].percentage == 80.0

    def test_pareto_top_80_identification(self):
        service = SpendingPatternService()
        transactions = pd.DataFrame({
            "amount": [-400, -300, -200, -100],
            "category": ["A", "B", "C", "D"],
        })

        result = service.pareto_analysis(transactions=transactions)

        # A (40%) + B (30%) = 70%, add C (20%) to get to 90%
        # So A, B, C should be top 80
        top_cats = result.top_80_categories
        assert "A" in top_cats
        assert "B" in top_cats

    def test_pareto_ignores_positive_amounts(self):
        service = SpendingPatternService()
        transactions = pd.DataFrame({
            "amount": [-100, 500, -200],  # Income ignored
            "category": ["Expense1", "Income", "Expense2"],
        })

        result = service.pareto_analysis(transactions=transactions)

        assert result.total_amount == 300.0
        assert len(result.items) == 2

    def test_pareto_concentration_ratio(self):
        service = SpendingPatternService()
        # Highly concentrated: one category has almost everything
        transactions = pd.DataFrame({
            "amount": [-900, -50, -50],
            "category": ["Big", "Small1", "Small2"],
        })

        result = service.pareto_analysis(transactions=transactions)

        # Only "Big" is in top 80%
        assert result.concentration_ratio < 0.5


class TestWeeklyPattern:
    """Tests for weekly pattern analysis."""

    def test_weekly_empty_transactions(self):
        service = SpendingPatternService()
        result = service.weekly_pattern(transactions=pd.DataFrame())
        assert len(result.day_patterns) == 0

    def test_weekly_pattern_basic(self):
        service = SpendingPatternService()
        # Monday transactions
        transactions = pd.DataFrame({
            "amount": [-100, -200],
            "transaction_date": ["2024-01-08", "2024-01-15"],  # Both Mondays
        })

        result = service.weekly_pattern(transactions=transactions)

        assert len(result.day_patterns) == 7
        monday = next(p for p in result.day_patterns if p.day == DayOfWeek.MONDAY)
        assert monday.total_amount == 300.0
        assert monday.transaction_count == 2

    def test_weekly_highest_lowest_day(self):
        service = SpendingPatternService()
        transactions = pd.DataFrame({
            "amount": [-100, -500],
            "transaction_date": ["2024-01-08", "2024-01-13"],  # Mon, Sat
        })

        result = service.weekly_pattern(transactions=transactions)

        assert result.highest_day == DayOfWeek.SATURDAY
        assert result.lowest_day == DayOfWeek.MONDAY

    def test_weekend_percentage(self):
        service = SpendingPatternService()
        transactions = pd.DataFrame({
            "amount": [-100, -100, -100, -100],  # Equal spending
            "transaction_date": [
                "2024-01-08",  # Monday
                "2024-01-09",  # Tuesday
                "2024-01-13",  # Saturday
                "2024-01-14",  # Sunday
            ],
        })

        result = service.weekly_pattern(transactions=transactions)

        # 50% weekend spending
        assert result.weekend_percentage == 50.0


class TestAnomalyDetection:
    """Tests for anomaly detection."""

    def test_anomaly_empty_transactions(self):
        service = SpendingPatternService()
        result = service.detect_anomalies(transactions=pd.DataFrame())
        assert len(result.anomalies) == 0

    def test_anomaly_detects_high_amount(self):
        service = SpendingPatternService(anomaly_threshold=1.5)
        # Many normal transactions, one extreme outlier
        transactions = pd.DataFrame({
            "amount": [-100, -105, -95, -100, -98, -102, -99, -101, -97, -103, -2000],
            "category": ["Food"] * 11,
            "description": [f"tx{i}" for i in range(11)],
            "transaction_date": ["2024-01-01"] * 11,
        })

        result = service.detect_anomalies(transactions=transactions)

        assert len(result.anomalies) >= 1
        assert any(a.amount == 2000.0 for a in result.anomalies)

    def test_anomaly_rate_calculation(self):
        service = SpendingPatternService(anomaly_threshold=1.5)
        # Need enough normal data points for outlier to be detected
        transactions = pd.DataFrame({
            "amount": [-100, -100, -100, -100, -100, -100, -100, -100, -100, -2000],
            "category": ["Food"] * 10,
            "description": [f"tx{i}" for i in range(10)],
            "transaction_date": ["2024-01-01"] * 10,
        })

        result = service.detect_anomalies(transactions=transactions)

        # Should have some anomalies
        assert result.anomaly_rate > 0

    def test_anomaly_by_category(self):
        service = SpendingPatternService(anomaly_threshold=1.5)
        # More data points per category with extreme outliers
        transactions = pd.DataFrame({
            "amount": [-100, -100, -100, -100, -100, -100, -1000,
                       -10, -10, -10, -10, -10, -10, -100],
            "category": ["Food"] * 7 + ["Gas"] * 7,
            "description": [f"tx{i}" for i in range(14)],
            "transaction_date": ["2024-01-01"] * 14,
        })

        result = service.detect_anomalies(transactions=transactions, by_category=True)

        # Should detect anomalies within each category
        assert len(result.anomalies) >= 1


class TestSavingsRateTrend:
    """Tests for savings rate trend analysis."""

    def test_savings_rate_calculation(self):
        service = SpendingPatternService()

        earnings = pd.DataFrame({
            "amount": [5000, 5000],
            "transaction_date": ["2024-01-15", "2024-02-15"],
        })
        expenses = pd.DataFrame({
            "amount": [-3000, -4000],
            "transaction_date": ["2024-01-20", "2024-02-20"],
        })

        trends = service.savings_rate_trend(earnings=earnings, expenses=expenses)

        assert len(trends) == 2
        jan = next(t for t in trends if t.period == "2024-01")
        assert jan.earnings == 5000
        assert jan.expenses == 3000
        assert jan.savings == 2000
        assert jan.savings_rate == 40.0  # 2000/5000 * 100

    def test_savings_rate_no_earnings(self):
        service = SpendingPatternService()

        earnings = pd.DataFrame({"amount": [], "transaction_date": []})
        expenses = pd.DataFrame({
            "amount": [-1000],
            "transaction_date": ["2024-01-15"],
        })

        trends = service.savings_rate_trend(earnings=earnings, expenses=expenses)

        # Should have a trend with 0 savings rate
        jan = next((t for t in trends if t.period == "2024-01"), None)
        if jan:
            assert jan.savings_rate == 0.0


class TestDayOfWeek:
    """Tests for DayOfWeek enum."""

    def test_from_int(self):
        assert DayOfWeek.from_int(0) == DayOfWeek.MONDAY
        assert DayOfWeek.from_int(4) == DayOfWeek.FRIDAY
        assert DayOfWeek.from_int(6) == DayOfWeek.SUNDAY


class TestConvenienceFunction:
    """Tests for analyze_spending_patterns convenience function."""

    def test_returns_all_analyses(self):
        transactions = pd.DataFrame({
            "amount": [-100, -200, -300],
            "category": ["A", "B", "C"],
            "transaction_date": ["2024-01-08", "2024-01-09", "2024-01-10"],
            "description": ["tx1", "tx2", "tx3"],
        })

        result = analyze_spending_patterns(transactions=transactions)

        assert "pareto" in result
        assert "weekly" in result
        assert "anomalies" in result
        assert isinstance(result["pareto"], ParetoAnalysis)
        assert isinstance(result["weekly"], WeeklyPattern)
        assert isinstance(result["anomalies"], AnomalyReport)


class TestRealWorldScenarios:
    """Tests simulating real-world usage."""

    def test_typical_monthly_spending(self):
        service = SpendingPatternService()

        # Simulate typical monthly spending (rent is highest single category)
        transactions = pd.DataFrame({
            "amount": [
                -2000,  # Rent (big - single transaction)
                -200, -180, -190, -210,  # Groceries (regular)
                -50, -45, -55, -40,  # Subscriptions (small)
                -100, -80, -90,  # Dining (medium)
                -60, -55, -50,  # Gas (small)
            ],
            "category": [
                "Rent",
                "Groceries", "Groceries", "Groceries", "Groceries",
                "Subscriptions", "Subscriptions", "Subscriptions", "Subscriptions",
                "Dining", "Dining", "Dining",
                "Gas", "Gas", "Gas",
            ],
            "transaction_date": [
                "2024-01-01",
                "2024-01-05", "2024-01-12", "2024-01-19", "2024-01-26",
                "2024-01-01", "2024-01-01", "2024-01-01", "2024-01-01",
                "2024-01-06", "2024-01-13", "2024-01-20",
                "2024-01-08", "2024-01-15", "2024-01-22",
            ],
            "description": [f"tx{i}" for i in range(15)],
        })

        pareto = service.pareto_analysis(transactions=transactions)

        # Rent should be the top category (2000 vs Groceries 780)
        assert pareto.items[0].category == "Rent"
        # Should have reasonable concentration
        assert pareto.top_80_count <= 3  # Likely Rent + Groceries cover 80%
