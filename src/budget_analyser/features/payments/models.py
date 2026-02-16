"""Payments feature DTOs.

Data transfer objects for payment matching and reconciliation.
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
        payment_confirmed_id: Index of the confirmation.
        amount: The matched amount (absolute value).
        payment_date: Date of the payment made.
        confirmation_date: Date of the confirmation.
        days_apart: Days between payment and confirmation.
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
        """Return net amount (0 for perfect match)."""
        return 0.0


@dataclass
class PaymentMatchResult:
    """Result of payment matching analysis.

    Attributes:
        matched_pairs: Successfully matched payment pairs.
        unmatched_payments: Payments without confirmations.
        unmatched_confirmations: Confirmations without payments.
    """

    matched_pairs: list[PaymentPair] = field(
        default_factory=list,
    )
    unmatched_payments: pd.DataFrame = field(
        default_factory=pd.DataFrame,
    )
    unmatched_confirmations: pd.DataFrame = field(
        default_factory=pd.DataFrame,
    )

    @property
    def match_rate(self) -> float:
        """Calculate match rate as percentage."""
        total = (
            len(self.matched_pairs)
            + len(self.unmatched_payments)
        )
        if total == 0:
            return 100.0
        return (len(self.matched_pairs) / total) * 100

    @property
    def total_matched_amount(self) -> float:
        """Sum of all matched payment amounts."""
        return sum(pair.amount for pair in self.matched_pairs)

    @property
    def total_unmatched_payment_amount(self) -> float:
        """Sum of unmatched payment amounts."""
        if (self.unmatched_payments.empty
                or "amount" not in self.unmatched_payments.columns):
            return 0.0
        return float(
            self.unmatched_payments["amount"].abs().sum(),
        )

    @property
    def total_unmatched_confirmation_amount(self) -> float:
        """Sum of unmatched confirmation amounts."""
        if (self.unmatched_confirmations.empty
                or "amount" not in
                self.unmatched_confirmations.columns):
            return 0.0
        return float(
            self.unmatched_confirmations["amount"].abs().sum(),
        )

    @property
    def is_fully_matched(self) -> bool:
        """Return True if all payments are matched."""
        return (
            self.unmatched_payments.empty
            and self.unmatched_confirmations.empty
        )


@dataclass(frozen=True)
class PaymentsReconciliationSummary:
    """Reconciliation summary for a single month.

    Attributes:
        period: The month period.
        payments_made: DataFrame of payments made.
        payment_confirmations: DataFrame of confirmations.
        total_payments_made: Total payment amounts.
        total_payment_confirmations: Total confirmation amounts.
        difference: Confirmations minus payments.
    """

    period: pd.Period
    payments_made: pd.DataFrame
    payment_confirmations: pd.DataFrame
    total_payments_made: float
    total_payment_confirmations: float
    difference: float
