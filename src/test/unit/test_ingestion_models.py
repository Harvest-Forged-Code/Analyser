"""Tests for ingestion feature DTOs."""

from __future__ import annotations

import pytest

from budget_analyser.features.ingestion.models import (
    ValidationResult,
    UploadStats,
    UploadHistoryEntry,
)


class TestValidationResult:
    """Tests for the ValidationResult frozen dataclass."""

    def test_instantiation_minimal(self) -> None:
        result = ValidationResult(valid=True, message="OK")
        assert result.valid is True
        assert result.message == "OK"
        assert result.row_count == 0
        assert result.date_range == ""

    def test_instantiation_full(self) -> None:
        result = ValidationResult(
            valid=False,
            message="Missing columns",
            row_count=100,
            date_range="2024-01 to 2024-12",
        )
        assert result.valid is False
        assert result.row_count == 100
        assert result.date_range == "2024-01 to 2024-12"

    def test_frozen(self) -> None:
        result = ValidationResult(valid=True, message="OK")
        with pytest.raises(AttributeError):
            result.valid = False  # type: ignore[misc]


class TestUploadStats:
    """Tests for the UploadStats frozen dataclass."""

    def test_instantiation(self) -> None:
        stats = UploadStats(
            total_transactions=500,
            total_accounts=3,
            last_upload_date="2024-06-15",
            total_uploads=10,
            total_duplicates_skipped=25,
            duplicate_rate=4.8,
        )
        assert stats.total_transactions == 500
        assert stats.total_accounts == 3
        assert stats.last_upload_date == "2024-06-15"
        assert stats.total_uploads == 10
        assert stats.total_duplicates_skipped == 25
        assert stats.duplicate_rate == 4.8

    def test_last_upload_date_none(self) -> None:
        stats = UploadStats(
            total_transactions=0,
            total_accounts=0,
            last_upload_date=None,
            total_uploads=0,
            total_duplicates_skipped=0,
            duplicate_rate=0.0,
        )
        assert stats.last_upload_date is None

    def test_frozen(self) -> None:
        stats = UploadStats(
            total_transactions=0,
            total_accounts=0,
            last_upload_date=None,
            total_uploads=0,
            total_duplicates_skipped=0,
            duplicate_rate=0.0,
        )
        with pytest.raises(AttributeError):
            stats.total_transactions = 1  # type: ignore[misc]


class TestUploadHistoryEntry:
    """Tests for the UploadHistoryEntry frozen dataclass."""

    def test_instantiation(self) -> None:
        entry = UploadHistoryEntry(
            file_name="citi.csv",
            bank_name="citi",
            account_type="credit",
            uploaded_at="2024-06-15 10:30:00",
            transactions_inserted=45,
            duplicates_skipped=5,
        )
        assert entry.file_name == "citi.csv"
        assert entry.bank_name == "citi"
        assert entry.account_type == "credit"
        assert entry.uploaded_at == "2024-06-15 10:30:00"
        assert entry.transactions_inserted == 45
        assert entry.duplicates_skipped == 5

    def test_frozen(self) -> None:
        entry = UploadHistoryEntry(
            file_name="citi.csv",
            bank_name="citi",
            account_type="credit",
            uploaded_at="2024-06-15",
            transactions_inserted=0,
            duplicates_skipped=0,
        )
        with pytest.raises(AttributeError):
            entry.file_name = "other.csv"  # type: ignore[misc]
