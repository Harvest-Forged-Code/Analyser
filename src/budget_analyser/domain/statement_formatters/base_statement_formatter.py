"""Base statement formatter and shared constants (domain logic).

Single responsibility:
    Provide common normalization steps for bank statement CSVs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import MappingNotFoundError


REQUIRED_COLUMNS = ["transaction_date", "description", "amount", "from_account"]


class BaseStatementFormatter(ABC):  # pylint: disable=too-few-public-methods
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
        self._account_name = account_name
        self._statement = statement
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
        """
        self._format_amount_column()
        self._rename_columns()
        self._add_from_account_col()
        self._required_columns()
        self._bank_specific_formatting()

        # Deterministic datetime parsing without inference warning
        self._statement["transaction_date"] = pd.to_datetime(
            self._statement["transaction_date"], format="mixed", errors="coerce"
        )
        return self._statement

    @abstractmethod
    def _bank_specific_formatting(self) -> None:
        """Apply bank-specific transformations to the statement."""

    def _format_amount_column(self) -> None:
        """Ensure the statement contains a canonical `amount` column.

        Behavior:
            - If a column named `amount` already exists (case-insensitive), do nothing.
            - Otherwise, derive `amount` from `Debit` and `Credit` columns.
        """
        lowercase_columns = [column.lower() for column in self._statement.columns]
        if "amount" in lowercase_columns:
            return

        if "Debit" not in self._statement.columns or "Credit" not in self._statement.columns:
            present = list(self._statement.columns)
            hint = (
                "Add an 'amount' column to the CSV or provide both 'Debit' and 'Credit' so the "
                "formatter can derive it. Update the INI mapping if column names differ."
            )
            raise MappingNotFoundError(
                f"[{self._account_name}] Amount column missing and Debit/Credit "
                f"columns not present to derive it. Present columns: {present}. "
                f"Hint: {hint}"
            )

        debit = self._statement["Debit"].fillna(0)
        credit = self._statement["Credit"].fillna(0)
        self._statement["amount"] = debit.where(debit != 0, credit)

    def _rename_columns(self) -> None:
        if not self._column_mapping:
            raise MappingNotFoundError(f"No column mapping provided for {self._account_name!r}.")
        self._statement = self._statement.rename(columns=self._column_mapping)

    def _required_columns(self) -> None:
        missing = [col for col in REQUIRED_COLUMNS if col not in self._statement.columns]
        if missing:
            present = list(self._statement.columns)
            raise MappingNotFoundError(
                f"Missing required columns after formatting for {self._account_name!r}: {missing}. "
                f"Present columns: {present}."
            )
        self._statement = self._statement[REQUIRED_COLUMNS]

    def _add_from_account_col(self) -> None:
        self._statement["from_account"] = self._account_name
