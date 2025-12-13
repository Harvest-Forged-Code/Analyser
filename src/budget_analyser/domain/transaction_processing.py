"""Transaction processing facades.

This module preserves the public API by re-exporting symbols while enforcing
one-class-per-file for behavior classes.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from budget_analyser.domain.category_mappers import CategoryMappers
from budget_analyser.domain.transaction_processor import TransactionProcessor


__all__ = ["CategoryMappers", "TransactionProcessor"]
