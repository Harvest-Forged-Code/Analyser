"""Upload controller for bank statement uploads.

Validates and copies uploaded bank statement CSV files to the
statements folder, then processes and stores transactions.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from budget_analyser.features.ingestion.models import UploadResult
from budget_analyser.infrastructure.ini_config import IniAppConfig

if TYPE_CHECKING:
    from budget_analyser.features.ingestion.service import (
        TransactionIngestionService,
    )


class UploadController:
    """Controller for uploading and validating bank statements."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        ini_config: IniAppConfig,
        statements_dir: Path,
        ingestion_service: (
            TransactionIngestionService | None
        ) = None,
    ) -> None:
        self._logger = logger
        self._ini_config = ini_config
        self._statements_dir = statements_dir
        self._ingestion_service = ingestion_service

    # ----------------------------------------------------------
    # Bank / statement queries
    # ----------------------------------------------------------

    def get_available_banks(
        self, account_type: str,
    ) -> list[str]:
        """Return available bank names for the given account type.

        Args:
            account_type: Either 'credit' or 'debit'.

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
                        self._ini_config.get_statement_filename(
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
                        self._ini_config.get_statement_filename(
                            section=section, account=bank,
                        )
                    )
                    path = self._statements_dir / filename
                    status.append(
                        (bank, acct_type, path.exists()),
                    )
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self._logger.warning(
                        "Error checking statement for %s: %s",
                        bank, exc,
                    )
                    status.append((bank, acct_type, False))
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
            Tuple of (is_valid, message, missing_columns).
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
            account_type: Either 'credit' or 'debit'.

        Returns:
            UploadResult with success status and message.
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

        txn_inserted, dup_skipped, ing_msg = (
            self._run_ingestion(bank_name, dest_path)
        )

        return UploadResult(
            success=True,
            message=(
                "Statement uploaded successfully "
                f"as '{dest_filename}'{ing_msg}"
            ),
            destination_path=str(dest_path),
            transactions_inserted=txn_inserted,
            duplicates_skipped=dup_skipped,
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
            and "amount" in [e.lower() for e in expected_columns]
        ):
            missing.append("Amount (or Debit+Credit)")

        return missing

    def _run_ingestion(
        self,
        bank_name: str,
        dest_path: Path,
    ) -> tuple[int, int, str]:
        """Run ingestion if service is available.

        Returns:
            Tuple of (inserted, duplicates, message_suffix).
        """
        if self._ingestion_service is None:
            return 0, 0, ""

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
                    "Ingestion complete for %s: "
                    "%d inserted, %d duplicates",
                    bank_name,
                    result.transactions_inserted,
                    result.duplicates_skipped,
                )
                return (
                    result.transactions_inserted,
                    result.duplicates_skipped,
                    f" | {result.transactions_inserted} "
                    f"transactions added to database "
                    f"({result.duplicates_skipped} "
                    f"duplicates skipped)",
                )

            self._logger.warning(
                "Ingestion failed for %s: %s",
                bank_name, result.message,
            )
            return (
                0, 0,
                f" | Warning: {result.message}",
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.warning(
                "Failed to ingest transactions: %s", exc,
            )
            return (
                0, 0,
                " | Warning: Failed to process "
                f"transactions: {exc}",
            )
