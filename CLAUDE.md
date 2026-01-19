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

**Always follow pylint coding standards.** Run `pylint src/budget_analyser` before committing.

Pylint configuration (`.pylintrc`):
- Max line length: 100 characters
- Max function arguments: 6
- Max local variables: 15
- Max branches: 12
- Max statements per function: 50
- Views layer (`src/budget_analyser/views/`) is exempted from linting
- Docstrings are not enforced

**Coding guidelines:**
- Use `from __future__ import annotations` for forward references
- Prefer keyword-only arguments (`def foo(*, arg1, arg2)`) for clarity
- Use type hints on all function signatures
- Keep functions focused and single-purpose
- Extract complex conditions into well-named boolean variables

## Versioning

- **Patch** version auto-increments on push to `main` via GitHub Actions
- **Minor/Major** versions: create Git tags manually (`git tag -a vX.Y.0 -m "..."`)
- Set `eng_ver = 0` in `pyproject.toml` during development to disable auto-increment

## Git Commits

**Always use signed commits and semantic commit messages.**

```bash
# Commit with GPG signing
git commit -S -m "type: description"
```

**Semantic commit format:**
```
<type>: <short description>

[optional body with more details]

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Commit types:**
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring (no feature/fix) |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks, dependencies |

## Design Patterns & Modularity

**Always use appropriate design patterns.** Select the best-fit pattern for the problem:

| Pattern | When to Use | Example in Codebase |
|---------|-------------|---------------------|
| **Strategy** | Multiple algorithms for same task | `StatementFormatters` (Citi, Discover, Default) |
| **Factory** | Object creation with selection logic | `create_statement_formatter()` |
| **Repository** | Abstract data access | `TransactionDatabase`, `CsvStatementRepository` |
| **Protocol/Interface** | Decouple layers, enable testing | `StatementRepository`, `ColumnMappingProvider` |
| **Service** | Encapsulate business logic | `ReportService`, `TransactionProcessor` |
| **Dependency Injection** | Loose coupling, testability | Controllers receive dependencies via constructor |

**Modularity principles:**
- **One class per file** - each module has a single responsibility
- **Layered architecture** - views → controllers → domain → infrastructure
- **Domain independence** - domain layer has no dependencies on infrastructure
- **Protocol-based abstractions** - define interfaces in domain, implement in infrastructure
- **Frozen dataclasses** for immutable configuration and DTOs
- **Pure functions** in domain where possible (no side effects)

**When adding new features:**
1. Identify which layer(s) the feature touches
2. Define protocols/interfaces first if crossing layers
3. Implement in infrastructure, consume in domain/controller
4. Keep business logic in domain layer, not in views or infrastructure
5. Use dependency injection to wire components together

## Diagrams (Hybrid Approach)

Use **Mermaid** for inline diagrams in markdown files (renders on GitHub):

```mermaid
flowchart LR
    A[Component] --> B[Component]
```

Use **PlantUML** for detailed UML diagrams in `docs/uml/*.puml` (requires export to PNG).

| Tool | Use For | Location |
|------|---------|----------|
| **Mermaid** | Architecture, flowcharts, sequences in docs | `docs/*.md`, `README.md` |
| **PlantUML** | Detailed class diagrams, complex UML | `docs/uml/*.puml` |

**Mermaid diagram types:**
- `flowchart` - Architecture, data flow
- `sequenceDiagram` - API calls, process flows
- `classDiagram` - Class relationships
- `erDiagram` - Database schema
- `stateDiagram-v2` - State machines

## Testing

- Tests in `tests/` directory using pytest
- `tests/conftest.py` adds `src/` to PYTHONPATH
- CI runs on Linux/macOS/Windows across Python 3.10-3.12