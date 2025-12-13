"""Transaction categorization (domain logic).

Purpose:
    Enrich normalized transactions with derived fields used for reporting.

Goal:
    Add:
        - sub_category (from description keywords)
        - category (from sub_category keywords)
        - c_or_d (earnings vs expenditures based on amount sign)

Steps:
    1. Validate required input columns.
    2. Map description -> sub_category.
    3. Map sub_category -> category.
    4. Derive c_or_d from amount.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from dataclasses import dataclass
from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import ValidationError


@dataclass(frozen=True)
class CategoryMappers:
    """Keyword mappers used by `TransactionProcessor`.

    Attributes:
        description_to_sub_category: Mapping of sub_category -> keywords list.
        sub_category_to_category: Mapping of category -> keywords list.
    """

    description_to_sub_category: Mapping[str, list[str]]
    sub_category_to_category: Mapping[str, list[str]]


def _map_by_keywords(content: str, keyword_map: Mapping[str, list[str]]) -> str:
    """Return the mapped key if any keyword appears in the content.

    Args:
        content: Free-text content such as a transaction description.
        keyword_map: Mapping of target label -> keywords list.

    Returns:
        The first matching label, or an empty string if no match is found.
    """
    # Normalize to lower-case for case-insensitive matching.
    content_lower = content.lower()
    # Traverse mapping in insertion order.
    for mapped_value, keywords in keyword_map.items():
        # Check all keywords for each mapped value.
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return mapped_value
    # Return default empty string when nothing matches.
    return ""


class TransactionProcessor:
    """Use-case/service to categorize transactions for reporting."""

    def __init__(self, *, mappers: CategoryMappers) -> None:
        """Create the processor.

        Args:
            mappers: Keyword mappings used for categorization.
        """
        # Store mappers for later processing.
        self._mappers = mappers

    def process(self, *, raw_transactions: pd.DataFrame) -> pd.DataFrame:
        """Process a normalized transaction DataFrame.

        Steps:
            1. Copy the input DataFrame.
            2. Validate required columns.
            3. Add sub_category/category/c_or_d columns.

        Args:
            raw_transactions: Input DataFrame (must contain `description` and `amount`).

        Returns:
            A new DataFrame containing additional categorization columns.

        Raises:
            ValidationError: If required columns are missing.
        """
        # Copy to avoid mutating caller's DataFrame.
        processed = raw_transactions.copy()

        # Validate required columns before processing.
        if "description" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'description' column")

        if "amount" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'amount' column")

        # Derive sub_category from description using keyword matching.
        processed["sub_category"] = processed["description"].astype(str).map(
            lambda description: _map_by_keywords(
                description, self._mappers.description_to_sub_category
            )
        )

        # Derive category from sub_category using keyword matching.
        processed["category"] = processed["sub_category"].astype(str).map(
            lambda sub_cat: _map_by_keywords(sub_cat, self._mappers.sub_category_to_category)
        )

        # Derive whether a row is earnings or expenditures.
        processed["c_or_d"] = processed["amount"].map(
            lambda amount: "earnings" if amount > 0 else "expenditures"
        )

        # Return the processed copy.
        return processed
