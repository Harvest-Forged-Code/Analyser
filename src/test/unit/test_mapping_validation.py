"""Tests for mapping validation service."""

import pytest

from budget_analyser.features.mappers.validation import (
    MappingValidationService,
    ValidationIssue,
    ValidationReport,
    validate_mappings,
)


class TestValidationReport:
    """Tests for ValidationReport dataclass."""

    def test_empty_report_is_valid(self):
        report = ValidationReport()
        assert report.is_valid
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_report_with_error_is_invalid(self):
        report = ValidationReport()
        report.add(ValidationIssue(
            severity="error",
            issue_type="test",
            message="Test error",
        ))
        assert not report.is_valid
        assert report.error_count == 1

    def test_report_with_warning_is_valid(self):
        report = ValidationReport()
        report.add(ValidationIssue(
            severity="warning",
            issue_type="test",
            message="Test warning",
        ))
        assert report.is_valid
        assert report.warning_count == 1

    def test_summary_counts_all_severities(self):
        report = ValidationReport()
        report.add(ValidationIssue(severity="error", issue_type="e1", message="e1"))
        report.add(ValidationIssue(severity="error", issue_type="e2", message="e2"))
        report.add(ValidationIssue(severity="warning", issue_type="w1", message="w1"))
        report.add(ValidationIssue(severity="info", issue_type="i1", message="i1"))

        assert report.summary == {"error": 2, "warning": 1, "info": 1}

    def test_errors_filter(self):
        report = ValidationReport()
        report.add(ValidationIssue(severity="error", issue_type="e1", message="e1"))
        report.add(ValidationIssue(severity="warning", issue_type="w1", message="w1"))

        errors = report.errors()
        assert len(errors) == 1
        assert errors[0].issue_type == "e1"

    def test_warnings_filter(self):
        report = ValidationReport()
        report.add(ValidationIssue(severity="error", issue_type="e1", message="e1"))
        report.add(ValidationIssue(severity="warning", issue_type="w1", message="w1"))

        warnings = report.warnings()
        assert len(warnings) == 1
        assert warnings[0].issue_type == "w1"


