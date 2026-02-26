# MCP SQLite Server — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Python MCP server in `mcp/` that exposes both Budget Analyser
SQLite databases (`budget_analyser.db` and `budget_goals.db`) to Claude via
read/write tools and pre-canned resources.

**Architecture:** A standalone Python package at `mcp/budget_analyser_mcp/`
using the `mcp` SDK (FastMCP). DB paths are resolved from env vars with a
fallback to the repo-relative defaults. Tools and resource logic live in
separate modules (`tools.py`, `resources.py`) so they are easily unit-testable
without going through the MCP protocol layer.

**Tech Stack:** Python 3.10+, `mcp[cli]>=1.0.0`, stdlib `sqlite3`, `pytest`,
`uv`

---

## Task 1: Scaffold the `mcp/` package

**Files:**
- Create: `mcp/pyproject.toml`
- Create: `mcp/budget_analyser_mcp/__init__.py`
- Create: `mcp/budget_analyser_mcp/__main__.py`

**Step 1: Create the directory tree**

```bash
mkdir -p mcp/budget_analyser_mcp
```

**Step 2: Create `mcp/pyproject.toml`**

```toml
[project]
name = "budget-analyser-mcp"
version = "0.1.0"
description = "MCP server for Budget Analyser SQLite databases"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["budget_analyser_mcp"]
```

**Step 3: Create `mcp/budget_analyser_mcp/__init__.py`**

```python
"""Budget Analyser MCP server package."""
```

**Step 4: Create `mcp/budget_analyser_mcp/__main__.py`**

```python
"""Entry point: python -m budget_analyser_mcp"""
from __future__ import annotations

from budget_analyser_mcp.server import mcp

mcp.run()
```

**Step 5: Install dependencies**

```bash
cd mcp && uv sync
```

Expected: lock file created, `mcp` package installed.

**Step 6: Commit**

```bash
git add mcp/
git commit -S -m "chore(mcp): scaffold mcp package structure"
```

---

## Task 2: DB path resolution module

**Files:**
- Create: `mcp/budget_analyser_mcp/db.py`
- Test: `src/test/unit/test_mcp_db.py`

### Step 1: Write the failing test

Create `src/test/unit/test_mcp_db.py`:

```python
"""Tests for MCP DB path resolution."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest


def test_get_db_path_transactions_default():
    """Default transactions path resolves to budget_analyser.db."""
    # Remove env var if set
    os.environ.pop("BUDGET_ANALYSER_DB", None)
    from budget_analyser_mcp.db import get_db_path
    path = get_db_path("transactions")
    assert path.name == "budget_analyser.db"


def test_get_db_path_goals_default():
    """Default goals path resolves to budget_goals.db."""
    os.environ.pop("BUDGET_ANALYSER_GOALS_DB", None)
    from budget_analyser_mcp.db import get_db_path
    path = get_db_path("goals")
    assert path.name == "budget_goals.db"


def test_get_db_path_env_override(monkeypatch, tmp_path):
    """Env var overrides the default DB path."""
    custom = tmp_path / "custom.db"
    monkeypatch.setenv("BUDGET_ANALYSER_DB", str(custom))
    from importlib import reload
    import budget_analyser_mcp.db as db_module
    reload(db_module)
    path = db_module.get_db_path("transactions")
    assert path == custom


def test_get_db_path_unknown_db():
    """Unknown db name raises ValueError."""
    from budget_analyser_mcp.db import get_db_path
    with pytest.raises(ValueError, match="Unknown db"):
        get_db_path("nonexistent")


def test_get_connection_file_not_found(monkeypatch, tmp_path):
    """get_connection raises FileNotFoundError for missing DB."""
    missing = tmp_path / "missing.db"
    monkeypatch.setenv("BUDGET_ANALYSER_DB", str(missing))
    from importlib import reload
    import budget_analyser_mcp.db as db_module
    reload(db_module)
    with pytest.raises(FileNotFoundError, match="Database not found"):
        db_module.get_connection("transactions")
```

### Step 2: Run test — verify it fails

```bash
cd /path/to/repo
uv run pytest src/test/unit/test_mcp_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'budget_analyser_mcp'`

