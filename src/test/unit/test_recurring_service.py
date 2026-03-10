"""Unit tests for RecurringAnalyticsService and pure helper functions.

Tests cover:
- normalize_description: lowercasing, date/ref/ID stripping, whitespace collapsing
- estimate_frequency: mapping intervals to frequency buckets
- calculate_confidence: weighted confidence scoring with edge cases
- RecurringAnalyticsService: detection, CRUD delegation, analytics summaries
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

from budget_analyser.features.recurring.models import RecurringModel
from budget_analyser.features.recurring.service import (
    RecurringAnalyticsService,
    calculate_confidence,
    estimate_frequency,
    normalize_description,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db_path(tmp_path: Path) -> Path:
    """Create a temporary transactions DB with detectable recurring patterns."""
    db_path = tmp_path / "transactions.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE transactions (
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            category TEXT,
            sub_category TEXT
        )
    """)
    # Monthly Netflix pattern: 6 months (Jul-Dec 2025)
    for i in range(6):
        month = 7 + i
        d = date(2025, month, 15)
        conn.execute(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
            (d.isoformat(), "NETFLIX.COM", -15.99, "Entertainment", "Streaming"),
        )
    # Weekly gym pattern: 8 weeks starting 2025-10-01
    for i in range(8):
        d = date(2025, 10, 1) + timedelta(weeks=i)
        conn.execute(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
            (d.isoformat(), "GYM MEMBERSHIP #12345", -49.99, "Health", "Gym"),
        )
    # Irregular pattern (should NOT be detected as recurring)
    for d_str in ["2025-08-03", "2025-09-22", "2025-12-01"]:
        conn.execute(
            "INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
            (d_str, "RANDOM STORE", -25.00, "Shopping", "Misc"),
        )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture()
def model(tmp_path: Path) -> RecurringModel:
    """Create a RecurringModel backed by a temporary database."""
    db_path = tmp_path / "budget_goals.db"
    return RecurringModel(db_path=db_path)


@pytest.fixture()
def service(model: RecurringModel, tmp_db_path: Path) -> RecurringAnalyticsService:
    """Create a RecurringAnalyticsService wired to temporary databases."""
    return RecurringAnalyticsService(model=model, db_path=tmp_db_path)


# ---------------------------------------------------------------------------
# Pure function tests: normalize_description
# ---------------------------------------------------------------------------


class TestNormalizeDescription:
    """Tests for the normalize_description helper function."""

    def test_normalize_description_lowercase(self) -> None:
        assert normalize_description("NETFLIX.COM") == "netflix.com"

    def test_normalize_description_strips_trailing_date_mmdd(self) -> None:
        assert normalize_description("PAYMENT 01/15") == "payment"

    def test_normalize_description_strips_trailing_date_mmddyy(self) -> None:
        assert normalize_description("PAYMENT 01/15/24") == "payment"

    def test_normalize_description_strips_trailing_date_mmddyyyy(self) -> None:
        assert normalize_description("PAYMENT 01/15/2024") == "payment"

    def test_normalize_description_strips_trailing_ref(self) -> None:
        assert normalize_description("STORE #ABC123") == "store"

    def test_normalize_description_strips_trailing_ref_prefix(self) -> None:
        assert normalize_description("PAYMENT REF:XYZ789") == "payment"

    def test_normalize_description_strips_trailing_id(self) -> None:
        result = normalize_description("STORE 123456")
        assert result == "store"

    def test_normalize_description_collapses_whitespace(self) -> None:
        assert normalize_description("SOME  STORE   NAME") == "some store name"

    def test_normalize_description_strips_leading_trailing_space(self) -> None:
        assert normalize_description("  HELLO  ") == "hello"

    def test_normalize_description_empty_string(self) -> None:
        assert normalize_description("") == ""


# ---------------------------------------------------------------------------
# Pure function tests: estimate_frequency
# ---------------------------------------------------------------------------


