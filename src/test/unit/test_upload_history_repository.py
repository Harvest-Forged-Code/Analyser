"""Tests for the UploadHistoryRepository."""

from __future__ import annotations

from pathlib import Path

import pytest

from budget_analyser.features.ingestion.models import (
    UploadHistoryModel as UploadHistoryRepository,
)


@pytest.fixture()
def repo(tmp_path: Path) -> UploadHistoryRepository:
    """Create a fresh UploadHistoryRepository with a temp DB."""
    return UploadHistoryRepository(
        db_path=tmp_path / "test.db",
    )


class TestSaveUpload:
    """Tests for save_upload."""

    def test_save_upload_records_entry(
        self, repo: UploadHistoryRepository,
    ) -> None:
        repo.save_upload(
            file_name="citi.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=50,
        )
        history = repo.get_recent_history(limit=10)
        assert len(history) == 1
        assert history[0].file_name == "citi.csv"
        assert history[0].bank_name == "citi"
        assert history[0].account_type == "credit"
        assert history[0].transactions_inserted == 50


class TestGetStats:
    """Tests for get_stats."""

    def test_stats_empty_database(
        self, repo: UploadHistoryRepository,
    ) -> None:
        stats = repo.get_stats()
        assert stats.total_uploads == 0
        assert stats.last_upload_date is None
        assert stats.total_accounts == 0

    def test_stats_after_uploads(
        self, repo: UploadHistoryRepository,
    ) -> None:
        repo.save_upload(
            file_name="citi.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=50,
        )
        repo.save_upload(
            file_name="discover.csv",
            bank_name="discover",
            account_type="credit",
            transactions_inserted=30,
        )

        stats = repo.get_stats()
        assert stats.total_uploads == 2
        assert stats.total_accounts == 2
        assert stats.last_upload_date is not None

    def test_stats_same_bank_counts_as_one_account(
        self, repo: UploadHistoryRepository,
    ) -> None:
        repo.save_upload(
            file_name="citi_jan.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=20,
        )
        repo.save_upload(
            file_name="citi_feb.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=25,
        )

        stats = repo.get_stats()
        assert stats.total_uploads == 2
        assert stats.total_accounts == 1


class TestGetRecentHistory:
    """Tests for get_recent_history."""

    def test_empty_database(
        self, repo: UploadHistoryRepository,
    ) -> None:
        history = repo.get_recent_history(limit=10)
        assert history == []

    def test_returns_entries_in_reverse_chronological_order(
        self, repo: UploadHistoryRepository,
    ) -> None:
        repo.save_upload(
            file_name="first.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=10,
        )
        repo.save_upload(
            file_name="second.csv",
            bank_name="discover",
            account_type="credit",
            transactions_inserted=20,
        )

        history = repo.get_recent_history(limit=10)
        assert len(history) == 2
        assert history[0].file_name == "second.csv"
        assert history[1].file_name == "first.csv"

    def test_limit_restricts_results(
        self, repo: UploadHistoryRepository,
    ) -> None:
        for i in range(5):
            repo.save_upload(
                file_name=f"file_{i}.csv",
                bank_name="citi",
                account_type="credit",
                transactions_inserted=i * 10,
            )

        history = repo.get_recent_history(limit=3)
        assert len(history) == 3
