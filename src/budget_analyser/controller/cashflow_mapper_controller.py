"""Cashflow mapper controller.

Backward-compatibility shim: re-exports from features.mappers.
New code should import from budget_analyser.features.mappers directly.
"""

from budget_analyser.features.mappers import (  # pylint: disable=unused-import  # noqa: F401
    CashflowMapperController,
)
