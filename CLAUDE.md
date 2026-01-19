# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Budget Analyser is a cross-platform desktop GUI application for personal finance tracking built with PySide6 (Qt) and pandas. It processes bank statements (CSV), categorizes transactions using JSON keyword mappings, stores them in SQLite, and presents reports in a GUI with light/dark themes.

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m budget_analyser

# Run tests
pytest -q

# Run linting
pylint src/budget_analyser
```

## Architecture

**Layered architecture** with one behavior class per file:

```
src/budget_analyser/
├── views/           # GUI layer (PySide6 widgets) - exempted from pylint
│   ├── app_gui.py   # Composition root, logging setup, flow control
│   ├── dashboard_window.py  # Main shell (menu, header, nav, stacked pages)
│   ├── pages/       # Dashboard pages (earnings, expenses, mapper, etc.)
│   └── widgets/     # Reusable Qt widgets
├── controller/      # Presentation layer (pure Python)
│   ├── backend_controller.py  # Orchestrates end-to-end workflow
│   └── *_controller.py        # Page-specific controllers
├── domain/          # Business logic
│   ├── statement_formatter.py      # Factory for bank-specific formatters
│   ├── statement_formatters/       # Bank-specific CSV parsers (Citi, Discover, etc.)
│   ├── transaction_processor.py    # Categorization logic
│   ├── transaction_ingestion.py    # CSV → DB pipeline
│   └── reporting.py                # Report generation service
├── infrastructure/  # Persistence & external systems
│   ├── database.py, budget_database.py  # SQLite adapters
│   ├── json_mappings.py                 # JSON mapper loader/saver
│   └── ini_config.py                    # INI config parsing
├── settings/        # Configuration (settings.py, preferences.py)
└── data/            # Application data (not code)
    ├── config/budget_analyser.ini   # Runtime config
    ├── mappers/*.json               # Keyword → category mappings
    ├── statements/                  # User CSV files
    └── budget_analyser.db           # SQLite database
```

**Key data flow:**
1. CSV files → Bank-specific formatter → Transaction processor → SQLite DB
2. SQLite DB → ReportService → MonthlyReports → Dashboard pages

**Entry point:** `python -m budget_analyser` → `views/app_gui.py::run_app()` → LoginWindow → DashboardWindow

## Code Style & Linting

Pylint configuration (`.pylintrc`):
- Max line length: 100 characters
- Max function arguments: 6
- Max local variables: 15
- Max branches: 12
- Max statements per function: 50
- Views layer (`src/budget_analyser/views/`) is exempted from linting
- Docstrings are not enforced

## Versioning

- **Patch** version auto-increments on push to `main` via GitHub Actions
- **Minor/Major** versions: create Git tags manually (`git tag -a vX.Y.0 -m "..."`)
- Set `eng_ver = 0` in `pyproject.toml` during development to disable auto-increment

## Key Patterns

- **Dependency injection** via constructors (controllers receive repositories, services)
- **Protocol-based abstractions** in domain layer for testability
- **Frozen dataclasses** for immutable configuration objects
- **Type hints** throughout (`from __future__ import annotations`)
- DB is single source of truth; CSV ingestion is one-way (CSV → DB → Reports)

## Testing

- Tests in `tests/` directory using pytest
- `tests/conftest.py` adds `src/` to PYTHONPATH
- CI runs on Linux/macOS/Windows across Python 3.10-3.12