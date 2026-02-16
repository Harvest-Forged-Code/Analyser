"""Unit tests for net_worth service pure functions."""
from __future__ import annotations

from budget_analyser.features.net_worth.models import Account
from budget_analyser.features.net_worth.service import (
    calculate_net_worth_summary,
)


def test_empty_accounts_returns_zero_summary() -> None:
    result = calculate_net_worth_summary(accounts=[])
    assert result.total_assets == 0.0
    assert result.total_liabilities == 0.0
    assert result.net_worth == 0.0
    assert result.assets_by_type == {}
    assert result.liabilities_by_type == {}
    assert result.accounts == []


def test_assets_only() -> None:
    accounts = [
        Account(id=1, name="Chase", account_type="checking",
                balance=5000, last_updated="2025-01-01"),
        Account(id=2, name="Fidelity", account_type="investment",
                balance=25000, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.total_assets == 30000.0
    assert result.total_liabilities == 0.0
    assert result.net_worth == 30000.0
    assert result.assets_by_type == {
        "checking": 5000.0, "investment": 25000.0,
    }


def test_liabilities_only() -> None:
    accounts = [
        Account(id=1, name="Visa", account_type="credit_card",
                balance=-2000, last_updated="2025-01-01"),
        Account(id=2, name="Mortgage", account_type="loan",
                balance=-150000, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.total_assets == 0.0
    assert result.total_liabilities == 152000.0
    assert result.net_worth == -152000.0


def test_mixed_assets_and_liabilities() -> None:
    accounts = [
        Account(id=1, name="Checking", account_type="checking",
                balance=10000, last_updated="2025-01-01"),
        Account(id=2, name="Savings", account_type="savings",
                balance=20000, last_updated="2025-01-01"),
        Account(id=3, name="Visa", account_type="credit_card",
                balance=-5000, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.total_assets == 30000.0
    assert result.total_liabilities == 5000.0
    assert result.net_worth == 25000.0


def test_multiple_accounts_same_type_aggregated() -> None:
    accounts = [
        Account(id=1, name="Chase", account_type="checking",
                balance=3000, last_updated="2025-01-01"),
        Account(id=2, name="BofA", account_type="checking",
                balance=7000, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.assets_by_type == {"checking": 10000.0}


def test_other_account_type_is_asset() -> None:
    accounts = [
        Account(id=1, name="Misc", account_type="other",
                balance=1000, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.total_assets == 1000.0
    assert result.assets_by_type == {"other": 1000.0}


def test_accounts_list_preserved_in_summary() -> None:
    accounts = [
        Account(id=1, name="Test", account_type="savings",
                balance=500, last_updated="2025-01-01"),
    ]
    result = calculate_net_worth_summary(accounts=accounts)
    assert result.accounts == accounts
