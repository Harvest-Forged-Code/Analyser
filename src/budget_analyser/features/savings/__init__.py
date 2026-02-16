"""Savings feature module.

Vertical slice owning all layers for savings rate tracking:
models, service, and controller.

Note: This feature has no repository — savings metrics are computed
from transaction data (earnings/expenses DataFrames), not stored
in a dedicated table.
"""

from budget_analyser.features.savings.controller import (
    SavingsController,
)
from budget_analyser.features.savings.models import SavingsMetrics

__all__ = [
    "SavingsController",
    "SavingsMetrics",
]
