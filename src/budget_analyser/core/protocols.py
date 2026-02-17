"""Shared domain protocols (interfaces).

Purpose:
    Define stable interfaces the domain/presentation can depend on.

Goal:
    Keep the domain free of concrete infrastructure implementations.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from collections.abc import Mapping
from typing import Protocol

import pandas as pd


class StatementRepository(Protocol):
    """Repository interface to load raw statements for all accounts.

    Example:
        >>> repo: StatementRepository = CsvStatementRepository(...)
        >>> stmts = repo.get_statements()
        >>> list(stmts.keys())
        ['citi', 'discover']
    """

    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        """Return a mapping of account name -> raw statement DataFrame.

        Returns:
            Mapping where keys are account identifiers and values are
            raw statement DataFrames read from CSV files.
        """


class ColumnMappingProvider(Protocol):
    """Provides per-account column rename mappings for statement normalization.

    Example:
        >>> provider: ColumnMappingProvider = IniColumnMappingProvider(...)
        >>> mapping = provider.get_column_mapping("citi")
        >>> mapping["Date"]
        'transaction_date'
    """

    def get_column_mapping(self, account_name: str) -> Mapping[str, str]:
        """Return mapping from *source* column name -> *desired* column name.

        Args:
            account_name: Identifier for the bank account (e.g. "citi").

        Returns:
            Mapping of source CSV column names to canonical column names.
        """


class CategoryMappingProvider(Protocol):
    """Provides keyword mappings used to categorize transactions.

    Example:
        >>> provider: CategoryMappingProvider = JsonCategoryMappingProvider(...)
        >>> desc_map = provider.description_to_sub_category()
        >>> "netflix" in desc_map.get("streaming", [])
        True
    """

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Return mapping of sub_category -> keywords list.

        Returns:
            Mapping where keys are sub-category labels and values are
            lists of description keywords that map to that sub-category.
        """

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Return mapping of category -> keywords list.

        Returns:
            Mapping where keys are category labels and values are
            lists of sub-category names that belong to that category.
        """
