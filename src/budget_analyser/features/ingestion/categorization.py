"""Transaction categorization logic.

Combines keyword matching, category mappers, and transaction
processing into a single module for the ingestion feature.

Scoring Algorithm:
    - Longer keyword matches score higher (more specific)
    - Exact matches score higher than substring matches
    - Optional weight field in mappings for manual priority
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import pandas as pd

from budget_analyser.core.errors import ValidationError


# -------------------------------------------------------------------
# Category mappers DTO
# -------------------------------------------------------------------

@dataclass(frozen=True)
class CategoryMappers:
    """Keyword mappers used by the TransactionProcessor.

    Attributes:
        description_to_sub_category: Mapping of sub_category to
            keywords list.
        sub_category_to_category: Mapping of category to keywords
            list.

    Example:
        >>> mappers = CategoryMappers(
        ...     description_to_sub_category={
        ...         "streaming": ["netflix"],
        ...     },
        ...     sub_category_to_category={
        ...         "entertainment": ["streaming"],
        ...     },
        ... )
    """

    description_to_sub_category: Mapping[str, list[str]]
    sub_category_to_category: Mapping[str, list[str]]


# -------------------------------------------------------------------
# Match result DTO
# -------------------------------------------------------------------

@dataclass(frozen=True)
class MatchResult:
    """Result of a keyword match with scoring information.

    Attributes:
        matched_value: The mapped category/sub-category value.
        keyword: The keyword that matched.
        score: Calculated match score (higher = better match).
        match_type: Type of match (exact, substring, weighted).
    """

    matched_value: str
    keyword: str
    score: float
    match_type: str

    @classmethod
    def no_match(cls) -> MatchResult:
        """Create a result representing no match.

        Returns:
            A MatchResult with empty values and zero score.
        """
        return cls(
            matched_value="", keyword="",
            score=0.0, match_type="none",
        )

    def __bool__(self) -> bool:
        """Return True if this represents a valid match."""
        return bool(self.matched_value)


# -------------------------------------------------------------------
# Scoring helpers
# -------------------------------------------------------------------

def calculate_match_score(
    *,
    keyword: str,
    content: str,
    is_exact: bool,
    weight: float = 1.0,
) -> float:
    """Calculate a match score for a keyword-content pair.

    Scoring factors:
        - Base score = keyword length (longer = more specific)
        - Exact match bonus = 100 points
        - Weight multiplier from mapping configuration

    Args:
        keyword: The keyword that matched.
        content: The original content being matched.
        is_exact: Whether this was an exact match vs substring.
        weight: Optional weight multiplier from mapping config.

    Returns:
        Calculated match score as a float.
    """
    base_score = len(keyword)
    exact_bonus = 100.0 if is_exact else 0.0

    content_lower = content.lower()
    keyword_lower = keyword.lower()
    position = content_lower.find(keyword_lower)
    position_bonus = (
        max(0, (len(content) - position) / len(content) * 10)
        if position >= 0
        else 0
    )

    return (base_score + exact_bonus + position_bonus) * weight


# -------------------------------------------------------------------
# Keyword matching functions
# -------------------------------------------------------------------

def match_by_keywords_scored(
    content: str,
    keyword_map: Mapping[str, list[str]],
    *,
    weights: Mapping[str, float] | None = None,
) -> MatchResult:
    """Match content against keywords using scored ranking.

    Evaluates all potential matches and returns the
    highest-scoring one.

    Args:
        content: Text to match (e.g. transaction description).
        keyword_map: Mapping of category -> list of keywords.
        weights: Optional category -> weight multiplier.

    Returns:
        MatchResult with the best match, or no_match if none.
    """
    if not content:
        return MatchResult.no_match()

    content_lower = content.lower()
    weights = weights or {}

    best_match: MatchResult | None = None

    for mapped_value, keywords in keyword_map.items():
        weight = weights.get(mapped_value, 1.0)

        for keyword in keywords:
            try:
                keyword_str = str(keyword).lower()
                if not keyword_str:
                    continue

                is_exact = content_lower == keyword_str
                if is_exact or keyword_str in content_lower:
                    score = calculate_match_score(
                        keyword=keyword_str,
                        content=content,
                        is_exact=is_exact,
                        weight=weight,
                    )
                    match_type = (
                        "exact" if is_exact else "substring"
                    )

                    if (
                        best_match is None
                        or score > best_match.score
                    ):
                        best_match = MatchResult(
                            matched_value=mapped_value,
                            keyword=str(keyword),
                            score=score,
                            match_type=match_type,
                        )

            except (TypeError, AttributeError):
                continue

    return best_match if best_match else MatchResult.no_match()


def match_by_keywords_exact_scored(
    content: str,
    keyword_map: Mapping[str, list[str]],
    *,
    weights: Mapping[str, float] | None = None,
) -> MatchResult:
    """Match content exactly against keywords using scored ranking.

    Only considers exact matches (case-insensitive).

    Args:
        content: The text to match against.
        keyword_map: Mapping of category -> list of keywords.
        weights: Optional category -> weight multiplier.

    Returns:
        MatchResult with the best exact match, or no_match.
    """
    if not content:
        return MatchResult.no_match()

    content_lower = content.lower()
    weights = weights or {}

    best_match: MatchResult | None = None

    for mapped_value, keywords in keyword_map.items():
        weight = weights.get(mapped_value, 1.0)

        for keyword in keywords:
            try:
                keyword_str = str(keyword).lower()
                if content_lower == keyword_str:
                    score = calculate_match_score(
                        keyword=keyword_str,
                        content=content,
                        is_exact=True,
                        weight=weight,
                    )

                    if (
                        best_match is None
                        or score > best_match.score
                    ):
                        best_match = MatchResult(
                            matched_value=mapped_value,
                            keyword=str(keyword),
                            score=score,
                            match_type="exact",
                        )

            except (TypeError, AttributeError):
                continue

    return best_match if best_match else MatchResult.no_match()


def map_by_keywords_substring(
    content: str,
    keyword_map: Mapping[str, list[str]],
) -> str:
    """Return the best-scored match for substring matching.

    Drop-in replacement for original first-match function.

    Args:
        content: Text to match (e.g. transaction description).
        keyword_map: Mapping of category -> list of keywords.

    Returns:
        Matched category/sub-category name, or empty string.
    """
    result = match_by_keywords_scored(content, keyword_map)
    return result.matched_value


def map_by_keywords_exact(
    content: str,
    keyword_map: Mapping[str, list[str]],
) -> str:
    """Return the best-scored exact match (case-insensitive).

    Drop-in replacement for original first-match function.

    Args:
        content: Text to match exactly.
        keyword_map: Mapping of category -> list of keywords.

    Returns:
        Matched category name, or empty string.
    """
    result = match_by_keywords_exact_scored(content, keyword_map)
    return result.matched_value


# -------------------------------------------------------------------
# Transaction processor
# -------------------------------------------------------------------

class TransactionProcessor:  # pylint: disable=too-few-public-methods
    """Categorize transactions by deriving sub_category, category, c_or_d.

    Uses priority-based keyword matching where longer/exact matches
    score higher.

    Example:
        >>> processor = TransactionProcessor(mappers=mappers)
        >>> processed = processor.process(raw_transactions=df)
    """

    def __init__(self, *, mappers: CategoryMappers) -> None:
        """Initialize the transaction processor.

        Args:
            mappers: CategoryMappers holding keyword-to-category
                mappings.
        """
        self._mappers = mappers

    def process(
        self, *, raw_transactions: pd.DataFrame,
    ) -> pd.DataFrame:
        """Process a normalized transaction DataFrame.

        Derives sub_category, category, and c_or_d columns from
        the description and amount columns using keyword matching.

        Args:
            raw_transactions: DataFrame with at least
                ``description`` and ``amount`` columns.

        Returns:
            A copy with added ``sub_category``, ``category``,
            and ``c_or_d`` columns.

        Raises:
            ValidationError: If ``description`` or ``amount``
                column is missing.
        """
        processed = raw_transactions.copy()

        if "description" not in processed.columns:
            raise ValidationError(
                "raw_transactions must contain "
                "'description' column",
            )
        if "amount" not in processed.columns:
            raise ValidationError(
                "raw_transactions must contain "
                "'amount' column",
            )

        processed["amount"] = pd.to_numeric(
            processed["amount"], errors="coerce",
        )
        processed["amount"] = processed["amount"].fillna(0)

        processed["sub_category"] = (
            processed["description"].astype(str).map(
                lambda description: map_by_keywords_substring(
                    description,
                    self._mappers.description_to_sub_category,
                )
            )
        )

        processed["category"] = (
            processed["sub_category"].astype(str).map(
                lambda sub_cat: map_by_keywords_exact(
                    sub_cat,
                    self._mappers.sub_category_to_category,
                )
            )
        )

        def classify_amount(amt: float) -> str:
            if amt > 0:
                return "earnings"
            if amt < 0:
                return "expenditures"
            return "neutral"

        processed["c_or_d"] = processed["amount"].map(
            classify_amount,
        )

        return processed
