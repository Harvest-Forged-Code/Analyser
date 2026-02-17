"""Unit tests for savings controller integration."""
from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.savings.controller import (
    SavingsController,
)


@pytest.fixture()
def controller() -> SavingsController:
    """Create a savings controller (no repository needed)."""
    return SavingsController()


def test_calculate_savings_metrics(
    controller: SavingsController,
) -> None:
    earnings = pd.DataFrame({
        "amount": [5000.0],
        "transaction_date": ["2025-01-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-3000.0],
        "transaction_date": ["2025-01-20"],
    })
    result = controller.calculate_savings_metrics(
        earnings, expenses, year=2025,
    )
    assert result.total_earnings == 5000.0
    assert result.total_expenses == 3000.0
    assert result.savings_rate == pytest.approx(40.0)


def test_calculate_monthly_savings(
    controller: SavingsController,
) -> None:
    earnings = pd.DataFrame({
        "amount": [5000.0],
        "transaction_date": ["2025-03-15"],
    })
    expenses = pd.DataFrame({
        "amount": [-2000.0],
        "transaction_date": ["2025-03-20"],
    })
    result = controller.calculate_monthly_savings(
        earnings, expenses, year=2025,
    )
    assert len(result) == 12
    # March (index 2)
    assert result[2][0] == "March"
    assert result[2][1] == 5000.0  # earnings
    assert result[2][2] == 2000.0  # expenses
    assert result[2][3] == 3000.0  # savings


def test_empty_data(controller: SavingsController) -> None:
    result = controller.calculate_savings_metrics(
        pd.DataFrame(), pd.DataFrame(),
    )
    assert result.net_savings == 0.0
    assert result.savings_rate == 0.0
