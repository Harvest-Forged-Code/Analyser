"""Categorization suggestions engine (domain logic).

Purpose:
    Provide intelligent suggestions for unmapped transactions using:
    - Fuzzy matching against existing mapped descriptions
    - Pattern detection (merchant prefixes like "SQ *", "TST*")
    - Historical learning from user mapping decisions

This helps users categorize new transactions more efficiently by
suggesting likely categories based on similar past transactions.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Mapping

import pandas as pd


@dataclass(frozen=True)
class Suggestion:
    """A single categorization suggestion.

    Attributes:
        sub_category: Suggested sub-category name.
        confidence: Confidence score (0.0-1.0).
        reason: Human-readable explanation for the suggestion.
        matched_description: The existing description that matched.
    """

    sub_category: str
    confidence: float
    reason: str
    matched_description: str = ""

    def __lt__(self, other: Suggestion) -> bool:
        """Allow sorting by confidence (descending)."""
        return self.confidence > other.confidence


@dataclass
class SuggestionResult:
    """Result containing multiple suggestions for a transaction.

    Attributes:
        description: The original unmapped description.
        suggestions: List of suggestions sorted by confidence.
        patterns_detected: List of merchant patterns found.
    """

    description: str
    suggestions: list[Suggestion] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)

    def top_suggestion(self) -> Suggestion | None:
        """Return the highest-confidence suggestion, or None."""
        return self.suggestions[0] if self.suggestions else None

    def has_suggestions(self) -> bool:
        """Return True if any suggestions are available."""
        return len(self.suggestions) > 0


# Common merchant prefix patterns
MERCHANT_PATTERNS: dict[str, str] = {
    r"^SQ \*": "Square merchant",
    r"^TST\*": "Toast restaurant",
    r"^TST \*": "Toast restaurant",
    r"^PY \*": "PayPal merchant",
    r"^SP \*": "Shopify merchant",
    r"^DOORDASH\*": "DoorDash delivery",
    r"^UBER \*": "Uber service",
    r"^LYFT \*": "Lyft ride",
    r"^AMZN\*": "Amazon purchase",
    r"^APPLE\.COM": "Apple purchase",
    r"^GOOGLE \*": "Google service",
    r"^CL \*": "Chase merchant",
    r"^IN \*": "Invoice/merchant",
    r"^GDP\*": "Generic merchant",
}


class CategorizationSuggestionEngine:
    """Engine for generating categorization suggestions.

    Uses multiple strategies to suggest categories:
    1. Pattern matching for known merchant prefixes
    2. Fuzzy matching against historical transactions
    3. Keyword similarity analysis
    """

    def __init__(
        self,
        *,
        min_confidence: float = 0.5,
        max_suggestions: int = 5,
        fuzzy_threshold: float = 0.6,
    ) -> None:
        """Initialize the suggestion engine.

        Args:
            min_confidence: Minimum confidence to include a suggestion.
            max_suggestions: Maximum number of suggestions to return.
            fuzzy_threshold: Threshold for fuzzy string matching.
        """
        self._min_confidence = min_confidence
        self._max_suggestions = max_suggestions
        self._fuzzy_threshold = fuzzy_threshold
        self._historical_mappings: dict[str, str] = {}

    def learn_from_history(self, *, transactions: pd.DataFrame) -> None:
        """Learn from historical mapped transactions.

        Args:
            transactions: DataFrame with 'description' and 'sub_category' columns.
        """
        if transactions.empty:
            return

        if "description" not in transactions.columns:
            return
        if "sub_category" not in transactions.columns:
            return

        for _, row in transactions.iterrows():
            desc = str(row.get("description", "")).strip()
            sub_cat = str(row.get("sub_category", "")).strip()
            if desc and sub_cat:
                self._historical_mappings[desc.lower()] = sub_cat

    def suggest(
        self,
        *,
        description: str,
        keyword_map: Mapping[str, list[str]] | None = None,
    ) -> SuggestionResult:
        """Generate suggestions for an unmapped transaction.

        Args:
            description: The transaction description to categorize.
            keyword_map: Optional current mapping of sub_category -> keywords.

        Returns:
            SuggestionResult with ranked suggestions.
        """
        result = SuggestionResult(description=description)

        if not description:
            return result

        desc_lower = description.lower()

        # Strategy 1: Detect merchant patterns
        patterns = self._detect_patterns(description)
        result.patterns_detected = patterns

        # Strategy 2: Fuzzy match against historical mappings
        historical_suggestions = self._match_historical(desc_lower)
        result.suggestions.extend(historical_suggestions)

        # Strategy 3: Match against keywords in keyword_map
        if keyword_map:
            keyword_suggestions = self._match_keywords(desc_lower, keyword_map)
            result.suggestions.extend(keyword_suggestions)

        # Deduplicate and sort by confidence
        result.suggestions = self._deduplicate_suggestions(result.suggestions)
        result.suggestions = sorted(result.suggestions)[:self._max_suggestions]

        # Filter by minimum confidence
        result.suggestions = [
            s for s in result.suggestions if s.confidence >= self._min_confidence
        ]

        return result

    def suggest_batch(
        self,
        *,
        descriptions: list[str],
        keyword_map: Mapping[str, list[str]] | None = None,
    ) -> list[SuggestionResult]:
        """Generate suggestions for multiple descriptions.

        Args:
            descriptions: List of transaction descriptions.
            keyword_map: Optional current mapping of sub_category -> keywords.

        Returns:
            List of SuggestionResult, one per description.
        """
        return [
            self.suggest(description=desc, keyword_map=keyword_map)
            for desc in descriptions
        ]

    def _detect_patterns(self, description: str) -> list[str]:
        """Detect known merchant patterns in description."""
        patterns_found = []
        for pattern, name in MERCHANT_PATTERNS.items():
            if re.search(pattern, description, re.IGNORECASE):
                patterns_found.append(name)
        return patterns_found

    def _match_historical(self, desc_lower: str) -> list[Suggestion]:
        """Find similar historical mappings using fuzzy matching."""
        suggestions = []

        for hist_desc, sub_cat in self._historical_mappings.items():
            similarity = SequenceMatcher(None, desc_lower, hist_desc).ratio()

            if similarity >= self._fuzzy_threshold:
                confidence = similarity * 0.9  # Historical match bonus
                suggestions.append(Suggestion(
                    sub_category=sub_cat,
                    confidence=confidence,
                    reason=f"Similar to previously mapped: {hist_desc[:50]}",
                    matched_description=hist_desc,
                ))

        return suggestions

    def _match_keywords(
        self,
        desc_lower: str,
        keyword_map: Mapping[str, list[str]],
    ) -> list[Suggestion]:
        """Find partial keyword matches."""
        suggestions = []

        for sub_category, keywords in keyword_map.items():
            best_match_score = 0.0
            best_keyword = ""

            for keyword in keywords:
                keyword_lower = str(keyword).lower()

                # Check if keyword is in description (partial match)
                if keyword_lower in desc_lower:
                    # Score based on keyword length relative to description
                    score = len(keyword_lower) / len(desc_lower)
                    score = min(score * 1.5, 0.85)  # Cap at 0.85 for partial matches

                    if score > best_match_score:
                        best_match_score = score
                        best_keyword = keyword

                # Also check fuzzy similarity for near-matches
                else:
                    similarity = SequenceMatcher(None, desc_lower, keyword_lower).ratio()
                    if similarity >= self._fuzzy_threshold and similarity > best_match_score:
                        best_match_score = similarity * 0.7  # Lower confidence for fuzzy
                        best_keyword = keyword

            if best_match_score > 0:
                suggestions.append(Suggestion(
                    sub_category=sub_category,
                    confidence=best_match_score,
                    reason=f"Keyword match: {best_keyword}",
                    matched_description=best_keyword,
                ))

        return suggestions

    def _deduplicate_suggestions(
        self,
        suggestions: list[Suggestion],
    ) -> list[Suggestion]:
        """Remove duplicate sub-category suggestions, keeping highest confidence."""
        seen: dict[str, Suggestion] = {}

        for suggestion in suggestions:
            key = suggestion.sub_category
            if key not in seen or suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion

        return list(seen.values())


def create_suggestion_engine(
    *,
    historical_transactions: pd.DataFrame | None = None,
    min_confidence: float = 0.5,
) -> CategorizationSuggestionEngine:
    """Factory function to create a configured suggestion engine.

    Args:
        historical_transactions: Optional DataFrame to learn from.
        min_confidence: Minimum confidence threshold.

    Returns:
        Configured CategorizationSuggestionEngine instance.
    """
    engine = CategorizationSuggestionEngine(min_confidence=min_confidence)

    if historical_transactions is not None and not historical_transactions.empty:
        engine.learn_from_history(transactions=historical_transactions)

    return engine
