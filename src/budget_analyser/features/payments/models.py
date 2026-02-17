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

    Represents a successful match between a payment made and its
    confirmation transaction, including the confidence score.

    Attributes:
        payment_made_id: Index of the payment made transaction.
        payment_confirmed_id: Index of the confirmation.
        amount: The matched amount (absolute value).
        payment_date: Date of the payment made.
        confirmation_date: Date of the confirmation.
        days_apart: Days between payment and confirmation.
        confidence: Match confidence score (0.0-1.0).

    Example:
        >>> from datetime import datetime
        >>> from budget_analyser.features.payments.models import (
        ...     PaymentPair,
        ... )
        >>> pair = PaymentPair(
        ...     payment_made_id=0,
        ...     payment_confirmed_id=5,
        ...     amount=150.00,
        ...     payment_date=datetime(2025, 1, 10),
        ...     confirmation_date=datetime(2025, 1, 12),
        ...     days_apart=2,
        ...     confidence=0.95,
        ... )
        >>> pair.net_amount
        0.0
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
        """Return net amount (0 for perfect match).

        Returns:
            Always ``0.0`` because matched pairs have equal
            payment and confirmation amounts.
        """
        return 0.0


@dataclass
class PaymentMatchResult:
    """Result of payment matching analysis.

    Contains matched pairs and any unmatched payments or
    confirmations remaining after the matching process.

    Attributes:
        matched_pairs: Successfully matched payment pairs.
        unmatched_payments: Payments without confirmations.
        unmatched_confirmations: Confirmations without payments.

    Example:
        >>> from budget_analyser.features.payments.models import (
        ...     PaymentMatchResult,
        ... )
        >>> result = PaymentMatchResult()
        >>> result.match_rate
        100.0
        >>> result.is_fully_matched
        True
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
        """Calculate match rate as percentage.

        Returns:
            Percentage of payments that were matched (0-100).
            Returns ``100.0`` when there are no payments.
        """
        total = (
            len(self.matched_pairs)
            + len(self.unmatched_payments)
        )
        if total == 0:
            return 100.0
        return (len(self.matched_pairs) / total) * 100

    @property
    def total_matched_amount(self) -> float:
        """Sum of all matched payment amounts.

        Returns:
            Total dollar amount across all matched pairs.
        """
        return sum(pair.amount for pair in self.matched_pairs)

    @property
    def total_unmatched_payment_amount(self) -> float:
        """Sum of unmatched payment amounts.

        Returns:
            Total absolute dollar amount of payments that
            could not be matched to confirmations. Returns
            ``0.0`` if there are no unmatched payments.
        """
        if (self.unmatched_payments.empty
                or "amount" not in self.unmatched_payments.columns):
            return 0.0
        return float(
            self.unmatched_payments["amount"].abs().sum(),
        )

    @property
    def total_unmatched_confirmation_amount(self) -> float:
        """Sum of unmatched confirmation amounts.

        Returns:
            Total absolute dollar amount of confirmations
            that could not be matched to payments. Returns
            ``0.0`` if there are no unmatched confirmations.
        """
        if (self.unmatched_confirmations.empty
                or "amount" not in
                self.unmatched_confirmations.columns):
            return 0.0
        return float(
            self.unmatched_confirmations["amount"].abs().sum(),
        )

    @property
    def is_fully_matched(self) -> bool:
        """Return True if all payments are matched.

        Returns:
            ``True`` when both unmatched DataFrames are empty,
            meaning every payment has a matching confirmation
            and vice versa.
        """
        return (
            self.unmatched_payments.empty
            and self.unmatched_confirmations.empty
        )


@dataclass(frozen=True)
class PaymentsReconciliationSummary:
    """Reconciliation summary for a single month.

    Aggregates payments made and their confirmations for a
    given month, along with computed totals and the net
    difference.

    Attributes:
        period: The month period.
        payments_made: DataFrame of payments made.
        payment_confirmations: DataFrame of confirmations.
        total_payments_made: Total payment amounts.
        total_payment_confirmations: Total confirmation amounts.
        difference: Confirmations minus payments.

    Example:
        >>> import pandas as pd
        >>> from budget_analyser.features.payments.models import (
        ...     PaymentsReconciliationSummary,
        ... )
        >>> summary = PaymentsReconciliationSummary(
        ...     period=pd.Period("2025-01", freq="M"),
        ...     payments_made=pd.DataFrame(),
        ...     payment_confirmations=pd.DataFrame(),
        ...     total_payments_made=500.0,
        ...     total_payment_confirmations=500.0,
        ...     difference=0.0,
        ... )
        >>> summary.difference
        0.0
    """

    period: pd.Period
    payments_made: pd.DataFrame
    payment_confirmations: pd.DataFrame
    total_payments_made: float
    total_payment_confirmations: float
    difference: float
