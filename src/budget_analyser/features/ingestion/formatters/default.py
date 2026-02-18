"""Default statement formatter.

Used when there are no bank-specific adjustments required.
"""

from __future__ import annotations

from budget_analyser.features.ingestion.formatters.base import (
    BaseStatementFormatter,
)


class DefaultStatementFormatter(BaseStatementFormatter):  # pylint: disable=too-few-public-methods
    """Default formatter for accounts without special rules."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # No-op bank specific formatting.
        return
