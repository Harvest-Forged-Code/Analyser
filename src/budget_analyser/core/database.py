"""Shared database utilities.

Provides a connection factory used by all feature repositories
that share the same SQLite database file, plus the shared
transaction storage classes.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Create a new SQLite connection with row-factory enabled.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------------------------------------------------
# Transaction record DTO
# -------------------------------------------------------------------

@dataclass
class TransactionRecord:
    """A single transaction record for database operations.

    Attributes:
        transaction_date: Date string in ISO format (YYYY-MM-DD).
        description: Transaction description text.
        amount: Transaction amount (positive=credit, negative=debit).
        from_account: Account identifier.
        sub_category: Derived sub-category label.
        category: Derived top-level category label.
        c_or_d: Classification: earnings, expenditures, or neutral.
    """

    transaction_date: str
    description: str
    amount: float
    from_account: str
    sub_category: str = ""
    category: str = ""
    c_or_d: str = ""


# -------------------------------------------------------------------
# Transaction database
# -------------------------------------------------------------------

class TransactionDatabase:
    """SQLite-backed transaction storage.

    Responsibilities:
        - Create and manage the transactions table
        - Insert transactions into the database
        - Read all transactions for report generation
    """

    TABLE_NAME = "transactions"

    def __init__(
        self,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.database",
        )
        self._ensure_table_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table_exists(self) -> None:
        """Create the transactions table if it doesn't exist.

        Also runs a one-time migration to remove the legacy
        UNIQUE constraint if it is present on an existing table.
        """
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            from_account TEXT NOT NULL,
            sub_category TEXT DEFAULT '',
            category TEXT DEFAULT '',
            c_or_d TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        with self._get_connection() as conn:
            conn.execute(create_sql)

            # Migration: remove UNIQUE constraint from existing tables
            row = conn.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type='table' AND name=?",
                (self.TABLE_NAME,),
            ).fetchone()
            if row and row[0] and "UNIQUE" in (row[0] or "").upper():
                self._logger.info(
                    "Migrating %s: removing UNIQUE constraint",
                    self.TABLE_NAME,
                )
                tmp = f"_{self.TABLE_NAME}_old"
                conn.execute(f"DROP TABLE IF EXISTS {tmp}")
                conn.execute(
                    f"ALTER TABLE {self.TABLE_NAME} RENAME TO {tmp}",
                )
                conn.execute(create_sql)
                conn.execute(f"""
                    INSERT INTO {self.TABLE_NAME}
                    SELECT id, transaction_date, description,
                           amount, from_account, sub_category,
                           category, c_or_d, created_at
                    FROM {tmp}
                """)
                conn.execute(f"DROP TABLE {tmp}")
                self._logger.info(
                    "Migration complete: UNIQUE constraint removed",
                )

            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS
                    idx_transaction_date
                ON {self.TABLE_NAME}(transaction_date)
            """)
            conn.commit()
        self._logger.info(
            "Database initialized at %s", self._db_path,
        )

    def insert_transactions(
        self, transactions: pd.DataFrame,
    ) -> int:
        """Insert transactions into the database.

        Args:
            transactions: DataFrame with columns:
                transaction_date, description, amount,
                from_account, sub_category, category, c_or_d

        Returns:
            Number of transactions inserted.
        """
        if transactions.empty:
            return 0

        insert_sql = f"""
        INSERT INTO {self.TABLE_NAME}
        (transaction_date, description, amount, from_account,
         sub_category, category, c_or_d)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for _, row in transactions.iterrows():
                raw_date = row.get("transaction_date")
                date_str = ""
                if raw_date is not None and pd.notna(raw_date):
                    if hasattr(raw_date, "strftime"):
                        date_str = raw_date.strftime("%Y-%m-%d")
                    else:
                        date_str = (
                            str(raw_date)
                            if str(raw_date).lower() != "none"
                            else ""
                        )

                cursor.execute(insert_sql, (
                    date_str,
                    str(row.get("description", "")),
                    float(row.get("amount", 0)),
                    str(row.get("from_account", "")),
                    str(row.get("sub_category", "")),
                    str(row.get("category", "")),
                    str(row.get("c_or_d", "")),
                ))

            conn.commit()
        except Exception:
            conn.rollback()
            self._logger.exception(
                "Error during transaction insert, rolling back",
            )
            raise
        finally:
            conn.close()

        self._logger.info(
            "Inserted %d transactions", len(transactions),
        )
        return len(transactions)

    def get_all_transactions(self) -> pd.DataFrame:
        """Read all transactions from the database.

        Returns:
            DataFrame with all stored transactions.
        """
        query = f"""
        SELECT transaction_date, description, amount,
               from_account, sub_category, category, c_or_d
        FROM {self.TABLE_NAME}
        ORDER BY transaction_date DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if not df.empty and "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"],
                format="mixed",
                errors="coerce",
            )

        self._logger.info(
            "Loaded %d transactions from database", len(df),
        )
        return df

    def get_transaction_count(self) -> int:
        """Return total number of transactions in the database.

        Returns:
            Integer count of all rows in the transactions table.
        """
        query = f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            row = cursor.fetchone()
            count = row[0] if row is not None else 0
        return count

    def clear_all_transactions(self) -> None:
        """Delete all transactions from the database.

        Use with caution -- primarily for testing or reset.
        """
        with self._get_connection() as conn:
            conn.execute(
                f"DELETE FROM {self.TABLE_NAME}",
            )
            conn.commit()
        self._logger.warning(
            "All transactions cleared from database",
        )

    def get_transactions_by_account(
        self, account: str,
    ) -> pd.DataFrame:
        """Read transactions for a specific account.

        Args:
            account: The from_account value to filter by.

        Returns:
            DataFrame with transactions for the account.
        """
        query = f"""
        SELECT transaction_date, description, amount,
               from_account, sub_category, category, c_or_d
        FROM {self.TABLE_NAME}
        WHERE from_account = ?
        ORDER BY transaction_date DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(
                query, conn, params=(account,),
            )

        if not df.empty and "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"],
                format="mixed",
                errors="coerce",
            )

        return df

    def update_categorization_batch(
        self, *, updates: pd.DataFrame,
    ) -> int:
        """Batch-update sub_category and category for rows.

        Matches rows by (transaction_date, description, amount,
        from_account) and overwrites their sub_category and
        category.

        Args:
            updates: DataFrame with columns transaction_date,
                description, amount, from_account, sub_category,
                category.

        Returns:
            Number of rows actually updated.
        """
        if updates.empty:
            return 0

        update_sql = f"""
        UPDATE {self.TABLE_NAME}
        SET sub_category = ?, category = ?
        WHERE transaction_date = ?
          AND description = ?
          AND amount = ?
          AND from_account = ?
        """

        updated_count = 0
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            for _, row in updates.iterrows():
                raw_date = row.get("transaction_date")
                if (
                    raw_date is not None
                    and pd.notna(raw_date)
                ):
                    if hasattr(raw_date, "strftime"):
                        date_str = raw_date.strftime(
                            "%Y-%m-%d",
                        )
                    else:
                        date_str = str(raw_date)
                else:
                    date_str = ""

                cursor.execute(update_sql, (
                    str(row.get("sub_category", "")),
                    str(row.get("category", "")),
                    date_str,
                    str(row.get("description", "")),
                    float(row.get("amount", 0)),
                    str(row.get("from_account", "")),
                ))
                updated_count += cursor.rowcount

            conn.commit()
        except Exception:
            conn.rollback()
            self._logger.exception(
                "Error during categorization update, "
                "rolling back",
            )
            raise
        finally:
            conn.close()

        self._logger.info(
            "Updated categorization for %d transactions",
            updated_count,
        )
        return updated_count

    def has_transactions(self) -> bool:
        """Check if the database has any transactions.

        Returns:
            True if the transactions table has at least one row.
        """
        return self.get_transaction_count() > 0


# -------------------------------------------------------------------
# Database transaction repository
# -------------------------------------------------------------------

class DatabaseTransactionRepository:
    """Repository providing pre-processed transactions from DB.

    Returns transactions that are already categorized,
    bypassing the need to re-process CSV files on startup.
    """

    def __init__(
        self,
        database: TransactionDatabase,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the repository.

        Args:
            database: TransactionDatabase instance.
            logger: Optional logger for diagnostics.
        """
        self._database = database
        self._logger = logger or logging.getLogger(
            "budget_analyser.database",
        )

    def get_processed_transactions(self) -> pd.DataFrame:
        """Return all processed transactions from the database.

        Returns:
            DataFrame with columns: transaction_date,
            description, amount, from_account, sub_category,
            category, c_or_d
        """
        df = self._database.get_all_transactions()
        self._logger.info(
            "Retrieved %d transactions from database", len(df),
        )
        return df

    def has_data(self) -> bool:
        """Check if the database has any transactions.

        Returns:
            True if the underlying database has at least one row.
        """
        return self._database.has_transactions()
