"""Citi statement formatter.

Implements bank-specific adjustments for Citi CSVs.
"""

from __future__ import annotations

from .base_statement_formatter import BaseStatementFormatter


class CitiStatementFormatter(BaseStatementFormatter):
    """Citi-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # Citi CSV typically reports credits/debits opposite to desired convention.
        self._statement["amount"] = self._statement["amount"] * -1
