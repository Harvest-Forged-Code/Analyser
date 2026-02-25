"""Citi statement formatter.

Implements bank-specific adjustments for Citi CSVs.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.formatters.base import (
    BaseStatementFormatter,
)


class CitiStatementFormatter(BaseStatementFormatter):  # pylint: disable=too-few-public-methods
    """Citi-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # Citi CSV reports credits/debits opposite to convention.
        self._statement["amount"] = (
            self._statement["amount"] * -1
        )
