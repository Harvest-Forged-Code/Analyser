"""Budget database operations.

Provides database storage for budget goals, accounts, and recurring transactions
to support financial planning features.
"""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd


@dataclass
class BudgetGoal:
    """A budget goal for a specific expense category."""
    
    id: Optional[int]
    category: str
    monthly_limit: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months


@dataclass
class EarningsGoal:
    """An expected earnings goal for a specific sub-category."""
    
    id: Optional[int]
    sub_category: str
    expected_amount: float
    year_month: str  # Format: "YYYY-MM" or "ALL" for all months
    
    
@dataclass
class Account:
    """A financial account for net worth tracking."""
    
    id: Optional[int]
    name: str
    account_type: str  # "checking", "savings", "credit_card", "investment", "loan", "other"
    balance: float
    last_updated: str  # ISO date format
    notes: str = ""


@dataclass
class RecurringTransaction:
    """A detected or user-defined recurring transaction."""
    
    id: Optional[int]
    description: str
    expected_amount: float
    frequency: str  # "monthly", "weekly", "yearly", "quarterly"
    category: str
    sub_category: str
    last_occurrence: str  # ISO date format
    is_active: bool = True


class BudgetDatabase:
    """SQLite-backed storage for budget goals, earnings goals, accounts, and recurring transactions."""

    BUDGETS_TABLE = "budget_goals"
    EARNINGS_GOALS_TABLE = "earnings_goals"
    ACCOUNTS_TABLE = "accounts"
    RECURRING_TABLE = "recurring_transactions"

    def __init__(self, db_path: Path, logger: logging.Logger | None = None) -> None:
        """Initialize the budget database.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger("budget_analyser.budget_database")
        self._ensure_tables_exist()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables_exist(self) -> None:
        """Create all budget-related tables if they don't exist."""
        with self._get_connection() as conn:
            # Budget goals table (for expenses)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.BUDGETS_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    monthly_limit REAL NOT NULL,
                    year_month TEXT NOT NULL DEFAULT 'ALL',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, year_month)
                )
            """)
            
            # Earnings goals table (for expected income)
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.EARNINGS_GOALS_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sub_category TEXT NOT NULL,
                    expected_amount REAL NOT NULL,
                    year_month TEXT NOT NULL DEFAULT 'ALL',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sub_category, year_month)
                )
            """)
            
            # Accounts table for net worth tracking
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
            
            # Recurring transactions table
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
        self._logger.info("Budget tables initialized at %s", self._db_path)

    # ==================== Budget Goals Methods ====================
    
    def set_budget_goal(self, category: str, monthly_limit: float, 
                        year_month: str = "ALL") -> BudgetGoal:
        """Set or update a budget goal for a category.
        
        Args:
            category: The expense category name.
            monthly_limit: The monthly spending limit.
            year_month: Specific month "YYYY-MM" or "ALL" for default.
            
        Returns:
            The created or updated BudgetGoal.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.BUDGETS_TABLE} (category, monthly_limit, year_month, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(category, year_month) DO UPDATE SET
                    monthly_limit = excluded.monthly_limit,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (category, monthly_limit, year_month))
            row = cursor.fetchone()
            conn.commit()
            
        self._logger.info("Set budget goal: %s = $%.2f (%s)", 
                         category, monthly_limit, year_month)
        return BudgetGoal(
            id=row["id"],
            category=category,
            monthly_limit=monthly_limit,
            year_month=year_month
        )

    def get_budget_goal(self, category: str, year_month: str = "ALL") -> Optional[BudgetGoal]:
        """Get budget goal for a category.
        
        First checks for month-specific goal, then falls back to "ALL".
        """
        with self._get_connection() as conn:
            # Try specific month first
            cursor = conn.execute(f"""
                SELECT id, category, monthly_limit, year_month
                FROM {self.BUDGETS_TABLE}
                WHERE category = ? AND year_month = ?
            """, (category, year_month))
            row = cursor.fetchone()
            
            # Fall back to ALL if no specific month
            if row is None and year_month != "ALL":
                cursor = conn.execute(f"""
                    SELECT id, category, monthly_limit, year_month
                    FROM {self.BUDGETS_TABLE}
                    WHERE category = ? AND year_month = 'ALL'
                """, (category,))
                row = cursor.fetchone()
                
        if row is None:
            return None
            
        return BudgetGoal(
            id=row["id"],
            category=row["category"],
            monthly_limit=row["monthly_limit"],
            year_month=row["year_month"]
        )

    def get_all_budget_goals(self) -> List[BudgetGoal]:
        """Get all budget goals."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT id, category, monthly_limit, year_month
                FROM {self.BUDGETS_TABLE}
                ORDER BY category, year_month
            """)
            rows = cursor.fetchall()
            
        return [
            BudgetGoal(
                id=row["id"],
                category=row["category"],
                monthly_limit=row["monthly_limit"],
                year_month=row["year_month"]
            )
            for row in rows
        ]

    def delete_budget_goal(self, category: str, year_month: str = "ALL") -> bool:
        """Delete a budget goal."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.BUDGETS_TABLE}
                WHERE category = ? AND year_month = ?
            """, (category, year_month))
            conn.commit()
            deleted = cursor.rowcount > 0
            
        if deleted:
            self._logger.info("Deleted budget goal: %s (%s)", category, year_month)
        return deleted

    # ==================== Earnings Goals Methods ====================
    
    def set_earnings_goal(self, sub_category: str, expected_amount: float,
                          year_month: str = "ALL") -> EarningsGoal:
        """Set or update an earnings goal for a sub-category.
        
        Args:
            sub_category: The earnings sub-category name (e.g., "salary").
            expected_amount: The expected monthly earnings amount.
            year_month: Specific month "YYYY-MM" or "ALL" for default.
            
        Returns:
            The created or updated EarningsGoal.
        """
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.EARNINGS_GOALS_TABLE} (sub_category, expected_amount, year_month, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(sub_category, year_month) DO UPDATE SET
                    expected_amount = excluded.expected_amount,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (sub_category, expected_amount, year_month))
            row = cursor.fetchone()
            conn.commit()
            
        self._logger.info("Set earnings goal: %s = $%.2f (%s)", 
                         sub_category, expected_amount, year_month)
        return EarningsGoal(
            id=row["id"],
            sub_category=sub_category,
            expected_amount=expected_amount,
            year_month=year_month
        )

    def get_earnings_goal(self, sub_category: str, year_month: str = "ALL") -> Optional[EarningsGoal]:
        """Get earnings goal for a sub-category.
        
        First checks for month-specific goal, then falls back to "ALL".
        """
        with self._get_connection() as conn:
            # Try specific month first
            cursor = conn.execute(f"""
                SELECT id, sub_category, expected_amount, year_month
                FROM {self.EARNINGS_GOALS_TABLE}
                WHERE sub_category = ? AND year_month = ?
            """, (sub_category, year_month))
            row = cursor.fetchone()
            
            # Fall back to ALL if no specific month
            if row is None and year_month != "ALL":
                cursor = conn.execute(f"""
                    SELECT id, sub_category, expected_amount, year_month
                    FROM {self.EARNINGS_GOALS_TABLE}
                    WHERE sub_category = ? AND year_month = 'ALL'
                """, (sub_category,))
                row = cursor.fetchone()
                
        if row is None:
            return None
            
        return EarningsGoal(
            id=row["id"],
            sub_category=row["sub_category"],
            expected_amount=row["expected_amount"],
            year_month=row["year_month"]
        )

    def get_all_earnings_goals(self) -> List[EarningsGoal]:
        """Get all earnings goals."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT id, sub_category, expected_amount, year_month
                FROM {self.EARNINGS_GOALS_TABLE}
                ORDER BY sub_category, year_month
            """)
            rows = cursor.fetchall()
            
        return [
            EarningsGoal(
                id=row["id"],
                sub_category=row["sub_category"],
                expected_amount=row["expected_amount"],
                year_month=row["year_month"]
            )
            for row in rows
        ]

    def delete_earnings_goal(self, sub_category: str, year_month: str = "ALL") -> bool:
        """Delete an earnings goal."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.EARNINGS_GOALS_TABLE}
                WHERE sub_category = ? AND year_month = ?
            """, (sub_category, year_month))
            conn.commit()
            deleted = cursor.rowcount > 0
            
        if deleted:
            self._logger.info("Deleted earnings goal: %s (%s)", sub_category, year_month)
        return deleted

    # ==================== Accounts Methods ====================
    
    def add_account(self, name: str, account_type: str, balance: float = 0,
                    notes: str = "") -> Account:
        """Add a new financial account."""
        from datetime import date
        today = date.today().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.ACCOUNTS_TABLE} (name, account_type, balance, last_updated, notes)
                VALUES (?, ?, ?, ?, ?)
                RETURNING id
            """, (name, account_type, balance, today, notes))
            row = cursor.fetchone()
            conn.commit()
            
        self._logger.info("Added account: %s (%s) = $%.2f", name, account_type, balance)
        return Account(
            id=row["id"],
            name=name,
            account_type=account_type,
            balance=balance,
            last_updated=today,
            notes=notes
        )

    def update_account_balance(self, account_id: int, balance: float) -> bool:
        """Update an account's balance."""
        from datetime import date
        today = date.today().isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE {self.ACCOUNTS_TABLE}
                SET balance = ?, last_updated = ?
                WHERE id = ?
            """, (balance, today, account_id))
            conn.commit()
            updated = cursor.rowcount > 0
            
        if updated:
            self._logger.info("Updated account %d balance to $%.2f", account_id, balance)
        return updated

    def get_all_accounts(self) -> List[Account]:
        """Get all financial accounts."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                SELECT id, name, account_type, balance, last_updated, notes
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
                notes=row["notes"]
            )
            for row in rows
        ]

    def delete_account(self, account_id: int) -> bool:
        """Delete a financial account."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.ACCOUNTS_TABLE}
                WHERE id = ?
            """, (account_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            
        if deleted:
            self._logger.info("Deleted account %d", account_id)
        return deleted

    def get_net_worth(self) -> dict:
        """Calculate net worth from all accounts.
        
        Returns:
            Dictionary with assets, liabilities, and net_worth.
        """
        accounts = self.get_all_accounts()
        
        assets = 0.0
        liabilities = 0.0
        
        asset_types = {"checking", "savings", "investment", "other"}
        liability_types = {"credit_card", "loan"}
        
        for account in accounts:
            if account.account_type in asset_types:
                assets += account.balance
            elif account.account_type in liability_types:
                liabilities += abs(account.balance)
                
        return {
            "assets": assets,
            "liabilities": liabilities,
            "net_worth": assets - liabilities,
            "accounts": accounts
        }

    # ==================== Recurring Transactions Methods ====================
    
    def add_recurring_transaction(self, description: str, expected_amount: float,
                                   frequency: str = "monthly", category: str = "",
                                   sub_category: str = "") -> RecurringTransaction:
        """Add a recurring transaction."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.RECURRING_TABLE} 
                (description, expected_amount, frequency, category, sub_category)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(description, expected_amount) DO UPDATE SET
                    frequency = excluded.frequency,
                    category = excluded.category,
                    sub_category = excluded.sub_category
                RETURNING id
            """, (description, expected_amount, frequency, category, sub_category))
            row = cursor.fetchone()
            conn.commit()
            
        self._logger.info("Added recurring transaction: %s ($%.2f %s)", 
                         description, expected_amount, frequency)
        return RecurringTransaction(
            id=row["id"],
            description=description,
            expected_amount=expected_amount,
            frequency=frequency,
            category=category,
            sub_category=sub_category,
            last_occurrence=""
        )

    def get_all_recurring_transactions(self, active_only: bool = True) -> List[RecurringTransaction]:
        """Get all recurring transactions."""
        query = f"""
            SELECT id, description, expected_amount, frequency, category, 
                   sub_category, last_occurrence, is_active
            FROM {self.RECURRING_TABLE}
        """
        if active_only:
            query += " WHERE is_active = 1"
        query += " ORDER BY description"
        
        with self._get_connection() as conn:
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
                is_active=bool(row["is_active"])
            )
            for row in rows
        ]

    def update_recurring_last_occurrence(self, recurring_id: int, 
                                          last_occurrence: str) -> bool:
        """Update the last occurrence date of a recurring transaction."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET last_occurrence = ?
                WHERE id = ?
            """, (last_occurrence, recurring_id))
            conn.commit()
            return cursor.rowcount > 0

    def deactivate_recurring_transaction(self, recurring_id: int) -> bool:
        """Mark a recurring transaction as inactive."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                UPDATE {self.RECURRING_TABLE}
                SET is_active = 0
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()
            return cursor.rowcount > 0

    def delete_recurring_transaction(self, recurring_id: int) -> bool:
        """Delete a recurring transaction."""
        with self._get_connection() as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.RECURRING_TABLE}
                WHERE id = ?
            """, (recurring_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            
        if deleted:
            self._logger.info("Deleted recurring transaction %d", recurring_id)
        return deleted

    def detect_recurring_transactions(self, transactions_df: pd.DataFrame,
                                       min_occurrences: int = 2) -> List[dict]:
        """Detect potential recurring transactions from transaction history.
        
        Args:
            transactions_df: DataFrame with transaction data.
            min_occurrences: Minimum times a transaction must appear.
            
        Returns:
            List of detected recurring transaction patterns.
        """
        if transactions_df.empty:
            return []
            
        # Group by description and amount (rounded to handle small variations)
        df = transactions_df.copy()
        df["amount_rounded"] = df["amount"].round(2)
        
        # Find transactions that appear multiple times
        grouped = df.groupby(["description", "amount_rounded"]).agg({
            "transaction_date": ["count", "min", "max"],
            "category": "first",
            "sub_category": "first"
        }).reset_index()
        
        grouped.columns = ["description", "amount", "count", "first_date", 
                          "last_date", "category", "sub_category"]
        
        # Filter to those appearing at least min_occurrences times
        recurring = grouped[grouped["count"] >= min_occurrences]
        
        detected = []
        for _, row in recurring.iterrows():
            # Estimate frequency based on date range and count
            if pd.notna(row["first_date"]) and pd.notna(row["last_date"]):
                days_span = (row["last_date"] - row["first_date"]).days
                if days_span > 0 and row["count"] > 1:
                    avg_days = days_span / (row["count"] - 1)
                    if avg_days <= 10:
                        frequency = "weekly"
                    elif avg_days <= 45:
                        frequency = "monthly"
                    elif avg_days <= 100:
                        frequency = "quarterly"
                    else:
                        frequency = "yearly"
                else:
                    frequency = "monthly"
            else:
                frequency = "monthly"
                
            detected.append({
                "description": row["description"],
                "amount": float(row["amount"]),
                "frequency": frequency,
                "occurrences": int(row["count"]),
                "category": row["category"] or "",
                "sub_category": row["sub_category"] or "",
                "last_date": str(row["last_date"])[:10] if pd.notna(row["last_date"]) else ""
            })
            
        # Sort by occurrence count descending
        detected.sort(key=lambda x: x["occurrences"], reverse=True)
        
        self._logger.info("Detected %d potential recurring transactions", len(detected))
        return detected


__all__ = [
    "BudgetGoal",
    "Account",
    "RecurringTransaction",
    "BudgetDatabase",
]
