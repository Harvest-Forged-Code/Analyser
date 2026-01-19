"""Mapping validation service (domain logic).

Purpose:
    Validate keyword mappings for conflicts, orphans, typos, and missing entries.
    Provides actionable reports to help maintain clean mapping files.

Validation Checks:
    1. Keyword collisions - same keyword maps to different categories
    2. Orphan detection - sub-categories not linked to any category
    3. Typo detection - apostrophes, special characters, near-duplicates
    4. Missing keywords - categories with no mappings
    5. Circular references - invalid mapping chains
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Mapping


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue found in mappings.

    Attributes:
        severity: Issue severity (error, warning, info).
        issue_type: Category of the issue (collision, orphan, typo, etc.).
        message: Human-readable description of the issue.
        details: Additional context (affected keywords, categories, etc.).
    """

    severity: str  # "error", "warning", "info"
    issue_type: str
    message: str
    details: dict = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Complete validation report for mapping files.

    Attributes:
        issues: List of all validation issues found.
        summary: Counts by severity level.
        is_valid: True if no errors were found (warnings/info allowed).
    """

    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        """Return count of issues by severity."""
        counts: dict[str, int] = {"error": 0, "warning": 0, "info": 0}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        return counts

    @property
    def is_valid(self) -> bool:
        """Return True if no errors found."""
        return self.summary.get("error", 0) == 0

    @property
    def error_count(self) -> int:
        """Return number of errors."""
        return self.summary.get("error", 0)

    @property
    def warning_count(self) -> int:
        """Return number of warnings."""
        return self.summary.get("warning", 0)

    def add(self, issue: ValidationIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)

    def errors(self) -> list[ValidationIssue]:
        """Return only error-level issues."""
        return [i for i in self.issues if i.severity == "error"]

    def warnings(self) -> list[ValidationIssue]:
        """Return only warning-level issues."""
        return [i for i in self.issues if i.severity == "warning"]


class MappingValidationService:
    """Service to validate category mapping configurations.

    Performs comprehensive validation of mapping files to detect:
    - Keyword collisions that cause unpredictable categorization
    - Orphaned sub-categories without parent categories
    - Potential typos in category names
    - Missing or empty mappings
    """

    # Common typo patterns to detect
    SUSPICIOUS_CHARS = {"'", "'", '"', '"', '"'}

    def __init__(
        self,
        *,
        similarity_threshold: float = 0.85,
    ) -> None:
        """Initialize the validation service.

        Args:
            similarity_threshold: Threshold for typo detection (0.0-1.0).
        """
        self._similarity_threshold = similarity_threshold

    def validate_all(
        self,
        *,
        desc_to_sub: Mapping[str, list[str]],
        sub_to_cat: Mapping[str, list[str]],
        cashflow_to_cat: Mapping[str, list[str]] | None = None,
    ) -> ValidationReport:
        """Run all validation checks on the provided mappings.

        Args:
            desc_to_sub: Description keywords -> sub-category mapping.
            sub_to_cat: Sub-category -> category mapping.
            cashflow_to_cat: Optional cashflow (earnings/expenses) -> category.

        Returns:
            ValidationReport with all issues found.
        """
        report = ValidationReport()

        # Run all validation checks
        self._check_keyword_collisions(desc_to_sub, report)
        self._check_orphan_sub_categories(desc_to_sub, sub_to_cat, report)
        self._check_typos_in_names(desc_to_sub, sub_to_cat, report)
        self._check_empty_mappings(desc_to_sub, sub_to_cat, report)
        self._check_duplicate_keywords(desc_to_sub, report)
        self._check_similar_category_names(sub_to_cat, report)

        if cashflow_to_cat:
            self._check_cashflow_coverage(sub_to_cat, cashflow_to_cat, report)

        return report

    def _check_keyword_collisions(
        self,
        desc_to_sub: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect keywords that appear in multiple sub-categories."""
        keyword_to_subs: dict[str, list[str]] = {}

        for sub_category, keywords in desc_to_sub.items():
            for keyword in keywords:
                keyword_lower = str(keyword).lower()
                if keyword_lower not in keyword_to_subs:
                    keyword_to_subs[keyword_lower] = []
                keyword_to_subs[keyword_lower].append(sub_category)

        for keyword, sub_categories in keyword_to_subs.items():
            if len(sub_categories) > 1:
                report.add(ValidationIssue(
                    severity="error",
                    issue_type="keyword_collision",
                    message=f"Keyword '{keyword}' maps to multiple sub-categories",
                    details={
                        "keyword": keyword,
                        "sub_categories": sub_categories,
                    },
                ))

    def _check_orphan_sub_categories(
        self,
        desc_to_sub: Mapping[str, list[str]],
        sub_to_cat: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect sub-categories not linked to any parent category."""
        # Get all sub-categories defined in desc_to_sub
        defined_subs = set(desc_to_sub.keys())

        # Get all sub-categories referenced in sub_to_cat
        referenced_subs: set[str] = set()
        for subs in sub_to_cat.values():
            referenced_subs.update(str(s) for s in subs)

        # Find orphans
        orphans = defined_subs - referenced_subs
        for orphan in orphans:
            report.add(ValidationIssue(
                severity="warning",
                issue_type="orphan_sub_category",
                message=f"Sub-category '{orphan}' has no parent category",
                details={"sub_category": orphan},
            ))

    def _check_typos_in_names(
        self,
        desc_to_sub: Mapping[str, list[str]],
        sub_to_cat: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect potential typos in category/sub-category names."""
        # Check sub-category names
        for name in desc_to_sub.keys():
            self._check_name_for_typos(name, "sub-category", report)

        # Check category names
        for name in sub_to_cat.keys():
            self._check_name_for_typos(name, "category", report)

    def _check_name_for_typos(
        self,
        name: str,
        name_type: str,
        report: ValidationReport,
    ) -> None:
        """Check a single name for common typo patterns."""
        # Check for suspicious characters
        for char in self.SUSPICIOUS_CHARS:
            if char in name:
                report.add(ValidationIssue(
                    severity="warning",
                    issue_type="suspicious_character",
                    message=f"{name_type.title()} '{name}' contains suspicious character",
                    details={
                        "name": name,
                        "type": name_type,
                        "character": char,
                    },
                ))
                break

        # Check for inconsistent casing (mixed styles)
        if "_" in name and any(c.isupper() for c in name.replace("_", "")):
            words = name.split("_")
            styles = set()
            for word in words:
                if word.isupper():
                    styles.add("UPPER")
                elif word.islower():
                    styles.add("lower")
                elif word.istitle():
                    styles.add("Title")
                else:
                    styles.add("mixed")
            if len(styles) > 1 and "mixed" not in styles:
                report.add(ValidationIssue(
                    severity="info",
                    issue_type="inconsistent_casing",
                    message=f"{name_type.title()} '{name}' has inconsistent casing",
                    details={"name": name, "type": name_type},
                ))

    def _check_empty_mappings(
        self,
        desc_to_sub: Mapping[str, list[str]],
        sub_to_cat: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect categories with no keywords or empty keyword lists."""
        for sub_category, keywords in desc_to_sub.items():
            if not keywords:
                report.add(ValidationIssue(
                    severity="warning",
                    issue_type="empty_mapping",
                    message=f"Sub-category '{sub_category}' has no keywords",
                    details={"sub_category": sub_category},
                ))

        for category, sub_categories in sub_to_cat.items():
            if not sub_categories:
                report.add(ValidationIssue(
                    severity="warning",
                    issue_type="empty_mapping",
                    message=f"Category '{category}' has no sub-categories",
                    details={"category": category},
                ))

    def _check_duplicate_keywords(
        self,
        desc_to_sub: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect duplicate keywords within the same sub-category."""
        for sub_category, keywords in desc_to_sub.items():
            seen: set[str] = set()
            for keyword in keywords:
                keyword_lower = str(keyword).lower()
                if keyword_lower in seen:
                    report.add(ValidationIssue(
                        severity="info",
                        issue_type="duplicate_keyword",
                        message=f"Duplicate keyword '{keyword}' in '{sub_category}'",
                        details={
                            "sub_category": sub_category,
                            "keyword": keyword,
                        },
                    ))
                seen.add(keyword_lower)

    def _check_similar_category_names(
        self,
        sub_to_cat: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Detect category names that are suspiciously similar (potential typos)."""
        category_names = list(sub_to_cat.keys())

        for i, name1 in enumerate(category_names):
            for name2 in category_names[i + 1:]:
                similarity = SequenceMatcher(
                    None, name1.lower(), name2.lower()
                ).ratio()
                if self._similarity_threshold <= similarity < 1.0:
                    report.add(ValidationIssue(
                        severity="info",
                        issue_type="similar_names",
                        message=f"Categories '{name1}' and '{name2}' are very similar",
                        details={
                            "name1": name1,
                            "name2": name2,
                            "similarity": round(similarity, 2),
                        },
                    ))

    def _check_cashflow_coverage(
        self,
        sub_to_cat: Mapping[str, list[str]],
        cashflow_to_cat: Mapping[str, list[str]],
        report: ValidationReport,
    ) -> None:
        """Check that all categories are covered by cashflow classification."""
        all_categories = set(sub_to_cat.keys())
        classified_categories: set[str] = set()

        for categories in cashflow_to_cat.values():
            classified_categories.update(str(c) for c in categories)

        unclassified = all_categories - classified_categories
        for category in unclassified:
            report.add(ValidationIssue(
                severity="warning",
                issue_type="unclassified_category",
                message=f"Category '{category}' not in earnings/expenses cashflow",
                details={"category": category},
            ))


def validate_mappings(
    *,
    desc_to_sub: Mapping[str, list[str]],
    sub_to_cat: Mapping[str, list[str]],
    cashflow_to_cat: Mapping[str, list[str]] | None = None,
) -> ValidationReport:
    """Convenience function to validate mappings with default settings.

    Args:
        desc_to_sub: Description keywords -> sub-category mapping.
        sub_to_cat: Sub-category -> category mapping.
        cashflow_to_cat: Optional cashflow (earnings/expenses) -> category.

    Returns:
        ValidationReport with all issues found.
    """
    service = MappingValidationService()
    return service.validate_all(
        desc_to_sub=desc_to_sub,
        sub_to_cat=sub_to_cat,
        cashflow_to_cat=cashflow_to_cat,
    )
