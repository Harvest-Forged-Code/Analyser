"""Unit tests for the filter panel components."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from budget_analyser.views.widgets.filter_panel import (
    FilterCriteria,
    DatePreset,
)


class TestFilterCriteria:
    """Tests for FilterCriteria dataclass."""

    def test_default_criteria_is_empty(self):
        """Default criteria should have no filters applied."""
        criteria = FilterCriteria()
        assert criteria.is_empty()

    def test_criteria_with_amount_min_not_empty(self):
        """Criteria with amount_min set should not be empty."""
        criteria = FilterCriteria(amount_min=100.0)
        assert not criteria.is_empty()

    def test_criteria_with_amount_max_not_empty(self):
        """Criteria with amount_max set should not be empty."""
        criteria = FilterCriteria(amount_max=500.0)
        assert not criteria.is_empty()

    def test_criteria_with_date_from_not_empty(self):
        """Criteria with date_from set should not be empty."""
        criteria = FilterCriteria(date_from=date(2024, 1, 1))
        assert not criteria.is_empty()

    def test_criteria_with_categories_not_empty(self):
        """Criteria with categories set should not be empty."""
        criteria = FilterCriteria(categories={"Food"})
        assert not criteria.is_empty()

    def test_criteria_with_search_text_not_empty(self):
        """Criteria with search text should not be empty."""
        criteria = FilterCriteria(search_text="coffee")
        assert not criteria.is_empty()

    def test_criteria_hiding_mapped_not_empty(self):
        """Criteria hiding mapped items should not be empty."""
        criteria = FilterCriteria(show_mapped=False)
        assert not criteria.is_empty()

    def test_criteria_hiding_unmapped_not_empty(self):
        """Criteria hiding unmapped items should not be empty."""
        criteria = FilterCriteria(show_unmapped=False)
        assert not criteria.is_empty()

    # Amount matching tests
    def test_matches_amount_no_filter(self):
        """Amount should match when no filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_amount(100.0)
        assert criteria.matches_amount(-500.0)
        assert criteria.matches_amount(0.0)

    def test_matches_amount_with_min(self):
        """Amount should only match if >= min."""
        criteria = FilterCriteria(amount_min=50.0)
        assert criteria.matches_amount(100.0)
        assert criteria.matches_amount(50.0)
        assert not criteria.matches_amount(49.99)
        assert not criteria.matches_amount(-10.0)

    def test_matches_amount_with_max(self):
        """Amount should only match if <= max."""
        criteria = FilterCriteria(amount_max=100.0)
        assert criteria.matches_amount(50.0)
        assert criteria.matches_amount(100.0)
        assert not criteria.matches_amount(100.01)
        assert criteria.matches_amount(-50.0)

    def test_matches_amount_with_range(self):
        """Amount should match if within min-max range."""
        criteria = FilterCriteria(amount_min=10.0, amount_max=100.0)
        assert criteria.matches_amount(50.0)
        assert criteria.matches_amount(10.0)
        assert criteria.matches_amount(100.0)
        assert not criteria.matches_amount(5.0)
        assert not criteria.matches_amount(150.0)

    # Date matching tests
    def test_matches_date_no_filter(self):
        """Date should match when no filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_date(date(2024, 1, 15))
        assert criteria.matches_date(date(2020, 6, 1))

    def test_matches_date_with_from(self):
        """Date should only match if >= date_from."""
        criteria = FilterCriteria(date_from=date(2024, 1, 1))
        assert criteria.matches_date(date(2024, 6, 15))
        assert criteria.matches_date(date(2024, 1, 1))
        assert not criteria.matches_date(date(2023, 12, 31))

    def test_matches_date_with_to(self):
        """Date should only match if <= date_to."""
        criteria = FilterCriteria(date_to=date(2024, 12, 31))
        assert criteria.matches_date(date(2024, 6, 15))
        assert criteria.matches_date(date(2024, 12, 31))
        assert not criteria.matches_date(date(2025, 1, 1))

    def test_matches_date_with_range(self):
        """Date should match if within date range."""
        criteria = FilterCriteria(
            date_from=date(2024, 1, 1),
            date_to=date(2024, 12, 31)
        )
        assert criteria.matches_date(date(2024, 6, 15))
        assert criteria.matches_date(date(2024, 1, 1))
        assert criteria.matches_date(date(2024, 12, 31))
        assert not criteria.matches_date(date(2023, 12, 31))
        assert not criteria.matches_date(date(2025, 1, 1))

    # Category matching tests
    def test_matches_category_no_filter(self):
        """Category should match when no filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_category("Food")
        assert criteria.matches_category("Transportation")

    def test_matches_category_with_filter(self):
        """Category should only match if in filter set."""
        criteria = FilterCriteria(categories={"Food", "Entertainment"})
        assert criteria.matches_category("Food")
        assert criteria.matches_category("Entertainment")
        assert not criteria.matches_category("Transportation")

    # Sub-category matching tests
    def test_matches_sub_category_no_filter(self):
        """Sub-category should match when no filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_sub_category("Groceries")
        assert criteria.matches_sub_category("Gas")

    def test_matches_sub_category_with_filter(self):
        """Sub-category should only match if in filter set."""
        criteria = FilterCriteria(sub_categories={"Groceries", "Coffee"})
        assert criteria.matches_sub_category("Groceries")
        assert criteria.matches_sub_category("Coffee")
        assert not criteria.matches_sub_category("Gas")

    # Account matching tests
    def test_matches_account_no_filter(self):
        """Account should match when no filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_account("Checking")
        assert criteria.matches_account("Credit Card")

    def test_matches_account_with_filter(self):
        """Account should only match if in filter set."""
        criteria = FilterCriteria(accounts={"Checking", "Savings"})
        assert criteria.matches_account("Checking")
        assert criteria.matches_account("Savings")
        assert not criteria.matches_account("Credit Card")

    # Mapping status tests
    def test_matches_mapping_status_both_shown(self):
        """Both mapped and unmapped should match when both shown."""
        criteria = FilterCriteria(show_mapped=True, show_unmapped=True)
        assert criteria.matches_mapping_status(True)
        assert criteria.matches_mapping_status(False)

    def test_matches_mapping_status_only_mapped(self):
        """Only mapped should match when unmapped hidden."""
        criteria = FilterCriteria(show_mapped=True, show_unmapped=False)
        assert criteria.matches_mapping_status(True)
        assert not criteria.matches_mapping_status(False)

    def test_matches_mapping_status_only_unmapped(self):
        """Only unmapped should match when mapped hidden."""
        criteria = FilterCriteria(show_mapped=False, show_unmapped=True)
        assert not criteria.matches_mapping_status(True)
        assert criteria.matches_mapping_status(False)

    # Search text tests
    def test_matches_search_no_filter(self):
        """Text should match when no search filter is set."""
        criteria = FilterCriteria()
        assert criteria.matches_search("STARBUCKS COFFEE")
        assert criteria.matches_search("")

    def test_matches_search_with_filter(self):
        """Text should only match if contains search term."""
        criteria = FilterCriteria(search_text="coffee")
        assert criteria.matches_search("STARBUCKS COFFEE #123")
        assert criteria.matches_search("Coffee Shop")
        assert not criteria.matches_search("GROCERY STORE")

    def test_matches_search_case_insensitive(self):
        """Search should be case-insensitive."""
        criteria = FilterCriteria(search_text="STARBUCKS")
        assert criteria.matches_search("starbucks coffee")
        assert criteria.matches_search("Starbucks")
        assert criteria.matches_search("STARBUCKS")