class TestEstimateFrequency:
    """Tests for the estimate_frequency helper function."""

    def test_estimate_frequency_daily(self) -> None:
        assert estimate_frequency(1.0) == "daily"

    def test_estimate_frequency_weekly(self) -> None:
        assert estimate_frequency(7.0) == "weekly"

    def test_estimate_frequency_biweekly(self) -> None:
        assert estimate_frequency(14.0) == "bi-weekly"

    def test_estimate_frequency_monthly(self) -> None:
        assert estimate_frequency(30.0) == "monthly"

    def test_estimate_frequency_quarterly(self) -> None:
        assert estimate_frequency(90.0) == "quarterly"

    def test_estimate_frequency_semiannual(self) -> None:
        assert estimate_frequency(182.0) == "semi-annual"

    def test_estimate_frequency_yearly(self) -> None:
        assert estimate_frequency(365.0) == "yearly"

    def test_estimate_frequency_unknown_returns_none(self) -> None:
        assert estimate_frequency(50.0) is None

    def test_estimate_frequency_boundary_low_weekly(self) -> None:
        assert estimate_frequency(5.0) == "weekly"

    def test_estimate_frequency_boundary_high_weekly(self) -> None:
        assert estimate_frequency(9.0) == "weekly"

    def test_estimate_frequency_between_buckets_returns_none(self) -> None:
        # 3.0 is between daily (0-2) and weekly (5-9)
        assert estimate_frequency(3.0) is None


# ---------------------------------------------------------------------------
# Pure function tests: calculate_confidence
# ---------------------------------------------------------------------------


class TestCalculateConfidence:
    """Tests for the calculate_confidence scoring function."""

    def test_calculate_confidence_high_for_consistent(self) -> None:
        score = calculate_confidence(
            occurrences=12,
            interval_std=1.0,
            median_interval=30.0,
            amount_cv=0.01,
            days_since_last=15.0,
            expected_interval=30.0,
        )
        assert score > 0.7

    def test_calculate_confidence_low_for_inconsistent(self) -> None:
        score = calculate_confidence(
            occurrences=2,
            interval_std=25.0,
            median_interval=30.0,
            amount_cv=0.9,
            days_since_last=120.0,
            expected_interval=30.0,
        )
        assert score < 0.4

    def test_calculate_confidence_capped_at_one(self) -> None:
        score = calculate_confidence(
            occurrences=100,
            interval_std=0.0,
            median_interval=30.0,
            amount_cv=0.0,
            days_since_last=1.0,
            expected_interval=30.0,
        )
        assert score <= 1.0

    def test_calculate_confidence_minimum_is_zero(self) -> None:
        score = calculate_confidence(
            occurrences=1,
            interval_std=100.0,
            median_interval=1.0,
            amount_cv=5.0,
            days_since_last=999.0,
            expected_interval=1.0,
        )
        assert score >= 0.0

    def test_calculate_confidence_single_occurrence_zero_occ_score(self) -> None:
        score = calculate_confidence(
            occurrences=1,
            interval_std=0.0,
            median_interval=30.0,
            amount_cv=0.0,
            days_since_last=10.0,
            expected_interval=30.0,
        )
        # With 1 occurrence, occ_score=0.0 (30% weight zeroed out)
        # Max possible: 0.30*0 + 0.30*1 + 0.25*1 + 0.15*1 = 0.70
        assert score <= 0.70 + 1e-9

    def test_calculate_confidence_zero_median_interval(self) -> None:
        score = calculate_confidence(
            occurrences=5,
            interval_std=0.0,
            median_interval=0.0,
            amount_cv=0.0,
            days_since_last=0.0,
            expected_interval=30.0,
        )
        # median_interval=0 => interval_score=0
        assert 0.0 <= score <= 1.0

    def test_calculate_confidence_recency_decay_when_overdue(self) -> None:
        recent = calculate_confidence(
            occurrences=6,
            interval_std=2.0,
            median_interval=30.0,
            amount_cv=0.05,
            days_since_last=20.0,
            expected_interval=30.0,
        )
        overdue = calculate_confidence(
            occurrences=6,
            interval_std=2.0,
            median_interval=30.0,
            amount_cv=0.05,
            days_since_last=120.0,
            expected_interval=30.0,
        )
        assert recent > overdue


