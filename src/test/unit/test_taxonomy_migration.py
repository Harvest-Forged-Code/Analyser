"""Unit tests for taxonomy migration SQL correctness."""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

import pytest

from budget_analyser.features.recategorize.migration import (
    CATEGORY_RENAMES,
    SUB_CATEGORY_RENAMES,
    SUB_CATEGORY_WITH_CATEGORY,
    OTP_REDISTRIBUTION,
    BUDGET_GOALS_RENAMES,
    migrate_transactions,
    migrate_budget_goals,
)


@pytest.fixture
def txn_db(tmp_path: Path) -> Path:
    """Create a temporary transactions database with old taxonomy."""
    db_path = tmp_path / "budget_analyser.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            from_account TEXT,
            sub_category TEXT DEFAULT '',
            category TEXT DEFAULT '',
            c_or_d TEXT DEFAULT ''
        )
    """)
    conn.executemany(
        "INSERT INTO transactions "
        "(transaction_date, description, amount, from_account, "
        "sub_category, category) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("2024-01-15", "PAYROLL", 5000, "checking",
             "Salary", "Income"),
            ("2024-01-16", "COSTCO", -50, "citi",
             "Groceries", "Needs"),
            ("2024-01-17", "STARBUCKS", -5, "citi",
             "Restaurants", "Luxuries"),
            ("2024-01-18", "UDEMY", -15, "citi",
             "Growth", "Flexible"),
            ("2024-01-19", "CVS", -20, "citi",
             "Medical", "Flexible"),
            ("2024-01-20", "IRS", -500, "checking",
             "TAX_Payments", "Needs"),
            ("2024-01-21", "AIRBNB", -200, "citi",
             "Trip-Rental", "Luxuries"),
            ("2024-01-22", "HARMONY THERAPY", -80, "citi",
             "Mistake", "Luxuries"),
            ("2024-01-23", "NAYAX AIR", -2, "citi",
             "Additional_charges", "Luxuries"),
            ("2024-01-24", "USCIS PHOENIX LOCKBOX", -500, "checking",
             "OTP", "Luxuries"),
            ("2024-01-25", "FEDEX", -15, "citi",
             "OTP", "Luxuries"),
            ("2024-01-26", "HRBLOCK RETAIL", -200, "citi",
             "OTP", "Luxuries"),
            ("2024-01-27", "MANCINIS", -30, "citi",
             "OTP", "Luxuries"),
            ("2024-01-28", "BLOSSOM VALLEY COLLISION", -500, "citi",
             "OTP", "Luxuries"),
            ("2024-01-29", "ROBINHOOD", -100, "checking",
             "OTP", "Luxuries"),
            ("2024-01-30", "TWO WHEEL SAFETY TRAINING", -300, "citi",
             "OTP", "Luxuries"),
            ("2024-02-01", "TEMU.com", 20, "citi",
             "Others_income", "Unplanned_income"),
            ("2024-01-31", "PETSMART # 0070", -25, "citi",
             "OTP", "Luxuries"),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def budget_db(tmp_path: Path) -> Path:
    """Create a temporary budget_goals database with old taxonomy."""
    db_path = tmp_path / "budget_goals.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE budget_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            amount REAL
        )
    """)
    conn.executemany(
        "INSERT INTO budget_goals (category, amount) VALUES (?, ?)",
        [
            ("Flexible", 500.0),
            ("Luxuries", 300.0),
            ("Needs", 1000.0),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


class TestCategoryRenames:
    """Test that top-level category renames work."""

    def test_income_renamed(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT category FROM transactions "
            "WHERE description = 'PAYROLL'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Primary_Income"

    def test_unplanned_income_renamed(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT category FROM transactions "
            "WHERE description = 'TEMU.com'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Secondary_Income"

    def test_flexible_renamed_to_wants(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT category FROM transactions "
            "WHERE description = 'UDEMY'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Wants"

    def test_luxuries_renamed_to_luxury(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT category FROM transactions "
            "WHERE description = 'STARBUCKS'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Luxury"


class TestSubCategoryRenames:
    """Test that sub-category renames work."""

    def test_medical_to_healthcare(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category FROM transactions "
            "WHERE description = 'CVS'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Healthcare"

    def test_tax_payments_to_taxes(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category FROM transactions "
            "WHERE description = 'IRS'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Taxes"

    def test_growth_to_education(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category FROM transactions "
            "WHERE description = 'UDEMY'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Education"

    def test_restaurants_to_dining(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category FROM transactions "
            "WHERE description = 'STARBUCKS'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Dining"


class TestDissolvedSubCategories:
    """Test that dissolved sub-categories are properly handled."""

    def test_mistake_to_healthcare(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'HARMONY THERAPY'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Healthcare"
        assert rows[0][1] == "Needs"

    def test_additional_charges_to_fees(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'NAYAX AIR'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Fees"
        assert rows[0][1] == "Needs"

    def test_trip_rental_to_vacation(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category FROM transactions "
            "WHERE description = 'AIRBNB'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Vacation"


class TestOtpRedistribution:
    """Test that OTP items are redistributed by keyword."""

    def test_uscis_to_government(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'USCIS PHOENIX LOCKBOX'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Government"
        assert rows[0][1] == "Needs"

    def test_fedex_to_shopping(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'FEDEX'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Shopping"
        assert rows[0][1] == "Wants"

    def test_hrblock_to_taxes(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'HRBLOCK RETAIL'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Taxes"
        assert rows[0][1] == "Needs"

    def test_mancinis_to_dining(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'MANCINIS'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Dining"
        assert rows[0][1] == "Wants"

    def test_blossom_valley_to_maintenance(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'BLOSSOM VALLEY COLLISION'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Maintenance"
        assert rows[0][1] == "Wants"

    def test_robinhood_to_investments(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'ROBINHOOD'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Investments"
        assert rows[0][1] == "Wants"

    def test_two_wheel_safety_to_education(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'TWO WHEEL SAFETY TRAINING'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Education"
        assert rows[0][1] == "Wants"

    def test_petsmart_to_shopping(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT sub_category, category FROM transactions "
            "WHERE description = 'PETSMART # 0070'",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Shopping"
        assert rows[0][1] == "Wants"


class TestNoOldNamesRemain:
    """Verify no old taxonomy names remain after migration."""

    def test_no_old_categories(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT DISTINCT category FROM transactions",
        ).fetchall()
        conn.close()
        categories = {r[0] for r in rows}
        old_names = {"Income", "Unplanned_income", "Flexible", "Luxuries"}
        assert not categories & old_names

    def test_no_old_sub_categories(self, txn_db: Path) -> None:
        migrate_transactions(txn_db)
        conn = sqlite3.connect(str(txn_db))
        rows = conn.execute(
            "SELECT DISTINCT sub_category FROM transactions",
        ).fetchall()
        conn.close()
        sub_categories = {r[0] for r in rows}
        old_names = {
            "Medical", "TAX_Payments", "Growth", "Restaurants",
            "Mistake", "Additional_charges", "Trip-Rental", "OTP",
        }
        assert not sub_categories & old_names


class TestBudgetGoalsMigration:
    """Test budget_goals table renames."""

    def test_flexible_to_wants(self, budget_db: Path) -> None:
        migrate_budget_goals(budget_db)
        conn = sqlite3.connect(str(budget_db))
        rows = conn.execute(
            "SELECT category FROM budget_goals WHERE amount = 500.0",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Wants"

    def test_luxuries_to_luxury(self, budget_db: Path) -> None:
        migrate_budget_goals(budget_db)
        conn = sqlite3.connect(str(budget_db))
        rows = conn.execute(
            "SELECT category FROM budget_goals WHERE amount = 300.0",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Luxury"

    def test_needs_unchanged(self, budget_db: Path) -> None:
        migrate_budget_goals(budget_db)
        conn = sqlite3.connect(str(budget_db))
        rows = conn.execute(
            "SELECT category FROM budget_goals WHERE amount = 1000.0",
        ).fetchall()
        conn.close()
        assert rows[0][0] == "Needs"

    def test_nonexistent_db_returns_zero(self, tmp_path: Path) -> None:
        result = migrate_budget_goals(tmp_path / "nonexistent.db")
        assert result == 0


class TestMigrateTransactionsReturnValue:
    """Test that migrate_transactions returns correct update count."""

    def test_returns_total_updated(self, txn_db: Path) -> None:
        total = migrate_transactions(txn_db)
        assert total > 0

    def test_unchanged_rows_not_counted(self, txn_db: Path) -> None:
        # Run migration twice - second time should update fewer
        first = migrate_transactions(txn_db)
        second = migrate_transactions(txn_db)
        assert second == 0
