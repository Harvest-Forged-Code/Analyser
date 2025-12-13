"""Factory for statement formatters.

Selects the appropriate formatter implementation for an account.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from .base_statement_formatter import BaseStatementFormatter
from .citi_statement_formatter import CitiStatementFormatter
from .discover_statement_formatter import DiscoverStatementFormatter
from .default_statement_formatter import DefaultStatementFormatter


def create_statement_formatter(
    *, account_name: str, statement: pd.DataFrame, column_mapping: Mapping[str, str]
) -> BaseStatementFormatter:
    """Factory to create the correct statement formatter for an account.

    Args:
        account_name: Account/bank identifier.
        statement: Raw statement DataFrame.
        column_mapping: Source->desired column mapping.

    Returns:
        A `BaseStatementFormatter` implementation.
    """
    if account_name == "citi":
        return CitiStatementFormatter(
            account_name=account_name, statement=statement, column_mapping=column_mapping
        )
    if account_name == "discover":
        return DiscoverStatementFormatter(
            account_name=account_name, statement=statement, column_mapping=column_mapping
        )

    return DefaultStatementFormatter(
        account_name=account_name, statement=statement, column_mapping=column_mapping
    )
