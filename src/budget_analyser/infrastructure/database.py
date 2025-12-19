"""SQLite database adapter (infrastructure).

Purpose:
    Provide persistent storage for processed transactions.

Goal:
    Store merged, categorized transactions in SQLite to avoid re-processing
    on every app startup and to prevent duplicate entries.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class TransactionRecord:
    """A single transaction record for database operations."""

    transaction_date: str
    description: str
    amount: float
    from_account: str
    sub_category: str = ""
    category: str = ""
    c_or_d: str = ""


class TransactionDatabase:
    """SQLite-backed transaction storage.

    Responsibilities:
        - Create and manage the transactions table
        - Insert transactions with duplicate prevention
        - Read all transactions for report generation
    """

    TABLE_NAME = "transactions"

    def __init__(self, db_path: Path, logger: logging.Logger | None = None) -> None:
        """Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger("budget_analyser.database")
        self._ensure_table_exists()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        # Ensure parent directory exists
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table_exists(self) -> None:
        """Create the transactions table if it doesn't exist."""
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(transaction_date, description, amount, from_account)
        )
        """
        with self._get_connection() as conn:
            conn.execute(create_sql)
            # Create index for faster date-based queries
            conn.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_transaction_date 
                ON {self.TABLE_NAME}(transaction_date)
            """)
            conn.commit()
        self._logger.info("Database initialized at %s", self._db_path)

    def insert_transactions(self, transactions: pd.DataFrame) -> int:
        """Insert transactions into the database, skipping duplicates.

        Args:
            transactions: DataFrame with columns:
                transaction_date, description, amount, from_account,
                sub_category, category, c_or_d

        Returns:
            Number of new transactions inserted (excludes duplicates).
        """
        if transactions.empty:
            return 0

        insert_sql = f"""
        INSERT OR IGNORE INTO {self.TABLE_NAME}
        (transaction_date, description, amount, from_account, 
         sub_category, category, c_or_d)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        inserted_count = 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for _, row in transactions.iterrows():
                # Convert transaction_date to string for storage
                date_str = str(row.get("transaction_date", ""))
                if hasattr(row.get("transaction_date"), "strftime"):
                    date_str = row["transaction_date"].strftime("%Y-%m-%d")

                cursor.execute(insert_sql, (
                    date_str,
                    str(row.get("description", "")),
                    float(row.get("amount", 0)),
                    str(row.get("from_account", "")),
                    str(row.get("sub_category", "")),
                    str(row.get("category", "")),
                    str(row.get("c_or_d", "")),
                ))
                if cursor.rowcount > 0:
                    inserted_count += 1

            conn.commit()

        self._logger.info(
            "Inserted %d new transactions (skipped %d duplicates)",
            inserted_count,
            len(transactions) - inserted_count,
        )
        return inserted_count

    def get_all_transactions(self) -> pd.DataFrame:
        """Read all transactions from the database.

        Returns:
            DataFrame with all stored transactions.
        """
        query = f"""
        SELECT transaction_date, description, amount, from_account,
               sub_category, category, c_or_d
        FROM {self.TABLE_NAME}
        ORDER BY transaction_date DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        # Convert transaction_date back to datetime
        if not df.empty and "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"], format="mixed", errors="coerce"
            )

        self._logger.info("Loaded %d transactions from database", len(df))
        return df

    def get_transaction_count(self) -> int:
        """Return the total number of transactions in the database."""
        query = f"SELECT COUNT(*) FROM {self.TABLE_NAME}"
        with self._get_connection() as conn:
            cursor = conn.execute(query)
            count = cursor.fetchone()[0]
        return count

    def clear_all_transactions(self) -> None:
        """Delete all transactions from the database.

        Use with caution - primarily for testing or reset scenarios.
        """
        with self._get_connection() as conn:
            conn.execute(f"DELETE FROM {self.TABLE_NAME}")
            conn.commit()
        self._logger.warning("All transactions cleared from database")

    def get_transactions_by_account(self, account: str) -> pd.DataFrame:
        """Read transactions for a specific account.

        Args:
            account: The from_account value to filter by.

        Returns:
            DataFrame with transactions for the specified account.
        """
        query = f"""
        SELECT transaction_date, description, amount, from_account,
               sub_category, category, c_or_d
        FROM {self.TABLE_NAME}
        WHERE from_account = ?
        ORDER BY transaction_date DESC
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(account,))

        if not df.empty and "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(
                df["transaction_date"], format="mixed", errors="coerce"
            )

        return df

    def has_transactions(self) -> bool:
        """Check if the database has any transactions."""
        return self.get_transaction_count() > 0


class DatabaseTransactionRepository:
    """Repository that provides pre-processed transactions from the database.

    This repository returns transactions that are already categorized,
    bypassing the need to re-process CSV files on every app startup.
    """

    def __init__(self, database: TransactionDatabase, logger: logging.Logger | None = None):
        """Initialize the repository.

        Args:
            database: TransactionDatabase instance.
            logger: Optional logger for diagnostics.
        """
        self._database = database
        self._logger = logger or logging.getLogger("budget_analyser.database")

    def get_processed_transactions(self) -> pd.DataFrame:
        """Return all processed transactions from the database.

        Returns:
            DataFrame with columns: transaction_date, description, amount,
            from_account, sub_category, category, c_or_d
        """
        df = self._database.get_all_transactions()
        self._logger.info("Retrieved %d transactions from database", len(df))
        return df

    def has_data(self) -> bool:
        """Check if the database has any transactions."""
        return self._database.has_transactions()
