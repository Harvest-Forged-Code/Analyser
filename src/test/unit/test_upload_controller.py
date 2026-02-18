"""Tests for the UploadController new methods.

Covers get_upload_stats, get_recent_history, and
upload_statement recording history.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from budget_analyser.features.ingestion.service import (
    UploadController,
)
from budget_analyser.features.ingestion.models import (
    UploadStats,
    UploadHistoryEntry,
    IngestionResult,
)
from budget_analyser.features.ingestion.models import (
    UploadHistoryModel as UploadHistoryRepository,
)


@pytest.fixture()
def mock_ini_config() -> MagicMock:
    """Create a mock IniAppConfig."""
    config = MagicMock()
    config.list_accounts.return_value = ["citi", "discover"]
    config.get_statement_filename.return_value = "citi.csv"
    config.get_column_mapping.return_value = {
        "Date": "transaction_date",
        "Description": "description",
        "Amount": "amount",
    }
    return config


@pytest.fixture()
def history_repo(tmp_path: Path) -> UploadHistoryRepository:
    """Create a real UploadHistoryRepository with a temp DB."""
    return UploadHistoryRepository(
        db_path=tmp_path / "test_history.db",
    )


@pytest.fixture()
def controller(
    tmp_path: Path,
    mock_ini_config: MagicMock,
    history_repo: UploadHistoryRepository,
) -> UploadController:
    """Create an UploadController with a real history repo."""
    statements = tmp_path / "statements"
    statements.mkdir()
    return UploadController(
        logger=logging.getLogger("test"),
        ini_config=mock_ini_config,
        statements_dir=statements,
        upload_history_repo=history_repo,
    )


@pytest.fixture()
def controller_no_repo(
    tmp_path: Path,
    mock_ini_config: MagicMock,
) -> UploadController:
    """Create an UploadController without history repo."""
    statements = tmp_path / "statements"
    statements.mkdir()
    return UploadController(
        logger=logging.getLogger("test"),
        ini_config=mock_ini_config,
        statements_dir=statements,
    )


class TestGetUploadStats:
    """Tests for get_upload_stats."""

    def test_returns_empty_stats_without_repo(
        self, controller_no_repo: UploadController,
    ) -> None:
        stats = controller_no_repo.get_upload_stats()
        assert stats.total_uploads == 0
        assert stats.total_transactions == 0
        assert stats.total_accounts == 0
        assert stats.last_upload_date is None
        assert stats.duplicate_rate == 0.0

    def test_delegates_to_repository(
        self, controller: UploadController,
        history_repo: UploadHistoryRepository,
    ) -> None:
        history_repo.save_upload(
            file_name="citi.csv",
            bank_name="citi",
            account_type="credit",
            transactions_inserted=40,
            duplicates_skipped=5,
        )
        stats = controller.get_upload_stats()
        assert stats.total_uploads == 1
        assert stats.total_duplicates_skipped == 5


class TestGetRecentHistory:
    """Tests for get_recent_history."""

    def test_returns_empty_list_without_repo(
        self, controller_no_repo: UploadController,
    ) -> None:
        history = controller_no_repo.get_recent_history()
        assert history == []

    def test_delegates_to_repository(
        self, controller: UploadController,
        history_repo: UploadHistoryRepository,
    ) -> None:
        history_repo.save_upload(
            file_name="discover.csv",
            bank_name="discover",
            account_type="credit",
            transactions_inserted=25,
            duplicates_skipped=2,
        )
        history = controller.get_recent_history(limit=5)
        assert len(history) == 1
        assert history[0].file_name == "discover.csv"

    def test_respects_limit(
        self, controller: UploadController,
        history_repo: UploadHistoryRepository,
    ) -> None:
        for i in range(5):
            history_repo.save_upload(
                file_name=f"file_{i}.csv",
                bank_name="citi",
                account_type="credit",
                transactions_inserted=i * 10,
                duplicates_skipped=0,
            )
        history = controller.get_recent_history(limit=2)
        assert len(history) == 2


class TestUploadStatementRecordsHistory:
    """Tests that upload_statement records history."""

    def _create_csv(self, path: Path) -> None:
        """Write a minimal valid CSV file."""
        path.write_text(
            "Date,Description,Amount\n"
            "2024-01-15,Grocery Store,50.00\n",
        )

    def test_successful_upload_records_history(
        self,
        controller: UploadController,
        history_repo: UploadHistoryRepository,
        tmp_path: Path,
    ) -> None:
        csv_file = tmp_path / "citi.csv"
        self._create_csv(csv_file)

        result = controller.upload_statement(
            source_path=csv_file,
            bank_name="citi",
            account_type="credit",
        )
        assert result.success is True

        history = history_repo.get_recent_history(limit=10)
        assert len(history) == 1
        assert history[0].file_name == "citi.csv"
        assert history[0].bank_name == "citi"
        assert history[0].account_type == "credit"

    def test_failed_validation_does_not_record_history(
        self,
        controller: UploadController,
        history_repo: UploadHistoryRepository,
        tmp_path: Path,
    ) -> None:
        nonexistent = tmp_path / "nonexistent.csv"

        result = controller.upload_statement(
            source_path=nonexistent,
            bank_name="citi",
            account_type="credit",
        )
        assert result.success is False

        history = history_repo.get_recent_history(limit=10)
        assert len(history) == 0

    def test_upload_without_repo_does_not_fail(
        self,
        controller_no_repo: UploadController,
        tmp_path: Path,
    ) -> None:
        csv_file = tmp_path / "citi.csv"
        self._create_csv(csv_file)

        result = controller_no_repo.upload_statement(
            source_path=csv_file,
            bank_name="citi",
            account_type="credit",
        )
        assert result.success is True

    def test_upload_with_ingestion_records_counts(
        self,
        tmp_path: Path,
        mock_ini_config: MagicMock,
    ) -> None:
        statements = tmp_path / "statements"
        statements.mkdir()
        history_repo = UploadHistoryRepository(
            db_path=tmp_path / "counts_test.db",
        )

        mock_service = MagicMock()
        mock_service.ingest_csv.return_value = IngestionResult(
            success=True,
            message="OK",
            transactions_processed=60,
            transactions_inserted=55,
            duplicates_skipped=5,
        )

        ctrl = UploadController(
            logger=logging.getLogger("test"),
            ini_config=mock_ini_config,
            statements_dir=statements,
            ingestion_service=mock_service,
            upload_history_repo=history_repo,
        )

        csv_file = tmp_path / "discover.csv"
        csv_file.write_text(
            "Date,Description,Amount\n"
            "2024-02-01,Payment,100.00\n",
        )

        result = ctrl.upload_statement(
            source_path=csv_file,
            bank_name="discover",
            account_type="credit",
        )
        assert result.success is True
        assert result.transactions_inserted == 55
        assert result.duplicates_skipped == 5

        history = history_repo.get_recent_history(limit=10)
        assert len(history) == 1
        assert history[0].transactions_inserted == 55
        assert history[0].duplicates_skipped == 5
