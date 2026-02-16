"""Recurring transactions repository.

Provides database storage for recurring transactions.
Operates on the shared SQLite database via the core connection factory.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from budget_analyser.core.database import get_connection
from budget_analyser.features.recurring.models import RecurringTransaction


class RecurringRepository:
    """SQLite-backed storage for recurring transactions."""

    RECURRING_TABLE = "recurring_transactions"

    def __init__(
        self,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the recurring transactions repository.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.recurring.repository"
        )
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Create recurring transactions table if it doesn't exist."""
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.RECURRING_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    expected_amount REAL NOT NULL,
                    frequency TEXT NOT NULL DEFAULT 'monthly',
                    category TEXT DEFAULT '',
                    sub_category TEXT DEFAULT '',
                    last_occurrence TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(description, expected_amount)
                )
            """)
            conn.commit()
        self._logger.info(
            "Recurring transactions table initialized at %s",
            self._db_path,
        )

    def add_recurring_transaction(  # pylint: disable=too-many-positional-arguments
        self,
        description: str,
        expected_amount: float,
        frequency: str = "monthly",
        category: str = "",
        sub_category: str = "",
    ) -> RecurringTransaction:
        """Add or update a recurring transaction.

        Args:
            description: Transaction description.
            expected_amount: Expected transaction amount.
            frequency: How often (weekly, monthly, quarterly, yearly).
            category: Transaction category.
            sub_category: Transaction sub-category.

        Returns:
            The created or updated RecurringTransaction.

        Raises:
            RuntimeError: If the database insert fails.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.RECURRING_TABLE}
                    (description, expected_amount, frequency,
                     category, sub_category)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(description, expected_amount) DO UPDATE SET
                    frequency = excluded.frequency,
                    category = excluded.category,
                    sub_category = excluded.sub_category
                RETURNING id
            """, (
                description, expected_amount, frequency,
                category, sub_category,
            ))
            row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError(
                f"Failed to insert recurring transaction: {description}"
            )

        self._logger.info(
            "Added recurring transaction: %s ($%.2f %s)",
            description, expected_amount, frequency,
        )
        return RecurringTransaction(
            id=row["id"],
            description=description,
            expected_amount=expected_amount,
            frequency=frequency,
            category=category,
            sub_category=sub_category,
            last_occurrence="",
        )

    def get_all_recurring_transactions(
        self,
        active_only: bool = True,
    ) -> list[RecurringTransaction]:
        """Get all recurring transactions.

        Args:
            active_only: If True, return only active transactions.

        Returns:
            List of RecurringTransaction entries ordered by description.
        """
        query = f"""
            SELECT id, description, expected_amount, frequency,
                   category, sub_category, last_occurrence, is_active
            FROM {self.RECURRING_TABLE}
        """
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY description"

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

        return [
            RecurringTransaction(
                id=row["id"],
                description=row["description"],
                expected_amount=row["expected_amount"],
                frequency=row["frequency"],
                category=row["category"],
                sub_category=row["sub_category"],
                last_occurrence=row["last_occurrence"] or "",
                is_active=bool(row["is_active"]),
            )
            for row in rows
        ]

    def update_last_occurrence(
        self,
        recurring_id: int,
        last_occurrence: str,
    ) -> bool:
        """Update the last occurrence date of a recurring transaction.

        Args:
            recurring_id: The recurring transaction ID.
            last_occurrence: ISO date string of last occurrence.

        Returns:
            True if the record was updated.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET last_occurrence = ?
                WHERE id = ?
            """, (last_occurrence, recurring_id))
            conn.commit()
            return cursor.rowcount > 0

    def deactivate_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Mark a recurring transaction as inactive.

        Args:
            recurring_id: The recurring transaction ID.

        Returns:
            True if the record was deactivated.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET is_active = 0
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_recurring_transaction(
        self,
        recurring_id: int,
    ) -> bool:
        """Delete a recurring transaction.

        Args:
            recurring_id: The recurring transaction ID.

        Returns:
            True if the record was deleted.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.RECURRING_TABLE}
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info(
                "Deleted recurring transaction %d", recurring_id,
            )
        return deleted

    def detect_recurring_transactions(
        self,
        transactions_df: pd.DataFrame,
        min_occurrences: int = 2,
    ) -> list[dict]:
        """Detect potential recurring transactions from history.

        Args:
            transactions_df: DataFrame with transaction data.
            min_occurrences: Minimum times a transaction must appear.

        Returns:
            List of detected recurring transaction patterns.
        """
        if transactions_df.empty:
            return []

        df = transactions_df.copy()
        df["amount_rounded"] = df["amount"].round(2)

        grouped = df.groupby(
            ["description", "amount_rounded"]
        ).agg({
            "transaction_date": ["count", "min", "max"],
            "category": "first",
            "sub_category": "first",
        }).reset_index()

        grouped.columns = [
            "description", "amount", "count", "first_date",
            "last_date", "category", "sub_category",
        ]

        recurring = grouped[grouped["count"] >= min_occurrences]

        detected = []
        for _, row in recurring.iterrows():
            frequency = self._estimate_frequency(
                row["first_date"], row["last_date"], row["count"],
            )
            detected.append({
                "description": row["description"],
                "amount": float(row["amount"]),
                "frequency": frequency,
                "occurrences": int(row["count"]),
                "category": row["category"] or "",
                "sub_category": row["sub_category"] or "",
                "last_date": (
                    str(row["last_date"])[:10]
                    if pd.notna(row["last_date"]) else ""
                ),
            })

        detected.sort(key=lambda x: x["occurrences"], reverse=True)

        self._logger.info(
            "Detected %d potential recurring transactions",
            len(detected),
        )
        return detected

    @staticmethod
    def _estimate_frequency(
        first_date: object,
        last_date: object,
        count: int,
    ) -> str:
        """Estimate transaction frequency from date range.

        Args:
            first_date: Earliest transaction date.
            last_date: Latest transaction date.
            count: Number of occurrences.

        Returns:
            Frequency string (weekly, monthly, quarterly, yearly).
        """
        if (pd.notna(first_date) and pd.notna(last_date)
                and count > 1):
            days_span = (last_date - first_date).days
            if days_span > 0:
                avg_days = days_span / (count - 1)
                if avg_days <= 10:
                    return "weekly"
                if avg_days <= 45:
                    return "monthly"
                if avg_days <= 100:
                    return "quarterly"
                return "yearly"
        return "monthly"
