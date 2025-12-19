"""Upload controller for bank statement uploads.

Single responsibility:
    Validate and copy uploaded bank statement CSV files to the statements folder,
    then process and store transactions in the database.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

import pandas as pd

from budget_analyser.infrastructure.ini_config import IniAppConfig

if TYPE_CHECKING:
    from budget_analyser.domain.transaction_ingestion import TransactionIngestionService


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation."""

    success: bool
    message: str
    destination_path: str | None = None
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


class UploadController:
    """Controller for uploading and validating bank statements."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        ini_config: IniAppConfig,
        statements_dir: Path,
        ingestion_service: Optional["TransactionIngestionService"] = None,
    ) -> None:
        self._logger = logger
        self._ini_config = ini_config
        self._statements_dir = statements_dir
        self._ingestion_service = ingestion_service

    def get_available_banks(self, account_type: str) -> List[str]:
        """Return list of available bank names for the given account type.

        Args:
            account_type: Either 'credit' or 'debit'.

        Returns:
            List of bank/account names configured in INI.
        """
        section = "credit_cards" if account_type == "credit" else "checking_accounts"
        try:
            return self._ini_config.list_accounts(section=section)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning("Failed to list accounts for %s: %s", section, exc)
            return []

    def get_missing_statements(self) -> List[Tuple[str, str, str]]:
        """Check which required CSV statement files are missing.

        Returns:
            List of tuples (bank_name, account_type, expected_filename) for missing files.
        """
        missing: List[Tuple[str, str, str]] = []

        # Check credit card statements
        for bank in self.get_available_banks("credit"):
            try:
                filename = self._ini_config.get_statement_filename(
                    section="credit_cards", account=bank
                )
                path = self._statements_dir / filename
                if not path.exists():
                    missing.append((bank, "credit", filename))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning("Error checking statement for %s: %s", bank, exc)

        # Check checking account statements
        for bank in self.get_available_banks("debit"):
            try:
                filename = self._ini_config.get_statement_filename(
                    section="checking_accounts", account=bank
                )
                path = self._statements_dir / filename
                if not path.exists():
                    missing.append((bank, "debit", filename))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning("Error checking statement for %s: %s", bank, exc)

        return missing

    def all_statements_present(self) -> bool:
        """Check if all required CSV statement files exist.

        Returns:
            True if all required statements are present, False otherwise.
        """
        return len(self.get_missing_statements()) == 0

    def get_bank_upload_status(self) -> List[Tuple[str, str, bool]]:
        """Get upload status for all configured banks.

        Returns:
            List of tuples (bank_name, account_type, is_uploaded) for all banks.
        """
        status: List[Tuple[str, str, bool]] = []

        # Check credit card statements
        for bank in self.get_available_banks("credit"):
            try:
                filename = self._ini_config.get_statement_filename(
                    section="credit_cards", account=bank
                )
                path = self._statements_dir / filename
                status.append((bank, "credit", path.exists()))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning("Error checking statement for %s: %s", bank, exc)
                status.append((bank, "credit", False))

        # Check checking account statements
        for bank in self.get_available_banks("debit"):
            try:
                filename = self._ini_config.get_statement_filename(
                    section="checking_accounts", account=bank
                )
                path = self._statements_dir / filename
                status.append((bank, "debit", path.exists()))
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning("Error checking statement for %s: %s", bank, exc)
                status.append((bank, "debit", False))

        return status

    def get_expected_columns(self, bank_name: str) -> List[str]:
        """Return the expected source column names for a bank.

        Args:
            bank_name: The bank/account identifier.

        Returns:
            List of expected column names from the CSV.
        """
        try:
            mapping = self._ini_config.get_column_mapping(account_name=bank_name)
            return list(mapping.keys())
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Failed to get column mapping for %s: %s", bank_name, exc
            )
            return []

    def _read_csv_columns(self, file_path: Path) -> Tuple[bool, str, List[str]]:
        """Read CSV and return columns or error."""
        try:
            df = pd.read_csv(file_path, nrows=5)
            if df.empty:
                return False, "CSV file is empty", []
            return True, "", list(df.columns)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            return False, f"Failed to read CSV: {exc}", []

    def _check_missing_columns(
        self, csv_columns: List[str], expected_columns: List[str]
    ) -> List[str]:
        """Check for missing columns and return list of missing ones.

        Special handling for 'amount' column: If the CSV has both 'Debit' and 'Credit'
        columns, the amount can be derived from them (as done in base_statement_formatter).
        """
        csv_columns_lower = [c.lower() for c in csv_columns]
        missing = []

        # Check if CSV has Debit+Credit (can derive amount from these)
        has_debit_credit = (
            "debit" in csv_columns_lower and "credit" in csv_columns_lower
        )

        for expected in expected_columns:
            expected_lower = expected.lower()
            if expected_lower not in csv_columns_lower:
                # Skip debit/credit as they're not directly expected
                if expected_lower in ("debit", "credit"):
                    continue
                # Skip 'amount' if CSV has Debit+Credit (amount can be derived)
                if expected_lower == "amount" and has_debit_credit:
                    continue
                missing.append(expected)

        # If amount is expected but missing and no Debit+Credit, report it
        if "amount" not in csv_columns_lower and not has_debit_credit:
            if "amount" in [e.lower() for e in expected_columns]:
                missing.append("Amount (or Debit+Credit)")

        return missing

    def validate_csv(
        self, file_path: Path, bank_name: str
    ) -> Tuple[bool, str, List[str]]:
        """Validate a CSV file against the expected format for a bank.

        Args:
            file_path: Path to the CSV file to validate.
            bank_name: The bank/account identifier.

        Returns:
            Tuple of (is_valid, message, missing_columns).
        """
        # Check file exists and has correct extension
        if not file_path.exists():
            return False, f"File not found: {file_path}", []
        if file_path.suffix.lower() != ".csv":
            return False, "File must be a CSV file (.csv extension)", []

        # Read CSV columns
        success, error_msg, csv_columns = self._read_csv_columns(file_path)
        if not success:
            return False, error_msg, []

        # Get expected columns from config
        expected_columns = self.get_expected_columns(bank_name)
        if not expected_columns:
            return (
                False,
                f"No column mapping found for bank '{bank_name}' in configuration",
                [],
            )

        # Check for missing columns
        missing = self._check_missing_columns(csv_columns, expected_columns)
        if missing:
            return (
                False,
                f"Missing required columns: {', '.join(missing)}. "
                f"Found columns: {', '.join(csv_columns)}",
                missing,
            )

        return True, "CSV format is valid", []

    def upload_statement(
        self,
        source_path: Path,
        bank_name: str,
        account_type: str,
    ) -> UploadResult:
        """Validate and copy a statement file to the statements directory.

        Args:
            source_path: Path to the source CSV file.
            bank_name: The bank/account identifier.
            account_type: Either 'credit' or 'debit'.

        Returns:
            UploadResult with success status and message.
        """
        is_valid, message, _ = self.validate_csv(source_path, bank_name)
        if not is_valid:
            self._logger.warning(
                "Upload validation failed for %s: %s", source_path, message
            )
            return UploadResult(success=False, message=message)

        # Get the expected filename from INI config (ensures consistency with status checks)
        section = "credit_cards" if account_type == "credit" else "checking_accounts"
        try:
            dest_filename = self._ini_config.get_statement_filename(
                section=section, account=bank_name
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.error("Failed to get filename from config for %s: %s", bank_name, exc)
            return UploadResult(
                success=False,
                message=f"Failed to determine destination filename: {exc}",
            )

        dest_path = self._statements_dir / dest_filename

        try:
            self._statements_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            self._logger.info(
                "Statement uploaded: %s -> %s", source_path, dest_path
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.error("Failed to copy statement: %s", exc)
            return UploadResult(
                success=False,
                message=f"Failed to copy file: {exc}",
            )

        # Process and store transactions in database if ingestion service is available
        transactions_inserted = 0
        duplicates_skipped = 0
        ingestion_msg = ""

        if self._ingestion_service is not None:
            try:
                column_mapping = self._ini_config.get_column_mapping(account_name=bank_name)
                ingestion_result = self._ingestion_service.ingest_csv(
                    csv_path=dest_path,
                    account_name=bank_name,
                    column_mapping=column_mapping,
                )
                if ingestion_result.success:
                    transactions_inserted = ingestion_result.transactions_inserted
                    duplicates_skipped = ingestion_result.duplicates_skipped
                    ingestion_msg = (
                        f" | {transactions_inserted} transactions added to database"
                        f" ({duplicates_skipped} duplicates skipped)"
                    )
                    self._logger.info(
                        "Ingestion complete for %s: %d inserted, %d duplicates",
                        bank_name,
                        transactions_inserted,
                        duplicates_skipped,
                    )
                else:
                    self._logger.warning(
                        "Ingestion failed for %s: %s",
                        bank_name,
                        ingestion_result.message,
                    )
                    ingestion_msg = f" | Warning: {ingestion_result.message}"
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning("Failed to ingest transactions: %s", exc)
                ingestion_msg = f" | Warning: Failed to process transactions: {exc}"

        return UploadResult(
            success=True,
            message=f"Statement uploaded successfully as '{dest_filename}'{ingestion_msg}",
            destination_path=str(dest_path),
            transactions_inserted=transactions_inserted,
            duplicates_skipped=duplicates_skipped,
        )
