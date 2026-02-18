"""Net worth feature models and data access.

Data transfer objects for accounts and net worth tracking,
plus SQLite-backed storage for financial accounts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from budget_analyser.core.database import get_connection


@dataclass
class Account:
    """A financial account for net worth tracking.

    Attributes:
        id: Database primary key, or None for unsaved accounts.
        name: Unique account name (e.g. "Chase Checking").
        account_type: One of "checking", "savings", "credit_card",
            "investment", "loan", or "other".
        balance: Current account balance in dollars.
        last_updated: Date of last balance update (ISO format).
        notes: Optional free-text notes about the account.

    Example:
        >>> account = Account(
        ...     id=1,
        ...     name="Chase Checking",
        ...     account_type="checking",
        ...     balance=2500.0,
        ...     last_updated="2024-01-15",
        ... )
        >>> account.name
        'Chase Checking'
    """

    id: int | None
    name: str
    account_type: str  # "checking", "savings", "credit_card", "investment", "loan", "other"
    balance: float
    last_updated: str  # ISO date format
    notes: str = ""


@dataclass
class NetWorthSummary:
    """Net worth summary with breakdown by account type.

    Attributes:
        total_assets: Sum of all asset account balances.
        total_liabilities: Sum of all liability account balances.
        net_worth: Total assets minus total liabilities.
        assets_by_type: Asset balances grouped by account type.
        liabilities_by_type: Liability balances grouped by type.
        accounts: All accounts included in the summary.

    Example:
        >>> summary = NetWorthSummary(
        ...     total_assets=10000.0,
        ...     total_liabilities=2000.0,
        ...     net_worth=8000.0,
        ...     assets_by_type={"checking": 5000.0, "savings": 5000.0},
        ...     liabilities_by_type={"credit_card": 2000.0},
        ...     accounts=[],
        ... )
        >>> summary.net_worth
        8000.0
    """

    total_assets: float
    total_liabilities: float
    net_worth: float
    assets_by_type: dict[str, float]
    liabilities_by_type: dict[str, float]
    accounts: list[Account]


class NetWorthModel:
    """SQLite-backed storage for financial accounts.

    Manages CRUD operations for financial accounts used in
    net worth tracking. The accounts table is created automatically.

    Example:
        >>> from pathlib import Path
        >>> model = NetWorthModel(db_path=Path("budget.db"))
        >>> account = model.add_account(
        ...     "Chase Checking", "checking", 2500.0,
        ... )
        >>> account.name
        'Chase Checking'
    """

    ACCOUNTS_TABLE = "accounts"

    def __init__(
        self,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the net worth model.

        Creates the accounts table if it does not already exist.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.

        Example:
            >>> from pathlib import Path
            >>> model = NetWorthModel(
            ...     db_path=Path("/tmp/test.db"),
            ... )
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.net_worth.models"
        )
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Create accounts table if it doesn't exist."""
        with get_connection(self._db_path) as conn:
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.ACCOUNTS_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    account_type TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0,
                    last_updated TEXT NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        self._logger.info(
            "Accounts table initialized at %s", self._db_path,
        )

    def add_account(
        self,
        name: str,
        account_type: str,
        balance: float = 0,
        notes: str = "",
    ) -> Account:
        """Add a new financial account.

        Args:
            name: Unique account name.
            account_type: Type of account (checking, savings, etc.).
            balance: Initial balance.
            notes: Optional notes about the account.

        Returns:
            The created Account.

        Raises:
            RuntimeError: If the database insert fails.

        Example:
            >>> model.add_account(
            ...     "Savings Account", "savings", 10000.0,
            ... )
            Account(id=1, name='Savings Account', ...)
        """
        today = date.today().isoformat()

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.ACCOUNTS_TABLE}
                    (name, account_type, balance, last_updated, notes)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """, (name, account_type, balance, today, notes))
            row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError(f"Failed to insert account: {name}")

        self._logger.info(
            "Added account: %s (%s) = $%.2f",
            name, account_type, balance,
        )
        return Account(
            id=row["id"],
            name=name,
            account_type=account_type,
            balance=balance,
            last_updated=today,
            notes=notes,
        )

    def update_account_balance(
        self,
        account_id: int,
        balance: float,
    ) -> bool:
        """Update an account's balance.

        Also updates the last_updated date to today.

        Args:
            account_id: The account ID to update.
            balance: The new balance.

        Returns:
            True if the account was updated.

        Example:
            >>> model.update_account_balance(1, 3000.0)
            True
        """
        today = date.today().isoformat()

        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                UPDATE {self.ACCOUNTS_TABLE}
                SET balance = ?, last_updated = ?
                WHERE id = ?
            """, (balance, today, account_id))
            conn.commit()
            updated = cursor.rowcount > 0

        if updated:
            self._logger.info(
                "Updated account %d balance to $%.2f",
                account_id, balance,
            )
        return updated

    def get_all_accounts(self) -> list[Account]:
        """Get all financial accounts.

        Returns:
            List of all Account entries ordered by type and name.

        Example:
            >>> accounts = model.get_all_accounts()
            >>> len(accounts)
            3
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                SELECT id, name, account_type, balance,
                       last_updated, notes
                FROM {self.ACCOUNTS_TABLE}
                ORDER BY account_type, name
            """)
            rows = cursor.fetchall()

        return [
            Account(
                id=row["id"],
                name=row["name"],
                account_type=row["account_type"],
                balance=row["balance"],
                last_updated=row["last_updated"],
                notes=row["notes"],
            )
            for row in rows
        ]

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account.

        Args:
            account_id: The account ID to delete.

        Returns:
            True if an account was deleted.

        Example:
            >>> model.delete_account(1)
            True
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.ACCOUNTS_TABLE}
                WHERE id = ?
            """, (account_id,))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info("Deleted account %d", account_id)
        return deleted


NetWorthRepository = NetWorthModel
