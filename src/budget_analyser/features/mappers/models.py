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
        return bool(self.suggestions)
