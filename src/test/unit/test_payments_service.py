"""Unit tests for payments reconciliation service."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from budget_analyser.features.payments.service import (
    PaymentReconciliationService,
)


@pytest.fixture()
def _create_db(tmp_path: Path):
    """Create a test DB and return (db_path, insert helper)."""
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
    conn.commit()

    def insert(rows: list[tuple]) -> None:
        conn_inner = sqlite3.connect(str(db_path))
        conn_inner.executemany(
            """INSERT INTO transactions
            (transaction_date, description, amount, from_account,
             sub_category, category, c_or_d)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        conn_inner.commit()
        conn_inner.close()

    conn.close()
    return db_path, insert


class TestPaymentReconciliationService:
    """Tests for PaymentReconciliationService."""

    def test_exact_amount_matching(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Payment Received", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 1
        assert len(summary.pending_payments) == 0
        assert summary.matched_pairs[0].amount == 500.0
        assert summary.matched_pairs[0].source_account == "checking"
        assert summary.matched_pairs[0].destination_account == "visa"
        assert summary.match_rate == 100.0

    def test_date_proximity_tiebreaker(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-20", "Payment Received", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
            ("2026-01-16", "Payment Received", 500.0, "amex",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 1
        # Should match the closer date (amex on 2026-01-16)
        assert summary.matched_pairs[0].destination_account == "amex"
        # The other confirmation should be pending
        assert len(summary.pending_payments) == 1

    def test_pending_status_for_unmatched(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 0
        assert len(summary.pending_payments) == 1
        assert summary.pending_payments[0].status == "pending"
        assert summary.match_rate == 0.0

    def test_empty_period_returns_empty_summary(
        self, _create_db,
    ) -> None:
        db_path, _ = _create_db
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-06")

        assert summary.period == "2026-06"
        assert len(summary.matched_pairs) == 0
        assert len(summary.pending_payments) == 0
        assert summary.total_matched == 0.0
        assert summary.total_pending == 0.0
        assert summary.match_rate == 0.0

    def test_match_rate_calculation(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment 1", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Payment Recv 1", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
            ("2026-01-20", "CC Payment 2", -300.0, "checking",
             "payments_made", "payments", "expenditures"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 1
        assert len(summary.pending_payments) == 1
        assert summary.match_rate == 50.0

    def test_single_account_no_pairs(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Payment Received", 500.0, "checking",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        # Same account should NOT match
        assert len(summary.matched_pairs) == 0
        assert len(summary.pending_payments) == 2

    def test_multiple_matched_pairs(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Pay 1", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Recv 1", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
            ("2026-01-20", "CC Pay 2", -300.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-21", "Recv 2", 300.0, "amex",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 2
        assert len(summary.pending_payments) == 0
        assert summary.total_matched == 800.0
        assert summary.match_rate == 100.0

    def test_get_available_periods(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-02-15", "CC Payment", -300.0, "checking",
             "payments_made", "payments", "expenditures"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        periods = svc.get_available_periods()

        assert periods == ["2026-01", "2026-02"]

    def test_get_available_periods_empty(self, _create_db) -> None:
        db_path, _ = _create_db
        svc = PaymentReconciliationService(db_path=db_path)
        periods = svc.get_available_periods()
        assert periods == []

    def test_reconcile_all_periods(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Pay", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Recv", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
            ("2026-02-15", "CC Pay", -300.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-02-16", "Recv", 300.0, "amex",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="ALL")

        assert summary.period == "ALL"
        assert len(summary.matched_pairs) == 2
        assert summary.total_matched == 800.0

    def test_amount_mismatch_no_match(self, _create_db) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Payment", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "Payment Recv", 499.0, "visa",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        assert len(summary.matched_pairs) == 0
        assert len(summary.pending_payments) == 2

    def test_greedy_matching_each_used_once(
        self, _create_db,
    ) -> None:
        db_path, insert = _create_db
        insert([
            ("2026-01-15", "CC Pay 1", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-16", "CC Pay 2", -500.0, "checking",
             "payments_made", "payments", "expenditures"),
            ("2026-01-17", "Recv 1", 500.0, "visa",
             "payment_confirmations", "payments", "earnings"),
        ])
        svc = PaymentReconciliationService(db_path=db_path)
        summary = svc.reconcile(period="2026-01")

        # Only one can match the single confirmation
        assert len(summary.matched_pairs) == 1
        assert len(summary.pending_payments) == 1
        assert summary.match_rate == 50.0