class TestDatePreset:
    """Tests for DatePreset class."""

    def test_this_month_starts_on_first(self):
        """This month should start on the 1st."""
        date_from, date_to = DatePreset.this_month()
        assert date_from.day == 1
        assert date_to == date.today()

    def test_this_month_same_month_year(self):
        """This month should have correct month and year."""
        today = date.today()
        date_from, date_to = DatePreset.this_month()
        assert date_from.month == today.month
        assert date_from.year == today.year

    def test_last_month_returns_previous_month(self):
        """Last month should return the previous month's range."""
        date_from, date_to = DatePreset.last_month()

        today = date.today()
        first_of_current = today.replace(day=1)
        expected_last = first_of_current - timedelta(days=1)

        assert date_to == expected_last
        assert date_from.month == expected_last.month
        assert date_from.day == 1

    def test_last_3_months_approximately_90_days(self):
        """Last 3 months should be approximately 90 days."""
        date_from, date_to = DatePreset.last_3_months()
        days_diff = (date_to - date_from).days
        assert 88 <= days_diff <= 92  # Allow small variance

    def test_last_6_months_approximately_180_days(self):
        """Last 6 months should be approximately 180 days."""
        date_from, date_to = DatePreset.last_6_months()
        days_diff = (date_to - date_from).days
        assert 178 <= days_diff <= 182  # Allow small variance

    def test_this_year_starts_january_first(self):
        """This year should start on January 1st."""
        date_from, date_to = DatePreset.this_year()
        today = date.today()
        assert date_from.year == today.year
        assert date_from.month == 1
        assert date_from.day == 1
        assert date_to == today

    def test_last_year_full_previous_year(self):
        """Last year should be the full previous year."""
        date_from, date_to = DatePreset.last_year()
        today = date.today()
        expected_year = today.year - 1

        assert date_from == date(expected_year, 1, 1)
        assert date_to == date(expected_year, 12, 31)

    def test_all_time_returns_none(self):
        """All time should return None for both dates."""
        date_from, date_to = DatePreset.all_time()
        assert date_from is None
        assert date_to is None


class TestFilterCriteriaCombined:
    """Tests for combined filter scenarios."""

    def test_multiple_filters_all_must_match(self):
        """When multiple filters are set, all must match."""
        criteria = FilterCriteria(
            amount_min=10.0,
            amount_max=100.0,
            categories={"Food"},
            search_text="coffee"
        )

        # All conditions met
        assert (
            criteria.matches_amount(50.0)
            and criteria.matches_category("Food")
            and criteria.matches_search("coffee shop")
        )

        # Amount fails
        assert not criteria.matches_amount(5.0)

        # Category fails
        assert not criteria.matches_category("Entertainment")

        # Search fails
        assert not criteria.matches_search("grocery store")

    def test_filter_workflow(self):
        """Test a realistic filtering workflow."""
        criteria = FilterCriteria(
            date_from=date(2024, 1, 1),
            date_to=date(2024, 3, 31),
            categories={"Food", "Entertainment"},
            show_mapped=True,
            show_unmapped=False,
        )

        # Transaction that passes all filters
        assert criteria.matches_date(date(2024, 2, 15))
        assert criteria.matches_category("Food")
        assert criteria.matches_mapping_status(True)

        # Transaction outside date range
        assert not criteria.matches_date(date(2024, 4, 1))

        # Transaction in wrong category
        assert not criteria.matches_category("Transportation")

        # Unmapped transaction
        assert not criteria.matches_mapping_status(False)
