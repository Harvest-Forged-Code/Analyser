"""Unit tests for net_worth repository CRUD operations."""
from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.net_worth.repository import (
    NetWorthRepository,
)


@pytest.fixture()
def repo(tmp_path: Path) -> NetWorthRepository:
    """Create a repository backed by a temporary SQLite database."""
    return NetWorthRepository(db_path=tmp_path / "test.db")


def test_add_account(repo: NetWorthRepository) -> None:
    account = repo.add_account("Chase", "checking", 5000.0, "main")
    assert account.id is not None
    assert account.name == "Chase"
    assert account.account_type == "checking"
    assert account.balance == 5000.0
    assert account.notes == "main"


def test_get_all_accounts_empty(repo: NetWorthRepository) -> None:
    assert repo.get_all_accounts() == []


def test_get_all_accounts_returns_sorted(
    repo: NetWorthRepository,
) -> None:
    repo.add_account("Visa", "credit_card", -1000.0)
    repo.add_account("Chase", "checking", 5000.0)
    repo.add_account("BofA", "checking", 3000.0)

    accounts = repo.get_all_accounts()
    assert len(accounts) == 3
    # Sorted by account_type then name
    assert accounts[0].name == "BofA"
    assert accounts[1].name == "Chase"
    assert accounts[2].name == "Visa"


def test_update_account_balance(repo: NetWorthRepository) -> None:
    account = repo.add_account("Chase", "checking", 5000.0)
    updated = repo.update_account_balance(account.id, 6000.0)
    assert updated is True

    accounts = repo.get_all_accounts()
    assert accounts[0].balance == 6000.0


def test_update_nonexistent_account_returns_false(
    repo: NetWorthRepository,
) -> None:
    assert repo.update_account_balance(9999, 100.0) is False


def test_delete_account(repo: NetWorthRepository) -> None:
    account = repo.add_account("Chase", "checking", 5000.0)
    deleted = repo.delete_account(account.id)
    assert deleted is True
    assert repo.get_all_accounts() == []


def test_delete_nonexistent_account_returns_false(
    repo: NetWorthRepository,
) -> None:
    assert repo.delete_account(9999) is False


def test_add_duplicate_name_raises(
    repo: NetWorthRepository,
) -> None:
    repo.add_account("Chase", "checking", 5000.0)
    with pytest.raises(Exception):
        repo.add_account("Chase", "savings", 1000.0)


def test_account_default_values(repo: NetWorthRepository) -> None:
    account = repo.add_account("Test", "other")
    assert account.balance == 0
    assert account.notes == ""
