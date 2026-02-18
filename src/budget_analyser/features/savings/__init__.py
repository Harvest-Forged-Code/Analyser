"""Savings feature module.

Vertical slice owning all layers for savings rate tracking:
models and service.

Note: This feature has no repository — savings metrics are computed
from transaction data (earnings/expenses DataFrames), not stored
in a dedicated table.
"""

from budget_analyser.features.savings.models import SavingsMetrics
from budget_analyser.features.savings.service import (
    SavingsController,
    SavingsService,
)

__all__ = [
    "SavingsController",
    "SavingsMetrics",
    "SavingsService",
]
