"""Transaction processor (domain logic).

Single responsibility:
    Categorize transactions by deriving sub_category, category, and c_or_d.
"""

from __future__ import annotations

from typing import Mapping

import pandas as pd

from budget_analyser.domain.errors import ValidationError
from budget_analyser.domain.category_mappers import CategoryMappers


def _map_by_keywords(content: str, keyword_map: Mapping[str, list[str]]) -> str:
    """Return the mapped key if any keyword appears in the content."""
    content_lower = content.lower()
    for mapped_value, keywords in keyword_map.items():
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return mapped_value
    return ""


class TransactionProcessor:
    """Use-case/service to categorize transactions for reporting."""

    def __init__(self, *, mappers: CategoryMappers) -> None:
        self._mappers = mappers

    def process(self, *, raw_transactions: pd.DataFrame) -> pd.DataFrame:
        """Process a normalized transaction DataFrame."""
        processed = raw_transactions.copy()

        if "description" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'description' column")
        if "amount" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'amount' column")

        processed["sub_category"] = processed["description"].astype(str).map(
            lambda description: _map_by_keywords(
                description, self._mappers.description_to_sub_category
            )
        )

        processed["category"] = processed["sub_category"].astype(str).map(
            lambda sub_cat: _map_by_keywords(sub_cat, self._mappers.sub_category_to_category)
        )

        processed["c_or_d"] = processed["amount"].map(
            lambda amount: "earnings" if amount > 0 else "expenditures"
        )

        return processed
