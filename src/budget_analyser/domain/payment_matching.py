"""Payment matching service (domain logic).

Purpose:
    Match credit card payments with their confirmations based on:
    - Amount matching (exact or near-exact)
    - Date proximity (within configurable business days)

This helps reconcile payments across accounts and identify
unmatched payments that may need attention.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd


@dataclass(frozen=True)
class PaymentPair:
    """A matched payment pair.

    Attributes:
        payment_made_id: Index of the payment made transaction.
        payment_confirmed_id: Index of the payment confirmation transaction.
        amount: The matched amount (absolute value).
        payment_date: Date of the payment made.
        confirmation_date: Date of the confirmation.
        days_apart: Number of days between payment and confirmation.
        confidence: Match confidence score (0.0-1.0).
    """

    payment_made_id: int
    payment_confirmed_id: int
    amount: float
    payment_date: datetime
    confirmation_date: datetime
    days_apart: int
    confidence: float

    @property
    def net_amount(self) -> float:
        """Return net amount (should be 0 for perfect match)."""
        return 0.0  # Matched pairs have net zero


@dataclass
class PaymentMatchResult:
    """Result of payment matching analysis.

    Attributes:
        matched_pairs: List of successfully matched payment pairs.
        unmatched_payments: DataFrame of payments without matching confirmations.
        unmatched_confirmations: DataFrame of confirmations without matching payments.
        match_rate: Percentage of payments successfully matched.
        total_matched_amount: Sum of matched payment amounts.
        total_unmatched_payment_amount: Sum of unmatched payment amounts.
        total_unmatched_confirmation_amount: Sum of unmatched confirmation amounts.
    """

    matched_pairs: list[PaymentPair] = field(default_factory=list)
    unmatched_payments: pd.DataFrame = field(default_factory=pd.DataFrame)
    unmatched_confirmations: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def match_rate(self) -> float:
        """Calculate match rate as percentage."""
        total_payments = len(self.matched_pairs) + len(self.unmatched_payments)
        if total_payments == 0:
            return 100.0
        return (len(self.matched_pairs) / total_payments) * 100

    @property
    def total_matched_amount(self) -> float:
        """Sum of all matched payment amounts."""
        return sum(pair.amount for pair in self.matched_pairs)

    @property
    def total_unmatched_payment_amount(self) -> float:
        """Sum of unmatched payment amounts."""
        if self.unmatched_payments.empty or "amount" not in self.unmatched_payments.columns:
            return 0.0
        return float(self.unmatched_payments["amount"].abs().sum())

    @property
    def total_unmatched_confirmation_amount(self) -> float:
        """Sum of unmatched confirmation amounts."""
        if (self.unmatched_confirmations.empty or
                "amount" not in self.unmatched_confirmations.columns):
            return 0.0
        return float(self.unmatched_confirmations["amount"].abs().sum())

    @property
    def is_fully_matched(self) -> bool:
        """Return True if all payments are matched."""
        return (self.unmatched_payments.empty and
                self.unmatched_confirmations.empty)


class PaymentMatchingService:
    """Service to match payments with their confirmations.

    Uses amount and date proximity to find matching pairs.
    """

    def __init__(
        self,
        *,
        max_days_apart: int = 5,
        amount_tolerance: float = 0.01,
    ) -> None:
        """Initialize the payment matching service.

        Args:
            max_days_apart: Maximum days between payment and confirmation.
            amount_tolerance: Maximum difference in amounts to consider a match.
        """
        self._max_days_apart = max_days_apart
        self._amount_tolerance = amount_tolerance

    def match_payments(
        self,
        *,
        payments_made: pd.DataFrame,
        payment_confirmations: pd.DataFrame,
    ) -> PaymentMatchResult:
        """Match payments with confirmations.

        Args:
            payments_made: DataFrame of payment transactions.
            payment_confirmations: DataFrame of confirmation transactions.

        Returns:
            PaymentMatchResult with matched pairs and unmatched transactions.
        """
        result = PaymentMatchResult()

        if payments_made.empty or payment_confirmations.empty:
            result.unmatched_payments = payments_made.copy()
            result.unmatched_confirmations = payment_confirmations.copy()
            return result

        # Ensure required columns exist
        required_cols = {"amount", "transaction_date"}
        for df in (payments_made, payment_confirmations):
            missing = required_cols - set(df.columns)
            if missing:
                # Return unmatched if missing required columns
                result.unmatched_payments = payments_made.copy()
                result.unmatched_confirmations = payment_confirmations.copy()
                return result

        # Track which transactions have been matched
        matched_payment_ids: set[int] = set()
        matched_confirmation_ids: set[int] = set()
        pairs: list[PaymentPair] = []

        # Convert dates to datetime for comparison
        pm_dates = pd.to_datetime(payments_made["transaction_date"], errors="coerce")
        pc_dates = pd.to_datetime(payment_confirmations["transaction_date"], errors="coerce")

        # Try to match each payment with a confirmation
        for pm_idx, pm_row in payments_made.iterrows():
            if pm_idx in matched_payment_ids:
                continue

            pm_amount = abs(float(pm_row["amount"]))
            pm_date = pm_dates.loc[pm_idx]

            if pd.isna(pm_date):
                continue

            best_match = None
            best_score = 0.0

            for pc_idx, pc_row in payment_confirmations.iterrows():
                if pc_idx in matched_confirmation_ids:
                    continue

                pc_amount = abs(float(pc_row["amount"]))
                pc_date = pc_dates.loc[pc_idx]

                if pd.isna(pc_date):
                    continue

                # Check amount match
                amount_diff = abs(pm_amount - pc_amount)
                if amount_diff > self._amount_tolerance:
                    continue

                # Check date proximity
                days_apart = abs((pc_date - pm_date).days)
                if days_apart > self._max_days_apart:
                    continue

                # Calculate match confidence
                # Higher confidence for closer dates and exact amounts
                date_score = 1.0 - (days_apart / (self._max_days_apart + 1))
                amount_score = 1.0 - (amount_diff / (self._amount_tolerance + 0.001))
                confidence = date_score * 0.6 + amount_score * 0.4

                if confidence > best_score:
                    best_score = confidence
                    best_match = (pc_idx, pc_row, pc_date, days_apart)

            if best_match is not None:
                pc_idx, pc_row, pc_date, days_apart = best_match
                matched_payment_ids.add(pm_idx)
                matched_confirmation_ids.add(pc_idx)

                pairs.append(PaymentPair(
                    payment_made_id=pm_idx,
                    payment_confirmed_id=pc_idx,
                    amount=pm_amount,
                    payment_date=pm_date.to_pydatetime(),
                    confirmation_date=pc_date.to_pydatetime(),
                    days_apart=days_apart,
                    confidence=best_score,
                ))

        result.matched_pairs = pairs
        result.unmatched_payments = payments_made.loc[
            ~payments_made.index.isin(matched_payment_ids)
        ].copy()
        result.unmatched_confirmations = payment_confirmations.loc[
            ~payment_confirmations.index.isin(matched_confirmation_ids)
        ].copy()

        return result

    def find_potential_matches(
        self,
        *,
        transaction: pd.Series,
        candidates: pd.DataFrame,
    ) -> list[tuple[int, float]]:
        """Find potential matches for a single transaction.

        Args:
            transaction: The transaction to match.
            candidates: DataFrame of potential matching transactions.

        Returns:
            List of (candidate_index, confidence_score) tuples.
        """
        if candidates.empty:
            return []

        if "amount" not in transaction.index or "transaction_date" not in transaction.index:
            return []

        tx_amount = abs(float(transaction["amount"]))
        tx_date = pd.to_datetime(transaction["transaction_date"])

        if pd.isna(tx_date):
            return []

        matches = []
        candidate_dates = pd.to_datetime(candidates["transaction_date"], errors="coerce")

        for idx, row in candidates.iterrows():
            cand_amount = abs(float(row["amount"]))
            cand_date = candidate_dates.loc[idx]

            if pd.isna(cand_date):
                continue

            # Check amount
            amount_diff = abs(tx_amount - cand_amount)
            if amount_diff > self._amount_tolerance:
                continue

            # Check date
            days_apart = abs((cand_date - tx_date).days)
            if days_apart > self._max_days_apart:
                continue

            # Calculate confidence
            date_score = 1.0 - (days_apart / (self._max_days_apart + 1))
            amount_score = 1.0 - (amount_diff / (self._amount_tolerance + 0.001))
            confidence = date_score * 0.6 + amount_score * 0.4

            matches.append((idx, confidence))

        return sorted(matches, key=lambda x: x[1], reverse=True)


def create_payment_matcher(
    *,
    max_days_apart: int = 5,
    amount_tolerance: float = 0.01,
) -> PaymentMatchingService:
    """Factory function to create a payment matching service.

    Args:
        max_days_apart: Maximum days between payment and confirmation.
        amount_tolerance: Maximum amount difference for a match.

    Returns:
        Configured PaymentMatchingService instance.
    """
    return PaymentMatchingService(
        max_days_apart=max_days_apart,
        amount_tolerance=amount_tolerance,
    )
