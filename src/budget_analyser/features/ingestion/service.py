"""Transaction ingestion service and upload service.

Processes uploaded CSV files and saves categorized transactions
to the database. Also validates and copies uploaded bank
statement CSV files to the statements folder.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

import pandas as pd

from budget_analyser.features.ingestion.formatters import (
    create_statement_formatter,
)
from budget_analyser.features.ingestion.categorization import (
    CategoryMappers,
    TransactionProcessor,
)
from budget_analyser.features.ingestion.models import (
    IngestionResult,
    UploadResult,
    UploadStats,
    UploadHistoryEntry,
    UploadHistoryModel,
)
from budget_analyser.core.database import TransactionDatabase
from budget_analyser.settings.ini_config import IniAppConfig

if TYPE_CHECKING:
    pass


class TransactionIngestionService:
    """Service to ingest bank statement CSVs into the database.

    Responsibilities:
        - Load and format CSV files using the appropriate formatter
        - Categorize transactions using keyword mappings
        - Insert processed transactions into the database
    """

    def __init__(
        self,
        *,
        database: TransactionDatabase,
        category_mappers: CategoryMappers,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the ingestion service.

        Args:
            database: TransactionDatabase for persistence.
            category_mappers: Mappers for categorization.
            logger: Optional logger for diagnostics.
        """
        self._database = database
        self._category_mappers = category_mappers
        self._logger = logger or logging.getLogger(
            "budget_analyser.ingestion",
        )

    def ingest_csv(
        self,
        csv_path: Path,
        account_name: str,
        column_mapping: Mapping[str, str],
    ) -> IngestionResult:
        """Ingest a single CSV file into the database.

        Args:
            csv_path: Path to the CSV file.
            account_name: Account identifier (e.g. ``"citi"``).
            column_mapping: Source-to-canonical column mapping.

        Returns:
            IngestionResult with success status and statistics.
        """
        try:
            return self._do_ingest(
                csv_path, account_name, column_mapping,
            )
        except FileNotFoundError:
            msg = f"CSV file not found: {csv_path}"
            self._logger.error(msg)
            return IngestionResult(success=False, message=msg)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            msg = f"Failed to ingest CSV: {exc}"
            self._logger.exception(msg)
            return IngestionResult(success=False, message=msg)

    def ingest_multiple_csvs(
        self,
        csv_files: list[tuple[Path, str, Mapping[str, str]]],
    ) -> IngestionResult:
        """Ingest multiple CSV files into the database.

        Args:
            csv_files: List of ``(csv_path, account_name,
                column_mapping)`` tuples, one per file.

        Returns:
            Aggregated IngestionResult with combined statistics.
        """
        total_processed = 0
        total_inserted = 0
        errors: list[str] = []

        for csv_path, account_name, column_mapping in csv_files:
            result = self.ingest_csv(
                csv_path, account_name, column_mapping,
            )
            if result.success:
                total_processed += result.transactions_processed
                total_inserted += result.transactions_inserted
            else:
                errors.append(
                    f"{account_name}: {result.message}",
                )

        if errors:
            return IngestionResult(
                success=False,
                message=(
                    f"Some files failed: "
                    f"{'; '.join(errors)}"
                ),
                transactions_processed=total_processed,
                transactions_inserted=total_inserted,
            )

        return IngestionResult(
            success=True,
            message=(
                f"Successfully ingested "
                f"{len(csv_files)} files"
            ),
            transactions_processed=total_processed,
            transactions_inserted=total_inserted,
        )

    # ----------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------

    def _do_ingest(
        self,
        csv_path: Path,
        account_name: str,
        column_mapping: Mapping[str, str],
    ) -> IngestionResult:
        """Core ingestion pipeline."""
        self._logger.info(
            "Loading CSV: %s for account: %s",
            csv_path, account_name,
        )
        raw_df = pd.read_csv(csv_path, encoding="utf-8-sig")

        if raw_df.empty:
            return IngestionResult(
                success=False, message="CSV file is empty",
            )

        self._logger.info(
            "Formatting %d rows for account: %s",
            len(raw_df), account_name,
        )
        formatter = create_statement_formatter(
            account_name=account_name,
            statement=raw_df,
            column_mapping=column_mapping,
        )
        formatted_df = formatter.get_desired_format()

        self._logger.info(
            "Categorizing transactions for account: %s",
            account_name,
        )
        processor = TransactionProcessor(
            mappers=self._category_mappers,
        )
        processed_df = processor.process(
            raw_transactions=formatted_df,
        )

        self._logger.info(
            "Inserting %d transactions into database",
            len(processed_df),
        )
        inserted_count = self._database.insert_transactions(
            processed_df,
        )

        self._logger.info(
            "Ingestion complete: %d processed, %d inserted",
            len(processed_df), inserted_count,
        )

        return IngestionResult(
            success=True,
            message=(
                f"Successfully processed "
                f"{len(processed_df)} transactions"
            ),
            transactions_processed=len(processed_df),
            transactions_inserted=inserted_count,
        )


