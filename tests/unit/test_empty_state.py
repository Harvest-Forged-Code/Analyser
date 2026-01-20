"""Unit tests for the empty state components."""

from __future__ import annotations

import pytest

from budget_analyser.views.widgets.empty_state import (
    EmptyStateConfig,
    EmptyStates,
)


class TestEmptyStateConfig:
    """Tests for EmptyStateConfig dataclass."""

    def test_config_with_required_fields(self):
        """Config should work with just required fields."""
        config = EmptyStateConfig(icon="📭", title="No data")
        assert config.icon == "📭"
        assert config.title == "No data"
        assert config.subtitle == ""
        assert config.action_text == ""
        assert config.is_success is False

    def test_config_with_all_fields(self):
        """Config should accept all fields."""
        config = EmptyStateConfig(
            icon="✅",
            title="All done!",
            subtitle="Great job completing everything.",
            action_text="Continue",
            is_success=True,
        )
        assert config.icon == "✅"
        assert config.title == "All done!"
        assert config.subtitle == "Great job completing everything."
        assert config.action_text == "Continue"
        assert config.is_success is True

    def test_config_is_frozen(self):
        """Config should be immutable."""
        config = EmptyStateConfig(icon="📭", title="No data")
        with pytest.raises(AttributeError):
            config.title = "Modified"

    def test_config_equality(self):
        """Identical configs should be equal."""
        config1 = EmptyStateConfig(icon="📭", title="No data")
        config2 = EmptyStateConfig(icon="📭", title="No data")
        assert config1 == config2

    def test_config_inequality(self):
        """Different configs should not be equal."""
        config1 = EmptyStateConfig(icon="📭", title="No data")
        config2 = EmptyStateConfig(icon="📭", title="Different title")
        assert config1 != config2


