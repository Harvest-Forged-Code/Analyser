"""Tests for categorization suggestions engine."""

import pandas as pd
import pytest

from budget_analyser.features.mappers import (
    CategorizationSuggestionEngine,
    Suggestion,
    SuggestionResult,
    create_suggestion_engine,
    MERCHANT_PATTERNS,
)


class TestSuggestion:
    """Tests for Suggestion dataclass."""

    def test_suggestion_sorting_by_confidence(self):
        suggestions = [
            Suggestion(sub_category="Low", confidence=0.3, reason="test"),
            Suggestion(sub_category="High", confidence=0.9, reason="test"),
            Suggestion(sub_category="Mid", confidence=0.6, reason="test"),
        ]
        sorted_suggestions = sorted(suggestions)
        assert sorted_suggestions[0].sub_category == "High"
        assert sorted_suggestions[1].sub_category == "Mid"
        assert sorted_suggestions[2].sub_category == "Low"


class TestSuggestionResult:
    """Tests for SuggestionResult dataclass."""

    def test_top_suggestion_returns_first(self):
        result = SuggestionResult(
            description="test",
            suggestions=[
                Suggestion(sub_category="First", confidence=0.9, reason="test"),
                Suggestion(sub_category="Second", confidence=0.5, reason="test"),
            ],
        )
        assert result.top_suggestion().sub_category == "First"

    def test_top_suggestion_returns_none_when_empty(self):
        result = SuggestionResult(description="test")
        assert result.top_suggestion() is None

    def test_has_suggestions(self):
        empty_result = SuggestionResult(description="test")
        assert not empty_result.has_suggestions()

        with_suggestions = SuggestionResult(
            description="test",
            suggestions=[Suggestion(sub_category="Cat", confidence=0.5, reason="test")],
        )
        assert with_suggestions.has_suggestions()


class TestPatternDetection:
    """Tests for merchant pattern detection."""

    def test_detects_square_pattern(self):
        engine = CategorizationSuggestionEngine()
        result = engine.suggest(description="SQ *COFFEE SHOP")
        assert "Square merchant" in result.patterns_detected

    def test_detects_toast_pattern(self):
        engine = CategorizationSuggestionEngine()
        result = engine.suggest(description="TST*RESTAURANT NAME")
        assert "Toast restaurant" in result.patterns_detected

    def test_detects_multiple_patterns(self):
        engine = CategorizationSuggestionEngine()
        # This would be unusual but tests the logic
        result = engine.suggest(description="DOORDASH*UBER DELIVERY")
        assert len(result.patterns_detected) >= 1

    def test_no_pattern_for_normal_text(self):
        engine = CategorizationSuggestionEngine()
        result = engine.suggest(description="WALMART STORE #1234")
        assert len(result.patterns_detected) == 0


class TestHistoricalLearning:
    """Tests for historical transaction learning."""

    def test_learns_from_transactions(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.3)
        historical = pd.DataFrame({
            "description": ["STARBUCKS COFFEE", "MCDONALDS #1234"],
            "sub_category": ["Dining", "Dining"],
        })
        engine.learn_from_history(transactions=historical)

        # Similar description should get suggestion
        result = engine.suggest(description="STARBUCKS RESERVE")
        assert result.has_suggestions()

    def test_empty_dataframe_handled(self):
        engine = CategorizationSuggestionEngine()
        engine.learn_from_history(transactions=pd.DataFrame())
        # Should not raise

    def test_missing_columns_handled(self):
        engine = CategorizationSuggestionEngine()
        engine.learn_from_history(transactions=pd.DataFrame({"other": ["value"]}))
        # Should not raise


class TestKeywordMatching:
    """Tests for keyword-based suggestions."""

    def test_matches_keyword_in_description(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1)
        keyword_map = {
            "Dining": ["starbucks", "coffee"],
            "Groceries": ["walmart", "costco"],
        }

        result = engine.suggest(
            description="STARBUCKS COFFEE SHOP",
            keyword_map=keyword_map,
        )
        assert result.has_suggestions()
        assert any(s.sub_category == "Dining" for s in result.suggestions)

    def test_partial_keyword_match(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1)
        keyword_map = {
            "Gas": ["shell", "chevron"],
        }

        result = engine.suggest(
            description="SHELL GAS STATION",
            keyword_map=keyword_map,
        )
        assert result.has_suggestions()
        assert result.suggestions[0].sub_category == "Gas"


