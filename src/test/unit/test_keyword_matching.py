"""Tests for keyword matching with priority scoring."""

import pytest

from budget_analyser.features.ingestion.categorization import (
    MatchResult,
    calculate_match_score,
    match_by_keywords_scored,
    match_by_keywords_exact_scored,
    map_by_keywords_substring,
    map_by_keywords_exact,
)


class TestMatchResult:
    """Tests for MatchResult dataclass."""

    def test_no_match_returns_empty_result(self):
        result = MatchResult.no_match()
        assert result.matched_value == ""
        assert result.score == 0.0
        assert result.match_type == "none"
        assert not result  # Should be falsy

    def test_valid_match_is_truthy(self):
        result = MatchResult(
            matched_value="Restaurants",
            keyword="starbucks",
            score=50.0,
            match_type="substring",
        )
        assert result  # Should be truthy
        assert result.matched_value == "Restaurants"


class TestCalculateMatchScore:
    """Tests for match score calculation."""

    def test_longer_keyword_scores_higher(self):
        short_score = calculate_match_score(
            keyword="tea", content="TEA HOUSE", is_exact=False
        )
        long_score = calculate_match_score(
            keyword="starbucks", content="STARBUCKS COFFEE", is_exact=False
        )
        assert long_score > short_score

    def test_exact_match_bonus(self):
        substring_score = calculate_match_score(
            keyword="coffee", content="STARBUCKS COFFEE", is_exact=False
        )
        exact_score = calculate_match_score(
            keyword="coffee", content="COFFEE", is_exact=True
        )
        assert exact_score > substring_score

    def test_weight_multiplier(self):
        base_score = calculate_match_score(
            keyword="test", content="TEST VALUE", is_exact=False, weight=1.0
        )
        weighted_score = calculate_match_score(
            keyword="test", content="TEST VALUE", is_exact=False, weight=2.0
        )
        assert weighted_score > base_score


class TestMatchByKeywordsScored:
    """Tests for scored substring matching."""

    def test_empty_content_returns_no_match(self):
        keyword_map = {"Category": ["keyword"]}
        result = match_by_keywords_scored("", keyword_map)
        assert not result

    def test_single_match_returns_result(self):
        keyword_map = {"Restaurants": ["starbucks"]}
        result = match_by_keywords_scored("STARBUCKS COFFEE", keyword_map)
        assert result.matched_value == "Restaurants"
        assert result.keyword == "starbucks"
        assert result.match_type == "substring"

    def test_longer_keyword_wins_over_shorter(self):
        # "STARBUCKS" should match "Restaurants" because it's more specific than "COFFEE"
        keyword_map = {
            "Restaurants": ["starbucks"],
            "Beverages": ["coffee"],
        }
        result = match_by_keywords_scored("STARBUCKS COFFEE", keyword_map)
        assert result.matched_value == "Restaurants"

    def test_exact_match_wins_over_substring(self):
        keyword_map = {
            "ExactCategory": ["test value"],
            "SubstringCategory": ["test"],
        }
        result = match_by_keywords_scored("test value", keyword_map)
        assert result.matched_value == "ExactCategory"

    def test_weighted_category_wins(self):
        keyword_map = {
            "HighPriority": ["key"],
            "LowPriority": ["key"],
        }
        weights = {"HighPriority": 10.0, "LowPriority": 1.0}
        result = match_by_keywords_scored("key test", keyword_map, weights=weights)
        assert result.matched_value == "HighPriority"

    def test_no_match_returns_no_match_result(self):
        keyword_map = {"Category": ["keyword"]}
        result = match_by_keywords_scored("no match here", keyword_map)
        assert not result


class TestMatchByKeywordsExactScored:
    """Tests for scored exact matching."""

    def test_empty_content_returns_no_match(self):
        keyword_map = {"Category": ["keyword"]}
        result = match_by_keywords_exact_scored("", keyword_map)
        assert not result

    def test_exact_match_required(self):
        keyword_map = {"Category": ["keyword"]}
        # Substring should not match
        result = match_by_keywords_exact_scored("keyword extra", keyword_map)
        assert not result

    def test_exact_match_case_insensitive(self):
        keyword_map = {"Category": ["KEYWORD"]}
        result = match_by_keywords_exact_scored("keyword", keyword_map)
        assert result.matched_value == "Category"


class TestLegacyCompatibility:
    """Tests for legacy function compatibility."""

    def test_map_by_keywords_substring_returns_string(self):
        keyword_map = {"Restaurants": ["starbucks"]}
        result = map_by_keywords_substring("STARBUCKS COFFEE", keyword_map)
        assert isinstance(result, str)
        assert result == "Restaurants"

    def test_map_by_keywords_substring_no_match_returns_empty(self):
        keyword_map = {"Category": ["keyword"]}
        result = map_by_keywords_substring("no match", keyword_map)
        assert result == ""

    def test_map_by_keywords_exact_returns_string(self):
        keyword_map = {"Category": ["keyword"]}
        result = map_by_keywords_exact("keyword", keyword_map)
        assert isinstance(result, str)
        assert result == "Category"

    def test_map_by_keywords_exact_no_match_returns_empty(self):
        keyword_map = {"Category": ["keyword"]}
        result = map_by_keywords_exact("keyword extra", keyword_map)
        assert result == ""


class TestRealWorldScenarios:
    """Tests simulating real-world categorization scenarios."""

    def test_restaurant_starbucks_scenario(self):
        """RESTAURANT STARBUCKS should match Restaurants via more specific keyword."""
        keyword_map = {
            "Restaurants": ["restaurant", "starbucks", "coffee"],
            "Shopping": ["store"],
        }
        result = match_by_keywords_scored("RESTAURANT STARBUCKS", keyword_map)
        assert result.matched_value == "Restaurants"

    def test_specific_merchant_beats_generic_keyword(self):
        """Specific merchant pattern should beat generic keyword."""
        keyword_map = {
            "Groceries": ["walmart", "wal-mart"],
            "Shopping": ["store"],
        }
        result = match_by_keywords_scored("WAL-MART STORE #1234", keyword_map)
        assert result.matched_value == "Groceries"

    def test_multiple_matches_returns_best(self):
        """When content matches multiple keywords, return highest scored."""
        keyword_map = {
            "Gas": ["shell", "gas"],
            "Shopping": ["store"],
        }
        result = match_by_keywords_scored("SHELL GAS STATION", keyword_map)
        # "shell" and "gas" both match; shell is longer but gas station has gas
        # The important thing is we get Gas category
        assert result.matched_value == "Gas"
