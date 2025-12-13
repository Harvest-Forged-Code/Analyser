from __future__ import annotations

# pylint: disable=too-few-public-methods

from typing import Mapping, Protocol

import pandas as pd


class StatementRepository(Protocol):
    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        """Return a mapping of account name -> raw statement DataFrame."""


class ColumnMappingProvider(Protocol):
    def get_column_mapping(self, account_name: str) -> Mapping[str, str]:
        """Return mapping from *source* column name -> *desired* column name."""


class CategoryMappingProvider(Protocol):
    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Return mapping of sub_category -> keywords list."""

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Return mapping of category -> keywords list."""
