"""Tests for budget burn rate tracking service."""

from datetime import date
import pandas as pd
import pytest

from budget_analyser.domain.burn_rate import (
    BurnRateService,
    BurnRateMetrics,
    CategoryBurnRate,
    calculate_burn_rate,
)


class TestBurnRateMetrics:
    """Tests for BurnRateMetrics dataclass."""

    def test_is_over_budget(self):
        metrics = BurnRateMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            budget_amount=1000.0,
            spent_amount=1200.0,  # Over budget
            days_elapsed=15,
            days_remaining=16,
            daily_burn_rate=80.0,
            projected_total=2480.0,
            budget_remaining=-200.0,
            safe_daily_spend=0.0,
            days_until_exhausted=0.0,
            burn_rate_status="over_budget",
            projected_over_under=1480.0,
        )
        assert metrics.is_over_budget

    def test_on_track(self):
        metrics = BurnRateMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            budget_amount=1000.0,
            spent_amount=400.0,
            days_elapsed=15,
            days_remaining=16,
            daily_burn_rate=26.67,
            projected_total=826.77,
            budget_remaining=600.0,
            safe_daily_spend=37.5,
            days_until_exhausted=22.5,
            burn_rate_status="on_track",
            projected_over_under=-173.23,
        )
        assert metrics.on_track
        assert not metrics.is_over_budget

    def test_burn_rate_percentage(self):
        metrics = BurnRateMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            budget_amount=1000.0,
            spent_amount=500.0,
            days_elapsed=15,
            days_remaining=16,
            daily_burn_rate=33.33,
            projected_total=1033.23,
            budget_remaining=500.0,
            safe_daily_spend=31.25,
            days_until_exhausted=15.0,
            burn_rate_status="warning",
            projected_over_under=33.23,
        )
        assert metrics.burn_rate_percentage == 50.0

    def test_time_percentage(self):
        metrics = BurnRateMetrics(
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
            budget_amount=1000.0,
            spent_amount=500.0,
            days_elapsed=15,
            days_remaining=16,
            daily_burn_rate=33.33,
            projected_total=1033.23,
            budget_remaining=500.0,
            safe_daily_spend=31.25,
            days_until_exhausted=15.0,
            burn_rate_status="warning",
            projected_over_under=33.23,
        )
        # 15 out of 31 days = ~48.4%
        assert 48 < metrics.time_percentage < 49


