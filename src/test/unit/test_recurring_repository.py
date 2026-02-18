"""Unit tests for recurring model (formerly repository) CRUD operations."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.recurring.models import (
    RecurringModel,
)


@pytest.fixture()
def model(tmp_path: Path) -> RecurringModel:
    """Create a model backed by a temporary SQLite database."""
    return RecurringModel(db_path=tmp_path / "test.db")


def test_add_recurring_transaction(
    model: RecurringModel,
) -> None:
    rec = model.add_recurring_transaction(
        "Netflix", 15.99, "monthly", "Subs", "streaming",
    )
    assert rec.id is not None
    assert rec.description == "Netflix"
    assert rec.expected_amount == 15.99
    assert rec.frequency == "monthly"


def test_get_all_empty(model: RecurringModel) -> None:
    assert model.get_all_recurring_transactions() == []


def test_get_all_returns_sorted(
    model: RecurringModel,
) -> None:
    model.add_recurring_transaction("Rent", 2000.0)
    model.add_recurring_transaction("Netflix", 15.0)

    txns = model.get_all_recurring_transactions()
    assert len(txns) == 2
    assert txns[0].description == "Netflix"
    assert txns[1].description == "Rent"


def test_get_active_only_filters(
    model: RecurringModel,
) -> None:
    rec = model.add_recurring_transaction("Netflix", 15.0)
    model.add_recurring_transaction("Rent", 2000.0)
    model.deactivate_recurring_transaction(rec.id)

    active = model.get_all_recurring_transactions(active_only=True)
    assert len(active) == 1
    assert active[0].description == "Rent"

    all_txns = model.get_all_recurring_transactions(active_only=False)
    assert len(all_txns) == 2


def test_deactivate_recurring(
    model: RecurringModel,
) -> None:
    rec = model.add_recurring_transaction("Netflix", 15.0)
    assert model.deactivate_recurring_transaction(rec.id) is True


def test_deactivate_nonexistent_returns_false(
    model: RecurringModel,
) -> None:
    assert model.deactivate_recurring_transaction(9999) is False


def test_delete_recurring(model: RecurringModel) -> None:
    rec = model.add_recurring_transaction("Netflix", 15.0)
    assert model.delete_recurring_transaction(rec.id) is True
    assert model.get_all_recurring_transactions() == []


def test_delete_nonexistent_returns_false(
    model: RecurringModel,
) -> None:
    assert model.delete_recurring_transaction(9999) is False


def test_upsert_on_conflict(model: RecurringModel) -> None:
    model.add_recurring_transaction(
        "Netflix", 15.0, "monthly", "Subs",
    )
    updated = model.add_recurring_transaction(
        "Netflix", 15.0, "yearly", "Entertainment",
    )
    assert updated.frequency == "yearly"
    assert updated.category == "Entertainment"
    assert len(model.get_all_recurring_transactions()) == 1


def test_update_last_occurrence(
    model: RecurringModel,
) -> None:
    rec = model.add_recurring_transaction("Netflix", 15.0)
    result = model.update_last_occurrence(rec.id, "2025-01-15")
    assert result is True

    txns = model.get_all_recurring_transactions()
    assert txns[0].last_occurrence == "2025-01-15"


def test_detect_recurring_empty_df(
    model: RecurringModel,
) -> None:
    result = model.detect_recurring_transactions(pd.DataFrame())
    assert result == []


def test_detect_recurring_finds_patterns(
    model: RecurringModel,
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
    result = model.detect_recurring_transactions(df, min_occurrences=2)
    assert len(result) == 1
    assert result[0]["description"] == "Netflix"
    assert result[0]["occurrences"] == 3
    assert result[0]["frequency"] == "monthly"
