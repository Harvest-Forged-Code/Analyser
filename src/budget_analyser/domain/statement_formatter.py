from __future__ import annotations

# pylint: disable=too-few-public-methods

from abc import ABC, abstractmethod
from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import MappingNotFoundError


REQUIRED_COLUMNS = ["transaction_date", "description", "amount", "from_account"]


class BaseStatementFormatter(ABC):
    def __init__(
        self,
        *,
        account_name: str,
        statement: pd.DataFrame,
        column_mapping: Mapping[str, str],
    ) -> None:
        self._account_name = account_name
        self._statement = statement
        self._column_mapping = dict(column_mapping)

    def get_desired_format(self) -> pd.DataFrame:
        self._format_amount_column()
        self._rename_columns()
        self._add_from_account_col()
        self._required_columns()
        self._bank_specific_formatting()
        self._statement["transaction_date"] = pd.to_datetime(self._statement["transaction_date"])
        return self._statement

    @abstractmethod
    def _bank_specific_formatting(self) -> None:
        raise NotImplementedError

    def _format_amount_column(self) -> None:
        lowercase_columns = [column.lower() for column in self._statement.columns]

        if "amount" in lowercase_columns:
            return

        if "Debit" not in self._statement.columns or "Credit" not in self._statement.columns:
            raise MappingNotFoundError(
                "Amount column missing and Debit/Credit columns not present to derive it."
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
            raise MappingNotFoundError(
                f"Missing required columns after formatting for {self._account_name!r}: {missing}"
            )

        self._statement = self._statement[REQUIRED_COLUMNS]

    def _add_from_account_col(self) -> None:
        self._statement["from_account"] = self._account_name


class CitiStatementFormatter(BaseStatementFormatter):
    def _bank_specific_formatting(self) -> None:
        self._statement["amount"] = self._statement["amount"] * -1


class DiscoverStatementFormatter(BaseStatementFormatter):
    def _bank_specific_formatting(self) -> None:
        self._statement["amount"] = self._statement["amount"] * -1


class DefaultStatementFormatter(BaseStatementFormatter):
    def _bank_specific_formatting(self) -> None:
        return


def create_statement_formatter(
    *,
    account_name: str,
    statement: pd.DataFrame,
    column_mapping: Mapping[str, str],
) -> BaseStatementFormatter:
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
