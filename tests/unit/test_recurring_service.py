"""Unit tests for recurring service pure functions."""
from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.recurring.models import (
    RecurringTransaction,
)
from budget_analyser.features.recurring.service import (
    calculate_recurring_summary,
    check_recurring_anomalies,
)


# ==================== calculate_recurring_summary ====================


def test_summary_empty_list() -> None:
    result = calculate_recurring_summary(recurring=[])
    assert result == {
        "monthly_total": 0.0,
        "yearly_projection": 0.0,
        "count": 0,
    }


def test_summary_monthly_only() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Netflix", expected_amount=15.0,
            frequency="monthly", category="Subs",
            sub_category="", last_occurrence="",
        ),
        RecurringTransaction(
            id=2, description="Rent", expected_amount=2000.0,
            frequency="monthly", category="Housing",
            sub_category="", last_occurrence="",
        ),
    ]
    result = calculate_recurring_summary(recurring=recurring)
    assert result["monthly_total"] == pytest.approx(2015.0)
    assert result["yearly_projection"] == pytest.approx(24180.0)
    assert result["count"] == 2


def test_summary_mixed_frequencies() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Weekly", expected_amount=100.0,
            frequency="weekly", category="", sub_category="",
            last_occurrence="",
        ),
        RecurringTransaction(
            id=2, description="Quarterly", expected_amount=300.0,
            frequency="quarterly", category="", sub_category="",
            last_occurrence="",
        ),
        RecurringTransaction(
            id=3, description="Yearly", expected_amount=1200.0,
            frequency="yearly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    result = calculate_recurring_summary(recurring=recurring)
    # weekly: 100 * 4.33 = 433.0
    # quarterly: 300 / 3 = 100.0
    # yearly: 1200 / 12 = 100.0
    assert result["monthly_total"] == pytest.approx(633.0)
    assert result["count"] == 3


def test_summary_uses_absolute_amounts() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Test", expected_amount=-50.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    result = calculate_recurring_summary(recurring=recurring)
    assert result["monthly_total"] == pytest.approx(50.0)


# ==================== check_recurring_anomalies ====================


def test_anomalies_empty_recurring_returns_empty() -> None:
    df = pd.DataFrame({"description": ["x"], "amount": [-10]})
    result = check_recurring_anomalies(
        recurring=[], transactions_df=df,
    )
    assert result == []


def test_anomalies_empty_transactions_returns_empty() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Netflix", expected_amount=15.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    result = check_recurring_anomalies(
        recurring=recurring, transactions_df=pd.DataFrame(),
    )
    assert result == []


def test_anomalies_within_tolerance() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Netflix", expected_amount=15.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    df = pd.DataFrame({
        "description": ["Netflix subscription"],
        "amount": [-15.50],
    })
    result = check_recurring_anomalies(
        recurring=recurring, transactions_df=df,
        tolerance_percent=10.0,
    )
    assert result == []


def test_anomalies_over_tolerance() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Netflix", expected_amount=15.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    df = pd.DataFrame({
        "description": ["Netflix subscription"],
        "amount": [-20.0],
    })
    result = check_recurring_anomalies(
        recurring=recurring, transactions_df=df,
        tolerance_percent=10.0,
    )
    assert len(result) == 1
    assert result[0]["description"] == "Netflix"
    assert result[0]["expected"] == 15.0
    assert result[0]["actual"] == 20.0


def test_anomalies_no_matching_transactions() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Netflix", expected_amount=15.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    df = pd.DataFrame({
        "description": ["Hulu"], "amount": [-12.0],
    })
    result = check_recurring_anomalies(
        recurring=recurring, transactions_df=df,
    )
    assert result == []


def test_anomalies_uses_most_recent_transaction() -> None:
    recurring = [
        RecurringTransaction(
            id=1, description="Gym", expected_amount=50.0,
            frequency="monthly", category="", sub_category="",
            last_occurrence="",
        ),
    ]
    df = pd.DataFrame({
        "description": ["Gym membership", "Gym membership"],
        "amount": [-50.0, -80.0],
        "transaction_date": ["2025-01-01", "2025-02-01"],
    })
    result = check_recurring_anomalies(
        recurring=recurring, transactions_df=df,
        tolerance_percent=10.0,
    )
    # Most recent (2025-02-01) is $80, expected $50 = 60% diff
    assert len(result) == 1
    assert result[0]["actual"] == 80.0
