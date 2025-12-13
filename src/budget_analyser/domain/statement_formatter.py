"""Statement formatter facades.

This module preserves the original import path while the implementation lives in
`budget_analyser.domain.statement_formatters` with one behavior class per file.
"""

from __future__ import annotations

from budget_analyser.domain.statement_formatters import (
    BaseStatementFormatter,
    CitiStatementFormatter,
    DefaultStatementFormatter,
    DiscoverStatementFormatter,
    REQUIRED_COLUMNS,
    create_statement_formatter,
)

__all__ = [
    "BaseStatementFormatter",
    "CitiStatementFormatter",
    "DiscoverStatementFormatter",
    "DefaultStatementFormatter",
    "REQUIRED_COLUMNS",
    "create_statement_formatter",
]
