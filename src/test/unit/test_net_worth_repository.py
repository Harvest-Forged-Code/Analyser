"""Unit tests for net_worth model (formerly repository) CRUD operations."""
from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.net_worth.models import (
    NetWorthModel,
    NetWorthRepository,
)


@pytest.fixture()
def model(tmp_path: Path) -> NetWorthModel:
    """Create a model backed by a temporary SQLite database."""
    return NetWorthModel(db_path=tmp_path / "test.db")


def test_backward_compat_alias() -> None:
    assert NetWorthRepository is NetWorthModel


def test_add_account(model: NetWorthModel) -> None:
    account = model.add_account("Chase", "checking", 5000.0, "main")
    assert account.id is not None
    assert account.name == "Chase"
    assert account.account_type == "checking"
    assert account.balance == 5000.0
    assert account.notes == "main"


def test_get_all_accounts_empty(model: NetWorthModel) -> None:
    assert model.get_all_accounts() == []


def test_get_all_accounts_returns_sorted(
    model: NetWorthModel,
) -> None:
    model.add_account("Visa", "credit_card", -1000.0)
    model.add_account("Chase", "checking", 5000.0)
    model.add_account("BofA", "checking", 3000.0)

    accounts = model.get_all_accounts()
    assert len(accounts) == 3
    # Sorted by account_type then name
    assert accounts[0].name == "BofA"
    assert accounts[1].name == "Chase"
    assert accounts[2].name == "Visa"


def test_update_account_balance(model: NetWorthModel) -> None:
    account = model.add_account("Chase", "checking", 5000.0)
    updated = model.update_account_balance(account.id, 6000.0)
    assert updated is True

    accounts = model.get_all_accounts()
    assert accounts[0].balance == 6000.0


def test_update_nonexistent_account_returns_false(
    model: NetWorthModel,
) -> None:
    assert model.update_account_balance(9999, 100.0) is False


def test_delete_account(model: NetWorthModel) -> None:
    account = model.add_account("Chase", "checking", 5000.0)
    deleted = model.delete_account(account.id)
    assert deleted is True
    assert model.get_all_accounts() == []


def test_delete_nonexistent_account_returns_false(
    model: NetWorthModel,
) -> None:
    assert model.delete_account(9999) is False


def test_add_duplicate_name_raises(
    model: NetWorthModel,
) -> None:
    model.add_account("Chase", "checking", 5000.0)
    with pytest.raises(Exception):
        model.add_account("Chase", "savings", 1000.0)


def test_account_default_values(model: NetWorthModel) -> None:
    account = model.add_account("Test", "other")
    assert account.balance == 0
    assert account.notes == ""