> Note: The test file imports from `budget_analyser_mcp`. Since `mcp/` is a
> separate package, add `mcp/` to `PYTHONPATH` when running these tests:
> `PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_db.py -v`

### Step 3: Create `mcp/budget_analyser_mcp/db.py`

```python
"""Database path resolution and connection utilities."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# Repo root: mcp/budget_analyser_mcp/db.py -> mcp/budget_analyser_mcp/ -> mcp/ -> repo root
_REPO_ROOT = Path(__file__).parent.parent.parent

_DB_DEFAULTS: dict[str, Path] = {
    "transactions": _REPO_ROOT / "src/budget_analyser/data/budget_analyser.db",
    "goals": _REPO_ROOT / "src/budget_analyser/data/budget_goals.db",
}

_DB_ENV_KEYS: dict[str, str] = {
    "transactions": "BUDGET_ANALYSER_DB",
    "goals": "BUDGET_ANALYSER_GOALS_DB",
}


def get_db_path(db: str) -> Path:
    """Resolve the filesystem path for the named database.

    Args:
        db: Database alias. One of 'transactions' or 'goals'.

    Returns:
        Path to the SQLite file.

    Raises:
        ValueError: If db is not a known alias.
    """
    if db not in _DB_DEFAULTS:
        valid = ", ".join(f"'{k}'" for k in _DB_DEFAULTS)
        raise ValueError(f"Unknown db '{db}'. Valid options: {valid}")

    env_key = _DB_ENV_KEYS[db]
    env_val = os.environ.get(env_key)
    return Path(env_val) if env_val else _DB_DEFAULTS[db]


def get_connection(db: str) -> sqlite3.Connection:
    """Open a sqlite3 connection for the named database.

    Args:
        db: Database alias. One of 'transactions' or 'goals'.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.

    Raises:
        ValueError: If db is not a known alias.
        FileNotFoundError: If the database file does not exist.
    """
    path = get_db_path(db)
    if not path.exists():
        raise FileNotFoundError(
            f"Database not found at {path}. "
            f"Set {_DB_ENV_KEYS[db]} to override the path."
        )
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn
```

### Step 4: Run tests — verify they pass

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_db.py -v
```

Expected: all 5 tests PASS.

### Step 5: Commit

```bash
git add mcp/budget_analyser_mcp/db.py src/test/unit/test_mcp_db.py
git commit -S -m "feat(mcp): add DB path resolution module with tests"
```

---

## Task 3: `query` and `execute` tools

**Files:**
- Create: `mcp/budget_analyser_mcp/tools.py`
- Test: `src/test/unit/test_mcp_tools.py`

### Step 1: Write the failing tests

Create `src/test/unit/test_mcp_tools.py`:

```python
"""Tests for MCP query and execute tools."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def transactions_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp transactions DB with one row."""
    db_path = tmp_path / "transactions.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            from_account TEXT,
            sub_category TEXT,
            category TEXT,
            c_or_d TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "INSERT INTO transactions (transaction_date, description, amount, "
        "from_account, sub_category, category, c_or_d) VALUES (?,?,?,?,?,?,?)",
        ("2026-01-15", "Grocery Store", -82.50, "chase", "Groceries", "Needs", "expenditures"),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("BUDGET_ANALYSER_DB", str(db_path))
    return db_path


@pytest.fixture()
def goals_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temp goals DB with one budget_goal row."""
    db_path = tmp_path / "goals.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE budget_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            year_month TEXT NOT NULL DEFAULT 'ALL'
        )
    """)
    conn.execute(
        "INSERT INTO budget_goals (category, monthly_limit, year_month) VALUES (?,?,?)",
        ("Needs", 1500.0, "ALL"),
    )
    conn.commit()
    conn.close()
    monkeypatch.setenv("BUDGET_ANALYSER_GOALS_DB", str(db_path))
    return db_path


# --- query tool ---

def test_query_returns_rows(transactions_db):
    """query returns JSON array of matching rows."""
    from budget_analyser_mcp.tools import query
    result = query(sql="SELECT description, amount FROM transactions", db="transactions")
    rows = json.loads(result)
    assert len(rows) == 1
    assert rows[0]["description"] == "Grocery Store"
    assert rows[0]["amount"] == pytest.approx(-82.50)


