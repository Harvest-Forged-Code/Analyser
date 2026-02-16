"""Expenses statistics controller.

Backward-compatibility shim: re-exports from features.reporting.
New code should import from budget_analyser.features.reporting directly.
"""

from budget_analyser.features.reporting import (  # pylint: disable=unused-import  # noqa: F401
    ExpensesStatsController,
)