# ---------------------------------------------------------------------------
# Service tests: detect_recurring_transactions
# ---------------------------------------------------------------------------


class TestDetectRecurringTransactions:
    """Tests for RecurringAnalyticsService.detect_recurring_transactions."""

    def test_detect_recurring_finds_monthly_pattern(
        self, service: RecurringAnalyticsService,
    ) -> None:
        detections = service.detect_recurring_transactions()
        descriptions = [d.description.lower() for d in detections]
        assert any("netflix" in desc for desc in descriptions)

        netflix = next(d for d in detections if "netflix" in d.description.lower())
        assert netflix.frequency == "monthly"
        assert netflix.occurrences == 6

    def test_detect_recurring_finds_weekly_pattern(
        self, service: RecurringAnalyticsService,
    ) -> None:
        detections = service.detect_recurring_transactions()
        descriptions = [d.description.lower() for d in detections]
        assert any("gym" in desc for desc in descriptions)

        gym = next(d for d in detections if "gym" in d.description.lower())
        assert gym.frequency == "weekly"
        assert gym.occurrences == 8

    def test_detect_recurring_skips_irregular(
        self, service: RecurringAnalyticsService,
    ) -> None:
        detections = service.detect_recurring_transactions()
        descriptions = [d.description.lower() for d in detections]
        assert not any("random store" in desc for desc in descriptions)

    def test_detect_recurring_respects_threshold(
        self, service: RecurringAnalyticsService,
    ) -> None:
        low_threshold = service.detect_recurring_transactions(threshold=0.1)
        high_threshold = service.detect_recurring_transactions(threshold=0.99)
        assert len(low_threshold) >= len(high_threshold)

    def test_detect_recurring_empty_db(
        self, model: RecurringModel, tmp_path: Path,
    ) -> None:
        empty_db = tmp_path / "empty.db"
        conn = sqlite3.connect(str(empty_db))
        conn.execute("""
            CREATE TABLE transactions (
                transaction_date TEXT,
                description TEXT,
                amount REAL,
                category TEXT,
                sub_category TEXT
            )
        """)
        conn.commit()
        conn.close()

        svc = RecurringAnalyticsService(model=model, db_path=empty_db)
        assert svc.detect_recurring_transactions() == []

    def test_detect_recurring_skips_already_tracked(
        self, service: RecurringAnalyticsService, model: RecurringModel,
    ) -> None:
        # Add Netflix as already tracked
        model.save_recurring(
            description="NETFLIX.COM",
            expected_amount=15.99,
            amount_variance=0.0,
            frequency="monthly",
            category="Entertainment",
            sub_category="Streaming",
            last_occurrence=None,
            next_expected=None,
            confidence_score=0.9,
            user_confirmed=True,
            is_expected=True,
            is_active=True,
            detection_method="manual",
        )
        detections = service.detect_recurring_transactions()
        descriptions = [d.description.lower() for d in detections]
        assert not any("netflix" in desc for desc in descriptions)

    def test_detect_recurring_returns_sorted_by_confidence(
        self, service: RecurringAnalyticsService,
    ) -> None:
        detections = service.detect_recurring_transactions()
        if len(detections) >= 2:
            scores = [d.confidence_score for d in detections]
            assert scores == sorted(scores, reverse=True)


# ---------------------------------------------------------------------------
# Service tests: CRUD operations
# ---------------------------------------------------------------------------