class TestEmptyStatesCollection:
    """Tests for pre-defined empty state configurations."""

    def test_no_transactions_defined(self):
        """NO_TRANSACTIONS config should be properly defined."""
        config = EmptyStates.NO_TRANSACTIONS
        assert config.icon == "📭"
        assert "transactions" in config.title.lower()
        assert config.action_text  # Should have action

    def test_no_transactions_for_filter_defined(self):
        """NO_TRANSACTIONS_FOR_FILTER config should be properly defined."""
        config = EmptyStates.NO_TRANSACTIONS_FOR_FILTER
        assert config.icon == "🔍"
        assert "filter" in config.subtitle.lower()
        assert config.action_text == "Clear Filters"

    def test_all_transactions_mapped_is_success(self):
        """ALL_TRANSACTIONS_MAPPED should be a success state."""
        config = EmptyStates.ALL_TRANSACTIONS_MAPPED
        assert config.is_success is True
        assert "✅" in config.icon

    def test_no_unmapped_transactions_is_success(self):
        """NO_UNMAPPED_TRANSACTIONS should be a success state."""
        config = EmptyStates.NO_UNMAPPED_TRANSACTIONS
        assert config.is_success is True

    def test_no_mapping_rules_has_action(self):
        """NO_MAPPING_RULES should have an action button."""
        config = EmptyStates.NO_MAPPING_RULES
        assert config.action_text == "Add Rule"

    def test_no_budget_goals_defined(self):
        """NO_BUDGET_GOALS config should be properly defined."""
        config = EmptyStates.NO_BUDGET_GOALS
        assert "budget" in config.title.lower()
        assert config.action_text  # Should have action

    def test_budget_on_track_is_success(self):
        """BUDGET_ON_TRACK should be a success state."""
        config = EmptyStates.BUDGET_ON_TRACK
        assert config.is_success is True

    def test_no_earnings_defined(self):
        """NO_EARNINGS config should be properly defined."""
        config = EmptyStates.NO_EARNINGS
        assert "earnings" in config.title.lower()

    def test_no_expenses_defined(self):
        """NO_EXPENSES config should be properly defined."""
        config = EmptyStates.NO_EXPENSES
        assert "expenses" in config.title.lower()

    def test_no_report_data_defined(self):
        """NO_REPORT_DATA config should be properly defined."""
        config = EmptyStates.NO_REPORT_DATA
        assert "data" in config.title.lower()

    def test_report_loading_no_action(self):
        """REPORT_LOADING should not have an action."""
        config = EmptyStates.REPORT_LOADING
        assert config.action_text == ""

    def test_no_categories_defined(self):
        """NO_CATEGORIES config should be properly defined."""
        config = EmptyStates.NO_CATEGORIES
        assert "categories" in config.title.lower()
        assert config.action_text == "Add Category"

    def test_no_search_results_defined(self):
        """NO_SEARCH_RESULTS config should be properly defined."""
        config = EmptyStates.NO_SEARCH_RESULTS
        assert "results" in config.title.lower()
        # Search results typically don't have an action
        assert config.action_text == ""

    def test_no_payments_defined(self):
        """NO_PAYMENTS config should be properly defined."""
        config = EmptyStates.NO_PAYMENTS
        assert "payment" in config.title.lower()

    def test_no_unmatched_payments_is_success(self):
        """NO_UNMATCHED_PAYMENTS should be a success state."""
        config = EmptyStates.NO_UNMATCHED_PAYMENTS
        assert config.is_success is True

    def test_no_validation_issues_is_success(self):
        """NO_VALIDATION_ISSUES should be a success state."""
        config = EmptyStates.NO_VALIDATION_ISSUES
        assert config.is_success is True

    def test_no_chart_data_defined(self):
        """NO_CHART_DATA config should be properly defined."""
        config = EmptyStates.NO_CHART_DATA
        assert "chart" in config.title.lower() or "data" in config.title.lower()

    def test_no_accounts_defined(self):
        """NO_ACCOUNTS config should be properly defined."""
        config = EmptyStates.NO_ACCOUNTS
        assert "accounts" in config.title.lower()
        assert config.action_text == "Add Account"

    def test_all_configs_have_icons(self):
        """All pre-defined configs should have icons."""
        configs = [
            EmptyStates.NO_TRANSACTIONS,
            EmptyStates.NO_TRANSACTIONS_FOR_FILTER,
            EmptyStates.ALL_TRANSACTIONS_MAPPED,
            EmptyStates.NO_UNMAPPED_TRANSACTIONS,
            EmptyStates.NO_MAPPING_RULES,
            EmptyStates.NO_BUDGET_GOALS,
            EmptyStates.BUDGET_ON_TRACK,
            EmptyStates.NO_EARNINGS,
            EmptyStates.NO_EXPENSES,
            EmptyStates.NO_REPORT_DATA,
            EmptyStates.REPORT_LOADING,
            EmptyStates.NO_CATEGORIES,
            EmptyStates.NO_SEARCH_RESULTS,
            EmptyStates.NO_PAYMENTS,
            EmptyStates.NO_UNMATCHED_PAYMENTS,
            EmptyStates.NO_VALIDATION_ISSUES,
            EmptyStates.NO_CHART_DATA,
            EmptyStates.NO_ACCOUNTS,
        ]

        for config in configs:
            assert config.icon, f"Config {config.title} missing icon"
            assert len(config.icon) > 0

    def test_all_configs_have_titles(self):
        """All pre-defined configs should have titles."""
        configs = [
            EmptyStates.NO_TRANSACTIONS,
            EmptyStates.NO_TRANSACTIONS_FOR_FILTER,
            EmptyStates.ALL_TRANSACTIONS_MAPPED,
            EmptyStates.NO_UNMAPPED_TRANSACTIONS,
            EmptyStates.NO_MAPPING_RULES,
            EmptyStates.NO_BUDGET_GOALS,
            EmptyStates.BUDGET_ON_TRACK,
            EmptyStates.NO_EARNINGS,
            EmptyStates.NO_EXPENSES,
            EmptyStates.NO_REPORT_DATA,
            EmptyStates.REPORT_LOADING,
            EmptyStates.NO_CATEGORIES,
            EmptyStates.NO_SEARCH_RESULTS,
            EmptyStates.NO_PAYMENTS,
            EmptyStates.NO_UNMATCHED_PAYMENTS,
            EmptyStates.NO_VALIDATION_ISSUES,
            EmptyStates.NO_CHART_DATA,
            EmptyStates.NO_ACCOUNTS,
        ]

        for config in configs:
            assert config.title, f"Config with icon {config.icon} missing title"
            assert len(config.title) > 0
