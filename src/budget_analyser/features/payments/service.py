"""Payment reconciliation business logic.

Provides ``PaymentReconciliationService`` which auto-detects
matched payment pairs by exact amount across different accounts.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from budget_analyser.features.payments.models import (
    PaymentPair,
    ReconciliationSummary,
    get_payment_transactions,
)


class PaymentReconciliationService:
    """Service for reconciling credit card payments across accounts.

    Matches payments_made (debits from checking) with
    payment_confirmations (credits on credit cards) by exact
    amount, using date proximity as a tiebreaker.

    Example:
        >>> svc = PaymentReconciliationService(
        ...     db_path=Path("budget.db"),
        ... )
        >>> summary = svc.reconcile(period="2026-01")
        >>> summary.match_rate
        100.0
    """

    def __init__(
        self,
        *,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the payment reconciliation service.

        Args:
            db_path: Path to the transactions SQLite database.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.payments.service",
        )

    def reconcile(
        self, *, period: str = "ALL",
    ) -> ReconciliationSummary:
        """Reconcile payment transactions for a period.

        Args:
            period: Year-month string (e.g. "2026-01") or "ALL".

        Returns:
            ReconciliationSummary with matched and pending pairs.
        """
        df = get_payment_transactions(
            db_path=self._db_path,
            period=period,
            logger=self._logger,
        )

        if df.empty:
            return ReconciliationSummary(period=period)

        payments_made = df[
            df["sub_category"] == "payments_made"
        ].copy()
        confirmations = df[
            df["sub_category"] == "payment_confirmations"
        ].copy()

        return self._match_payments(
            period=period,
            payments_made=payments_made,
            confirmations=confirmations,
        )

    def get_available_periods(self) -> list[str]:
        """Get all periods that have payment transactions.

        Returns:
            Sorted list of year-month strings.
        """
        df = get_payment_transactions(
            db_path=self._db_path,
            period="ALL",
            logger=self._logger,
        )

        if df.empty or "transaction_date" not in df.columns:
            return []

        periods = (
            df["transaction_date"]
            .dt.strftime("%Y-%m")
            .dropna()
            .unique()
            .tolist()
        )
        return sorted(periods)

    def _match_payments(
        self,
        *,
        period: str,
        payments_made: pd.DataFrame,
        confirmations: pd.DataFrame,
    ) -> ReconciliationSummary:
        """Match payment pairs using greedy exact-amount matching.

        For each payment_made, finds a confirmation with matching
        absolute amount from a different account. When multiple
        candidates exist, picks the closest by date.

        Args:
            period: The reconciliation period.
            payments_made: DataFrame of payments_made transactions.
            confirmations: DataFrame of payment_confirmations.

        Returns:
            ReconciliationSummary with results.
        """
        matched_pairs: list[PaymentPair] = []
        pending_payments: list[PaymentPair] = []
        used_indices: set[int] = set()

        for _, payment_row in payments_made.iterrows():
            pair = self._try_match_payment(
                payment_row, confirmations, used_indices,
            )
            if pair.status == "matched":
                matched_pairs.append(pair)
            else:
                pending_payments.append(pair)

        self._collect_unmatched_confirmations(
            confirmations, used_indices, pending_payments,
        )

        return self._build_summary(
            period, matched_pairs, pending_payments,
            len(payments_made),
        )

    def _try_match_payment(
        self,
        payment_row: pd.Series,
        confirmations: pd.DataFrame,
        used_indices: set[int],
    ) -> PaymentPair:
        """Attempt to match a single payment to a confirmation.

        Args:
            payment_row: The payment_made transaction row.
            confirmations: All confirmation candidates.
            used_indices: Already-matched confirmation indices.

        Returns:
            PaymentPair with matched or pending status.
        """
        amount = abs(float(payment_row["amount"]))
        account = str(payment_row["from_account"])
        date = payment_row["transaction_date"]
        date_str = _format_date(date)

        match = self._find_best_match(
            payment_amount=amount,
            payment_account=account,
            payment_date=date,
            confirmations=confirmations,
            used_indices=used_indices,
        )

        if match is not None:
            idx, conf_row = match
            used_indices.add(idx)
            return PaymentPair(
                payment_made=payment_row.to_dict(),
                payment_confirmation=conf_row.to_dict(),
                status="matched",
                amount=amount,
                source_account=account,
                destination_account=str(
                    conf_row["from_account"],
                ),
                payment_date=date_str,
                confirmation_date=_format_date(
                    conf_row["transaction_date"],
                ),
            )

        return PaymentPair(
            payment_made=payment_row.to_dict(),
            payment_confirmation=None,
            status="pending",
            amount=amount,
            source_account=account,
            payment_date=date_str,
        )

    @staticmethod
    def _collect_unmatched_confirmations(
        confirmations: pd.DataFrame,
        used_indices: set[int],
        pending_payments: list[PaymentPair],
    ) -> None:
        """Add unmatched confirmations to the pending list.

        Args:
            confirmations: All confirmation transactions.
            used_indices: Indices already matched.
            pending_payments: List to append unmatched items to.
        """
        for idx, conf_row in confirmations.iterrows():
            if idx not in used_indices:
                pending_payments.append(PaymentPair(
                    payment_made=conf_row.to_dict(),
                    payment_confirmation=None,
                    status="pending",
                    amount=abs(float(conf_row["amount"])),
                    source_account=str(
                        conf_row["from_account"],
                    ),
                    payment_date=_format_date(
                        conf_row["transaction_date"],
                    ),
                ))

    def _build_summary(
        self,
        period: str,
        matched_pairs: list[PaymentPair],
        pending_payments: list[PaymentPair],
        total_payments: int,
    ) -> ReconciliationSummary:
        """Build the final reconciliation summary.

        Args:
            period: The reconciliation period.
            matched_pairs: Successfully matched pairs.
            pending_payments: Unmatched payment entries.
            total_payments: Total payments_made count.

        Returns:
            ReconciliationSummary with computed totals.
        """
        total_matched = sum(p.amount for p in matched_pairs)
        total_pending = sum(p.amount for p in pending_payments)
        match_rate = (
            (len(matched_pairs) / total_payments * 100)
            if total_payments > 0
            else 0.0
        )

        self._logger.info(
            "Reconciliation for %s: %d matched, %d pending, "
            "rate=%.1f%%",
            period, len(matched_pairs),
            len(pending_payments), match_rate,
        )

        return ReconciliationSummary(
            period=period,
            matched_pairs=matched_pairs,
            pending_payments=pending_payments,
            total_matched=total_matched,
            total_pending=total_pending,
            match_rate=match_rate,
        )

    def _find_best_match(
        self,
        *,
        payment_amount: float,
        payment_account: str,
        payment_date: object,
        confirmations: pd.DataFrame,
        used_indices: set[int],
    ) -> tuple[int, pd.Series] | None:
        """Find the best matching confirmation for a payment.

        Args:
            payment_amount: Absolute amount to match.
            payment_account: Source account (must differ).
            payment_date: Date of the payment for proximity.
            confirmations: DataFrame of confirmation candidates.
            used_indices: Indices already matched.

        Returns:
            Tuple of (index, row) for best match, or None.
        """
        best_idx: int | None = None
        best_row: pd.Series | None = None
        best_delta: float = float("inf")

        for idx, conf_row in confirmations.iterrows():
            if idx in used_indices:
                continue

            conf_amount = abs(float(conf_row["amount"]))
            conf_account = str(conf_row["from_account"])

            if conf_account == payment_account:
                continue

            if abs(conf_amount - payment_amount) > 0.01:
                continue

            # Date proximity tiebreaker
            try:
                delta = abs(
                    (payment_date - conf_row["transaction_date"])
                    .days
                )
            except (TypeError, AttributeError):
                delta = 0

            if delta < best_delta:
                best_delta = delta
                best_idx = idx
                best_row = conf_row

        if best_idx is not None and best_row is not None:
            return (best_idx, best_row)
        return None


def _format_date(date_val: object) -> str:
    """Format a date value to ISO string.

    Args:
        date_val: A datetime-like value or string.

    Returns:
        ISO date string or empty string.
    """
    if date_val is None or (
        isinstance(date_val, float)
        and pd.isna(date_val)
    ):
        return ""
    if hasattr(date_val, "strftime"):
        return date_val.strftime("%Y-%m-%d")
    return str(date_val)
