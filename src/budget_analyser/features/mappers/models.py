"""Mappers feature DTOs.

Data transfer objects for categorization suggestions.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Suggestion:
    """A single categorization suggestion.

    Attributes:
        sub_category: Suggested sub-category name.
        confidence: Confidence score (0.0-1.0).
        reason: Human-readable explanation for the suggestion.
        matched_description: The existing description that matched.

    Example:
        >>> suggestion = Suggestion(
        ...     sub_category="Groceries",
        ...     confidence=0.85,
        ...     reason="Keyword match: TRADER JOES",
        ...     matched_description="TRADER JOES #123",
        ... )
        >>> suggestion.confidence
        0.85
    """

    sub_category: str
    confidence: float
    reason: str
    matched_description: str = ""

    def __lt__(self, other: Suggestion) -> bool:
        """Allow sorting by confidence (descending).

        Sorts in descending order so the highest-confidence
        suggestion appears first when using ``sorted()``.

        Args:
            other: Another Suggestion to compare against.

        Returns:
            True if this suggestion has higher confidence
            than *other*.

        Example:
            >>> a = Suggestion("A", 0.9, "high", "")
            >>> b = Suggestion("B", 0.5, "low", "")
            >>> sorted([b, a])[0].sub_category
            'A'
        """
        return self.confidence > other.confidence


@dataclass
class SuggestionResult:
    """Result containing multiple suggestions for a transaction.

    Attributes:
        description: The original unmapped description.
        suggestions: List of suggestions sorted by confidence.
        patterns_detected: List of merchant patterns found.

    Example:
        >>> result = SuggestionResult(description="TRADER JOES")
        >>> result.has_suggestions()
        False
    """

    description: str
    suggestions: list[Suggestion] = field(default_factory=list)
    patterns_detected: list[str] = field(default_factory=list)

    def top_suggestion(self) -> Suggestion | None:
        """Return the highest-confidence suggestion, or None.

        Returns:
            The first Suggestion in the list (highest confidence)
            or ``None`` if no suggestions exist.

        Example:
            >>> result = SuggestionResult(
            ...     description="WHOLE FOODS",
            ...     suggestions=[
            ...         Suggestion("Groceries", 0.9, "match", ""),
            ...     ],
            ... )
            >>> result.top_suggestion().sub_category
            'Groceries'
        """
        return self.suggestions[0] if self.suggestions else None

    def has_suggestions(self) -> bool:
        """Return True if any suggestions are available.

        Returns:
            True when the suggestions list is non-empty.

        Example:
            >>> result = SuggestionResult(description="UNKNOWN")
            >>> result.has_suggestions()
            False
        """
        return bool(self.suggestions)
