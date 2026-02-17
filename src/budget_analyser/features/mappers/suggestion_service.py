"""Categorization suggestion engine (business logic).

Provides intelligent suggestions for unmapped transactions using:
- Fuzzy matching against existing mapped descriptions
- Pattern detection (merchant prefixes like "SQ *", "TST*")
- Historical learning from user mapping decisions
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Mapping

import pandas as pd

from budget_analyser.features.mappers.models import (
    Suggestion,
    SuggestionResult,
)

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
            min_confidence: Minimum confidence to include.
                Suggestions below this threshold are discarded.
            max_suggestions: Maximum number of suggestions
                returned per description.
            fuzzy_threshold: Threshold for fuzzy matching.
                Higher values require closer matches.

        Example:
            >>> engine = CategorizationSuggestionEngine(
            ...     min_confidence=0.6,
            ...     max_suggestions=3,
            ... )
        """
        self._min_confidence = min_confidence
        self._max_suggestions = max_suggestions
        self._fuzzy_threshold = fuzzy_threshold
        self._historical_mappings: dict[str, str] = {}

    def learn_from_history(
        self, *, transactions: pd.DataFrame,
    ) -> None:
        """Learn from historical mapped transactions.

        Populates the internal mapping of descriptions to
        sub-categories so future suggestions can use fuzzy
        matching against known history.

        Args:
            transactions: DataFrame with 'description' and
                'sub_category' columns.

        Example:
            >>> import pandas as pd
            >>> engine = CategorizationSuggestionEngine()
            >>> df = pd.DataFrame({
            ...     "description": ["TRADER JOES"],
            ...     "sub_category": ["Groceries"],
            ... })
            >>> engine.learn_from_history(transactions=df)
        """
        if transactions.empty:
            return
        if "description" not in transactions.columns:
            return
        if "sub_category" not in transactions.columns:
            return

        for _, row in transactions.iterrows():
            desc = str(row.get("description", "")).strip()
            sub_cat = str(
                row.get("sub_category", ""),
            ).strip()
            if desc and sub_cat:
                self._historical_mappings[
                    desc.lower()
                ] = sub_cat

    def suggest(
        self,
        *,
        description: str,
        keyword_map: Mapping[str, list[str]] | None = None,
    ) -> SuggestionResult:
        """Generate suggestions for an unmapped transaction.

        Combines pattern detection, historical fuzzy matching,
        and keyword matching to produce ranked suggestions.

        Args:
            description: The transaction description.
            keyword_map: Optional mapping of sub_category to
                keywords.

        Returns:
            SuggestionResult with ranked suggestions.

        Example:
            >>> engine = CategorizationSuggestionEngine()
            >>> result = engine.suggest(
            ...     description="SQ *COFFEE SHOP",
            ...     keyword_map={"Coffee": ["COFFEE"]},
            ... )
            >>> result.description
            'SQ *COFFEE SHOP'
        """
        result = SuggestionResult(description=description)

        if not description:
            return result

        desc_lower = description.lower()

        patterns = self._detect_patterns(description)
        result.patterns_detected = patterns

        historical = self._match_historical(desc_lower)
        result.suggestions.extend(historical)

        if keyword_map:
            keyword_sugg = self._match_keywords(
                desc_lower, keyword_map,
            )
            result.suggestions.extend(keyword_sugg)

        result.suggestions = self._deduplicate_suggestions(
            result.suggestions,
        )
        result.suggestions = sorted(
            result.suggestions,
        )[:self._max_suggestions]

        result.suggestions = [
            s for s in result.suggestions
            if s.confidence >= self._min_confidence
        ]

        return result

    def suggest_batch(
        self,
        *,
        descriptions: list[str],
        keyword_map: Mapping[str, list[str]] | None = None,
    ) -> list[SuggestionResult]:
        """Generate suggestions for multiple descriptions.

        Convenience wrapper that calls :meth:`suggest` for each
        description in the list.

        Args:
            descriptions: List of transaction descriptions.
            keyword_map: Optional keyword mapping.

        Returns:
            List of SuggestionResult, one per description.

        Example:
            >>> engine = CategorizationSuggestionEngine()
            >>> results = engine.suggest_batch(
            ...     descriptions=["WHOLE FOODS", "SHELL OIL"],
            ... )
            >>> len(results)
            2
        """
        return [
            self.suggest(
                description=desc, keyword_map=keyword_map,
            )
            for desc in descriptions
        ]

    def _detect_patterns(
        self, description: str,
    ) -> list[str]:
        """Detect known merchant patterns in description.

        Args:
            description: Raw transaction description string.

        Returns:
            List of human-readable pattern names found
            (e.g. ``["Square merchant"]``).
        """
        patterns_found = []
        for pattern, name in MERCHANT_PATTERNS.items():
            if re.search(pattern, description, re.IGNORECASE):
                patterns_found.append(name)
        return patterns_found

    def _match_historical(
        self, desc_lower: str,
    ) -> list[Suggestion]:
        """Find similar historical mappings.

        Args:
            desc_lower: Lowercased transaction description.

        Returns:
            List of Suggestion objects from historical matches
            that meet the fuzzy threshold.
        """
        suggestions = []

        for hist_desc, sub_cat in (
            self._historical_mappings.items()
        ):
            similarity = SequenceMatcher(
                None, desc_lower, hist_desc,
            ).ratio()

            if similarity >= self._fuzzy_threshold:
                confidence = similarity * 0.9
                suggestions.append(Suggestion(
                    sub_category=sub_cat,
                    confidence=confidence,
                    reason=(
                        "Similar to previously mapped: "
                        f"{hist_desc[:50]}"
                    ),
                    matched_description=hist_desc,
                ))

        return suggestions

    def _match_keywords(
        self,
        desc_lower: str,
        keyword_map: Mapping[str, list[str]],
    ) -> list[Suggestion]:
        """Find partial keyword matches.

        Args:
            desc_lower: Lowercased transaction description.
            keyword_map: Mapping of sub-category names to their
                keyword lists.

        Returns:
            List of Suggestion objects for keyword matches,
            one per sub-category at most.
        """
        suggestions = []

        for sub_category, keywords in keyword_map.items():
            best_match_score = 0.0
            best_keyword = ""

            for keyword in keywords:
                keyword_lower = str(keyword).lower()

                if keyword_lower in desc_lower:
                    score = len(keyword_lower) / len(desc_lower)
                    score = min(score * 1.5, 0.85)

                    if score > best_match_score:
                        best_match_score = score
                        best_keyword = keyword
                else:
                    similarity = SequenceMatcher(
                        None, desc_lower, keyword_lower,
                    ).ratio()
                    if (similarity >= self._fuzzy_threshold
                            and similarity > best_match_score):
                        best_match_score = similarity * 0.7
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
        """Remove duplicates, keeping highest confidence.

        Args:
            suggestions: List of Suggestion objects that may
                contain duplicates for the same sub-category.

        Returns:
            Deduplicated list with only the highest-confidence
            Suggestion per sub-category.
        """
        seen: dict[str, Suggestion] = {}

        for suggestion in suggestions:
            key = suggestion.sub_category
            if (key not in seen
                    or suggestion.confidence
                    > seen[key].confidence):
                seen[key] = suggestion

        return list(seen.values())


def create_suggestion_engine(
    *,
    historical_transactions: pd.DataFrame | None = None,
    min_confidence: float = 0.5,
) -> CategorizationSuggestionEngine:
    """Factory function to create a configured suggestion engine.

    Creates an engine and optionally pre-loads it with
    historical transaction data for fuzzy matching.

    Args:
        historical_transactions: Optional DataFrame to learn
            from. Must have 'description' and 'sub_category'
            columns if provided.
        min_confidence: Minimum confidence threshold.

    Returns:
        Configured CategorizationSuggestionEngine instance.

    Example:
        >>> import pandas as pd
        >>> history = pd.DataFrame({
        ...     "description": ["TRADER JOES"],
        ...     "sub_category": ["Groceries"],
        ... })
        >>> engine = create_suggestion_engine(
        ...     historical_transactions=history,
        ...     min_confidence=0.6,
        ... )
    """
    engine = CategorizationSuggestionEngine(
        min_confidence=min_confidence,
    )

    if (historical_transactions is not None
            and not historical_transactions.empty):
        engine.learn_from_history(
            transactions=historical_transactions,
        )

    return engine