def test_query_goals_db(goals_db):
    """query works against the goals database."""
    from budget_analyser_mcp.tools import query
    result = query(sql="SELECT category, monthly_limit FROM budget_goals", db="goals")
    rows = json.loads(result)
    assert rows[0]["category"] == "Needs"


def test_query_bad_sql_returns_error(transactions_db):
    """query returns error JSON on bad SQL, does not raise."""
    from budget_analyser_mcp.tools import query
    result = query(sql="SELECT * FROM nonexistent_table", db="transactions")
    data = json.loads(result)
    assert "error" in data


def test_query_unknown_db():
    """query returns error JSON for unknown db name."""
    from budget_analyser_mcp.tools import query
    result = query(sql="SELECT 1", db="unknown")
    data = json.loads(result)
    assert "error" in data


# --- execute tool ---

def test_execute_insert(transactions_db):
    """execute inserts a row and returns rows_affected."""
    from budget_analyser_mcp.tools import execute
    result = execute(
        sql="INSERT INTO transactions (transaction_date, description, amount, "
            "from_account) VALUES ('2026-02-01', 'Coffee', -4.50, 'bilt')",
        db="transactions",
    )
    data = json.loads(result)
    assert data["rows_affected"] == 1
    assert data["last_insert_id"] == 2


def test_execute_update(transactions_db):
    """execute updates rows and returns correct rows_affected."""
    from budget_analyser_mcp.tools import execute
    result = execute(
        sql="UPDATE transactions SET category='Wants' WHERE description='Grocery Store'",
        db="transactions",
    )
    data = json.loads(result)
    assert data["rows_affected"] == 1


def test_execute_delete(transactions_db):
    """execute deletes rows correctly."""
    from budget_analyser_mcp.tools import execute
    result = execute(
        sql="DELETE FROM transactions WHERE description='Grocery Store'",
        db="transactions",
    )
    data = json.loads(result)
    assert data["rows_affected"] == 1


def test_execute_blocks_drop_table(transactions_db):
    """execute rejects DROP TABLE with an error message."""
    from budget_analyser_mcp.tools import execute
    result = execute(sql="DROP TABLE transactions", db="transactions")
    data = json.loads(result)
    assert "error" in data
    assert "blocked" in data["error"].lower()


def test_execute_blocks_drop_database(transactions_db):
    """execute rejects DROP DATABASE."""
    from budget_analyser_mcp.tools import execute
    result = execute(sql="DROP DATABASE budget_analyser", db="transactions")
    data = json.loads(result)
    assert "error" in data


def test_execute_bad_sql_returns_error(transactions_db):
    """execute returns error JSON on invalid SQL, does not raise."""
    from budget_analyser_mcp.tools import execute
    result = execute(sql="THIS IS NOT SQL", db="transactions")
    data = json.loads(result)
    assert "error" in data
```

### Step 2: Run tests — verify they fail

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_tools.py -v
```

Expected: `ImportError: cannot import name 'query' from 'budget_analyser_mcp.tools'`

### Step 3: Create `mcp/budget_analyser_mcp/tools.py`

