"""Statement formatter public API.

This package separates each behavior class into its own module
while exposing the same import surface.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.formatters.base import (
    BaseStatementFormatter,
    REQUIRED_COLUMNS,
)
from budget_analyser.features.ingestion.formatters.citi import (
    CitiStatementFormatter,
)
from budget_analyser.features.ingestion.formatters.discover import (
    DiscoverStatementFormatter,
)
from budget_analyser.features.ingestion.formatters.default import (
    DefaultStatementFormatter,
)
from budget_analyser.features.ingestion.formatters.factory import (
    create_statement_formatter,
)

__all__ = [
    "BaseStatementFormatter",
    "REQUIRED_COLUMNS",
    "CitiStatementFormatter",
    "DiscoverStatementFormatter",
    "DefaultStatementFormatter",
    "create_statement_formatter",
]
