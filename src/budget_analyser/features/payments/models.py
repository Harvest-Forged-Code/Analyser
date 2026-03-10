"""Payment reconciliation DTOs and data access.

Contains frozen dataclasses for payment pair matching and
a data access function for querying payment transactions.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from budget_analyser.core.database import get_connection


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PaymentPair:  # pylint: disable=too-many-instance-attributes
    """A matched or pending payment pair.

    Attributes:
        payment_made: Transaction record dict for the debit side.
        payment_confirmation: Transaction record dict for the
            credit side, or None if unmatched.
        status: Reconciliation status: "matched" or "pending".
        amount: Absolute payment amount.
        source_account: Account that made the payment.
        destination_account: Account that received the payment,
            or None if unmatched.
        payment_date: Date of the payment made transaction.
        confirmation_date: Date of the confirmation, or None.
    """

    payment_made: dict[str, object]
    payment_confirmation: dict[str, object] | None
    status: str
    amount: float
    source_account: str
    destination_account: str | None = None
    payment_date: str = ""
    confirmation_date: str | None = None


@dataclass(frozen=True)
class ReconciliationSummary:
    """Summary of payment reconciliation for a period.

    Attributes:
        period: Year-month string (e.g. "2026-01") or "ALL".
        matched_pairs: List of matched payment pairs.
        pending_payments: List of unmatched payment pairs.
        total_matched: Total dollar amount of matched payments.
        total_pending: Total dollar amount of pending payments.
        match_rate: Percentage of payments successfully matched.
    """

    period: str
    matched_pairs: list[PaymentPair] = field(default_factory=list)
    pending_payments: list[PaymentPair] = field(default_factory=list)
    total_matched: float = 0.0
    total_pending: float = 0.0
    match_rate: float = 0.0


# ---------------------------------------------------------------------------
# Data access
# ---------------------------------------------------------------------------

def get_payment_transactions(
    *,
    db_path: Path,
    period: str = "ALL",
    logger: logging.Logger | None = None,
) -> pd.DataFrame:
    """Query transactions with payment sub-categories.

    Args:
        db_path: Path to the SQLite database file.
        period: Year-month filter (e.g. "2026-01") or "ALL".
        logger: Optional logger for diagnostics.

    Returns:
        DataFrame with payment transactions filtered by period.
    """
    log = logger or logging.getLogger(
        "budget_analyser.features.payments.models",
    )

    base_query = """
    SELECT transaction_date, description, amount,
           from_account, sub_category, category, c_or_d
    FROM transactions
    WHERE sub_category IN ('payments_made', 'payment_confirmations')
    """

    params: tuple[str, ...] = ()
    if period != "ALL":
        base_query += (
            " AND strftime('%Y-%m', transaction_date) = ?"
        )
        params = (period,)

    base_query += " ORDER BY transaction_date"

    try:
        with get_connection(db_path) as conn:
            df = pd.read_sql_query(base_query, conn, params=params)
    except (OSError, sqlite3.Error):
        log.exception("Error querying payment transactions")
        return pd.DataFrame()

    if not df.empty and "transaction_date" in df.columns:
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"],
            format="mixed",
            errors="coerce",
        )

    log.info(
        "Loaded %d payment transactions for period=%s",
        len(df), period,
    )
    return df
