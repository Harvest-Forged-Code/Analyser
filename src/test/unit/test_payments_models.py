"""Unit tests for payments feature models and DTOs."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from budget_analyser.features.payments.models import (
    PaymentPair,
    ReconciliationSummary,
    get_payment_transactions,
)


class TestPaymentPair:
    """Tests for PaymentPair frozen dataclass."""

    def test_create_matched_pair(self) -> None:
        pair = PaymentPair(
            payment_made={"amount": -500.0, "from_account": "checking"},
            payment_confirmation={"amount": 500.0, "from_account": "visa"},
            status="matched",
            amount=500.0,
            source_account="checking",
            destination_account="visa",
            payment_date="2026-01-15",
            confirmation_date="2026-01-16",
        )
        assert pair.status == "matched"
        assert pair.amount == 500.0
        assert pair.source_account == "checking"
        assert pair.destination_account == "visa"

    def test_create_pending_pair(self) -> None:
        pair = PaymentPair(
            payment_made={"amount": -200.0, "from_account": "checking"},
            payment_confirmation=None,
            status="pending",
            amount=200.0,
            source_account="checking",
        )
        assert pair.status == "pending"
        assert pair.payment_confirmation is None
        assert pair.destination_account is None

    def test_frozen_immutability(self) -> None:
        pair = PaymentPair(
            payment_made={},
            payment_confirmation=None,
            status="pending",
            amount=100.0,
            source_account="checking",
        )
        with pytest.raises(AttributeError):
            pair.status = "matched"  # type: ignore[misc]


class TestReconciliationSummary:
    """Tests for ReconciliationSummary frozen dataclass."""

    def test_empty_summary(self) -> None:
        summary = ReconciliationSummary(period="2026-01")
        assert summary.period == "2026-01"
        assert summary.matched_pairs == []
        assert summary.pending_payments == []
        assert summary.total_matched == 0.0
        assert summary.total_pending == 0.0
        assert summary.match_rate == 0.0

    def test_summary_with_data(self) -> None:
        pair = PaymentPair(
            payment_made={},
            payment_confirmation={},
            status="matched",
            amount=500.0,
            source_account="checking",
            destination_account="visa",
        )
        summary = ReconciliationSummary(
            period="2026-01",
            matched_pairs=[pair],
            total_matched=500.0,
            match_rate=100.0,
        )
        assert len(summary.matched_pairs) == 1
        assert summary.total_matched == 500.0
        assert summary.match_rate == 100.0

    def test_frozen_immutability(self) -> None:
        summary = ReconciliationSummary(period="2026-01")
        with pytest.raises(AttributeError):
            summary.period = "2026-02"  # type: ignore[misc]


class TestGetPaymentTransactions:
    """Tests for get_payment_transactions data access function."""

    @pytest.fixture()
    def db_with_payments(self, tmp_path: Path) -> Path:
        """Create a test DB with payment transactions."""
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                from_account TEXT NOT NULL,
                sub_category TEXT DEFAULT '',
                category TEXT DEFAULT '',
                c_or_d TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.executemany(
            """INSERT INTO transactions
            (transaction_date, description, amount, from_account,
             sub_category, category, c_or_d)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [
                ("2026-01-15", "CC Payment", -500.0, "checking",
                 "payments_made", "payments", "expenditures"),
                ("2026-01-16", "Payment Received", 500.0, "visa",
                 "payment_confirmations", "payments", "earnings"),
                ("2026-02-15", "CC Payment", -300.0, "checking",
                 "payments_made", "payments", "expenditures"),
                ("2026-01-10", "Groceries", -50.0, "visa",
                 "groceries", "food", "expenditures"),
            ],
        )
        conn.commit()
        conn.close()
        return db_path

    def test_get_all_payments(
        self, db_with_payments: Path,
    ) -> None:
        df = get_payment_transactions(
            db_path=db_with_payments, period="ALL",
        )
        assert len(df) == 3
        assert set(df["sub_category"].unique()) == {
            "payments_made", "payment_confirmations",
        }

    def test_get_payments_by_period(
        self, db_with_payments: Path,
    ) -> None:
        df = get_payment_transactions(
            db_path=db_with_payments, period="2026-01",
        )
        assert len(df) == 2

    def test_empty_period(
        self, db_with_payments: Path,
    ) -> None:
        df = get_payment_transactions(
            db_path=db_with_payments, period="2025-06",
        )
        assert df.empty

    def test_excludes_non_payment_transactions(
        self, db_with_payments: Path,
    ) -> None:
        df = get_payment_transactions(
            db_path=db_with_payments, period="ALL",
        )
        assert "groceries" not in df["sub_category"].values

    def test_date_column_is_datetime(
        self, db_with_payments: Path,
    ) -> None:
        df = get_payment_transactions(
            db_path=db_with_payments, period="ALL",
        )
        assert pd.api.types.is_datetime64_any_dtype(
            df["transaction_date"],
        )

    def test_empty_database(self, tmp_path: Path) -> None:
        db_path = tmp_path / "empty.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                from_account TEXT NOT NULL,
                sub_category TEXT DEFAULT '',
                category TEXT DEFAULT '',
                c_or_d TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
        df = get_payment_transactions(
            db_path=db_path, period="ALL",
        )
        assert df.empty
