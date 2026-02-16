"""Unit tests for net_worth controller integration."""
from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.net_worth.controller import (
    NetWorthController,
)
from budget_analyser.features.net_worth.repository import (
    NetWorthRepository,
)


@pytest.fixture()
def controller(tmp_path: Path) -> NetWorthController:
    """Create a controller backed by a temporary SQLite database."""
    repo = NetWorthRepository(db_path=tmp_path / "test.db")
    return NetWorthController(repository=repo)


def test_add_and_get_accounts(
    controller: NetWorthController,
) -> None:
    controller.add_account("Chase", "checking", 5000.0)
    controller.add_account("Visa", "credit_card", -2000.0)

    accounts = controller.get_all_accounts()
    assert len(accounts) == 2


def test_update_balance(controller: NetWorthController) -> None:
    account = controller.add_account("Chase", "checking", 5000.0)
    result = controller.update_account_balance(account.id, 6000.0)
    assert result is True

    accounts = controller.get_all_accounts()
    assert accounts[0].balance == 6000.0


def test_delete_account(controller: NetWorthController) -> None:
    account = controller.add_account("Chase", "checking", 5000.0)
    assert controller.delete_account(account.id) is True
    assert controller.get_all_accounts() == []


def test_get_net_worth_summary(
    controller: NetWorthController,
) -> None:
    controller.add_account("Checking", "checking", 10000.0)
    controller.add_account("Savings", "savings", 20000.0)
    controller.add_account("Visa", "credit_card", -5000.0)

    summary = controller.get_net_worth_summary()
    assert summary.total_assets == 30000.0
    assert summary.total_liabilities == 5000.0
    assert summary.net_worth == 25000.0
    assert len(summary.accounts) == 3


def test_net_worth_summary_empty(
    controller: NetWorthController,
) -> None:
    summary = controller.get_net_worth_summary()
    assert summary.net_worth == 0.0
    assert summary.accounts == []
