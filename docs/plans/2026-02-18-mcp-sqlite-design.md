# MCP SQLite Server — Design Document

**Date:** 2026-02-18
**Status:** Approved

## Overview

A Model Context Protocol (MCP) server that exposes both Budget Analyser SQLite
databases to Claude. Serves dual use cases: natural-language personal finance
analysis ("how much did I spend on Needs last month?") and developer tooling
(inspecting DB state while working on the codebase).

## Databases

| Alias | File | Tables |
|-------|------|--------|
| `transactions` | `src/budget_analyser/data/budget_analyser.db` | `transactions` |
| `goals` | `src/budget_analyser/data/budget_goals.db` | `budget_goals`, `earnings_goals`, `accounts`, `recurring_transactions`, `upload_history` |

## Architecture

```
mcp/
├── budget_analyser_mcp/
│   ├── __init__.py
│   ├── server.py       # MCP server entry point (FastMCP)
│   ├── tools.py        # query + execute tools
│   └── resources.py    # all resource handlers
├── pyproject.toml      # deps: mcp[cli] only (stdlib sqlite3)
└── README.md
```

- **Transport:** stdio (standard MCP subprocess pattern)
- **Runtime:** Python, using the `mcp` SDK
- **DB path resolution:** Relative to repo root by default; overridable via
  `BUDGET_ANALYSER_DB` (transactions) and `BUDGET_ANALYSER_GOALS_DB` (goals)
  environment variables

## Tools

Both tools accept a `db` parameter to select which database to operate on.

### `query(sql: str, db: "transactions" | "goals" = "transactions") -> list[dict]`

Runs an arbitrary SELECT and returns rows as a JSON array. Validates the DB path
exists before executing.

### `execute(sql: str, db: "transactions" | "goals") -> dict`

Runs an arbitrary DML statement (INSERT, UPDATE, DELETE, ALTER). Wraps in a
transaction and rolls back on failure. Returns `{"rows_affected": int,
"last_insert_id": int}`.

**Blocked statements:** `DROP TABLE` and `DROP DATABASE` are rejected with an
explanatory message. All other DML is permitted.

## Resources

Resources are read-only and fetched fresh from the DB on each access.

| URI | Content |
|-----|---------|
| `budget-analyser://overview` | Both DBs, all tables, row counts |
| `budget-analyser://transactions/schema` | DDL for `budget_analyser.db` |
| `budget-analyser://transactions/sample` | 10 most recent transactions (JSON) |
| `budget-analyser://transactions/accounts` | Distinct `from_account` values |
| `budget-analyser://transactions/categories` | Distinct `category` + `sub_category` |
| `budget-analyser://goals/schema` | DDL for `budget_goals.db` (all 5 tables) |
| `budget-analyser://goals/budget-goals` | All budget limit rows |
| `budget-analyser://goals/earnings-goals` | All earnings goal rows |
| `budget-analyser://goals/accounts` | All net worth accounts |
| `budget-analyser://goals/recurring` | Active recurring transactions |
| `budget-analyser://goals/upload-history` | Recent upload history |

## Error Handling

| Scenario | Behaviour |
|----------|-----------|
| DB file not found | Clear message with expected path |
| SQL syntax error | Return sqlite3 error message to Claude; server stays up |
| Blocked DDL | Return rejection message explaining why |
| Execute failure | Rollback transaction; return error message |
| Unknown `db` value | Return validation error listing valid options |

## Testing

- File: `src/test/unit/test_mcp_server.py`
- Uses a temp in-memory SQLite DB (no file I/O in tests)
- Run with: `uv run pytest src/test/unit/ -q`
- Coverage:
  - `query` happy path
  - `execute` happy path (INSERT, UPDATE, DELETE)
  - Blocked DDL rejection
  - Bad SQL error handling
  - Unknown `db` parameter

## Claude Code Integration

Add to `.claude/settings.json` (or `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "budget-analyser": {
      "command": "uv",
      "args": ["run", "python", "-m", "budget_analyser_mcp"],
      "cwd": "<repo-root>/mcp"
    }
  }
}
```