# -------------------------------------------------------------------
# Upload service (was controller.py)
# -------------------------------------------------------------------

class UploadService:
    """Service for uploading and validating bank statements."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        ini_config: IniAppConfig,
        statements_dir: Path,
        ingestion_service: (
            TransactionIngestionService | None
        ) = None,
        upload_history_repo: (
            UploadHistoryModel | None
        ) = None,
    ) -> None:
        """Initialize the upload service.

        Args:
            logger: Logger for diagnostic messages.
            ini_config: Application INI configuration.
            statements_dir: Directory where uploaded statement
                CSV files are stored.
            ingestion_service: Optional ingestion service for
                automatic processing after upload.
            upload_history_repo: Optional model for recording
                upload history.
        """
        self._logger = logger
        self._ini_config = ini_config
        self._statements_dir = statements_dir
        self._ingestion_service = ingestion_service
        self._upload_history_model = upload_history_repo

    # ----------------------------------------------------------
    # Bank / statement queries
    # ----------------------------------------------------------

    def get_available_banks(
        self, account_type: str,
    ) -> list[str]:
        """Return available bank names for the account type.

        Args:
            account_type: Either ``'credit'`` or ``'debit'``.

        Returns:
            List of bank/account names from INI config.
        """
        section = (
            "credit_cards"
            if account_type == "credit"
            else "checking_accounts"
        )
        try:
            return self._ini_config.list_accounts(
                section=section,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Failed to list accounts for %s: %s",
                section, exc,
            )
            return []

    def get_missing_statements(
        self,
    ) -> list[tuple[str, str, str]]:
        """Check which required CSV statement files are missing.

        Returns:
            List of (bank_name, account_type, expected_filename)
            for each missing file.
        """
        missing: list[tuple[str, str, str]] = []
        for acct_type, section in (
            ("credit", "credit_cards"),
            ("debit", "checking_accounts"),
        ):
            for bank in self.get_available_banks(acct_type):
                try:
                    filename = (
                        self._ini_config
                        .get_statement_filename(
                            section=section, account=bank,
                        )
                    )
                    path = self._statements_dir / filename
                    if not path.exists():
                        missing.append(
                            (bank, acct_type, filename),
                        )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self._logger.warning(
                        "Error checking statement for %s: %s",
                        bank, exc,
                    )
        return missing

    def all_statements_present(self) -> bool:
        """Check if all required CSV statement files exist.

        Returns:
            True if every required statement is present.
        """
        return len(self.get_missing_statements()) == 0

    def get_bank_upload_status(
        self,
    ) -> list[tuple[str, str, bool]]:
        """Get upload status for all configured banks.

        Returns:
            List of (bank_name, account_type, is_uploaded).
        """
        status: list[tuple[str, str, bool]] = []
        for acct_type, section in (
            ("credit", "credit_cards"),
            ("debit", "checking_accounts"),
        ):
            for bank in self.get_available_banks(acct_type):
                try:
                    filename = (
                        self._ini_config
                        .get_statement_filename(
                            section=section, account=bank,
                        )
                    )
                    path = self._statements_dir / filename
                    status.append(
                        (bank, acct_type, path.exists()),
                    )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self._logger.warning(
                        "Error checking statement for "
                        "%s: %s", bank, exc,
                    )
                    status.append(
                        (bank, acct_type, False),
                    )
        return status

    def get_expected_columns(
        self, bank_name: str,
    ) -> list[str]:
        """Return expected source column names for a bank.

        Args:
            bank_name: The bank/account identifier.

        Returns:
            List of expected column names from the CSV.
        """
        try:
            mapping = self._ini_config.get_column_mapping(
                account_name=bank_name,
            )
            return list(mapping.keys())
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Failed to get column mapping for %s: %s",
                bank_name, exc,
            )
            return []

    # ----------------------------------------------------------
    # Upload stats / history
    # ----------------------------------------------------------

    def get_upload_stats(self) -> UploadStats:
        """Return aggregate upload statistics.

        Returns:
            UploadStats with totals.
        """
        if self._upload_history_model is None:
            return UploadStats(
                total_transactions=0,
                total_accounts=0,
                last_upload_date=None,
                total_uploads=0,
            )
        return self._upload_history_model.get_stats()

    def get_recent_history(
        self, *, limit: int = 10,
    ) -> list[UploadHistoryEntry]:
        """Return recent upload history entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of UploadHistoryEntry, most recent first.
        """
        if self._upload_history_model is None:
            return []
        return self._upload_history_model.get_recent_history(
            limit=limit,
        )

    # ----------------------------------------------------------
    # CSV validation
    # ----------------------------------------------------------

    def validate_csv(
        self,
        file_path: Path,
        bank_name: str,
    ) -> tuple[bool, str, list[str]]:
        """Validate a CSV file against the expected bank format.

        Args:
            file_path: Path to the CSV file.
            bank_name: The bank/account identifier.

        Returns:
            Tuple of ``(is_valid, message, missing_columns)``.
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}", []
        if file_path.suffix.lower() != ".csv":
            return (
                False,
                "File must be a CSV file (.csv extension)",
                [],
            )

        ok, err, csv_cols = self._read_csv_columns(file_path)
        if not ok:
            return False, err, []

        expected = self.get_expected_columns(bank_name)
        if not expected:
            return (
                False,
                f"No column mapping found for bank "
                f"'{bank_name}' in configuration",
                [],
            )

        missing = self._check_missing_columns(
            csv_cols, expected,
        )
        if missing:
            return (
                False,
                f"Missing required columns: "
                f"{', '.join(missing)}. "
                f"Found columns: {', '.join(csv_cols)}",
                missing,
            )

        return True, "CSV format is valid", []

    # ----------------------------------------------------------
    # Upload
    # ----------------------------------------------------------

    def upload_statement(
        self,
        source_path: Path,
        bank_name: str,
        account_type: str,
    ) -> UploadResult:
        """Validate and copy a statement file to statements dir.

        Args:
            source_path: Path to the source CSV file.
            bank_name: The bank/account identifier.
            account_type: Either ``'credit'`` or ``'debit'``.

        Returns:
            UploadResult with success status and counts.
        """
        is_valid, message, _ = self.validate_csv(
            source_path, bank_name,
        )
        if not is_valid:
            self._logger.warning(
                "Upload validation failed for %s: %s",
                source_path, message,
            )
            return UploadResult(success=False, message=message)

        section = (
            "credit_cards"
            if account_type == "credit"
            else "checking_accounts"
        )
        try:
            dest_filename = (
                self._ini_config.get_statement_filename(
                    section=section, account=bank_name,
                )
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.error(
                "Failed to get filename from config "
                "for %s: %s", bank_name, exc,
            )
            return UploadResult(
                success=False,
                message=(
                    "Failed to determine destination "
                    f"filename: {exc}"
                ),
            )

        dest_path = self._statements_dir / dest_filename

        try:
            self._statements_dir.mkdir(
                parents=True, exist_ok=True,
            )
            shutil.copy2(source_path, dest_path)
            self._logger.info(
                "Statement uploaded: %s -> %s",
                source_path, dest_path,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.error(
                "Failed to copy statement: %s", exc,
            )
            return UploadResult(
                success=False,
                message=f"Failed to copy file: {exc}",
            )

        txn_inserted, ing_msg = (
            self._run_ingestion(bank_name, dest_path)
        )

        if self._upload_history_model is not None:
            self._upload_history_model.save_upload(
                file_name=source_path.name,
                bank_name=bank_name,
                account_type=account_type,
                transactions_inserted=txn_inserted,
            )

        return UploadResult(
            success=True,
            message=(
                "Statement uploaded successfully "
                f"as '{dest_filename}'{ing_msg}"
            ),
            destination_path=str(dest_path),
            transactions_inserted=txn_inserted,
        )

    # ----------------------------------------------------------
    # Private helpers
    # ----------------------------------------------------------

    def _read_csv_columns(
        self, file_path: Path,
    ) -> tuple[bool, str, list[str]]:
        """Read CSV and return columns or error."""
        try:
            df = pd.read_csv(
                file_path, nrows=5, encoding="utf-8-sig",
            )
            if df.empty:
                return False, "CSV file is empty", []
            return True, "", list(df.columns)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return (
                False, f"Failed to read CSV: {exc}", [],
            )

    @staticmethod
    def _check_missing_columns(
        csv_columns: list[str],
        expected_columns: list[str],
    ) -> list[str]:
        """Check for missing columns.

        Special handling: if CSV has both 'Debit' and 'Credit'
        columns, the 'amount' column can be derived from them.
        """
        csv_lower = [c.lower() for c in csv_columns]
        missing: list[str] = []

        has_debit_credit = (
            "debit" in csv_lower and "credit" in csv_lower
        )

        for expected in expected_columns:
            exp_lower = expected.lower()
            if exp_lower not in csv_lower:
                if exp_lower in ("debit", "credit"):
                    continue
                if exp_lower == "amount" and has_debit_credit:
                    continue
                missing.append(expected)

        if (
            "amount" not in csv_lower
            and not has_debit_credit
            and "amount" in [
                e.lower() for e in expected_columns
            ]
        ):
            missing.append("Amount (or Debit+Credit)")

        return missing

    def _run_ingestion(
        self,
        bank_name: str,
        dest_path: Path,
    ) -> tuple[int, str]:
        """Run ingestion if service is available.

        Returns:
            Tuple of ``(inserted, message_suffix)``.
        """
        if self._ingestion_service is None:
            return 0, ""

        try:
            col_map = self._ini_config.get_column_mapping(
                account_name=bank_name,
            )
            result = self._ingestion_service.ingest_csv(
                csv_path=dest_path,
                account_name=bank_name,
                column_mapping=col_map,
            )
            if result.success:
                self._logger.info(
                    "Ingestion complete for %s: %d inserted",
                    bank_name,
                    result.transactions_inserted,
                )
                return (
                    result.transactions_inserted,
                    f" | {result.transactions_inserted} "
                    f"transactions added to database",
                )

            self._logger.warning(
                "Ingestion failed for %s: %s",
                bank_name, result.message,
            )
            return (
                0,
                f" | Warning: {result.message}",
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Failed to ingest transactions: %s", exc,
            )
            return (
                0,
                " | Warning: Failed to process "
                f"transactions: {exc}",
            )


# -------------------------------------------------------------------
# Backward-compat alias
# -------------------------------------------------------------------
UploadController = UploadService
