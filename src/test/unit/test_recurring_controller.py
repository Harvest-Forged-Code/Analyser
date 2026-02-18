"""Unit tests for recurring service (formerly controller) integration."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.recurring.service import (
    RecurringService,
)
from budget_analyser.features.recurring.models import (
    RecurringModel,
)


@pytest.fixture()
def service(tmp_path: Path) -> RecurringService:
    """Create a service backed by a temporary SQLite database."""
    model = RecurringModel(db_path=tmp_path / "test.db")
    return RecurringService(model=model)


def test_add_and_list(service: RecurringService) -> None:
    service.add_recurring_transaction("Netflix", 15.0, "monthly")
    service.add_recurring_transaction("Rent", 2000.0, "monthly")

    txns = service.get_all_recurring_transactions()
    assert len(txns) == 2


def test_delete(service: RecurringService) -> None:
    rec = service.add_recurring_transaction("Netflix", 15.0)
    assert service.delete_recurring_transaction(rec.id) is True
    assert service.get_all_recurring_transactions() == []


def test_deactivate(service: RecurringService) -> None:
    rec = service.add_recurring_transaction("Netflix", 15.0)
    assert service.deactivate_recurring_transaction(rec.id) is True

    active = service.get_all_recurring_transactions(
        active_only=True,
    )
    assert len(active) == 0


def test_recurring_summary(service: RecurringService) -> None:
    service.add_recurring_transaction("Netflix", 15.0, "monthly")
    service.add_recurring_transaction("Rent", 2000.0, "monthly")

    summary = service.get_recurring_summary(pd.DataFrame())
    assert summary["monthly_total"] == pytest.approx(2015.0)
    assert summary["count"] == 2


def test_check_anomalies_no_recurring(
    service: RecurringService,
) -> None:
    df = pd.DataFrame({"description": ["test"], "amount": [-10]})
    result = service.check_recurring_anomalies(df)
    assert result == []


def test_detect_recurring(service: RecurringService) -> None:
    df = pd.DataFrame({
        "description": ["Netflix", "Netflix", "Hulu"],
        "amount": [-15.0, -15.0, -12.0],
        "transaction_date": pd.to_datetime([
            "2025-01-01", "2025-02-01", "2025-01-05",
        ]),
        "category": ["Subs", "Subs", "Subs"],
        "sub_category": ["", "", ""],
    })
    detected = service.detect_recurring_transactions(df)
    assert len(detected) == 1
    assert detected[0]["description"] == "Netflix"