class TestSuggestionDeduplication:
    """Tests for suggestion deduplication."""

    def test_keeps_highest_confidence(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1)

        # Create historical data with same category appearing multiple times
        historical = pd.DataFrame({
            "description": ["STARBUCKS #1", "STARBUCKS #2", "STARBUCKS #3"],
            "sub_category": ["Dining", "Dining", "Dining"],
        })
        engine.learn_from_history(transactions=historical)

        result = engine.suggest(description="STARBUCKS #1")
        # Should only have one Dining suggestion
        restaurants = [s for s in result.suggestions if s.sub_category == "Dining"]
        assert len(restaurants) <= 1


class TestConfidenceFiltering:
    """Tests for confidence threshold filtering."""

    def test_filters_low_confidence(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.8)
        keyword_map = {
            "Category": ["keyword"],
        }

        # Very different description should have low confidence
        result = engine.suggest(
            description="COMPLETELY DIFFERENT TEXT",
            keyword_map=keyword_map,
        )
        # Should filter out low confidence matches
        assert all(s.confidence >= 0.8 for s in result.suggestions)

    def test_max_suggestions_limit(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1, max_suggestions=3)
        keyword_map = {
            f"Category{i}": [f"keyword{i}"] for i in range(10)
        }

        result = engine.suggest(
            description="keyword1 keyword2 keyword3 keyword4 keyword5",
            keyword_map=keyword_map,
        )
        assert len(result.suggestions) <= 3


class TestBatchSuggestions:
    """Tests for batch suggestion generation."""

    def test_batch_returns_same_length(self):
        engine = CategorizationSuggestionEngine()
        descriptions = ["DESC1", "DESC2", "DESC3"]

        results = engine.suggest_batch(descriptions=descriptions)
        assert len(results) == 3

    def test_batch_with_keyword_map(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1)
        keyword_map = {"Dining": ["starbucks"]}
        descriptions = ["STARBUCKS", "WALMART"]

        results = engine.suggest_batch(
            descriptions=descriptions,
            keyword_map=keyword_map,
        )
        assert results[0].has_suggestions()


class TestFactoryFunction:
    """Tests for create_suggestion_engine factory."""

    def test_creates_engine_without_history(self):
        engine = create_suggestion_engine()
        assert isinstance(engine, CategorizationSuggestionEngine)

    def test_creates_engine_with_history(self):
        historical = pd.DataFrame({
            "description": ["TEST DESCRIPTION"],
            "sub_category": ["TestCategory"],
        })
        engine = create_suggestion_engine(historical_transactions=historical)
        assert isinstance(engine, CategorizationSuggestionEngine)

    def test_respects_min_confidence(self):
        engine = create_suggestion_engine(min_confidence=0.9)
        # Engine created with high threshold
        result = engine.suggest(description="random text")
        assert all(s.confidence >= 0.9 for s in result.suggestions)


class TestRealWorldScenarios:
    """Tests simulating real-world usage."""

    def test_restaurant_suggestion(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1, fuzzy_threshold=0.5)

        # Learn from history
        historical = pd.DataFrame({
            "description": [
                "STARBUCKS COFFEE #1234",
                "CHIPOTLE MEXICAN GRILL",
                "TST*OLIVE GARDEN",
            ],
            "sub_category": ["Dining", "Dining", "Dining"],
        })
        engine.learn_from_history(transactions=historical)

        # New similar transaction (very similar to historical)
        result = engine.suggest(description="STARBUCKS COFFEE #5678")
        assert result.has_suggestions()
        top = result.top_suggestion()
        assert top is not None
        assert top.sub_category == "Dining"

    def test_square_merchant_detection(self):
        engine = CategorizationSuggestionEngine(min_confidence=0.1)
        keyword_map = {
            "Dining": ["restaurant", "cafe", "coffee"],
            "Farmers_Markets": ["farm", "market"],
        }

        result = engine.suggest(
            description="SQ *FARMERS MARKET PRODUCE",
            keyword_map=keyword_map,
        )
        assert "Square merchant" in result.patterns_detected
        # Should suggest Farmers_Markets based on keyword
        assert any(s.sub_category == "Farmers_Markets" for s in result.suggestions)
