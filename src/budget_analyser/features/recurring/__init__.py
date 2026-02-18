"""Recurring transactions feature module.

Vertical slice owning all layers for recurring transaction management:
models (with persistence), service (with orchestration), and
backward-compat shims for the old repository/controller names.
"""

from budget_analyser.features.recurring.models import (
    RecurringModel,
    RecurringRepository,
    RecurringTransaction,
)
from budget_analyser.features.recurring.service import (
    RecurringController,
    RecurringService,
)

__all__ = [
    "RecurringController",
    "RecurringModel",
    "RecurringRepository",
    "RecurringService",
    "RecurringTransaction",
]
