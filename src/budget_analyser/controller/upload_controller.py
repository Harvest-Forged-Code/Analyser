"""Upload controller for bank statement uploads.

Single responsibility:
    Validate and copy uploaded bank statement CSV files to the statements folder.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from budget_analyser.infrastructure.ini_config import IniAppConfig


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation."""

    success: bool
    message: str
    destination_path: str | None = None


class UploadController:
    """Controller for uploading and validating bank statements."""

    def __init__(
        self,
        *,
        logger: logging.Logger,
        ini_config: IniAppConfig,
        statements_dir: Path,
    ) -> None:
        self._logger = logger
        self._ini_config = ini_config
        self._statements_dir = statements_dir

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
        """Check for missing columns and return list of missing ones."""
        csv_columns_lower = [c.lower() for c in csv_columns]
        missing = []

        for expected in expected_columns:
            if expected.lower() not in csv_columns_lower:
                if expected.lower() not in ("debit", "credit"):
                    missing.append(expected)

        # Check for amount column (can be derived from Debit+Credit)
        if "amount" not in csv_columns_lower:
            has_debit_credit = (
                "debit" in csv_columns_lower and "credit" in csv_columns_lower
            )
            if not has_debit_credit and "amount" in [e.lower() for e in expected_columns]:
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

        suffix = "credit" if account_type == "credit" else "debit"
        dest_filename = f"{bank_name}_{suffix}.csv"
        dest_path = self._statements_dir / dest_filename

        try:
            self._statements_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            self._logger.info(
                "Statement uploaded: %s -> %s", source_path, dest_path
            )
            return UploadResult(
                success=True,
                message=f"Statement uploaded successfully as '{dest_filename}'",
                destination_path=str(dest_path),
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._logger.error("Failed to copy statement: %s", exc)
            return UploadResult(
                success=False,
                message=f"Failed to copy file: {exc}",
            )