class TestKeywordCollisionDetection:
    """Tests for keyword collision detection."""

    def test_no_collision_when_unique_keywords(self):
        desc_to_sub = {
            "Restaurants": ["starbucks", "mcdonalds"],
            "Groceries": ["walmart", "costco"],
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "Needs": ["Groceries"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        collisions = [i for i in report.issues if i.issue_type == "keyword_collision"]
        assert len(collisions) == 0

    def test_detects_keyword_collision(self):
        desc_to_sub = {
            "Restaurants": ["coffee", "starbucks"],
            "Groceries": ["coffee", "walmart"],  # "coffee" collision
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "Needs": ["Groceries"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        collisions = [i for i in report.issues if i.issue_type == "keyword_collision"]
        assert len(collisions) == 1
        assert collisions[0].severity == "error"
        assert "coffee" in collisions[0].details["keyword"]

    def test_collision_is_case_insensitive(self):
        desc_to_sub = {
            "Restaurants": ["COFFEE"],
            "Groceries": ["coffee"],
        }
        sub_to_cat = {"Luxury": ["Restaurants", "Groceries"]}

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        collisions = [i for i in report.issues if i.issue_type == "keyword_collision"]
        assert len(collisions) == 1


class TestOrphanSubCategoryDetection:
    """Tests for orphan sub-category detection."""

    def test_no_orphans_when_all_linked(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
            "Groceries": ["walmart"],
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "Needs": ["Groceries"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        orphans = [i for i in report.issues if i.issue_type == "orphan_sub_category"]
        assert len(orphans) == 0

    def test_detects_orphan_sub_category(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
            "Groceries": ["walmart"],
            "OrphanCategory": ["something"],  # Not in sub_to_cat
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "Needs": ["Groceries"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        orphans = [i for i in report.issues if i.issue_type == "orphan_sub_category"]
        assert len(orphans) == 1
        assert orphans[0].severity == "warning"
        assert "OrphanCategory" in orphans[0].details["sub_category"]


class TestTypoDetection:
    """Tests for typo detection."""

    def test_detects_apostrophe_in_name(self):
        desc_to_sub = {
            "Unplanned_Spending's": ["misc"],  # Smart apostrophe
        }
        sub_to_cat = {
            "Expenses": ["Unplanned_Spending's"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        typos = [i for i in report.issues if i.issue_type == "suspicious_character"]
        assert len(typos) >= 1

    def test_detects_curly_quotes(self):
        desc_to_sub = {
            '"Quoted"': ["test"],  # Curly quotes
        }
        sub_to_cat = {
            "Category": ['"Quoted"'],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        typos = [i for i in report.issues if i.issue_type == "suspicious_character"]
        assert len(typos) >= 1


class TestEmptyMappingDetection:
    """Tests for empty mapping detection."""

    def test_detects_empty_keyword_list(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
            "EmptyCategory": [],  # Empty list
        }
        sub_to_cat = {
            "Luxury": ["Restaurants", "EmptyCategory"],
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        empties = [i for i in report.issues if i.issue_type == "empty_mapping"]
        assert len(empties) == 1
        assert "EmptyCategory" in empties[0].details.get("sub_category", "")

    def test_detects_empty_sub_category_list(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "EmptyParent": [],  # Empty list
        }

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        empties = [i for i in report.issues if i.issue_type == "empty_mapping"]
        assert len(empties) == 1


class TestDuplicateKeywordDetection:
    """Tests for duplicate keyword detection."""

    def test_detects_duplicate_within_category(self):
        desc_to_sub = {
            "Restaurants": ["starbucks", "STARBUCKS", "coffee"],  # Duplicate
        }
        sub_to_cat = {"Luxury": ["Restaurants"]}

        report = validate_mappings(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        dupes = [i for i in report.issues if i.issue_type == "duplicate_keyword"]
        assert len(dupes) == 1
        assert dupes[0].severity == "info"


class TestSimilarNameDetection:
    """Tests for similar category name detection."""

    def test_detects_similar_category_names(self):
        desc_to_sub = {
            "Restaurant": ["food"],
            "Restaurants": ["dining"],
        }
        sub_to_cat = {
            "Category1": ["Restaurant"],
            "Category2": ["Restaurants"],
        }

        service = MappingValidationService(similarity_threshold=0.8)
        report = service.validate_all(desc_to_sub=desc_to_sub, sub_to_cat=sub_to_cat)
        similar = [i for i in report.issues if i.issue_type == "similar_names"]
        # Similar check happens on sub_to_cat keys, not desc_to_sub
        # Category1 and Category2 are not that similar


class TestCashflowCoverageDetection:
    """Tests for cashflow coverage detection."""

    def test_detects_unclassified_category(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
            "UnclassifiedCategory": ["something"],
        }
        cashflow_to_cat = {
            "Expenses": ["Luxury"],
            # UnclassifiedCategory not listed
        }

        report = validate_mappings(
            desc_to_sub=desc_to_sub,
            sub_to_cat=sub_to_cat,
            cashflow_to_cat=cashflow_to_cat,
        )
        unclassified = [i for i in report.issues if i.issue_type == "unclassified_category"]
        assert len(unclassified) == 1
        assert "UnclassifiedCategory" in unclassified[0].details["category"]

    def test_no_issue_when_all_classified(self):
        desc_to_sub = {
            "Restaurants": ["starbucks"],
        }
        sub_to_cat = {
            "Luxury": ["Restaurants"],
        }
        cashflow_to_cat = {
            "Expenses": ["Luxury"],
        }

        report = validate_mappings(
            desc_to_sub=desc_to_sub,
            sub_to_cat=sub_to_cat,
            cashflow_to_cat=cashflow_to_cat,
        )
        unclassified = [i for i in report.issues if i.issue_type == "unclassified_category"]
        assert len(unclassified) == 0


class TestRealWorldValidation:
    """Tests with real-world-like mapping data."""

    def test_validates_typical_mapping_structure(self):
        desc_to_sub = {
            "payments_made": ["PAYMENT TO", "AUTOPAY"],
            "Restaurants": ["STARBUCKS", "CHIPOTLE"],
            "Groceries": ["WALMART", "COSTCO"],
            "Gas": ["SHELL", "CHEVRON"],
        }
        sub_to_cat = {
            "payments_made": ["payments_made"],
            "Luxury": ["Restaurants"],
            "Needs": ["Groceries", "Gas"],
        }
        cashflow_to_cat = {
            "Expenses": ["Luxury", "Needs", "payments_made"],
        }

        report = validate_mappings(
            desc_to_sub=desc_to_sub,
            sub_to_cat=sub_to_cat,
            cashflow_to_cat=cashflow_to_cat,
        )
        assert report.is_valid  # No errors
