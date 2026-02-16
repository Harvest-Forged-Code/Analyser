"""Unit tests for savings service pure functions."""
from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.savings.service import (
    calculate_monthly_savings,
    calculate_savings_metrics,
)


# ==================== calculate_savings_metrics ====================


def test_metrics_empty_dataframes() -> None:
    result = calculate_savings_metrics(
        earnings_df=pd.DataFrame(),
        expenses_df=pd.DataFrame(),
    )
    assert result.total_earnings == 0.0
    assert result.total_expenses == 0.0
    assert result.net_savings == 0.0
    assert result.savings_rate == 0.0


def test_metrics_basic_calculation() -> None:
    earnings = pd.DataFrame({
        "amount": [5000.0, 5000.0],
        "transaction_date": ["2025-01-15", "2025-02-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-3000.0, -3000.0],
        "transaction_date": ["2025-01-20", "2025-02-20"],
    })
    result = calculate_savings_metrics(
        earnings_df=earnings, expenses_df=expenses,
    )
    assert result.total_earnings == 10000.0
    assert result.total_expenses == 6000.0
    assert result.net_savings == 4000.0
    assert result.savings_rate == pytest.approx(40.0)
    assert result.months_of_data == 2
    assert result.monthly_average_savings == pytest.approx(2000.0)


def test_metrics_filter_by_year() -> None:
    earnings = pd.DataFrame({
        "amount": [5000.0, 6000.0],
        "transaction_date": ["2024-12-15", "2025-01-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-3000.0, -4000.0],
        "transaction_date": ["2024-12-20", "2025-01-20"],
    })
    result = calculate_savings_metrics(
        earnings_df=earnings, expenses_df=expenses, year=2025,
    )
    assert result.total_earnings == 6000.0
    assert result.total_expenses == 4000.0


def test_metrics_zero_earnings_rate_is_zero() -> None:
    result = calculate_savings_metrics(
        earnings_df=pd.DataFrame(),
        expenses_df=pd.DataFrame({
            "amount": [-100.0],
            "transaction_date": ["2025-01-01"],
        }),
    )
    assert result.savings_rate == 0.0


def test_metrics_negative_savings() -> None:
    earnings = pd.DataFrame({
        "amount": [1000.0],
        "transaction_date": ["2025-01-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-3000.0],
        "transaction_date": ["2025-01-20"],
    })
    result = calculate_savings_metrics(
        earnings_df=earnings, expenses_df=expenses,
    )
    assert result.net_savings == -2000.0
    assert result.savings_rate == pytest.approx(-200.0)


# ==================== calculate_monthly_savings ====================


def test_monthly_returns_12_months() -> None:
    result = calculate_monthly_savings(
        earnings_df=pd.DataFrame(),
        expenses_df=pd.DataFrame(),
        year=2025,
    )
    assert len(result) == 12
    assert result[0][0] == "January"
    assert result[11][0] == "December"


def test_monthly_with_data() -> None:
    earnings = pd.DataFrame({
        "amount": [5000.0],
        "transaction_date": ["2025-01-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-3000.0],
        "transaction_date": ["2025-01-20"],
    })
    result = calculate_monthly_savings(
        earnings_df=earnings, expenses_df=expenses, year=2025,
    )
    # January
    month_name, earn, exp, sav, rate = result[0]
    assert month_name == "January"
    assert earn == 5000.0
    assert exp == 3000.0
    assert sav == 2000.0
    assert rate == pytest.approx(40.0)

    # February should be all zeros
    _, earn2, exp2, sav2, rate2 = result[1]
    assert earn2 == 0.0
    assert exp2 == 0.0
    assert sav2 == 0.0
    assert rate2 == 0.0


def test_monthly_empty_data_all_zeros() -> None:
    result = calculate_monthly_savings(
        earnings_df=pd.DataFrame(),
        expenses_df=pd.DataFrame(),
        year=2025,
    )
    for _, earn, exp, sav, rate in result:
        assert earn == 0.0
        assert exp == 0.0
        assert sav == 0.0
        assert rate == 0.0
