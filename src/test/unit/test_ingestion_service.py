"""Unit tests for features.ingestion.models."""

from __future__ import annotations

import pytest

from budget_analyser.features.ingestion.models import (
    IngestionResult,
    UploadResult,
)


class TestIngestionResult:
    """Tests for IngestionResult DTO."""

    def test_success(self) -> None:
        r = IngestionResult(
            success=True, message="ok",
            transactions_processed=10,
            transactions_inserted=8,
            duplicates_skipped=2,
        )
        assert r.success is True
        assert r.transactions_processed == 10
        assert r.transactions_inserted == 8
        assert r.duplicates_skipped == 2

    def test_failure(self) -> None:
        r = IngestionResult(success=False, message="bad csv")
        assert r.success is False
        assert r.transactions_processed == 0


class TestUploadResult:
    """Tests for UploadResult DTO."""

    def test_success(self) -> None:
        r = UploadResult(
            success=True, message="uploaded",
            destination_path="/tmp/foo.csv",
            transactions_inserted=5,
            duplicates_skipped=1,
        )
        assert r.success is True
        assert r.destination_path == "/tmp/foo.csv"

    def test_failure(self) -> None:
        r = UploadResult(success=False, message="invalid")
        assert r.destination_path is None
        assert r.transactions_inserted == 0
