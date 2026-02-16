"""Payment matching service (business logic).

Matches credit card payments with their confirmations based on:
- Amount matching (exact or near-exact)
- Date proximity (within configurable business days)
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.payments.models import (
    PaymentMatchResult,
    PaymentPair,
)


class PaymentMatchingService:
    """Service to match payments with their confirmations."""

    def __init__(
        self,
        *,
        max_days_apart: int = 5,
        amount_tolerance: float = 0.01,
    ) -> None:
        """Initialize the payment matching service.

        Args:
            max_days_apart: Maximum days between payment and
                confirmation.
            amount_tolerance: Maximum difference in amounts.
        """
        self._max_days_apart = max_days_apart
        self._amount_tolerance = amount_tolerance

    def match_payments(  # pylint: disable=too-many-locals
        self,
        *,
        payments_made: pd.DataFrame,
        payment_confirmations: pd.DataFrame,
    ) -> PaymentMatchResult:
        """Match payments with confirmations.

        Args:
            payments_made: DataFrame of payment transactions.
            payment_confirmations: DataFrame of confirmations.

        Returns:
            PaymentMatchResult with matched and unmatched items.
        """
        if not self._has_required_columns(
            payments_made, payment_confirmations,
        ):
            return PaymentMatchResult(
                unmatched_payments=payments_made.copy(),
                unmatched_confirmations=(
                    payment_confirmations.copy()
                ),
            )

        matched_payment_ids: set[int] = set()
        matched_confirmation_ids: set[int] = set()
        pairs: list[PaymentPair] = []

        pm_dates = pd.to_datetime(
            payments_made["transaction_date"], errors="coerce",
        )
        pc_dates = pd.to_datetime(
            payment_confirmations["transaction_date"],
            errors="coerce",
        )

        for pm_idx, pm_row in payments_made.iterrows():
            if pm_idx in matched_payment_ids:
                continue

            pm_amount = abs(float(pm_row["amount"]))
            pm_date = pm_dates.loc[pm_idx]
            if pd.isna(pm_date):
                continue

            match = self._find_best_confirmation(
                pm_amount, pm_date, payment_confirmations,
                conf_dates=pc_dates,
                already_matched=matched_confirmation_ids,
            )
            if match is None:
                continue

            pc_idx, pc_date, days_apart, score = match
            matched_payment_ids.add(pm_idx)
            matched_confirmation_ids.add(pc_idx)
            pairs.append(PaymentPair(
                payment_made_id=pm_idx,
                payment_confirmed_id=pc_idx,
                amount=pm_amount,
                payment_date=pm_date.to_pydatetime(),
                confirmation_date=pc_date.to_pydatetime(),
                days_apart=days_apart,
                confidence=score,
            ))

        return PaymentMatchResult(
            matched_pairs=pairs,
            unmatched_payments=payments_made.loc[
                ~payments_made.index.isin(matched_payment_ids)
            ].copy(),
            unmatched_confirmations=(
                payment_confirmations.loc[
                    ~payment_confirmations.index.isin(
                        matched_confirmation_ids,
                    )
                ].copy()
            ),
        )

    @staticmethod
    def _has_required_columns(
        *dataframes: pd.DataFrame,
    ) -> bool:
        """Return True if all DataFrames have required columns."""
        required = {"amount", "transaction_date"}
        return all(
            not df.empty and required.issubset(df.columns)
            for df in dataframes
        )

    def _find_best_confirmation(
        self,
        pm_amount: float,
        pm_date: object,
        confirmations: pd.DataFrame,
        *,
        conf_dates: pd.Series,
        already_matched: set[int],
    ) -> tuple[int, object, int, float] | None:
        """Find the best matching confirmation for a payment."""
        best_match = None
        best_score = 0.0

        for pc_idx, pc_row in confirmations.iterrows():
            if pc_idx in already_matched:
                continue

            pc_date = conf_dates.loc[pc_idx]
            if pd.isna(pc_date):
                continue

            score = self._calculate_confidence(
                pm_amount, pm_date,
                abs(float(pc_row["amount"])), pc_date,
            )
            if score is not None and score > best_score:
                best_score = score
                best_match = (
                    pc_idx, pc_date,
                    abs((pc_date - pm_date).days), score,
                )

        return best_match

    def _calculate_confidence(
        self,
        amount_a: float,
        date_a: object,
        amount_b: float,
        date_b: object,
    ) -> float | None:
        """Calculate match confidence between two transactions.

        Returns None if the transactions are not within tolerances.
        """
        amount_diff = abs(amount_a - amount_b)
        if amount_diff > self._amount_tolerance:
            return None

        days_apart = abs((date_b - date_a).days)
        if days_apart > self._max_days_apart:
            return None

        date_score = 1.0 - (
            days_apart / (self._max_days_apart + 1)
        )
        amount_score = 1.0 - (
            amount_diff / (self._amount_tolerance + 0.001)
        )
        return date_score * 0.6 + amount_score * 0.4

    def find_potential_matches(
        self,
        *,
        transaction: pd.Series,
        candidates: pd.DataFrame,
    ) -> list[tuple[int, float]]:
        """Find potential matches for a single transaction.

        Args:
            transaction: The transaction to match.
            candidates: DataFrame of potential matches.

        Returns:
            List of (candidate_index, confidence_score) tuples.
        """
        if candidates.empty:
            return []

        required = {"amount", "transaction_date"}
        if not required.issubset(transaction.index):
            return []

        tx_amount = abs(float(transaction["amount"]))
        tx_date = pd.to_datetime(
            transaction["transaction_date"],
        )
        if pd.isna(tx_date):
            return []

        matches: list[tuple[int, float]] = []
        candidate_dates = pd.to_datetime(
            candidates["transaction_date"], errors="coerce",
        )

        for idx, row in candidates.iterrows():
            cand_date = candidate_dates.loc[idx]
            if pd.isna(cand_date):
                continue

            confidence = self._calculate_confidence(
                tx_amount, tx_date,
                abs(float(row["amount"])), cand_date,
            )
            if confidence is not None:
                matches.append((idx, confidence))

        return sorted(matches, key=lambda x: x[1], reverse=True)


def create_payment_matcher(
    *,
    max_days_apart: int = 5,
    amount_tolerance: float = 0.01,
) -> PaymentMatchingService:
    """Factory function to create a payment matching service.

    Args:
        max_days_apart: Maximum days between payment and
            confirmation.
        amount_tolerance: Maximum amount difference for a match.

    Returns:
        Configured PaymentMatchingService instance.
    """
    return PaymentMatchingService(
        max_days_apart=max_days_apart,
        amount_tolerance=amount_tolerance,
    )
