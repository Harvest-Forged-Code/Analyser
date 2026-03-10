"""Unit tests for RecurringModel database operations.

Tests cover CRUD operations for recurring transactions and anomalies
using an in-memory SQLite database via tmp_path fixtures.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.recurring.models import (
    RecurringAnomaly,
    RecurringModel,
    RecurringTransaction,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def model(tmp_path: Path) -> RecurringModel:
    """Create a RecurringModel backed by a temporary SQLite database."""
    return RecurringModel(db_path=tmp_path / "test.db")


@pytest.fixture
def saved_recurring(model: RecurringModel) -> RecurringTransaction:
    """Save and return a sample recurring transaction."""
    return model.save_recurring(
        description="Netflix",
        expected_amount=15.99,
        amount_variance=0.0,
        frequency="monthly",
        category="Entertainment",
        sub_category="Streaming",
        last_occurrence="2026-02-15",
        next_expected="2026-03-15",
        confidence_score=0.95,
        user_confirmed=False,
        is_expected=True,
        is_active=True,
        detection_method="auto",
    )


# ---------------------------------------------------------------------------
# Helper to save additional recurring transactions
# ---------------------------------------------------------------------------

def _save_spotify(model: RecurringModel) -> RecurringTransaction:
    """Save a Spotify recurring transaction."""
    return model.save_recurring(
        description="Spotify",
        expected_amount=9.99,
        amount_variance=0.0,
        frequency="monthly",
        category="Entertainment",
        sub_category="Music",
        last_occurrence="2026-02-10",
        next_expected="2026-03-10",
        confidence_score=0.90,
        user_confirmed=True,
        is_expected=True,
        is_active=True,
        detection_method="manual",
    )


def _save_gym(model: RecurringModel, *, is_active: bool = True) -> RecurringTransaction:
    """Save a gym membership recurring transaction."""
    return model.save_recurring(
        description="Planet Fitness",
        expected_amount=25.00,
        amount_variance=0.0,
        frequency="monthly",
        category="Health",
        sub_category="Gym",
        last_occurrence="2026-02-01",
        next_expected="2026-03-01",
        confidence_score=0.85,
        user_confirmed=False,
        is_expected=True,
        is_active=is_active,
        detection_method="auto",
    )


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

def test_tables_created_on_init(model: RecurringModel) -> None:
    """Verify both recurring_transactions and recurring_anomalies tables exist."""
    from budget_analyser.core.database import get_connection

    with get_connection(model._db_path) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "ORDER BY name",
        )
        tables = [row["name"] for row in cursor.fetchall()]

    assert "recurring_transactions" in tables
    assert "recurring_anomalies" in tables


# ---------------------------------------------------------------------------
# save_recurring
# ---------------------------------------------------------------------------

def test_save_recurring_inserts_new(
    saved_recurring: RecurringTransaction,
) -> None:
    """Saving a new recurring transaction returns object with correct fields."""
    assert saved_recurring.id is not None
    assert saved_recurring.description == "Netflix"
    assert saved_recurring.expected_amount == 15.99
    assert saved_recurring.amount_variance == 0.0
    assert saved_recurring.frequency == "monthly"
    assert saved_recurring.category == "Entertainment"
    assert saved_recurring.sub_category == "Streaming"
    assert saved_recurring.last_occurrence == "2026-02-15"
    assert saved_recurring.next_expected == "2026-03-15"
    assert saved_recurring.confidence_score == pytest.approx(0.95)
    assert saved_recurring.user_confirmed is False
    assert saved_recurring.is_expected is True
    assert saved_recurring.is_active is True
    assert saved_recurring.detection_method == "auto"


def test_save_recurring_upsert_on_duplicate(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Saving same description+frequency twice upserts rather than duplicating."""
    updated = model.save_recurring(
        description="Netflix",
        expected_amount=19.99,
        amount_variance=1.0,
        frequency="monthly",
        category="Entertainment",
        sub_category="Streaming Premium",
        last_occurrence="2026-03-15",
        next_expected="2026-04-15",
        confidence_score=0.99,
        user_confirmed=True,
        is_expected=True,
        is_active=True,
        detection_method="manual",
    )

    all_records = model.get_all_recurring()
    assert len(all_records) == 1, "Upsert should not create a duplicate"
    assert updated.expected_amount == 19.99
    assert updated.sub_category == "Streaming Premium"


