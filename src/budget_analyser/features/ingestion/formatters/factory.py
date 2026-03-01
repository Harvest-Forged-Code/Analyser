"""Factory for statement formatters.

Selects the appropriate formatter implementation for an account.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from budget_analyser.features.ingestion.formatters.base import (
    BaseStatementFormatter,
)
from budget_analyser.features.ingestion.formatters.apple import (
    AppleStatementFormatter,
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


def create_statement_formatter(
    *,
    account_name: str,
    statement: pd.DataFrame,
    column_mapping: Mapping[str, str],
) -> BaseStatementFormatter:
    """Create the correct statement formatter for an account.

    Args:
        account_name: Account/bank identifier.
        statement: Raw statement DataFrame.
        column_mapping: Source to desired column mapping.

    Returns:
        A ``BaseStatementFormatter`` implementation for the account.

    Example:
        >>> formatter = create_statement_formatter(
        ...     account_name="citi",
        ...     statement=raw_df,
        ...     column_mapping={"Date": "transaction_date"},
        ... )
        >>> type(formatter).__name__
        'CitiStatementFormatter'
    """
    if account_name == "apple":
        return AppleStatementFormatter(
            account_name=account_name,
            statement=statement,
            column_mapping=column_mapping,
        )
    if account_name == "citi":
        return CitiStatementFormatter(
            account_name=account_name,
            statement=statement,
            column_mapping=column_mapping,
        )
    if account_name == "discover":
        return DiscoverStatementFormatter(
            account_name=account_name,
            statement=statement,
            column_mapping=column_mapping,
        )

    return DefaultStatementFormatter(
        account_name=account_name,
        statement=statement,
        column_mapping=column_mapping,
    )
