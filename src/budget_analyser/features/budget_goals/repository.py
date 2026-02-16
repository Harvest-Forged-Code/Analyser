"""Budget goals repository.

Provides database storage for budget goals and earnings goals.
Operates on the shared SQLite database via the core connection factory.
"""

from __future__ import annotations

import logging
from pathlib import Path

from budget_analyser.core.database import get_connection
from budget_analyser.features.budget_goals.models import BudgetGoal, EarningsGoal


class BudgetGoalsRepository:
    """SQLite-backed storage for budget goals and earnings goals."""

    BUDGETS_TABLE = "budget_goals"
    EARNINGS_GOALS_TABLE = "earnings_goals"

    def __init__(
        self,
        db_path: Path,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the budget goals repository.

        Args:
            db_path: Path to the SQLite database file.
            logger: Optional logger for diagnostics.
        """
        self._db_path = db_path
        self._logger = logger or logging.getLogger(
            "budget_analyser.features.budget_goals.repository"
        )
        self._ensure_tables_exist()

    def _ensure_tables_exist(self) -> None:
        """Create budget-related tables if they don't exist."""
        with get_connection(self._db_path) as conn:
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
            conn.commit()
        self._logger.info("Budget goals tables initialized at %s", self._db_path)

    # ==================== Budget Goals ====================

    def set_budget_goal(
        self,
        category: str,
        monthly_limit: float,
        year_month: str = "ALL",
    ) -> BudgetGoal:
        """Set or update a budget goal for a category.

        Args:
            category: The expense category name.
            monthly_limit: The monthly spending limit.
            year_month: Specific month "YYYY-MM" or "ALL" for default.

        Returns:
            The created or updated BudgetGoal.

        Raises:
            RuntimeError: If the database insert fails.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.BUDGETS_TABLE}
                    (category, monthly_limit, year_month, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(category, year_month) DO UPDATE SET
                    monthly_limit = excluded.monthly_limit,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (category, monthly_limit, year_month))
            row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError(
                f"Failed to set budget goal for category: {category}"
            )

        self._logger.info(
            "Set budget goal: %s = $%.2f (%s)",
            category, monthly_limit, year_month,
        )
        return BudgetGoal(
            id=row["id"],
            category=category,
            monthly_limit=monthly_limit,
            year_month=year_month,
        )

    def get_budget_goal(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> BudgetGoal | None:
        """Get budget goal for a category.

        First checks for month-specific goal, then falls back to "ALL".

        Args:
            category: The expense category name.
            year_month: Specific month "YYYY-MM" or "ALL".

        Returns:
            BudgetGoal if found, None otherwise.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                SELECT id, category, monthly_limit, year_month
                FROM {self.BUDGETS_TABLE}
                WHERE category = ? AND year_month = ?
            """, (category, year_month))
            row = cursor.fetchone()

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
            year_month=row["year_month"],
        )

    def get_all_budget_goals(self) -> list[BudgetGoal]:
        """Get all budget goals.

        Returns:
            List of all BudgetGoal entries ordered by category.
        """
        with get_connection(self._db_path) as conn:
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
                year_month=row["year_month"],
            )
            for row in rows
        ]

    def delete_budget_goal(
        self,
        category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete a budget goal.

        Args:
            category: The expense category name.
            year_month: Specific month or "ALL".

        Returns:
            True if a goal was deleted.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.BUDGETS_TABLE}
                WHERE category = ? AND year_month = ?
            """, (category, year_month))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info(
                "Deleted budget goal: %s (%s)", category, year_month,
            )
        return deleted

    def set_budget_goals_for_year(
        self,
        category: str,
        monthly_limit: float,
        year: int,
    ) -> list[BudgetGoal]:
        """Create/update budget goals for all 12 months of a year.

        Args:
            category: The expense category name.
            monthly_limit: The monthly spending limit.
            year: The year to set goals for (e.g., 2025).

        Returns:
            List of 12 BudgetGoal objects, one for each month.
        """
        goals = []
        for month in range(1, 13):
            year_month = f"{year}-{month:02d}"
            goal = self.set_budget_goal(category, monthly_limit, year_month)
            goals.append(goal)

        self._logger.info(
            "Set budget goals for year %d: %s = $%.2f/month (12 entries)",
            year, category, monthly_limit,
        )
        return goals

    # ==================== Earnings Goals ====================

    def set_earnings_goal(
        self,
        sub_category: str,
        expected_amount: float,
        year_month: str = "ALL",
    ) -> EarningsGoal:
        """Set or update an earnings goal for a sub-category.

        Args:
            sub_category: The earnings sub-category name.
            expected_amount: The expected monthly earnings amount.
            year_month: Specific month "YYYY-MM" or "ALL" for default.

        Returns:
            The created or updated EarningsGoal.

        Raises:
            RuntimeError: If the database insert fails.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                INSERT INTO {self.EARNINGS_GOALS_TABLE}
                    (sub_category, expected_amount, year_month, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(sub_category, year_month) DO UPDATE SET
                    expected_amount = excluded.expected_amount,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (sub_category, expected_amount, year_month))
            row = cursor.fetchone()
            conn.commit()

        if row is None:
            raise RuntimeError(
                f"Failed to set earnings goal for: {sub_category}"
            )

        self._logger.info(
            "Set earnings goal: %s = $%.2f (%s)",
            sub_category, expected_amount, year_month,
        )
        return EarningsGoal(
            id=row["id"],
            sub_category=sub_category,
            expected_amount=expected_amount,
            year_month=year_month,
        )

    def get_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> EarningsGoal | None:
        """Get earnings goal for a sub-category.

        First checks for month-specific goal, then falls back to "ALL".

        Args:
            sub_category: The earnings sub-category name.
            year_month: Specific month "YYYY-MM" or "ALL".

        Returns:
            EarningsGoal if found, None otherwise.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                SELECT id, sub_category, expected_amount, year_month
                FROM {self.EARNINGS_GOALS_TABLE}
                WHERE sub_category = ? AND year_month = ?
            """, (sub_category, year_month))
            row = cursor.fetchone()

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
            year_month=row["year_month"],
        )

    def get_all_earnings_goals(self) -> list[EarningsGoal]:
        """Get all earnings goals.

        Returns:
            List of all EarningsGoal entries ordered by sub_category.
        """
        with get_connection(self._db_path) as conn:
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
                year_month=row["year_month"],
            )
            for row in rows
        ]

    def delete_earnings_goal(
        self,
        sub_category: str,
        year_month: str = "ALL",
    ) -> bool:
        """Delete an earnings goal.

        Args:
            sub_category: The earnings sub-category name.
            year_month: Specific month or "ALL".

        Returns:
            True if a goal was deleted.
        """
        with get_connection(self._db_path) as conn:
            cursor = conn.execute(f"""
                DELETE FROM {self.EARNINGS_GOALS_TABLE}
                WHERE sub_category = ? AND year_month = ?
            """, (sub_category, year_month))
            conn.commit()
            deleted = cursor.rowcount > 0

        if deleted:
            self._logger.info(
                "Deleted earnings goal: %s (%s)",
                sub_category, year_month,
            )
        return deleted

    def set_earnings_goals_for_year(
        self,
        sub_category: str,
        expected_amount: float,
        year: int,
    ) -> list[EarningsGoal]:
        """Create/update earnings goals for all 12 months of a year.

        Args:
            sub_category: The earnings sub-category name.
            expected_amount: The expected monthly earnings amount.
            year: The year to set goals for (e.g., 2025).

        Returns:
            List of 12 EarningsGoal objects, one for each month.
        """
        goals = []
        for month in range(1, 13):
            year_month = f"{year}-{month:02d}"
            goal = self.set_earnings_goal(
                sub_category, expected_amount, year_month,
            )
            goals.append(goal)

        self._logger.info(
            "Set earnings goals for year %d: %s = $%.2f/month (12 entries)",
            year, sub_category, expected_amount,
        )
        return goals
