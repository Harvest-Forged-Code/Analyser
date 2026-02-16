"""Unit tests for features.mappers.suggestion_service."""

from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.mappers.models import (
    Suggestion,
    SuggestionResult,
)
from budget_analyser.features.mappers.suggestion_service import (
    CategorizationSuggestionEngine,
    create_suggestion_engine,
    MERCHANT_PATTERNS,
)


class TestSuggestionModels:
    """Tests for Suggestion and SuggestionResult DTOs."""

    def test_suggestion_ordering(self) -> None:
        high = Suggestion(
            sub_category="A", confidence=0.9, reason="r",
        )
        low = Suggestion(
            sub_category="B", confidence=0.5, reason="r",
        )
        # __lt__ sorts by confidence descending
        assert high < low  # high confidence sorts first

    def test_suggestion_result_no_suggestions(self) -> None:
        r = SuggestionResult(description="test")
        assert r.top_suggestion() is None
        assert r.has_suggestions() is False

    def test_suggestion_result_with_suggestions(self) -> None:
        s = Suggestion(
            sub_category="Food", confidence=0.8, reason="match",
        )
        r = SuggestionResult(description="test", suggestions=[s])
        assert r.top_suggestion() == s
        assert r.has_suggestions() is True


class TestCategorizationSuggestionEngine:
    """Tests for CategorizationSuggestionEngine."""

    def test_empty_description(self) -> None:
        engine = CategorizationSuggestionEngine()
        result = engine.suggest(description="")
        assert not result.has_suggestions()

    def test_pattern_detection(self) -> None:
        engine = CategorizationSuggestionEngine()
        result = engine.suggest(description="SQ *COFFEE SHOP")
        assert "Square merchant" in result.patterns_detected

    def test_historical_matching(self) -> None:
        df = pd.DataFrame({
            "description": ["WALMART STORE 1234"],
            "sub_category": ["Groceries"],
        })
        engine = CategorizationSuggestionEngine(
            min_confidence=0.3,
        )
        engine.learn_from_history(transactions=df)
        result = engine.suggest(
            description="WALMART STORE 5678",
        )
        assert result.has_suggestions()
        assert result.suggestions[0].sub_category == "Groceries"

    def test_keyword_matching(self) -> None:
        engine = CategorizationSuggestionEngine(
            min_confidence=0.3,
        )
        keyword_map = {
            "Gas": ["shell", "chevron", "exxon"],
        }
        result = engine.suggest(
            description="SHELL OIL STATION",
            keyword_map=keyword_map,
        )
        assert result.has_suggestions()

    def test_suggest_batch(self) -> None:
        engine = CategorizationSuggestionEngine()
        results = engine.suggest_batch(
            descriptions=["test1", "test2"],
        )
        assert len(results) == 2

    def test_learn_from_empty_df(self) -> None:
        engine = CategorizationSuggestionEngine()
        engine.learn_from_history(transactions=pd.DataFrame())
        # Should not crash


class TestCreateSuggestionEngine:
    """Tests for factory function."""

    def test_create_without_history(self) -> None:
        engine = create_suggestion_engine()
        assert isinstance(engine, CategorizationSuggestionEngine)

    def test_create_with_history(self) -> None:
        df = pd.DataFrame({
            "description": ["STARBUCKS"],
            "sub_category": ["Coffee"],
        })
        engine = create_suggestion_engine(
            historical_transactions=df,
        )
        result = engine.suggest(description="STARBUCKS STORE")
        assert result.has_suggestions()


class TestMerchantPatterns:
    """Tests for MERCHANT_PATTERNS dict."""

    def test_patterns_not_empty(self) -> None:
        assert len(MERCHANT_PATTERNS) > 0

    def test_patterns_are_regex(self) -> None:
        import re
        for pattern in MERCHANT_PATTERNS:
            # Should compile without error
            re.compile(pattern)