class TestCrudOperations:
    """Tests for CRUD methods that delegate to RecurringModel."""

    def test_add_manual_recurring_creates_record(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Spotify Premium",
            expected_amount=9.99,
            frequency="monthly",
            category="Entertainment",
            sub_category="Music",
        )
        assert txn.description == "Spotify Premium"
        assert txn.expected_amount == 9.99
        assert txn.frequency == "monthly"
        assert txn.detection_method == "manual"
        assert txn.user_confirmed is True
        assert txn.is_expected is True
        assert txn.is_active is True
        assert txn.confidence_score == 1.0

    def test_add_manual_recurring_default_frequency(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Some Bill",
            expected_amount=50.0,
        )
        assert txn.frequency == "monthly"

    def test_confirm_detection_delegates(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Test Service",
            expected_amount=10.0,
        )
        confirmed = service.confirm_detection(txn.id)
        assert confirmed is not None
        assert confirmed.user_confirmed is True

    def test_confirm_detection_not_found_returns_none(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.confirm_detection(9999) is None

    def test_dismiss_detection_delegates(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Unwanted Service",
            expected_amount=5.0,
        )
        dismissed = service.dismiss_detection(txn.id)
        assert dismissed is not None
        assert dismissed.is_active is False

    def test_dismiss_detection_not_found_returns_none(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.dismiss_detection(9999) is None

    def test_mark_expected_sets_flag(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Toggleable",
            expected_amount=20.0,
        )
        updated = service.mark_expected(txn.id, is_expected=False)
        assert updated is not None
        assert updated.is_expected is False

    def test_update_recurring_changes_fields(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Updatable",
            expected_amount=30.0,
        )
        updated = service.update_recurring(txn.id, expected_amount=35.0)
        assert updated is not None
        assert updated.expected_amount == 35.0

    def test_update_recurring_not_found_returns_none(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.update_recurring(9999, expected_amount=1.0) is None

    def test_delete_recurring_removes_record(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Deletable",
            expected_amount=10.0,
        )
        assert service.delete_recurring(txn.id) is True
        # Verify it's gone
        all_recurring = service.get_all_recurring()
        assert not any(r.id == txn.id for r in all_recurring)

    def test_delete_recurring_not_found_returns_false(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.delete_recurring(9999) is False

    def test_get_all_recurring_returns_all(
        self, service: RecurringAnalyticsService,
    ) -> None:
        service.add_manual_recurring(description="A", expected_amount=10.0)
        service.add_manual_recurring(description="B", expected_amount=20.0)
        all_items = service.get_all_recurring()
        assert len(all_items) == 2

    def test_get_all_recurring_active_only(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn_a = service.add_manual_recurring(description="Active", expected_amount=10.0)
        service.add_manual_recurring(description="Dismissed", expected_amount=20.0)
        # Dismiss one
        service.dismiss_detection(
            service.get_all_recurring()[-1].id,
        )
        active = service.get_all_recurring(active_only=True)
        assert len(active) == 1
        assert active[0].id == txn_a.id


# ---------------------------------------------------------------------------
# Service tests: analytics
# ---------------------------------------------------------------------------


class TestAnalytics:
    """Tests for analytics methods: counts, costs, summaries."""

    def test_get_active_count(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.get_active_count() == 0
        service.add_manual_recurring(description="Sub1", expected_amount=10.0)
        service.add_manual_recurring(description="Sub2", expected_amount=20.0)
        assert service.get_active_count() == 2

    def test_get_active_count_excludes_dismissed(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(description="Gone", expected_amount=10.0)
        service.dismiss_detection(txn.id)
        assert service.get_active_count() == 0

    def test_get_monthly_recurring_cost_single_monthly(
        self, service: RecurringAnalyticsService,
    ) -> None:
        service.add_manual_recurring(
            description="Monthly Sub",
            expected_amount=-15.99,
            frequency="monthly",
        )
        cost = service.get_monthly_recurring_cost()
        assert cost == pytest.approx(15.99, abs=0.01)

    def test_get_monthly_recurring_cost_normalizes_frequencies(
        self, service: RecurringAnalyticsService,
    ) -> None:
        # Weekly at $10 => $10 * 4.33 = $43.30/month
        service.add_manual_recurring(
            description="Weekly Sub",
            expected_amount=-10.0,
            frequency="weekly",
        )
        # Monthly at $20 => $20 * 1.0 = $20.00/month
        service.add_manual_recurring(
            description="Monthly Sub",
            expected_amount=-20.0,
            frequency="monthly",
        )
        cost = service.get_monthly_recurring_cost()
        expected = (10.0 * 4.33) + (20.0 * 1.0)
        assert cost == pytest.approx(expected, abs=0.01)

    def test_get_monthly_recurring_cost_quarterly(
        self, service: RecurringAnalyticsService,
    ) -> None:
        service.add_manual_recurring(
            description="Quarterly Bill",
            expected_amount=-90.0,
            frequency="quarterly",
        )
        cost = service.get_monthly_recurring_cost()
        expected = 90.0 * (1.0 / 3.0)
        assert cost == pytest.approx(expected, abs=0.01)

    def test_get_monthly_recurring_cost_excludes_dismissed(
        self, service: RecurringAnalyticsService,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Cancelled",
            expected_amount=-50.0,
        )
        service.dismiss_detection(txn.id)
        assert service.get_monthly_recurring_cost() == 0.0

    def test_get_summary_aggregates_correctly(
        self, service: RecurringAnalyticsService,
    ) -> None:
        service.add_manual_recurring(
            description="Netflix",
            expected_amount=-15.99,
            frequency="monthly",
            category="Entertainment",
        )
        service.add_manual_recurring(
            description="Gym",
            expected_amount=-49.99,
            frequency="weekly",
            category="Health",
        )
        summary = service.get_summary()

        assert summary.active_count == 2
        assert summary.confirmed_count == 2  # manual => user_confirmed=True
        assert summary.unconfirmed_count == 0

        # Check by_frequency
        assert summary.by_frequency.get("monthly") == 1
        assert summary.by_frequency.get("weekly") == 1

        # Check by_category has both categories
        assert "Entertainment" in summary.by_category
        assert "Health" in summary.by_category

        # Monthly cost should match get_monthly_recurring_cost
        assert summary.total_monthly_cost == service.get_monthly_recurring_cost()
        assert summary.total_yearly_projection == pytest.approx(
            summary.total_monthly_cost * 12, abs=0.01,
        )

    def test_get_summary_empty(
        self, service: RecurringAnalyticsService,
    ) -> None:
        summary = service.get_summary()
        assert summary.active_count == 0
        assert summary.total_monthly_cost == 0.0
        assert summary.total_yearly_projection == 0.0


# ---------------------------------------------------------------------------
# Service tests: anomalies
# ---------------------------------------------------------------------------


class TestAnomalyDetection:
    """Tests for anomaly detection and resolution."""

    def test_resolve_anomaly_delegates(
        self, service: RecurringAnalyticsService, model: RecurringModel,
    ) -> None:
        # Create a recurring and a manual anomaly
        txn = service.add_manual_recurring(
            description="Test",
            expected_amount=-10.0,
        )
        anomaly = model.save_anomaly(
            recurring_id=txn.id,
            anomaly_type="missed_payment",
            expected_date="2025-12-01",
            actual_date=None,
            expected_amount=-10.0,
            actual_amount=None,
            severity="warning",
            message="Test anomaly",
        )
        assert service.resolve_anomaly(anomaly.id) is True

    def test_resolve_anomaly_not_found_returns_false(
        self, service: RecurringAnalyticsService,
    ) -> None:
        assert service.resolve_anomaly(9999) is False

    def test_get_anomalies_returns_unresolved(
        self, service: RecurringAnalyticsService, model: RecurringModel,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Anomalous",
            expected_amount=-10.0,
        )
        model.save_anomaly(
            recurring_id=txn.id,
            anomaly_type="amount_spike",
            expected_date=None,
            actual_date="2025-12-01",
            expected_amount=-10.0,
            actual_amount=-50.0,
            severity="critical",
            message="Spike detected",
        )
        anomalies = service.get_anomalies()
        assert len(anomalies) == 1
        assert anomalies[0].anomaly_type == "amount_spike"

    def test_get_anomalies_excludes_resolved(
        self, service: RecurringAnalyticsService, model: RecurringModel,
    ) -> None:
        txn = service.add_manual_recurring(
            description="Resolved Item",
            expected_amount=-10.0,
        )
        anomaly = model.save_anomaly(
            recurring_id=txn.id,
            anomaly_type="missed_payment",
            expected_date="2025-12-01",
            actual_date=None,
            expected_amount=-10.0,
            actual_amount=None,
            severity="warning",
            message="Was missed",
        )
        model.resolve_anomaly(anomaly.id)
        assert service.get_anomalies() == []
