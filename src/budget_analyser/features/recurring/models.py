"""Recurring payment analytics DTOs and database model.

Contains all DTOs specific to the recurring payment analytics feature
(recurring transactions, anomalies, detection results, summaries) and
the ``RecurringModel`` class that provides SQLite persistence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from budget_analyser.core.database import get_connection


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecurringTransaction:  # pylint: disable=too-many-instance-attributes
    """A detected or manually added recurring transaction.

    Attributes:
        id: Database primary key, or None for unsaved records.
        description: Transaction description text.
        expected_amount: Expected payment amount in dollars.
        amount_variance: Allowed variance from expected amount.
        frequency: Payment frequency (e.g. "monthly", "weekly").
        category: Top-level expense category.
        sub_category: Detailed sub-category label.
        last_occurrence: Date of last observed payment (ISO format).
        next_expected: Projected date of next payment (ISO format).
        confidence_score: Auto-detection confidence (0.0 to 1.0).
        user_confirmed: Whether the user has confirmed this recurring.
        is_expected: Whether a payment is currently expected.
        is_active: Whether this recurring entry is active.
        detection_method: How it was detected ("auto" or "manual").
    """

    id: int | None
    description: str
    expected_amount: float
    amount_variance: float
    frequency: str
    category: str
    sub_category: str
    last_occurrence: str | None
    next_expected: str | None
    confidence_score: float
    user_confirmed: bool
    is_expected: bool
    is_active: bool
    detection_method: str


@dataclass(frozen=True)
class RecurringAnomaly:  # pylint: disable=too-many-instance-attributes
    """An anomaly detected for a recurring transaction.

    Attributes:
        id: Database primary key, or None for unsaved records.
        recurring_id: Foreign key to the recurring transaction.
        anomaly_type: Type of anomaly ("missed_payment" or "amount_spike").
        expected_date: When the payment was expected (ISO format).
        actual_date: When the payment actually occurred (ISO format).
        expected_amount: Amount that was expected.
        actual_amount: Amount that was actually charged.
        severity: Anomaly severity ("info", "warning", "critical").
        message: Human-readable anomaly description.
        resolved: Whether the anomaly has been resolved.
        detected_at: Timestamp when the anomaly was detected.
    """

    id: int | None
    recurring_id: int
    anomaly_type: str
    expected_date: str | None
    actual_date: str | None
    expected_amount: float | None
    actual_amount: float | None
    severity: str
    message: str
    resolved: bool
    detected_at: str | None


@dataclass(frozen=True)
class RecurringDetection:  # pylint: disable=too-many-instance-attributes
    """Transient detection result from auto-detection (not persisted).

    Attributes:
        description: Transaction description text.
        expected_amount: Average payment amount detected.
        amount_variance: Standard deviation of payment amounts.
        frequency: Detected payment frequency.
        category: Top-level expense category.
        sub_category: Detailed sub-category label.
        last_occurrence: Date of most recent occurrence (ISO format).
        occurrences: Total number of matching transactions found.
        confidence_score: Detection confidence (0.0 to 1.0).
        matching_dates: List of dates where matching payments occurred.
    """

    description: str
    expected_amount: float
    amount_variance: float
    frequency: str
    category: str
    sub_category: str
    last_occurrence: str | None
    occurrences: int
    confidence_score: float
    matching_dates: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RecurringSummary:  # pylint: disable=too-many-instance-attributes
    """Analytics summary for recurring transactions.

    Attributes:
        total_monthly_cost: Sum of all active recurring monthly costs.
        total_yearly_projection: Projected annual cost from recurrings.
        active_count: Number of active recurring transactions.
        confirmed_count: Number of user-confirmed recurrings.
        unconfirmed_count: Number of auto-detected, unconfirmed recurrings.
        by_frequency: Count of recurrings grouped by frequency.
        by_category: Total cost grouped by category.
        trend_data: Monthly cost trend data points.
    """

    total_monthly_cost: float
    total_yearly_projection: float
    active_count: int
    confirmed_count: int
    unconfirmed_count: int
    by_frequency: dict[str, int] = field(default_factory=dict)
    by_category: dict[str, float] = field(default_factory=dict)
    trend_data: list[dict[str, float]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Allowed fields for partial updates
# ---------------------------------------------------------------------------

_UPDATABLE_FIELDS: frozenset[str] = frozenset({
    "description",
    "expected_amount",
    "amount_variance",
    "frequency",
    "category",
    "sub_category",
    "is_expected",
    "last_occurrence",
    "next_expected",
})


# ---------------------------------------------------------------------------
# Database model
# ---------------------------------------------------------------------------

class RecurringModel:
    """SQLite-backed storage for recurring transactions and anomalies.

    Manages persistence of detected recurring payments and their
    anomalies in a shared SQLite database. Tables are created
    automatically on first use.

    Example:
        >>> from pathlib import Path
        >>> model = RecurringModel(db_path=Path("budget.db"))
        >>> txn = model.save_recurring(
        ...     description="Netflix",
        ...     expected_amount=15.99,
        ...     amount_variance=0.0,
        ...     frequency="monthly",
        ...     category="Entertainment",
        ...     sub_category="Streaming",
        ...     last_occurrence="2025-12-01",
        ...     next_expected="2026-01-01",
        ...     confidence_score=0.95,
        ...     user_confirmed=False,
        ...     is_expected=True,
        ...     is_active=True,
        ...     detection_method="auto",
        ... )
        >>> txn.description
        'Netflix'
    """

    RECURRING_TABLE = "recurring_transactions"
    ANOMALIES_TABLE = "recurring_anomalies"

    def __init__(
        self,
        *,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the recurring model.

        Creates recurring_transactions and recurring_anomalies tables
        if they do not already exist.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.recurring.models"
        )
        self._ensure_tables_exist()

    # ------------------------------------------------------------------
    # Table setup
    # ------------------------------------------------------------------

    def _ensure_tables_exist(self) -> None:
        """Create recurring-related tables if they don't exist."""
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.RECURRING_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    expected_amount REAL NOT NULL,
                    amount_variance REAL NOT NULL DEFAULT 0.0,
                    frequency TEXT NOT NULL DEFAULT 'monthly',
                    category TEXT NOT NULL DEFAULT '',
                    sub_category TEXT NOT NULL DEFAULT '',
                    last_occurrence TEXT,
                    next_expected TEXT,
                    confidence_score REAL NOT NULL DEFAULT 0.0,
                    user_confirmed INTEGER NOT NULL DEFAULT 0,
                    is_expected INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    detection_method TEXT NOT NULL DEFAULT 'auto',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(description, frequency)
                )
            """)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.ANOMALIES_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recurring_id INTEGER NOT NULL,
                    anomaly_type TEXT NOT NULL,
                    expected_date TEXT,
                    actual_date TEXT,
                    expected_amount REAL,
                    actual_amount REAL,
                    severity TEXT NOT NULL DEFAULT 'info',
                    message TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recurring_id)
                        REFERENCES {self.RECURRING_TABLE}(id)
                )
            """)
            conn.commit()
        self._logger.info(
            "Recurring tables initialized at %s", self._db_path,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _row_to_recurring(
        self, row: Any,
    ) -> RecurringTransaction:
        """Convert a database row to a RecurringTransaction DTO.

        Args:
            row: A sqlite3.Row from the recurring_transactions table.

        Returns:
            A RecurringTransaction instance.
        """
        return RecurringTransaction(
            id=row["id"],
            description=row["description"],
            expected_amount=row["expected_amount"],
            amount_variance=row["amount_variance"],
            frequency=row["frequency"],
            category=row["category"],
            sub_category=row["sub_category"],
            last_occurrence=row["last_occurrence"],
            next_expected=row["next_expected"],
            confidence_score=row["confidence_score"],
            user_confirmed=bool(row["user_confirmed"]),
            is_expected=bool(row["is_expected"]),
            is_active=bool(row["is_active"]),
            detection_method=row["detection_method"],
        )

    def _row_to_anomaly(
        self, row: Any,
    ) -> RecurringAnomaly:
        """Convert a database row to a RecurringAnomaly DTO.

        Args:
            row: A sqlite3.Row from the recurring_anomalies table.

        Returns:
            A RecurringAnomaly instance.
        """
        return RecurringAnomaly(
            id=row["id"],
            recurring_id=row["recurring_id"],
            anomaly_type=row["anomaly_type"],
            expected_date=row["expected_date"],
            actual_date=row["actual_date"],
            expected_amount=row["expected_amount"],
            actual_amount=row["actual_amount"],
            severity=row["severity"],
            message=row["message"],
            resolved=bool(row["resolved"]),
            detected_at=row["detected_at"],
        )

    # ------------------------------------------------------------------
    # Recurring transaction CRUD
    # ------------------------------------------------------------------

    def save_recurring(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        description: str,
        expected_amount: float,
        amount_variance: float,
        frequency: str,
        category: str,
        sub_category: str,
        last_occurrence: str | None,
        next_expected: str | None,
        confidence_score: float,
        user_confirmed: bool,
        is_expected: bool,
        is_active: bool,
        detection_method: str,
    ) -> RecurringTransaction:
        """Save or update a recurring transaction (upsert).

        Uses INSERT OR REPLACE on the (description, frequency) unique
        constraint to handle both new inserts and updates.

        Args:
            description: Transaction description text.
            expected_amount: Expected payment amount.
            amount_variance: Allowed variance from expected amount.
            frequency: Payment frequency (e.g. "monthly").
            category: Top-level expense category.
            sub_category: Detailed sub-category label.
            last_occurrence: Date of last payment (ISO format).
            next_expected: Projected next payment date (ISO format).
            confidence_score: Detection confidence (0.0 to 1.0).
            user_confirmed: Whether user has confirmed this recurring.
            is_expected: Whether a payment is currently expected.
            is_active: Whether this entry is active.
            detection_method: Detection method ("auto" or "manual").

        Returns:
            The saved RecurringTransaction with its database id.

        Raises:
            RuntimeError: If the database insert fails.
        """
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                INSERT OR REPLACE INTO {self.RECURRING_TABLE}
                    (description, expected_amount, amount_variance,
                     frequency, category, sub_category,
                     last_occurrence, next_expected,
                     confidence_score, user_confirmed,
                     is_expected, is_active, detection_method,
                     updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        CURRENT_TIMESTAMP)
            """, (
                description, expected_amount, amount_variance,
                frequency, category, sub_category,
                last_occurrence, next_expected,
                confidence_score, int(user_confirmed),
                int(is_expected), int(is_active), detection_method,
            ))
            conn.commit()

            cursor = conn.execute(f"""
                SELECT * FROM {self.RECURRING_TABLE}
                WHERE description = ? AND frequency = ?
            """, (description, frequency))
            row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                f"Failed to save recurring transaction: {description}"
            )

        self._logger.info(
            "Saved recurring: %s (%s, $%.2f)",
            description, frequency, expected_amount,
        )
        return self._row_to_recurring(row)

    def get_all_recurring(
        self,
        *,
        active_only: bool = False,
    ) -> list[RecurringTransaction]:
        """Get all recurring transactions.

        Args:
            active_only: If True, return only active entries.

        Returns:
            List of RecurringTransaction entries ordered by description.
        """
        query = f"""
            SELECT * FROM {self.RECURRING_TABLE}
        """
        params: tuple[Any, ...] = ()
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY description"

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_recurring(row) for row in rows]

    def get_recurring_by_id(
        self,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        """Get a recurring transaction by its database id.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            RecurringTransaction if found, None otherwise.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                SELECT * FROM {self.RECURRING_TABLE}
                WHERE id = ?
            """, (recurring_id,))
            row = cursor.fetchone()

        if row is None:
            return None
        return self._row_to_recurring(row)

    def update_recurring(
        self,
        recurring_id: int,
        **kwargs: Any,
    ) -> RecurringTransaction | None:
        """Partially update a recurring transaction.

        Only the provided keyword arguments are updated. Allowed
        fields: description, expected_amount, amount_variance,
        frequency, category, sub_category, is_expected,
        last_occurrence, next_expected.

        Args:
            recurring_id: The primary key of the recurring record.
            **kwargs: Field names and their new values.

        Returns:
            The updated RecurringTransaction, or None if not found.

        Raises:
            ValueError: If an unsupported field name is provided.
        """
        invalid_fields = set(kwargs) - _UPDATABLE_FIELDS
        if invalid_fields:
            raise ValueError(
                f"Cannot update fields: {', '.join(invalid_fields)}"
            )

        if not kwargs:
            return self.get_recurring_by_id(recurring_id)

        set_clauses = [f"{key} = ?" for key in kwargs]
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        set_sql = ", ".join(set_clauses)

        values = list(kwargs.values())
        values.append(recurring_id)

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(
                f"UPDATE {self.RECURRING_TABLE} "
                f"SET {set_sql} WHERE id = ?",
                values,
            )
            conn.commit()

            if cursor.rowcount == 0:
                return None

        self._logger.info(
            "Updated recurring id=%d: %s",
            recurring_id, list(kwargs.keys()),
        )
        return self.get_recurring_by_id(recurring_id)

    def delete_recurring(self, recurring_id: int) -> bool:
        """Delete a recurring transaction by id.

        Also deletes all associated anomalies.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            True if the record was deleted, False if not found.
        """
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                DELETE FROM {self.ANOMALIES_TABLE}
                WHERE recurring_id = ?
            """, (recurring_id,))
            cursor = conn.execute(f"""
                DELETE FROM {self.RECURRING_TABLE}
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info(
                "Deleted recurring id=%d", recurring_id,
            )
        return deleted

    def confirm_recurring(
        self,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        """Mark a recurring transaction as user-confirmed.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            The updated RecurringTransaction, or None if not found.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET user_confirmed = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return None

        self._logger.info(
            "Confirmed recurring id=%d", recurring_id,
        )
        return self.get_recurring_by_id(recurring_id)

    def dismiss_recurring(
        self,
        recurring_id: int,
    ) -> RecurringTransaction | None:
        """Dismiss a recurring transaction by marking it inactive.

        Args:
            recurring_id: The primary key of the recurring record.

        Returns:
            The updated RecurringTransaction, or None if not found.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()

            if cursor.rowcount == 0:
                return None

        self._logger.info(
            "Dismissed recurring id=%d", recurring_id,
        )
        return self.get_recurring_by_id(recurring_id)

    # ------------------------------------------------------------------
    # Anomaly CRUD
    # ------------------------------------------------------------------

    def save_anomaly(  # pylint: disable=too-many-arguments
        self,
        *,
        recurring_id: int,
        anomaly_type: str,
        expected_date: str | None,
        actual_date: str | None,
        expected_amount: float | None,
        actual_amount: float | None,
        severity: str,
        message: str,
    ) -> RecurringAnomaly:
        """Save a new anomaly record for a recurring transaction.

        Args:
            recurring_id: Foreign key to the recurring transaction.
            anomaly_type: Type ("missed_payment" or "amount_spike").
            expected_date: When the payment was expected (ISO format).
            actual_date: When the payment occurred (ISO format).
            expected_amount: Amount that was expected.
            actual_amount: Amount that was actually charged.
            severity: Severity level ("info", "warning", "critical").
            message: Human-readable anomaly description.

        Returns:
            The saved RecurringAnomaly with its database id.

        Raises:
            RuntimeError: If the database insert fails.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.ANOMALIES_TABLE}
                    (recurring_id, anomaly_type, expected_date,
                     actual_date, expected_amount, actual_amount,
                     severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                RETURNING id, detected_at
            """, (
                recurring_id, anomaly_type, expected_date,
                actual_date, expected_amount, actual_amount,
                severity, message,
            ))
            row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError(
                f"Failed to save anomaly for recurring_id={recurring_id}"
            )

        self._logger.info(
            "Saved anomaly: type=%s, recurring_id=%d, severity=%s",
            anomaly_type, recurring_id, severity,
        )
        return RecurringAnomaly(
            id=row["id"],
            recurring_id=recurring_id,
            anomaly_type=anomaly_type,
            expected_date=expected_date,
            actual_date=actual_date,
            expected_amount=expected_amount,
            actual_amount=actual_amount,
            severity=severity,
            message=message,
            resolved=False,
            detected_at=row["detected_at"],
        )

    def get_anomalies(
        self,
        *,
        recurring_id: int | None = None,
        unresolved_only: bool = False,
    ) -> list[RecurringAnomaly]:
        """Get anomalies with optional filters.

        Args:
            recurring_id: Filter by recurring transaction id.
            unresolved_only: If True, return only unresolved anomalies.

        Returns:
            List of RecurringAnomaly entries ordered by detected_at.
        """
        query = f"SELECT * FROM {self.ANOMALIES_TABLE}"
        conditions: list[str] = []
        params: list[Any] = []

        if recurring_id is not None:
            conditions.append("recurring_id = ?")
            params.append(recurring_id)
        if unresolved_only:
            conditions.append("resolved = 0")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY detected_at DESC"

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        return [self._row_to_anomaly(row) for row in rows]

    def resolve_anomaly(self, anomaly_id: int) -> bool:
        """Mark an anomaly as resolved.

        Args:
            anomaly_id: The primary key of the anomaly record.

        Returns:
            True if the anomaly was resolved, False if not found.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.ANOMALIES_TABLE}
                SET resolved = 1
                WHERE id = ?
            """, (anomaly_id,))
            conn.commit()
            resolved = cursor.rowcount > 0

        if resolved:
            self._logger.info(
                "Resolved anomaly id=%d", anomaly_id,
            )
        return resolved
