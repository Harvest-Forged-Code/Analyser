
"""Ingestion feature DTOs and data models.

Data transfer objects for CSV ingestion and upload results,
column mapping provider, statement repository, and upload
history persistence.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from budget_analyser.core.database import get_connection
from budget_analyser.core.errors import DataSourceError
from budget_analyser.core.protocols import (
    ColumnMappingProvider,
    StatementRepository,
)
from budget_analyser.settings.ini_config import IniAppConfig


# -------------------------------------------------------------------
# DTOs
# -------------------------------------------------------------------

@dataclass
class IngestionResult:
    """Result of a transaction ingestion operation.

    Captures the outcome of ingesting one or more CSV files,
    including how many transactions were processed and inserted.

    Attributes:
        success: Whether the ingestion succeeded.
        message: Human-readable status message.
        transactions_processed: Total transactions in the CSV.
        transactions_inserted: Transactions stored in the DB.
    """

    success: bool
    message: str
    transactions_processed: int = 0
    transactions_inserted: int = 0


@dataclass(frozen=True)
class UploadResult:
    """Result of an upload operation.

    Captures the outcome of uploading a bank statement CSV,
    including the destination path and ingestion statistics.

    Attributes:
        success: Whether the upload succeeded.
        message: Human-readable status message.
        destination_path: Path where the file was copied.
        transactions_inserted: Transactions stored in the DB.
    """

    success: bool
    message: str
    destination_path: str | None = None
    transactions_inserted: int = 0


@dataclass(frozen=True)
class ValidationResult:
    """Result of a CSV validation check.

    Attributes:
        valid: Whether the CSV passed validation.
        message: Human-readable validation message.
        row_count: Number of data rows in the CSV.
        date_range: Date range covered by the CSV.
    """

    valid: bool
    message: str
    row_count: int = 0
    date_range: str = ""


@dataclass(frozen=True)
class UploadStats:
    """Aggregate statistics for the upload history.

    Attributes:
        total_transactions: Total transactions in the database.
        total_accounts: Number of unique bank/account combos.
        last_upload_date: ISO timestamp of most recent upload.
        total_uploads: Total number of uploads recorded.
    """

    total_transactions: int
    total_accounts: int
    last_upload_date: str | None
    total_uploads: int


@dataclass(frozen=True)
class UploadHistoryEntry:
    """Single entry in the upload history log.

    Attributes:
        file_name: Name of the uploaded CSV file.
        bank_name: Bank/account identifier.
        account_type: Either 'credit' or 'debit'.
        uploaded_at: ISO timestamp of the upload.
        transactions_inserted: Transactions stored in the DB.
    """

    file_name: str
    bank_name: str
    account_type: str
    uploaded_at: str
    transactions_inserted: int


# -------------------------------------------------------------------
# Column mapping provider (was infrastructure/column_mappings.py)
# -------------------------------------------------------------------

@dataclass(frozen=True)
class IniColumnMappingProvider(ColumnMappingProvider):
    """INI-backed column mapping provider.

    Example:
        >>> provider = IniColumnMappingProvider(config=ini)
        >>> mapping = provider.get_column_mapping("citi")
        >>> mapping["Date"]
        'transaction_date'
    """

    config: IniAppConfig

    def get_column_mapping(
        self, account_name: str,
    ) -> Mapping[str, str]:
        """Get source-to-desired column mapping for an account.

        Args:
            account_name: Account identifier (e.g. ``"citi"``).

        Returns:
            Mapping from source CSV column names to canonical
            names.

        Raises:ste
            configparser.NoSectionError: If the INI mapping
                section for the account does not exist.
        """
        return self.config.get_column_mapping(
            account_name=account_name,
        )


# -------------------------------------------------------------------
# Statement repository (was infrastructure/statement_repository.py)
# -------------------------------------------------------------------

@dataclass(frozen=True)
class CsvStatementRepository(StatementRepository):
    """CSV-backed statement repository."""

    statement_dir: Path
    config: IniAppConfig
    logger: logging.Logger | None = None

    def _log(self, level: int, msg: str, *args: object) -> None:
        log = self.logger or logging.getLogger(
            "budget_analyser.gui",
        )
        try:
            log.log(level, msg, *args)
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    def get_statements(self) -> Mapping[str, pd.DataFrame]:
        """Load all configured statements from disk.

        Returns:
            Mapping of account_name to raw statement DataFrame.

        Raises:
            DataSourceError: When a required statement file
                cannot be found.
        """
        statements: dict[str, pd.DataFrame] = {}

        for section in ("credit_cards", "checking_accounts"):
            for account in self.config.list_accounts(
                section=section,
            ):
                filename = self.config.get_statement_filename(
                    section=section, account=account,
                )
                path = self.statement_dir / filename
                try:
                    self._log(
                        logging.INFO,
                        "Loading statement: section=%s "
                        "account=%s file=%s",
                        section, account, str(path.resolve()),
                    )
                    df = pd.read_csv(
                        path, encoding="utf-8-sig",
                    )
                    statements[account] = df
                    self._log(
                        logging.INFO,
                        "Loaded statement: account=%s "
                        "rows=%s cols=%s",
                        account, len(df.index), len(df.columns),
                    )
                except FileNotFoundError as exc:
                    self._log(
                        logging.ERROR,
                        "Statement file not found for "
                        "account=%s path=%s",
                        account, str(path.resolve()),
                    )
                    raise DataSourceError(
                        f"Statement file not found: {path}",
                    ) from exc
                except Exception as exc:  # pragma: no cover
                    self._log(
                        logging.ERROR,
                        "Failed reading CSV for account=%s "
                        "path=%s error=%s",
                        account, str(path.resolve()), exc,
                    )
                    raise DataSourceError(
                        f"Failed reading CSV for "
                        f"{account}: {path}",
                    ) from exc

        return statements


# -------------------------------------------------------------------
# Upload history model (was repository.py)
# -------------------------------------------------------------------

class UploadHistoryModel:
    """SQLite-backed storage for upload history.

    Manages persistence of upload history records in a shared
    SQLite database.  The table is created automatically on
    first use.

    Example:
        >>> model = UploadHistoryModel(
        ...     db_path=Path("budget.db"),
        ... )
        >>> model.save_upload(
        ...     file_name="citi.csv",
        ...     bank_name="citi",
        ...     account_type="credit",
        ...     transactions_inserted=50,
        ... )
    """

    TABLE = "upload_history"

    def __init__(
        self,
        *,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the upload history model.

        Creates the upload_history table if it does not already
        exist.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.ingestion.models",
        )
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Create upload_history table if it doesn't exist.

        Also drops the legacy duplicates_skipped column from
        existing tables if present.
        """
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_name TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    account_type TEXT NOT NULL,
                    uploaded_at TIMESTAMP
                        DEFAULT CURRENT_TIMESTAMP,
                    transactions_inserted INTEGER
                        NOT NULL DEFAULT 0
                )
            """)

            # Migration: drop duplicates_skipped column if present
            columns = {
                row["name"]
                for row in conn.execute(
                    f"PRAGMA table_info({self.TABLE})",
                ).fetchall()
            }
            if "duplicates_skipped" in columns:
                try:
                    conn.execute(
                        f"ALTER TABLE {self.TABLE} "
                        f"DROP COLUMN duplicates_skipped",
                    )
                    self._logger.info(
                        "Migrated %s: dropped duplicates_skipped",
                        self.TABLE,
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    self._logger.warning(
                        "Could not drop duplicates_skipped "
                        "column from %s", self.TABLE,
                    )

            conn.commit()

    def save_upload(
        self,
        *,
        file_name: str,
        bank_name: str,
        account_type: str,
        transactions_inserted: int,
    ) -> None:
        """Record a completed upload in history.

        Args:
            file_name: Name of the uploaded CSV file.
            bank_name: Bank/account identifier.
            account_type: Either 'credit' or 'debit'.
            transactions_inserted: Transactions stored in the DB.
        """
        with get_connection(self._db_path) as conn:
            conn.execute(
                f"""
                INSERT INTO {self.TABLE}
                    (file_name, bank_name, account_type,
                     transactions_inserted)
                VALUES (?, ?, ?, ?)
                """,
                (
                    file_name, bank_name, account_type,
                    transactions_inserted,
                ),
            )
            conn.commit()

    def get_stats(self) -> UploadStats:
        """Return aggregate stats from upload history.

        Returns:
            UploadStats with totals.
        """
        with get_connection(self._db_path) as conn:
            row = conn.execute(f"""
                SELECT
                    COUNT(*) as total_uploads,
                    MAX(uploaded_at) as last_upload
                FROM {self.TABLE}
            """).fetchone()

            accounts_row = conn.execute(f"""
                SELECT COUNT(DISTINCT bank_name || account_type)
                    as cnt
                FROM {self.TABLE}
            """).fetchone()

            try:
                txn_row = conn.execute(
                    "SELECT COUNT(*) as cnt "
                    "FROM transactions",
                ).fetchone()
                total_transactions = (
                    txn_row["cnt"] if txn_row else 0
                )
            except Exception:  # pylint: disable=broad-exception-caught
                total_transactions = 0

        total_uploads = row["total_uploads"] if row else 0
        last_upload = row["last_upload"] if row else None
        total_accounts = (
            accounts_row["cnt"] if accounts_row else 0
        )

        return UploadStats(
            total_transactions=total_transactions,
            total_accounts=total_accounts,
            last_upload_date=last_upload,
            total_uploads=total_uploads,
        )

    def get_recent_history(
        self, *, limit: int = 10,
    ) -> list[UploadHistoryEntry]:
        """Return the most recent upload history entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of UploadHistoryEntry ordered most recent first.
        """
        with get_connection(self._db_path) as conn:
            rows = conn.execute(
                f"""
                SELECT file_name, bank_name, account_type,
                       uploaded_at, transactions_inserted
                FROM {self.TABLE}
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            UploadHistoryEntry(
                file_name=row["file_name"],
                bank_name=row["bank_name"],
                account_type=row["account_type"],
                uploaded_at=str(row["uploaded_at"]),
                transactions_inserted=(
                    row["transactions_inserted"]
                ),
            )
            for row in rows
        ]


# -------------------------------------------------------------------
# Backward-compat aliases
# -------------------------------------------------------------------
UploadHistoryRepository = UploadHistoryModel
