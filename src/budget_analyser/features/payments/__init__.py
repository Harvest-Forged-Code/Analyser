"""Payments feature module.

Provides payment matching and reconciliation:
- Match payments with confirmations by amount and date proximity
- Reconciliation summaries comparing payments made vs confirmed
"""

from budget_analyser.features.payments.models import (
    PaymentPair,
    PaymentMatchResult,
    PaymentsReconciliationSummary,
)
from budget_analyser.features.payments.service import (
    PaymentMatchingService,
    PaymentsReconciliationService,
    PaymentsReconciliationController,
    create_payment_matcher,
)

__all__ = [
    "PaymentPair",
    "PaymentMatchResult",
    "PaymentsReconciliationSummary",
    "PaymentMatchingService",
    "PaymentsReconciliationService",
    "PaymentsReconciliationController",
    "create_payment_matcher",
]