```python
"""MCP tools: query and execute."""
from __future__ import annotations

import json
import sqlite3

from .db import get_connection

_BLOCKED_STATEMENTS = ("DROP TABLE", "DROP DATABASE")


def query(*, sql: str, db: str = "transactions") -> str:
    """Run a SELECT query and return results as a JSON array.

    Args:
        sql: A SQL SELECT statement.
        db: Database alias ('transactions' or 'goals').

    Returns:
        JSON string — array of row dicts, or {"error": "..."} on failure.
    """
    try:
        conn = get_connection(db)
    except (ValueError, FileNotFoundError) as exc:
        return json.dumps({"error": str(exc)})

    try:
        cursor = conn.execute(sql)
        rows = [dict(row) for row in cursor.fetchall()]
        return json.dumps(rows, default=str)
    except sqlite3.Error as exc:
        return json.dumps({"error": str(exc)})
    finally:
        conn.close()


def execute(*, sql: str, db: str = "transactions") -> str:
    """Run an INSERT, UPDATE, DELETE, or ALTER statement.

    DROP TABLE and DROP DATABASE are blocked.

    Args:
        sql: A SQL DML statement.
        db: Database alias ('transactions' or 'goals').

    Returns:
        JSON string — {"rows_affected": int, "last_insert_id": int}
        or {"error": "..."} on failure.
    """
    sql_upper = sql.upper().strip()
    for blocked in _BLOCKED_STATEMENTS:
        if blocked in sql_upper:
            return json.dumps({
                "error": (
                    f"Statement blocked: '{blocked}' is not permitted. "
                    "Only INSERT, UPDATE, DELETE, and ALTER are allowed."
                )
            })

    try:
        conn = get_connection(db)
    except (ValueError, FileNotFoundError) as exc:
        return json.dumps({"error": str(exc)})

    try:
        with conn:
            cursor = conn.execute(sql)
            return json.dumps({
                "rows_affected": cursor.rowcount,
                "last_insert_id": cursor.lastrowid,
            })
    except sqlite3.Error as exc:
        return json.dumps({"error": str(exc)})
    finally:
        conn.close()
```

> **Note:** The MCP tool decorator does not support keyword-only args.
> `server.py` will call `tools.query(sql=sql, db=db)` explicitly.

