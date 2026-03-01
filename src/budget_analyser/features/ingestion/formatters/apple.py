"""Apple Card statement formatter.

Implements bank-specific adjustments for Apple Card CSVs.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.formatters.base import (
    BaseStatementFormatter,
)


class AppleStatementFormatter(BaseStatementFormatter):  # pylint: disable=too-few-public-methods
    """Apple Card-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # Apple CSV reports purchases as positive, payments as negative.
        self._statement["amount"] = (
            self._statement["amount"] * -1
        )
