"""Unit tests for net_worth service (formerly controller) integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.net_worth.service import (
    NetWorthService,
)
from budget_analyser.features.net_worth.models import (
    NetWorthModel,
)


@pytest.fixture()
def service(tmp_path: Path) -> NetWorthService:
    """Create a service backed by a temporary SQLite database."""
    model = NetWorthModel(db_path=tmp_path / "test.db")
    return NetWorthService(model=model)


def test_add_and_get_accounts(
    service: NetWorthService,
) -> None:
    service.add_account("Chase", "checking", 5000.0)
    service.add_account("Visa", "credit_card", -2000.0)

    accounts = service.get_all_accounts()
    assert len(accounts) == 2


def test_update_balance(service: NetWorthService) -> None:
    account = service.add_account("Chase", "checking", 5000.0)
    result = service.update_account_balance(account.id, 6000.0)
    assert result is True

    accounts = service.get_all_accounts()
    assert accounts[0].balance == 6000.0


def test_delete_account(service: NetWorthService) -> None:
    account = service.add_account("Chase", "checking", 5000.0)
    assert service.delete_account(account.id) is True
    assert service.get_all_accounts() == []


def test_get_net_worth_summary(
    service: NetWorthService,
) -> None:
    service.add_account("Checking", "checking", 10000.0)
    service.add_account("Savings", "savings", 20000.0)
    service.add_account("Visa", "credit_card", -5000.0)

    summary = service.get_net_worth_summary()
    assert summary.total_assets == 30000.0
    assert summary.total_liabilities == 5000.0
    assert summary.net_worth == 25000.0
    assert len(summary.accounts) == 3


def test_net_worth_summary_empty(
    service: NetWorthService,
) -> None:
    summary = service.get_net_worth_summary()
    assert summary.net_worth == 0.0
    assert summary.accounts == []
