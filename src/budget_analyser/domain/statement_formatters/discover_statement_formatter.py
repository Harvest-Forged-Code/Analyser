"""Discover statement formatter.

Implements bank-specific adjustments for Discover CSVs.
"""

from __future__ import annotations

from .base_statement_formatter import BaseStatementFormatter


class DiscoverStatementFormatter(BaseStatementFormatter):  # pylint: disable=too-few-public-methods
    """Discover-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # Discover CSV typically reports credits/debits opposite to desired convention.
        self._statement["amount"] = self._statement["amount"] * -1
