"""Default statement formatter.

Used when there are no bank-specific adjustments required.
"""

from __future__ import annotations

from .base_statement_formatter import BaseStatementFormatter


class DefaultStatementFormatter(BaseStatementFormatter):
    """Default formatter for accounts without special rules."""

    def _bank_specific_formatting(self) -> None:  # noqa: D401
        # No-op bank specific formatting.
        return
