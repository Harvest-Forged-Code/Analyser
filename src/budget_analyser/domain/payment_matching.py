"""Payment matching service (domain logic).

Backward-compatibility shim: re-exports from features.payments.
New code should import from budget_analyser.features.payments directly.
"""

from budget_analyser.features.payments import (  # pylint: disable=unused-import  # noqa: F401
    PaymentPair,
    PaymentMatchResult,
    PaymentMatchingService,
    create_payment_matcher,
)
