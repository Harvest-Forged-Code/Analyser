"""Transaction processor (domain logic).

Single responsibility:
    Categorize transactions by deriving sub_category, category, and c_or_d.

Uses priority-based keyword matching where:
    - Longer keyword matches score higher (more specific)
    - Exact matches score higher than substring matches
    - Returns the highest-scoring match instead of first match
"""

from __future__ import annotations

import pandas as pd

from budget_analyser.domain.errors import ValidationError
from budget_analyser.domain.category_mappers import CategoryMappers
from budget_analyser.domain.keyword_matching import (
    map_by_keywords_substring,
    map_by_keywords_exact,
)


class TransactionProcessor:  # pylint: disable=too-few-public-methods
    """Use-case/service to categorize transactions for reporting.

    Example:
        >>> processor = TransactionProcessor(mappers=mappers)
        >>> processed = processor.process(raw_transactions=df)
        >>> list(processed.columns)
        ['description', 'amount', 'sub_category', 'category', 'c_or_d']
    """

    def __init__(self, *, mappers: CategoryMappers) -> None:
        """Initialize the transaction processor.

        Args:
            mappers: CategoryMappers holding keyword-to-category mappings.
        """
        self._mappers = mappers

    def process(self, *, raw_transactions: pd.DataFrame) -> pd.DataFrame:
        """Process a normalized transaction DataFrame.

        Derives sub_category, category, and c_or_d columns from the
        description and amount columns using keyword matching.

        Args:
            raw_transactions: DataFrame with at least ``description``
                and ``amount`` columns.

        Returns:
            A copy of the input DataFrame with added ``sub_category``,
            ``category``, and ``c_or_d`` columns.

        Raises:
            ValidationError: If ``description`` or ``amount`` column
                is missing from the input DataFrame.

        Example:
            >>> processor = TransactionProcessor(mappers=mappers)
            >>> result = processor.process(raw_transactions=raw_df)
            >>> "sub_category" in result.columns
            True
        """
        processed = raw_transactions.copy()

        if "description" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'description' column")
        if "amount" not in processed.columns:
            raise ValidationError("raw_transactions must contain 'amount' column")

        # Validate and clean amount column - convert to numeric and handle NaN
        processed["amount"] = pd.to_numeric(processed["amount"], errors="coerce")
        nan_count = processed["amount"].isna().sum()
        if nan_count > 0:
            # Fill NaN amounts with 0 and log a warning (could also filter them out)
            processed["amount"] = processed["amount"].fillna(0)

        processed["sub_category"] = processed["description"].astype(str).map(
            lambda description: map_by_keywords_substring(
                description, self._mappers.description_to_sub_category
            )
        )

        processed["category"] = processed["sub_category"].astype(str).map(
            lambda sub_cat: map_by_keywords_exact(
                sub_cat, self._mappers.sub_category_to_category
            )
        )

        def classify_amount(amt: float) -> str:
            if amt > 0:
                return "earnings"
            if amt < 0:
                return "expenditures"
            return "neutral"

        processed["c_or_d"] = processed["amount"].map(classify_amount)

        return processed