### Step 4: Run tests — verify they pass

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_tools.py -v
```

Expected: all 11 tests PASS.

### Step 5: Commit

```bash
git add mcp/budget_analyser_mcp/tools.py src/test/unit/test_mcp_tools.py
git commit -S -m "feat(mcp): add query and execute tools with tests"
```

---

## Task 4: Resources module

**Files:**
- Create: `mcp/budget_analyser_mcp/resources.py`
- Test: `src/test/unit/test_mcp_resources.py`

### Step 1: Write the failing tests

Create `src/test/unit/test_mcp_resources.py`:

```python
"""Tests for MCP resources."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest


@pytest.fixture()
def both_dbs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Create both temp DBs with minimal schema and data."""
    # Transactions DB
    t_path = tmp_path / "transactions.db"
    tc = sqlite3.connect(str(t_path))
    tc.execute("""
        CREATE TABLE transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date TEXT, description TEXT, amount REAL,
            from_account TEXT, sub_category TEXT, category TEXT, c_or_d TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    tc.execute(
        "INSERT INTO transactions VALUES (1,'2026-01-15','Coffee',-4.5,'chase',"
        "'Coffee','Needs','expenditures',CURRENT_TIMESTAMP)"
    )
    tc.execute(
        "INSERT INTO transactions VALUES (2,'2026-01-16','Salary',5000.0,'bilt',"
        "'Salary','Primary_Income','earnings',CURRENT_TIMESTAMP)"
    )
    tc.commit()
    tc.close()

    # Goals DB
    g_path = tmp_path / "goals.db"
    gc = sqlite3.connect(str(g_path))
    gc.execute(
        "CREATE TABLE budget_goals (id INTEGER PRIMARY KEY, category TEXT, "
        "monthly_limit REAL, year_month TEXT DEFAULT 'ALL')"
    )
    gc.execute(
        "CREATE TABLE earnings_goals (id INTEGER PRIMARY KEY, sub_category TEXT, "
        "expected_amount REAL, year_month TEXT DEFAULT 'ALL')"
    )
    gc.execute(
        "CREATE TABLE accounts (id INTEGER PRIMARY KEY, name TEXT, account_type TEXT, "
        "balance REAL DEFAULT 0, last_updated TEXT, notes TEXT DEFAULT '')"
    )
    gc.execute(
        "CREATE TABLE recurring_transactions (id INTEGER PRIMARY KEY, description TEXT, "
        "expected_amount REAL, frequency TEXT DEFAULT 'monthly', is_active INTEGER DEFAULT 1)"
    )
    gc.execute(
        "CREATE TABLE upload_history (id INTEGER PRIMARY KEY, file_name TEXT, "
        "bank_name TEXT, account_type TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "transactions_inserted INTEGER DEFAULT 0, duplicates_skipped INTEGER DEFAULT 0)"
    )
    gc.execute("INSERT INTO budget_goals VALUES (1,'Needs',1500.0,'ALL')")
    gc.execute("INSERT INTO earnings_goals VALUES (1,'Salary',5000.0,'ALL')")
    gc.execute("INSERT INTO accounts VALUES (1,'Chase Checking','checking',2500.0,'2026-02-01','')")
    gc.execute("INSERT INTO recurring_transactions VALUES (1,'Netflix',15.99,'monthly',1)")
    gc.execute("INSERT INTO upload_history VALUES (1,'jan.csv','chase','checking',CURRENT_TIMESTAMP,10,0)")
    gc.commit()
    gc.close()

    monkeypatch.setenv("BUDGET_ANALYSER_DB", str(t_path))
    monkeypatch.setenv("BUDGET_ANALYSER_GOALS_DB", str(g_path))
    return {"transactions": t_path, "goals": g_path}


def test_get_overview_contains_both_dbs(both_dbs):
    """Overview includes both 'transactions' and 'goals' keys."""
    from budget_analyser_mcp.resources import get_overview
    result = json.loads(get_overview())
    assert "transactions" in result
    assert "goals" in result
    assert result["transactions"]["transactions"] == 2


def test_get_schema_transactions(both_dbs):
    """Schema for transactions db contains CREATE TABLE."""
    from budget_analyser_mcp.resources import get_schema
    result = get_schema("transactions")
    assert "CREATE TABLE" in result.upper()
    assert "transactions" in result


def test_get_schema_goals(both_dbs):
    """Schema for goals db contains all 5 table names."""
    from budget_analyser_mcp.resources import get_schema
    result = get_schema("goals")
    for table in ("budget_goals", "earnings_goals", "accounts",
                  "recurring_transactions", "upload_history"):
        assert table in result


def test_get_sample_transactions(both_dbs):
    """Sample returns a list with at most 10 items."""
    from budget_analyser_mcp.resources import get_sample_transactions
    rows = json.loads(get_sample_transactions())
    assert isinstance(rows, list)
    assert len(rows) <= 10
    assert rows[0]["description"] in ("Coffee", "Salary")


def test_get_distinct_accounts(both_dbs):
    """Distinct accounts returns a list of account strings."""
    from budget_analyser_mcp.resources import get_distinct_accounts
    accounts = json.loads(get_distinct_accounts())
    assert "chase" in accounts
    assert "bilt" in accounts


def test_get_distinct_categories(both_dbs):
    """Distinct categories returns list of dicts with category key."""
    from budget_analyser_mcp.resources import get_distinct_categories
    cats = json.loads(get_distinct_categories())
    assert any(c["category"] == "Needs" for c in cats)


def test_get_budget_goals(both_dbs):
    """Budget goals returns list with the seeded row."""
    from budget_analyser_mcp.resources import get_budget_goals
    rows = json.loads(get_budget_goals())
    assert rows[0]["category"] == "Needs"
    assert rows[0]["monthly_limit"] == pytest.approx(1500.0)


def test_get_earnings_goals(both_dbs):
    """Earnings goals returns the seeded row."""
    from budget_analyser_mcp.resources import get_earnings_goals
    rows = json.loads(get_earnings_goals())
    assert rows[0]["sub_category"] == "Salary"


def test_get_accounts(both_dbs):
    """Net worth accounts returns the seeded row."""
    from budget_analyser_mcp.resources import get_accounts
    rows = json.loads(get_accounts())
    assert rows[0]["name"] == "Chase Checking"


def test_get_recurring(both_dbs):
    """Recurring transactions returns only active rows."""
    from budget_analyser_mcp.resources import get_recurring
    rows = json.loads(get_recurring())
    assert rows[0]["description"] == "Netflix"


def test_get_upload_history(both_dbs):
    """Upload history returns the seeded row."""
    from budget_analyser_mcp.resources import get_upload_history
    rows = json.loads(get_upload_history())
    assert rows[0]["file_name"] == "jan.csv"
```

### Step 2: Run tests — verify they fail

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_resources.py -v
```

Expected: `ImportError`

### Step 3: Create `mcp/budget_analyser_mcp/resources.py`

```python
"""MCP resource handlers — all return JSON strings."""
from __future__ import annotations

import json
import sqlite3

from .db import get_connection


def get_overview() -> str:
    """Return both DBs, all tables, and row counts as JSON.

    Returns:
        JSON object mapping db alias -> {table_name: row_count}.
    """
    result: dict[str, dict[str, int] | dict[str, str]] = {}
    for db in ("transactions", "goals"):
        try:
            conn = get_connection(db)
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [
                row[0] for row in cursor.fetchall()
                if not row[0].startswith("sqlite_")
            ]
            table_counts: dict[str, int] = {}
            for table in tables:
                count_row = conn.execute(
                    f"SELECT COUNT(*) FROM {table}"  # noqa: S608
                ).fetchone()
                table_counts[table] = count_row[0] if count_row else 0
            conn.close()
            result[db] = table_counts
        except Exception as exc:  # pylint: disable=broad-except
            result[db] = {"error": str(exc)}
    return json.dumps(result, indent=2)


def get_schema(db: str) -> str:
    """Return CREATE TABLE DDL for every table in the database.

    Args:
        db: Database alias ('transactions' or 'goals').

    Returns:
        Concatenated DDL strings separated by blank lines.
    """
    conn = get_connection(db)
    try:
        cursor = conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND sql IS NOT NULL "
            "ORDER BY name"
        )
        return "\n\n".join(row[0] for row in cursor.fetchall())
    finally:
        conn.close()


def get_sample_transactions() -> str:
    """Return the 10 most recent transactions as JSON.

    Returns:
        JSON array of transaction dicts.
    """
    conn = get_connection("transactions")
    try:
        cursor = conn.execute(
            "SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 10"
        )
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()


def get_distinct_accounts() -> str:
    """Return distinct from_account values as a JSON array.

    Returns:
        JSON array of account name strings.
    """
    conn = get_connection("transactions")
    try:
        cursor = conn.execute(
            "SELECT DISTINCT from_account FROM transactions ORDER BY from_account"
        )
        return json.dumps([row[0] for row in cursor.fetchall()])
    finally:
        conn.close()


def get_distinct_categories() -> str:
    """Return distinct category + sub_category pairs as JSON.

    Returns:
        JSON array of {"category": str, "sub_category": str} dicts.
    """
    conn = get_connection("transactions")
    try:
        cursor = conn.execute(
            "SELECT DISTINCT category, sub_category "
            "FROM transactions ORDER BY category, sub_category"
        )
        return json.dumps(
            [{"category": row[0], "sub_category": row[1]} for row in cursor.fetchall()],
            indent=2,
        )
    finally:
        conn.close()


def get_budget_goals() -> str:
    """Return all budget_goals rows as JSON."""
    conn = get_connection("goals")
    try:
        cursor = conn.execute("SELECT * FROM budget_goals ORDER BY category")
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()


def get_earnings_goals() -> str:
    """Return all earnings_goals rows as JSON."""
    conn = get_connection("goals")
    try:
        cursor = conn.execute("SELECT * FROM earnings_goals ORDER BY sub_category")
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()


def get_accounts() -> str:
    """Return all net worth accounts as JSON."""
    conn = get_connection("goals")
    try:
        cursor = conn.execute("SELECT * FROM accounts ORDER BY name")
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()


def get_recurring() -> str:
    """Return active recurring_transactions as JSON."""
    conn = get_connection("goals")
    try:
        cursor = conn.execute(
            "SELECT * FROM recurring_transactions "
            "WHERE is_active = 1 ORDER BY description"
        )
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()


def get_upload_history() -> str:
    """Return the 20 most recent upload_history rows as JSON."""
    conn = get_connection("goals")
    try:
        cursor = conn.execute(
            "SELECT * FROM upload_history ORDER BY uploaded_at DESC LIMIT 20"
        )
        return json.dumps([dict(row) for row in cursor.fetchall()], default=str, indent=2)
    finally:
        conn.close()
```

### Step 4: Run tests — verify they pass

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_resources.py -v
```

Expected: all 11 tests PASS.

### Step 5: Commit

```bash
git add mcp/budget_analyser_mcp/resources.py src/test/unit/test_mcp_resources.py
git commit -S -m "feat(mcp): add resources module with tests"
```

---

## Task 5: Wire the MCP server

**Files:**
- Create: `mcp/budget_analyser_mcp/server.py`

No separate tests — the tools and resources are already tested. This is pure
wiring.

### Step 1: Create `mcp/budget_analyser_mcp/server.py`

```python
"""Budget Analyser MCP server — wires tools and resources into FastMCP."""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import resources as r
from . import tools as t

mcp = FastMCP("budget-analyser")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def query(sql: str, db: str = "transactions") -> str:
    """Run a SELECT query against the specified database.

    Args:
        sql: A SQL SELECT statement.
        db: Database to query — 'transactions' (budget_analyser.db)
            or 'goals' (budget_goals.db). Defaults to 'transactions'.

    Returns:
        JSON array of row dicts, or {"error": "..."} on failure.
    """
    return t.query(sql=sql, db=db)


@mcp.tool()
def execute(sql: str, db: str = "transactions") -> str:
    """Run an INSERT, UPDATE, DELETE, or ALTER statement.

    DROP TABLE and DROP DATABASE are blocked for safety.

    Args:
        sql: A SQL DML statement.
        db: Database to modify — 'transactions' or 'goals'.
            Defaults to 'transactions'.

    Returns:
        JSON with rows_affected and last_insert_id, or {"error": "..."}.
    """
    return t.execute(sql=sql, db=db)


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@mcp.resource("budget-analyser://overview")
def overview() -> str:
    """Overview of all databases: table names and row counts."""
    return r.get_overview()


@mcp.resource("budget-analyser://transactions/schema")
def transactions_schema() -> str:
    """DDL schema for budget_analyser.db (transactions table)."""
    return r.get_schema("transactions")


@mcp.resource("budget-analyser://transactions/sample")
def transactions_sample() -> str:
    """10 most recent transactions."""
    return r.get_sample_transactions()


@mcp.resource("budget-analyser://transactions/accounts")
def transactions_accounts() -> str:
    """Distinct from_account values in the transactions database."""
    return r.get_distinct_accounts()


@mcp.resource("budget-analyser://transactions/categories")
def transactions_categories() -> str:
    """Distinct category and sub_category combinations."""
    return r.get_distinct_categories()


@mcp.resource("budget-analyser://goals/schema")
def goals_schema() -> str:
    """DDL schema for budget_goals.db (all 5 tables)."""
    return r.get_schema("goals")


@mcp.resource("budget-analyser://goals/budget-goals")
def goals_budget_goals() -> str:
    """All budget goal rows."""
    return r.get_budget_goals()


@mcp.resource("budget-analyser://goals/earnings-goals")
def goals_earnings_goals() -> str:
    """All earnings goal rows."""
    return r.get_earnings_goals()


@mcp.resource("budget-analyser://goals/accounts")
def goals_accounts() -> str:
    """All net worth account rows."""
    return r.get_accounts()


@mcp.resource("budget-analyser://goals/recurring")
def goals_recurring() -> str:
    """Active recurring transactions."""
    return r.get_recurring()


@mcp.resource("budget-analyser://goals/upload-history")
def goals_upload_history() -> str:
    """Recent upload history (last 20 entries)."""
    return r.get_upload_history()
```

### Step 2: Smoke test — verify the server starts

```bash
cd mcp && uv run python -m budget_analyser_mcp &
sleep 2 && kill %1
```

Expected: server starts without error (you'll see it wait for stdin — that's correct stdio transport behaviour).

### Step 3: Commit

```bash
git add mcp/budget_analyser_mcp/server.py
git commit -S -m "feat(mcp): wire FastMCP server with all tools and resources"
```

---

## Task 6: README and Claude Code integration

**Files:**
- Create: `mcp/README.md`
- Modify: `.claude/settings.json`

### Step 1: Create `mcp/README.md`

````markdown
# Budget Analyser MCP Server

MCP server exposing both Budget Analyser SQLite databases to Claude.

## Databases

| Alias | File | Tables |
|-------|------|--------|
| `transactions` | `src/budget_analyser/data/budget_analyser.db` | `transactions` |
| `goals` | `src/budget_analyser/data/budget_goals.db` | `budget_goals`, `earnings_goals`, `accounts`, `recurring_transactions`, `upload_history` |

## Tools

- **`query(sql, db)`** — Run any SELECT. `db` defaults to `"transactions"`.
- **`execute(sql, db)`** — Run INSERT/UPDATE/DELETE/ALTER. DROP blocked.

## Resources

| URI | Content |
|-----|---------|
| `budget-analyser://overview` | Row counts for all tables in both DBs |
| `budget-analyser://transactions/schema` | DDL for budget_analyser.db |
| `budget-analyser://transactions/sample` | 10 most recent transactions |
| `budget-analyser://transactions/accounts` | Distinct account names |
| `budget-analyser://transactions/categories` | Distinct category pairs |
| `budget-analyser://goals/schema` | DDL for budget_goals.db |
| `budget-analyser://goals/budget-goals` | Budget limits |
| `budget-analyser://goals/earnings-goals` | Earnings targets |
| `budget-analyser://goals/accounts` | Net worth accounts |
| `budget-analyser://goals/recurring` | Active recurring transactions |
| `budget-analyser://goals/upload-history` | Last 20 uploads |

## Setup

```bash
cd mcp && uv sync
```

## Claude Code Integration

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "budget-analyser": {
      "command": "uv",
      "args": ["run", "python", "-m", "budget_analyser_mcp"],
      "cwd": "/absolute/path/to/repo/mcp"
    }
  }
}
```

## Environment Variable Overrides

| Variable | Default |
|----------|---------|
| `BUDGET_ANALYSER_DB` | `src/budget_analyser/data/budget_analyser.db` |
| `BUDGET_ANALYSER_GOALS_DB` | `src/budget_analyser/data/budget_goals.db` |
````

### Step 2: Add MCP server to `.claude/settings.json`

The existing file is:
```json
{
  "enabledPlugins": {
    "playwright@claude-plugins-official": true,
    "claude-code-setup@claude-plugins-official": true
  }
}
```

Add the `mcpServers` key — replace `<REPO_ROOT>` with the actual absolute path:

```json
{
  "enabledPlugins": {
    "playwright@claude-plugins-official": true,
    "claude-code-setup@claude-plugins-official": true
  },
  "mcpServers": {
    "budget-analyser": {
      "command": "uv",
      "args": ["run", "python", "-m", "budget_analyser_mcp"],
      "cwd": "<REPO_ROOT>/mcp"
    }
  }
}
```

> **Note:** `.claude/settings.json` is gitignored (untracked). Do not commit it.
> Each developer sets their own absolute `cwd` path.

### Step 3: Verify MCP appears in Claude Code

Restart Claude Code (or run `/mcp` to refresh). The `budget-analyser` server
should appear with 2 tools and 11 resources.

### Step 4: Commit

```bash
git add mcp/README.md
git commit -S -m "docs(mcp): add README and Claude Code integration instructions"
```

---

## Task 7: Run full test suite

### Step 1: Run all unit tests

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/ -q
```

Expected: all existing tests + 27 new MCP tests pass.

### Step 2: Run MCP-specific tests only

```bash
PYTHONPATH=mcp uv run pytest src/test/unit/test_mcp_db.py src/test/unit/test_mcp_tools.py src/test/unit/test_mcp_resources.py -v
```

Expected: 27 tests PASS.

### Step 3: Final commit

```bash
git commit -S -m "test(mcp): verify full test suite passes with MCP additions"
```

---

## Summary

| Task | Files created | Tests |
|------|--------------|-------|
| 1 | `mcp/pyproject.toml`, `__init__.py`, `__main__.py` | — |
| 2 | `db.py` | 5 tests in `test_mcp_db.py` |
| 3 | `tools.py` | 11 tests in `test_mcp_tools.py` |
| 4 | `resources.py` | 11 tests in `test_mcp_resources.py` |
| 5 | `server.py` | smoke test |
| 6 | `mcp/README.md`, `.claude/settings.json` | — |
| 7 | — | full suite run |