class TestBurnRateService:
    """Tests for BurnRateService."""

    def test_calculate_monthly_burn_rate_mid_month(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=500.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.budget_amount == 1000.0
        assert metrics.spent_amount == 500.0
        assert metrics.days_elapsed == 15
        assert metrics.days_remaining == 16
        # Daily rate: 500 / 15 = ~33.33
        assert abs(metrics.daily_burn_rate - 33.33) < 0.1

    def test_calculate_monthly_burn_rate_start_of_month(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=100.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 1),
        )

        assert metrics.days_elapsed == 1
        assert metrics.daily_burn_rate == 100.0

    def test_calculate_monthly_burn_rate_end_of_month(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=900.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 31),
        )

        assert metrics.days_elapsed == 31
        assert metrics.days_remaining == 0

    def test_on_track_status(self):
        service = BurnRateService()

        # Spending at 30% with 50% of month elapsed = on track
        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=300.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.burn_rate_status == "on_track"

    def test_warning_status_projected_over(self):
        service = BurnRateService()

        # Spending fast - will go over budget
        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=700.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        # Projected: 700/15 * 31 = ~1446
        assert metrics.burn_rate_status == "warning"

    def test_over_budget_status(self):
        service = BurnRateService()

        # Already over budget
        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=1100.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.burn_rate_status == "over_budget"
        assert metrics.is_over_budget

    def test_safe_daily_spend(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=400.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        # Remaining: 600, Days remaining: 16
        # Safe daily: 600 / 16 = 37.5
        assert abs(metrics.safe_daily_spend - 37.5) < 0.1

    def test_days_until_exhausted(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=500.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        # Daily rate: 500/15 = ~33.33
        # Remaining: 500
        # Days until exhausted: 500 / 33.33 = ~15
        assert metrics.days_until_exhausted is not None
        assert abs(metrics.days_until_exhausted - 15) < 0.5

    def test_days_until_exhausted_already_over(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=1100.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.days_until_exhausted == 0.0


class TestCalculateFromTransactions:
    """Tests for calculate_from_transactions method."""

    def test_calculates_from_transaction_data(self):
        service = BurnRateService()

        transactions = pd.DataFrame({
            "amount": [-100.0, -200.0, -150.0],
            "transaction_date": ["2024-01-05", "2024-01-10", "2024-01-14"],
        })

        metrics = service.calculate_from_transactions(
            transactions=transactions,
            budget_amount=1000.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.spent_amount == 450.0

    def test_handles_empty_transactions(self):
        service = BurnRateService()

        metrics = service.calculate_from_transactions(
            transactions=pd.DataFrame(),
            budget_amount=1000.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.spent_amount == 0.0

    def test_ignores_positive_amounts(self):
        service = BurnRateService()

        transactions = pd.DataFrame({
            "amount": [-100.0, 500.0, -200.0],  # 500 is income, ignore
            "transaction_date": ["2024-01-05", "2024-01-10", "2024-01-14"],
        })

        metrics = service.calculate_from_transactions(
            transactions=transactions,
            budget_amount=1000.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.spent_amount == 300.0  # Only -100 and -200


class TestCalculateByCategory:
    """Tests for calculate_by_category method."""

    def test_calculates_multiple_categories(self):
        service = BurnRateService()

        transactions = pd.DataFrame({
            "amount": [-100.0, -200.0, -150.0, -50.0],
            "category": ["Needs", "Luxury", "Needs", "Luxury"],
            "transaction_date": ["2024-01-05", "2024-01-10", "2024-01-14", "2024-01-15"],
        })

        budgets = {
            "Needs": 500.0,
            "Luxury": 300.0,
        }

        results = service.calculate_by_category(
            transactions=transactions,
            budgets=budgets,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert len(results) == 2

        # Find each category
        needs = next(r for r in results if r.category == "Needs")
        luxuries = next(r for r in results if r.category == "Luxury")

        assert needs.metrics.spent_amount == 250.0
        assert luxuries.metrics.spent_amount == 250.0

    def test_sorts_by_burn_rate_descending(self):
        service = BurnRateService()

        transactions = pd.DataFrame({
            "amount": [-100.0, -400.0],
            "category": ["Needs", "Luxury"],
            "transaction_date": ["2024-01-10", "2024-01-10"],
        })

        budgets = {
            "Needs": 500.0,  # 20% spent
            "Luxury": 500.0,  # 80% spent
        }

        results = service.calculate_by_category(
            transactions=transactions,
            budgets=budgets,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        # Luxury should be first (higher burn rate)
        assert results[0].category == "Luxury"


class TestConvenienceFunction:
    """Tests for calculate_burn_rate convenience function."""

    def test_convenience_function(self):
        metrics = calculate_burn_rate(
            budget=1000.0,
            spent=500.0,
            year=2024,
            month=1,
        )

        assert isinstance(metrics, BurnRateMetrics)
        assert metrics.budget_amount == 1000.0
        assert metrics.spent_amount == 500.0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_zero_budget(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=0.0,
            spent_amount=100.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.burn_rate_percentage == 0.0

    def test_february_leap_year(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=500.0,
            year=2024,  # Leap year
            month=2,
            as_of_date=date(2024, 2, 15),
        )

        assert metrics.period_end == date(2024, 2, 29)

    def test_february_non_leap_year(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=500.0,
            year=2023,  # Non-leap year
            month=2,
            as_of_date=date(2023, 2, 15),
        )

        assert metrics.period_end == date(2023, 2, 28)

    def test_no_spending(self):
        service = BurnRateService()

        metrics = service.calculate_monthly_burn_rate(
            budget_amount=1000.0,
            spent_amount=0.0,
            year=2024,
            month=1,
            as_of_date=date(2024, 1, 15),
        )

        assert metrics.daily_burn_rate == 0.0
        assert metrics.days_until_exhausted is None  # Won't exhaust
        assert metrics.burn_rate_status == "on_track"
