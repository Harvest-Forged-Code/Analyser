"""Statement formatting (domain logic).

Purpose:
    Normalize bank-specific statement CSV data into a consistent schema.

Goal:
    Produce a DataFrame with required columns so downstream processing/reporting can
    be bank-agnostic.

Steps (high-level):
    1. Ensure there is a unified `amount` column.
    2. Rename statement columns using an account-specific mapping.
    3. Add `from_account` so the source account is preserved.
    4. Filter down to required columns.
    5. Apply bank-specific adjustments.
    6. Parse `transaction_date` as datetime.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from abc import ABC, abstractmethod
from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import MappingNotFoundError


REQUIRED_COLUMNS = ["transaction_date", "description", "amount", "from_account"]


class BaseStatementFormatter(ABC):
    """Base formatter that provides common normalization steps.

    Child classes implement `_bank_specific_formatting` for per-bank adjustments.
    """

    def __init__(
        self,
        *,
        account_name: str,
        statement: pd.DataFrame,
        column_mapping: Mapping[str, str],
    ) -> None:
        """Create a statement formatter.

        Args:
            account_name: Identifier for the account/bank (e.g., "citi").
            statement: Raw statement DataFrame.
            column_mapping: Mapping from source column names -> desired column names.
        """
        # Store configuration and input statement.
        self._account_name = account_name
        self._statement = statement
        # Defensive copy to avoid external mutation.
        self._column_mapping = dict(column_mapping)

    def get_desired_format(self) -> pd.DataFrame:
        """Return a normalized statement DataFrame.

        Steps:
            1. Ensure an `amount` column exists.
            2. Rename columns to the canonical names.
            3. Add `from_account`.
            4. Keep only required columns.
            5. Apply bank-specific formatting.
            6. Parse `transaction_date` as datetime.

        Returns:
            A DataFrame with columns `REQUIRED_COLUMNS`.
        """
        # Step 1: unify debit/credit into amount.
        self._format_amount_column()
        # Step 2: map bank-specific column names to canonical names.
        self._rename_columns()
        # Step 3: annotate with account name.
        self._add_from_account_col()
        # Step 4: filter only required columns.
        self._required_columns()
        # Step 5: bank-specific adjustments.
        self._bank_specific_formatting()
        # Step 6: parse transaction_date.
        self._statement["transaction_date"] = pd.to_datetime(self._statement["transaction_date"])
        return self._statement

    @abstractmethod
    def _bank_specific_formatting(self) -> None:
        """Apply bank-specific transformations to the statement.

        Purpose:
            Allow each bank formatter to adjust sign conventions or other quirks.
        """
        raise NotImplementedError

    def _format_amount_column(self) -> None:
        """Ensure the statement contains a canonical `amount` column.

        Behavior:
            - If a column named `amount` already exists (case-insensitive), do nothing.
            - Otherwise, derive `amount` from `Debit` and `Credit` columns.

        Raises:
            MappingNotFoundError: If `amount` is missing and Debit/Credit are not present.
        """
        # Normalize column names for presence check.
        lowercase_columns = [column.lower() for column in self._statement.columns]

        if "amount" in lowercase_columns:
            # Amount already exists.
            return

        if "Debit" not in self._statement.columns or "Credit" not in self._statement.columns:
            # Cannot derive amount without these columns.
            raise MappingNotFoundError(
                "Amount column missing and Debit/Credit columns not present to derive it."
            )

        # Prefer debit where present; otherwise use credit.
        debit = self._statement["Debit"].fillna(0)
        credit = self._statement["Credit"].fillna(0)
        self._statement["amount"] = debit.where(debit != 0, credit)

    def _rename_columns(self) -> None:
        """Rename source columns to the canonical column names.

        Raises:
            MappingNotFoundError: If no mapping is available for this account.
        """
        if not self._column_mapping:
            raise MappingNotFoundError(f"No column mapping provided for {self._account_name!r}.")
        # Apply mapping (source -> desired).
        self._statement = self._statement.rename(columns=self._column_mapping)

    def _required_columns(self) -> None:
        """Keep only the required canonical columns.

        Raises:
            MappingNotFoundError: If required columns are missing after mapping.
        """
        # Validate presence of canonical columns.
        missing = [col for col in REQUIRED_COLUMNS if col not in self._statement.columns]
        if missing:
            raise MappingNotFoundError(
                f"Missing required columns after formatting for {self._account_name!r}: {missing}"
            )
        # Filter to stable schema.
        self._statement = self._statement[REQUIRED_COLUMNS]

    def _add_from_account_col(self) -> None:
        """Add a `from_account` column to preserve statement provenance."""
        # Fill the account name for every row.
        self._statement["from_account"] = self._account_name


class CitiStatementFormatter(BaseStatementFormatter):
    """Citi-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:
        """Invert the sign of amounts to match project convention."""
        # Citi CSV typically reports credits/debits opposite to desired convention.
        self._statement["amount"] = self._statement["amount"] * -1


class DiscoverStatementFormatter(BaseStatementFormatter):
    """Discover-specific statement normalization."""

    def _bank_specific_formatting(self) -> None:
        """Invert the sign of amounts to match project convention."""
        # Discover CSV typically reports credits/debits opposite to desired convention.
        self._statement["amount"] = self._statement["amount"] * -1


class DefaultStatementFormatter(BaseStatementFormatter):
    """Default formatter for accounts without special rules."""

    def _bank_specific_formatting(self) -> None:
        """No-op bank specific formatting."""
        return


def create_statement_formatter(
    *,
    account_name: str,
    statement: pd.DataFrame,
    column_mapping: Mapping[str, str],
) -> BaseStatementFormatter:
    """Factory to create the correct statement formatter for an account.

    Purpose:
        Hide bank-selection logic from callers.

    Args:
        account_name: Account/bank identifier.
        statement: Raw statement DataFrame.
        column_mapping: Source->desired column mapping.

    Returns:
        A `BaseStatementFormatter` implementation.
    """
    # Select by account name; default for unknown accounts.
    if account_name == "citi":
        return CitiStatementFormatter(
            account_name=account_name, statement=statement, column_mapping=column_mapping
        )
    if account_name == "discover":
        return DiscoverStatementFormatter(
            account_name=account_name, statement=statement, column_mapping=column_mapping
        )

    # Fallback formatter.
    return DefaultStatementFormatter(
        account_name=account_name, statement=statement, column_mapping=column_mapping
    )
