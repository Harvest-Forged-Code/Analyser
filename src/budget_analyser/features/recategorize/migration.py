"""Database migration for category taxonomy redesign.

Renames categories and sub-categories in the transactions and
budget_goals tables to match the new taxonomy:

- Income → Primary_Income
- Unplanned_income → Secondary_Income
- Flexible → Wants
- Luxuries → Luxury
- Medical → Healthcare
- TAX_Payments → Taxes
- Growth → Education
- Restaurants → Dining
- Mistake → Healthcare (Needs)
- Additional_charges → Fees (Needs)
- Trip-Rental → Vacation
- OTP items redistributed by keyword

Usage:
    python -m budget_analyser.features.recategorize.migration
"""

from __future__ import annotations

import logging
import shutil
import sqlite3
from pathlib import Path

from budget_analyser.settings.settings import load_settings

logger = logging.getLogger("budget_analyser.migration")


# ------------------------------------------------------------------
# Category renames (simple 1:1 mappings)
# ------------------------------------------------------------------

CATEGORY_RENAMES = [
    ("UPDATE transactions SET category = 'Primary_Income' "
     "WHERE category = 'Income'"),
    ("UPDATE transactions SET category = 'Secondary_Income' "
     "WHERE category = 'Unplanned_income'"),
    ("UPDATE transactions SET category = 'Wants' "
     "WHERE category = 'Flexible'"),
    ("UPDATE transactions SET category = 'Luxury' "
     "WHERE category = 'Luxuries'"),
]

SUB_CATEGORY_RENAMES = [
    ("UPDATE transactions SET sub_category = 'Healthcare' "
     "WHERE sub_category = 'Medical'"),
    ("UPDATE transactions SET sub_category = 'Taxes' "
     "WHERE sub_category = 'TAX_Payments'"),
    ("UPDATE transactions SET sub_category = 'Education' "
     "WHERE sub_category = 'Growth'"),
    ("UPDATE transactions SET sub_category = 'Dining' "
     "WHERE sub_category = 'Restaurants'"),
]

# Sub-categories that also need their parent category corrected
SUB_CATEGORY_WITH_CATEGORY = [
    ("UPDATE transactions "
     "SET sub_category = 'Healthcare', category = 'Needs' "
     "WHERE sub_category = 'Mistake'"),
    ("UPDATE transactions "
     "SET sub_category = 'Fees', category = 'Needs' "
     "WHERE sub_category = 'Additional_charges'"),
    ("UPDATE transactions "
     "SET sub_category = 'Vacation' "
     "WHERE sub_category = 'Trip-Rental'"),
]

# ------------------------------------------------------------------
# OTP redistribution (keyword-based)
# ------------------------------------------------------------------

OTP_REDISTRIBUTION = [
    ("UPDATE transactions "
     "SET sub_category = 'Government', category = 'Needs' "
     "WHERE sub_category = 'OTP' "
     "AND (description LIKE '%USCIS%' "
     "OR description LIKE '%CA DMV%')"),
    ("UPDATE transactions "
     "SET sub_category = 'Shopping', category = 'Wants' "
     "WHERE sub_category = 'OTP' "
     "AND (description LIKE '%FEDEX%' "
     "OR description LIKE '%PETSMART%' "
     "OR description LIKE '%CRICKET STORE%' "
     "OR description LIKE '%SAREE PALACE%')"),
    ("UPDATE transactions "
     "SET sub_category = 'Taxes', category = 'Needs' "
     "WHERE sub_category = 'OTP' "
     "AND description LIKE '%HRBLOCK%'"),
    ("UPDATE transactions "
     "SET sub_category = 'Dining', category = 'Wants' "
     "WHERE sub_category = 'OTP' "
     "AND description LIKE '%MANCINIS%'"),
    ("UPDATE transactions "
     "SET sub_category = 'Maintenance', category = 'Wants' "
     "WHERE sub_category = 'OTP' "
     "AND description LIKE '%BLOSSOM VALLEY%'"),
    ("UPDATE transactions "
     "SET sub_category = 'Investments', category = 'Wants' "
     "WHERE sub_category = 'OTP' "
     "AND description LIKE '%ROBINHOOD%'"),
    ("UPDATE transactions "
     "SET sub_category = 'Education', category = 'Wants' "
     "WHERE sub_category = 'OTP' "
     "AND description LIKE '%TWO WHEEL SAFETY%'"),
]

# ------------------------------------------------------------------
# Budget goals renames
# ------------------------------------------------------------------

BUDGET_GOALS_RENAMES = [
    ("UPDATE budget_goals SET category = 'Wants' "
     "WHERE category = 'Flexible'"),
    ("UPDATE budget_goals SET category = 'Luxury' "
     "WHERE category = 'Luxuries'"),
]


def _backup_database(db_path: Path) -> Path:
    """Create a timestamped backup of a database file.

    Args:
        db_path: Path to the database file.

    Returns:
        Path to the backup file.
    """
    backup_path = db_path.with_suffix(".db.bak")
    shutil.copy2(db_path, backup_path)
    logger.info("Backed up %s → %s", db_path, backup_path)
    return backup_path


def migrate_transactions(db_path: Path) -> int:
    """Run all transaction table migrations.

    Args:
        db_path: Path to the transactions SQLite database.

    Returns:
        Total number of rows updated across all statements.
    """
    total_updated = 0
    all_statements = (
        CATEGORY_RENAMES
        + SUB_CATEGORY_RENAMES
        + SUB_CATEGORY_WITH_CATEGORY
        + OTP_REDISTRIBUTION
    )

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        for sql in all_statements:
            cursor.execute(sql)
            total_updated += cursor.rowcount
            logger.info(
                "SQL: %s → %d rows", sql[:60], cursor.rowcount,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Transaction migration failed, rolled back")
        raise
    finally:
        conn.close()

    logger.info(
        "Transaction migration complete: %d rows updated",
        total_updated,
    )
    return total_updated


def migrate_budget_goals(db_path: Path) -> int:
    """Run budget_goals table migrations.

    Args:
        db_path: Path to the budget_goals SQLite database.

    Returns:
        Total number of rows updated.
    """
    if not db_path.exists():
        logger.info("Budget goals DB not found, skipping: %s", db_path)
        return 0

    total_updated = 0
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        for sql in BUDGET_GOALS_RENAMES:
            cursor.execute(sql)
            total_updated += cursor.rowcount
            logger.info(
                "SQL: %s → %d rows", sql[:60], cursor.rowcount,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        logger.exception("Budget goals migration failed, rolled back")
        raise
    finally:
        conn.close()

    logger.info(
        "Budget goals migration complete: %d rows updated",
        total_updated,
    )
    return total_updated


def run_migration() -> None:
    """Execute the full taxonomy migration.

    Backs up databases, then runs all rename and redistribution
    SQL statements against the transactions and budget_goals tables.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )

    settings = load_settings()
    txn_db_path = settings.database_path
    budget_db_path = txn_db_path.parent / "budget_goals.db"

    logger.info("Starting category taxonomy migration")

    # Back up databases
    if txn_db_path.exists():
        _backup_database(txn_db_path)
    if budget_db_path.exists():
        _backup_database(budget_db_path)

    # Run migrations
    txn_updated = migrate_transactions(txn_db_path)
    goals_updated = migrate_budget_goals(budget_db_path)

    logger.info(
        "Migration complete: %d transaction rows, "
        "%d budget goal rows updated",
        txn_updated, goals_updated,
    )


if __name__ == "__main__":
    run_migration()
