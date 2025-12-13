"""Domain protocols (interfaces).

Purpose:
    Define stable interfaces the domain/presentation can depend on.

Goal:
    Keep the domain free of concrete infrastructure implementations.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from typing import Mapping, Protocol

import pandas as pd


class StatementRepository(Protocol):
    """Repository interface to load raw statements for all accounts."""

    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        """Return a mapping of account name -> raw statement DataFrame."""


class ColumnMappingProvider(Protocol):
    """Provides per-account column rename mappings for statement normalization."""

    def get_column_mapping(self, account_name: str) -> Mapping[str, str]:
        """Return mapping from *source* column name -> *desired* column name."""


class CategoryMappingProvider(Protocol):
    """Provides keyword mappings used to categorize transactions."""

    def description_to_sub_category(self) -> Mapping[str, list[str]]:
        """Return mapping of sub_category -> keywords list."""

    def sub_category_to_category(self) -> Mapping[str, list[str]]:
        """Return mapping of category -> keywords list."""
