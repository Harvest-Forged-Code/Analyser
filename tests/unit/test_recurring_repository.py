"""Unit tests for recurring repository CRUD operations."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.recurring.repository import (
    RecurringRepository,
)


@pytest.fixture()
def repo(tmp_path: Path) -> RecurringRepository:
    """Create a repository backed by a temporary SQLite database."""
    return RecurringRepository(db_path=tmp_path / "test.db")


def test_add_recurring_transaction(
    repo: RecurringRepository,
) -> None:
    rec = repo.add_recurring_transaction(
        "Netflix", 15.99, "monthly", "Subs", "streaming",
    )
    assert rec.id is not None
    assert rec.description == "Netflix"
    assert rec.expected_amount == 15.99
    assert rec.frequency == "monthly"


def test_get_all_empty(repo: RecurringRepository) -> None:
    assert repo.get_all_recurring_transactions() == []


def test_get_all_returns_sorted(
    repo: RecurringRepository,
) -> None:
    repo.add_recurring_transaction("Rent", 2000.0)
    repo.add_recurring_transaction("Netflix", 15.0)

    txns = repo.get_all_recurring_transactions()
    assert len(txns) == 2
    assert txns[0].description == "Netflix"
    assert txns[1].description == "Rent"


def test_get_active_only_filters(
    repo: RecurringRepository,
) -> None:
    rec = repo.add_recurring_transaction("Netflix", 15.0)
    repo.add_recurring_transaction("Rent", 2000.0)
    repo.deactivate_recurring_transaction(rec.id)

    active = repo.get_all_recurring_transactions(active_only=True)
    assert len(active) == 1
    assert active[0].description == "Rent"

    all_txns = repo.get_all_recurring_transactions(active_only=False)
    assert len(all_txns) == 2


def test_deactivate_recurring(
    repo: RecurringRepository,
) -> None:
    rec = repo.add_recurring_transaction("Netflix", 15.0)
    assert repo.deactivate_recurring_transaction(rec.id) is True


def test_deactivate_nonexistent_returns_false(
    repo: RecurringRepository,
) -> None:
    assert repo.deactivate_recurring_transaction(9999) is False


def test_delete_recurring(repo: RecurringRepository) -> None:
    rec = repo.add_recurring_transaction("Netflix", 15.0)
    assert repo.delete_recurring_transaction(rec.id) is True
    assert repo.get_all_recurring_transactions() == []


def test_delete_nonexistent_returns_false(
    repo: RecurringRepository,
) -> None:
    assert repo.delete_recurring_transaction(9999) is False


def test_upsert_on_conflict(repo: RecurringRepository) -> None:
    repo.add_recurring_transaction(
        "Netflix", 15.0, "monthly", "Subs",
    )
    updated = repo.add_recurring_transaction(
        "Netflix", 15.0, "yearly", "Entertainment",
    )
    assert updated.frequency == "yearly"
    assert updated.category == "Entertainment"
    assert len(repo.get_all_recurring_transactions()) == 1


def test_update_last_occurrence(
    repo: RecurringRepository,
) -> None:
    rec = repo.add_recurring_transaction("Netflix", 15.0)
    result = repo.update_last_occurrence(rec.id, "2025-01-15")
    assert result is True

    txns = repo.get_all_recurring_transactions()
    assert txns[0].last_occurrence == "2025-01-15"


def test_detect_recurring_empty_df(
    repo: RecurringRepository,
) -> None:
    result = repo.detect_recurring_transactions(pd.DataFrame())
    assert result == []


def test_detect_recurring_finds_patterns(
    repo: RecurringRepository,
) -> None:
    df = pd.DataFrame({
        "description": ["Netflix", "Netflix", "Netflix", "Groceries"],
        "amount": [-15.0, -15.0, -15.0, -120.0],
        "transaction_date": pd.to_datetime([
            "2025-01-01", "2025-02-01", "2025-03-01", "2025-01-05",
        ]),
        "category": ["Subs", "Subs", "Subs", "Food"],
        "sub_category": ["streaming", "streaming", "streaming", ""],
    })
    result = repo.detect_recurring_transactions(df, min_occurrences=2)
    assert len(result) == 1
    assert result[0]["description"] == "Netflix"
    assert result[0]["occurrences"] == 3
    assert result[0]["frequency"] == "monthly"
