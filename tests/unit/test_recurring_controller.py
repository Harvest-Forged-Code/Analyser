"""Unit tests for recurring controller integration."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from budget_analyser.features.recurring.controller import (
    RecurringController,
)
from budget_analyser.features.recurring.repository import (
    RecurringRepository,
)


@pytest.fixture()
def controller(tmp_path: Path) -> RecurringController:
    """Create a controller backed by a temporary SQLite database."""
    repo = RecurringRepository(db_path=tmp_path / "test.db")
    return RecurringController(repository=repo)


def test_add_and_list(controller: RecurringController) -> None:
    controller.add_recurring_transaction("Netflix", 15.0, "monthly")
    controller.add_recurring_transaction("Rent", 2000.0, "monthly")

    txns = controller.get_all_recurring_transactions()
    assert len(txns) == 2


def test_delete(controller: RecurringController) -> None:
    rec = controller.add_recurring_transaction("Netflix", 15.0)
    assert controller.delete_recurring_transaction(rec.id) is True
    assert controller.get_all_recurring_transactions() == []


def test_deactivate(controller: RecurringController) -> None:
    rec = controller.add_recurring_transaction("Netflix", 15.0)
    assert controller.deactivate_recurring_transaction(rec.id) is True

    active = controller.get_all_recurring_transactions(
        active_only=True,
    )
    assert len(active) == 0


def test_recurring_summary(controller: RecurringController) -> None:
    controller.add_recurring_transaction("Netflix", 15.0, "monthly")
    controller.add_recurring_transaction("Rent", 2000.0, "monthly")

    summary = controller.get_recurring_summary(pd.DataFrame())
    assert summary["monthly_total"] == pytest.approx(2015.0)
    assert summary["count"] == 2


def test_check_anomalies_no_recurring(
    controller: RecurringController,
) -> None:
    df = pd.DataFrame({"description": ["test"], "amount": [-10]})
    result = controller.check_recurring_anomalies(df)
    assert result == []


def test_detect_recurring(controller: RecurringController) -> None:
    df = pd.DataFrame({
        "description": ["Netflix", "Netflix", "Hulu"],
        "amount": [-15.0, -15.0, -12.0],
        "transaction_date": pd.to_datetime([
            "2025-01-01", "2025-02-01", "2025-01-05",
        ]),
        "category": ["Subs", "Subs", "Subs"],
        "sub_category": ["", "", ""],
    })
    detected = controller.detect_recurring_transactions(df)
    assert len(detected) == 1
    assert detected[0]["description"] == "Netflix"