# ---------------------------------------------------------------------------
# get_all_recurring
# ---------------------------------------------------------------------------

def test_get_all_recurring_returns_all(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """get_all_recurring returns all saved records."""
    _save_spotify(model)
    _save_gym(model)

    results = model.get_all_recurring()
    assert len(results) == 3


def test_get_all_recurring_active_only(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """active_only=True filters out inactive records."""
    _save_spotify(model)
    _save_gym(model, is_active=False)

    active = model.get_all_recurring(active_only=True)
    all_records = model.get_all_recurring(active_only=False)

    assert len(all_records) == 3
    assert len(active) == 2
    descriptions = {r.description for r in active}
    assert "Planet Fitness" not in descriptions


# ---------------------------------------------------------------------------
# get_recurring_by_id
# ---------------------------------------------------------------------------

def test_get_recurring_by_id_found(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Retrieving an existing recurring by id returns the correct record."""
    result = model.get_recurring_by_id(saved_recurring.id)

    assert result is not None
    assert result.id == saved_recurring.id
    assert result.description == "Netflix"
    assert result.expected_amount == 15.99


def test_get_recurring_by_id_not_found(model: RecurringModel) -> None:
    """Querying a non-existent id returns None."""
    result = model.get_recurring_by_id(9999)
    assert result is None


# ---------------------------------------------------------------------------
# update_recurring
# ---------------------------------------------------------------------------

def test_update_recurring_partial_fields(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Updating only specific fields leaves other fields unchanged."""
    updated = model.update_recurring(
        saved_recurring.id,
        description="Netflix Premium",
        expected_amount=22.99,
    )

    assert updated is not None
    assert updated.description == "Netflix Premium"
    assert updated.expected_amount == 22.99
    # Unchanged fields
    assert updated.frequency == "monthly"
    assert updated.category == "Entertainment"
    assert updated.sub_category == "Streaming"
    assert updated.confidence_score == pytest.approx(0.95)


def test_update_recurring_not_found(model: RecurringModel) -> None:
    """Updating a non-existent id returns None."""
    result = model.update_recurring(
        9999,
        description="Ghost",
    )
    assert result is None


# ---------------------------------------------------------------------------
# confirm_recurring / dismiss_recurring
# ---------------------------------------------------------------------------

def test_confirm_recurring_sets_confirmed(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Confirming a recurring transaction sets user_confirmed to True."""
    assert saved_recurring.user_confirmed is False

    confirmed = model.confirm_recurring(saved_recurring.id)

    assert confirmed is not None
    assert confirmed.user_confirmed is True
    assert confirmed.is_active is True  # should remain active


def test_dismiss_recurring_sets_inactive(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Dismissing a recurring transaction sets is_active to False."""
    assert saved_recurring.is_active is True

    dismissed = model.dismiss_recurring(saved_recurring.id)

    assert dismissed is not None
    assert dismissed.is_active is False


# ---------------------------------------------------------------------------
# delete_recurring
# ---------------------------------------------------------------------------

def test_delete_recurring_removes_record(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Deleting an existing record removes it from the database."""
    result = model.delete_recurring(saved_recurring.id)

    assert result is True
    assert model.get_recurring_by_id(saved_recurring.id) is None
    assert len(model.get_all_recurring()) == 0


def test_delete_recurring_not_found(model: RecurringModel) -> None:
    """Deleting a non-existent id returns False."""
    result = model.delete_recurring(9999)
    assert result is False


# ---------------------------------------------------------------------------
# save_anomaly
# ---------------------------------------------------------------------------

def test_save_anomaly_creates_record(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Saving an anomaly returns a complete RecurringAnomaly object."""
    anomaly = model.save_anomaly(
        recurring_id=saved_recurring.id,
        anomaly_type="missed_payment",
        expected_date="2026-03-15",
        actual_date=None,
        expected_amount=15.99,
        actual_amount=None,
        severity="warning",
        message="Netflix payment was not detected on expected date",
    )

    assert anomaly.id is not None
    assert anomaly.recurring_id == saved_recurring.id
    assert anomaly.anomaly_type == "missed_payment"
    assert anomaly.expected_date == "2026-03-15"
    assert anomaly.actual_date is None
    assert anomaly.expected_amount == 15.99
    assert anomaly.actual_amount is None
    assert anomaly.severity == "warning"
    assert anomaly.message == "Netflix payment was not detected on expected date"
    assert anomaly.resolved is False
    assert anomaly.detected_at is not None


# ---------------------------------------------------------------------------
# get_anomalies
# ---------------------------------------------------------------------------

def _create_test_anomalies(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> list[RecurringAnomaly]:
    """Create multiple anomalies for testing filter operations."""
    a1 = model.save_anomaly(
        recurring_id=saved_recurring.id,
        anomaly_type="missed_payment",
        expected_date="2026-02-15",
        actual_date=None,
        expected_amount=15.99,
        actual_amount=None,
        severity="warning",
        message="Missed Netflix payment in February",
    )
    a2 = model.save_anomaly(
        recurring_id=saved_recurring.id,
        anomaly_type="amount_spike",
        expected_date="2026-01-15",
        actual_date="2026-01-16",
        expected_amount=15.99,
        actual_amount=22.99,
        severity="info",
        message="Netflix charged more than expected",
    )
    return [a1, a2]


def test_get_anomalies_all(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """get_anomalies with no filters returns all anomalies."""
    _create_test_anomalies(model, saved_recurring)

    anomalies = model.get_anomalies()
    assert len(anomalies) == 2


def test_get_anomalies_by_recurring_id(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """get_anomalies filters correctly by recurring_id."""
    _create_test_anomalies(model, saved_recurring)

    # Create a second recurring and add an anomaly for it
    spotify = _save_spotify(model)
    model.save_anomaly(
        recurring_id=spotify.id,
        anomaly_type="missed_payment",
        expected_date="2026-03-10",
        actual_date=None,
        expected_amount=9.99,
        actual_amount=None,
        severity="critical",
        message="Spotify payment missed",
    )

    netflix_anomalies = model.get_anomalies(
        recurring_id=saved_recurring.id,
    )
    spotify_anomalies = model.get_anomalies(
        recurring_id=spotify.id,
    )
    all_anomalies = model.get_anomalies()

    assert len(netflix_anomalies) == 2
    assert len(spotify_anomalies) == 1
    assert len(all_anomalies) == 3


def test_get_anomalies_unresolved_only(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """unresolved_only=True filters out resolved anomalies."""
    anomalies = _create_test_anomalies(model, saved_recurring)

    # Resolve the first anomaly
    model.resolve_anomaly(anomalies[0].id)

    unresolved = model.get_anomalies(unresolved_only=True)
    all_anomalies = model.get_anomalies(unresolved_only=False)

    assert len(all_anomalies) == 2
    assert len(unresolved) == 1
    assert unresolved[0].anomaly_type == "amount_spike"


# ---------------------------------------------------------------------------
# resolve_anomaly
# ---------------------------------------------------------------------------

def test_resolve_anomaly_sets_resolved(
    model: RecurringModel,
    saved_recurring: RecurringTransaction,
) -> None:
    """Resolving an anomaly sets its resolved flag to True."""
    anomaly = model.save_anomaly(
        recurring_id=saved_recurring.id,
        anomaly_type="missed_payment",
        expected_date="2026-03-15",
        actual_date=None,
        expected_amount=15.99,
        actual_amount=None,
        severity="warning",
        message="Missed payment",
    )
    assert anomaly.resolved is False

    result = model.resolve_anomaly(anomaly.id)
    assert result is True

    # Verify via get_anomalies
    all_anomalies = model.get_anomalies()
    assert len(all_anomalies) == 1
    assert all_anomalies[0].resolved is True


def test_resolve_anomaly_not_found(model: RecurringModel) -> None:
    """Resolving a non-existent anomaly returns False."""
    result = model.resolve_anomaly(9999)
    assert result is False
