"""Keyword matching strategies (domain logic).

Purpose:
    Provide intelligent keyword matching with priority scoring for transaction
    categorization. Replaces simple first-match-wins with scored matching.

Scoring Algorithm:
    - Longer keyword matches score higher (more specific)
    - Exact matches score higher than substring matches
    - Optional weight field in mappings for manual priority override
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


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

        Example:
            >>> result = MatchResult.no_match()
            >>> bool(result)
            False
        """
        return cls(matched_value="", keyword="", score=0.0, match_type="none")

    def __bool__(self) -> bool:
        """Return True if this represents a valid match."""
        return bool(self.matched_value)


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

    Example:
        >>> calculate_match_score(
        ...     keyword="netflix", content="NETFLIX INC", is_exact=False
        ... )
        16.09...
    """
    base_score = len(keyword)

    # Exact match bonus
    exact_bonus = 100.0 if is_exact else 0.0

    # Position bonus: earlier matches slightly preferred
    content_lower = content.lower()
    keyword_lower = keyword.lower()
    position = content_lower.find(keyword_lower)
    position_bonus = max(0, (len(content) - position) / len(content) * 10) if position >= 0 else 0

    return (base_score + exact_bonus + position_bonus) * weight


def match_by_keywords_scored(
    content: str,
    keyword_map: Mapping[str, list[str]],
    *,
    weights: Mapping[str, float] | None = None,
) -> MatchResult:
    """Match content against keywords using scored ranking.

    Instead of returning the first match, this function evaluates all
    potential matches and returns the highest-scoring one.

    Args:
        content: The text to match against (e.g., transaction description).
        keyword_map: Mapping of category/sub-category -> list of keywords.
        weights: Optional mapping of category -> weight multiplier.

    Returns:
        MatchResult with the best match, or no_match if none found.

    Example:
        >>> mapping = {"streaming": ["netflix", "hulu"]}
        >>> result = match_by_keywords_scored("NETFLIX INC", mapping)
        >>> result.matched_value
        'streaming'
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

                # Check for exact match
                is_exact = content_lower == keyword_str
                if is_exact or keyword_str in content_lower:
                    score = calculate_match_score(
                        keyword=keyword_str,
                        content=content,
                        is_exact=is_exact,
                        weight=weight,
                    )
                    match_type = "exact" if is_exact else "substring"

                    if best_match is None or score > best_match.score:
                        best_match = MatchResult(
                            matched_value=mapped_value,
                            keyword=str(keyword),
                            score=score,
                            match_type=match_type,
                        )

            except (TypeError, AttributeError):
                # Skip keywords that can't be converted to string
                continue

    return best_match if best_match else MatchResult.no_match()


def match_by_keywords_exact_scored(
    content: str,
    keyword_map: Mapping[str, list[str]],
    *,
    weights: Mapping[str, float] | None = None,
) -> MatchResult:
    """Match content exactly against keywords using scored ranking.

    Only considers exact matches (case-insensitive). Returns the
    highest-scoring exact match.

    Args:
        content: The text to match against.
        keyword_map: Mapping of category -> list of keywords.
        weights: Optional mapping of category -> weight multiplier.

    Returns:
        MatchResult with the best exact match, or no_match if none found.

    Example:
        >>> mapping = {"utilities": ["electric", "gas"]}
        >>> result = match_by_keywords_exact_scored("electric", mapping)
        >>> result.matched_value
        'utilities'
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

                    if best_match is None or score > best_match.score:
                        best_match = MatchResult(
                            matched_value=mapped_value,
                            keyword=str(keyword),
                            score=score,
                            match_type="exact",
                        )

            except (TypeError, AttributeError):
                continue

    return best_match if best_match else MatchResult.no_match()


# Legacy compatibility functions (maintain backward compatibility)
def map_by_keywords_substring(content: str, keyword_map: Mapping[str, list[str]]) -> str:
    """Return the best-scored match if any keyword appears as a substring.

    This is a drop-in replacement for the original first-match function.

    Args:
        content: Text to match against (e.g. transaction description).
        keyword_map: Mapping of category -> list of keywords.

    Returns:
        The matched category/sub-category name, or empty string if
        no match is found.

    Example:
        >>> mapping = {"streaming": ["netflix", "hulu"]}
        >>> map_by_keywords_substring("NETFLIX INC", mapping)
        'streaming'
    """
    result = match_by_keywords_scored(content, keyword_map)
    return result.matched_value


def map_by_keywords_exact(content: str, keyword_map: Mapping[str, list[str]]) -> str:
    """Return the best-scored exact match (case-insensitive).

    This is a drop-in replacement for the original first-match function.

    Args:
        content: Text to match exactly (e.g. sub-category name).
        keyword_map: Mapping of category -> list of keywords.

    Returns:
        The matched category name, or empty string if no match.

    Example:
        >>> mapping = {"utilities": ["electric", "gas"]}
        >>> map_by_keywords_exact("electric", mapping)
        'utilities'
    """
    result = match_by_keywords_exact_scored(content, keyword_map)
    return result.matched_value
