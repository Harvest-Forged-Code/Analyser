# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## [IDENTITY] Project Overview

- **Project:** Budget Analyser
- **Tech stack:** Python 3.10+, PySide6 (Qt), pandas, SQLite, pytest
- **Type:** Cross-platform desktop GUI application for personal finance tracking
- **Goals:** Process bank statements (CSV), categorize transactions using JSON mappings, store in SQLite, present reports in GUI with light/dark theme support

Budget Analyser is a personal finance tracking application that:
- Imports bank statements in CSV format (supports Citi, Discover, and custom formats)
- Categorizes transactions using keyword-based JSON mappings
- Stores transaction data in SQLite database
- Generates monthly reports with spending analysis, trends, forecasting, and budget tracking
- Provides dashboard with earnings, expenses, net worth, recurring transactions, and budget goals
- Supports payment reconciliation and transaction export (CSV, Excel, PDF)

## [WORKFLOW] Development Process

### Core Principle
**Vertical Slices First** — When adding features, create self-contained feature modules that own all layers (models, repository, service, controller, page). Do not scatter logic across horizontal layers.

### Mandatory Workflow

1. **Understand the existing code** — Budget Analyser uses a hybrid architecture. Most features are migrated to vertical slices under `features/`. Check if your feature already exists.
2. **For new features:** Follow the vertical slice pattern (see "When Adding New Features" section below)
3. **For migrations:** Extract horizontal layer code into vertical slices incrementally, use backward-compat shims
4. **Test everything:** All unit tests must pass before committing (`pytest tests/unit/ -q`)
5. **Verify imports:** Ensure no circular dependencies between features or with core

### Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m budget_analyser

# Run tests (REQUIRED before committing)
pytest tests/unit/ -q

# Run with coverage
pytest --cov=src/budget_analyser

# Run linting
pylint src/budget_analyser
```

## [ARCHITECTURE] System Design

### Architecture Overview

**Vertical feature slices architecture** — All 11 core features are now organized as self-contained vertical slices. Each feature owns all its layers: models, repository, service, controller, and view. Shared infrastructure lives in `core/`.

```
src/budget_analyser/
├── core/            # Shared foundation (protocols, errors, DB utils, shared DTOs)
│   ├── __init__.py
│   ├── protocols.py     # Domain interfaces (StatementRepository, etc.)
│   ├── errors.py        # Domain exception hierarchy
│   ├── database.py      # Shared SQLite connection factory
│   └── models.py        # Cross-feature DTOs (MonthlyReports)
├── features/        # Vertical feature slices (11 complete modules)
│   ├── budget_goals/    # Budget and earnings goals management
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── controller.py
│   │   └── page.py
│   ├── net_worth/       # Financial accounts and net worth tracking
│   ├── recurring/       # Recurring transaction management
│   ├── savings/         # Savings metrics and tracking
│   ├── forecasting/     # Expense forecasting service
│   ├── trends/          # Spending trends and burn rate analysis
│   ├── export/          # CSV/Excel/PDF export service
│   ├── payments/        # Payment reconciliation
│   ├── reporting/       # Monthly report generation
│   ├── mappers/         # Category and cashflow mapping
│   ├── ingestion/       # CSV ingestion pipeline
│   └── settings/        # Settings management
├── views/           # GUI layer (PySide6 widgets) - exempted from pylint
│   ├── app_gui.py   # Composition root, logging setup, flow control
│   ├── dashboard_window.py  # Main shell (menu, header, nav, stacked pages)
│   ├── pages/       # Dashboard pages (earnings, expenses, mapper, etc.)
│   └── widgets/     # Reusable Qt widgets
├── controller/      # Legacy presentation layer (being migrated to features/)
│   ├── backend_controller.py  # Orchestrates end-to-end workflow
│   ├── budget_controller.py   # Facade: delegates goals to features/budget_goals
│   └── *_controller.py        # Page-specific controllers
├── domain/          # Legacy business logic (being migrated to features/)
│   ├── protocols.py             # Backward-compat shim → core.protocols
│   ├── errors.py                # Backward-compat shim → core.errors
│   ├── statement_formatter.py   # Factory for bank-specific formatters
│   ├── statement_formatters/    # Bank-specific CSV parsers
│   ├── transaction_processor.py # Categorization logic
│   ├── transaction_ingestion.py # CSV → DB pipeline
│   ├── reporting.py             # Report generation service
│   ├── forecasting.py           # Expense forecasting
│   ├── trend_analysis.py        # MoM/YoY trend analysis
│   ├── burn_rate.py             # Budget burn rate calculations
│   ├── spending_patterns.py     # Pareto, anomaly detection
│   ├── payment_matching.py      # Payment reconciliation
│   ├── categorization_suggestions.py  # Auto-suggest categories
│   └── export_service.py        # CSV/Excel/PDF export
├── infrastructure/  # Persistence & external systems
│   ├── database.py, budget_database.py  # SQLite adapters (budget_goals migrated)
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

**Migration status:** Phase 3 complete — all 11 features migrated to vertical slices.
- ✅ 11 feature modules with complete stack (models, repo, service, controller, page)
- ✅ 17 backward-compat shims for old locations (9 domain + 8 controller files)
- ✅ Shared core layer with protocols, errors, database utilities
- ✅ 453 unit tests passing (64 new tests added for Phase 3)
- ⏳ Remaining: Decompose BudgetController/BudgetDatabase facades after all consumers migrate

**Backward compatibility:** Old imports still work via re-export shims. Example:
```python
# OLD WAY (still works, via shim)
from budget_analyser.domain.budget_goals import create_budget

# NEW WAY (preferred)
from budget_analyser.features.budget_goals.service import create_budget
```

## Code Style & Linting

**All code must comply with PEP 8 and pylint.** Run `pylint src/budget_analyser` before committing.

Pylint configuration (`.pylintrc`):
- Max line length: 100 characters
- Max function arguments: 6
- Max local variables: 15
- Max branches: 12
- Max statements per function: 50
- Views layer (`src/budget_analyser/views/`) is exempted from linting

### Type Hints (Mandatory)

Type hints are **required** on all function and method signatures (parameters and return types).

```python
from __future__ import annotations  # Required in every module

# Use modern type syntax (Python 3.10+):
def process(self, *, raw_transactions: pd.DataFrame) -> pd.DataFrame: ...
def get_budget(self, category: str, year_month: str = "ALL") -> BudgetGoal | None: ...
def get_accounts(self) -> list[Account]: ...
def get_mappings(self) -> dict[str, list[str]]: ...

# Use collections.abc for abstract types:
from collections.abc import Callable, Mapping, Sequence
def run(self, *, formatter: Callable[[str], str]) -> Sequence[dict[str, float]]: ...
```

**Rules:**
- `from __future__ import annotations` in every module
- Use `X | None` instead of `Optional[X]`
- Use `list[x]`, `dict[k, v]`, `tuple[a, b]` instead of `List`, `Dict`, `Tuple` from `typing`
- Use `collections.abc` for `Callable`, `Mapping`, `Sequence`, `Iterable`
- Only import from `typing` when needed: `Any`, `Protocol`, `ClassVar`, `TypeVar`

### Coding Guidelines

- Prefer keyword-only arguments (`def foo(*, arg1, arg2)`) for clarity
- Keep functions focused and single-purpose
- Extract complex conditions into well-named boolean variables
- No magic numbers — use named constants
- Meaningful names over comments (code should be self-documenting)
- Functions should operate at one level of abstraction

## Documentation Standards

**All public classes, methods, and functions must have Google-style docstrings.**

```python
def calculate_burn_rate(
    *,
    transactions: pd.DataFrame,
    budget_limit: float,
    as_of_date: date | None = None,
) -> BurnRateMetrics:
    """Calculate daily spending velocity and project monthly total.

    Computes how fast the budget is being consumed based on
    spending patterns up to the given date.

    Args:
        transactions: DataFrame with 'amount' and 'transaction_date' columns.
        budget_limit: Monthly budget ceiling for the category.
        as_of_date: Date to calculate burn rate as of. Defaults to today.

    Returns:
        BurnRateMetrics with daily rate, projection, and remaining budget.

    Raises:
        ValidationError: If transactions DataFrame is missing required columns.
    """
```

**When to write docstrings:**

| Scope | Required | Notes |
|-------|----------|-------|
| Public classes | Yes | Describe purpose and usage |
| Public methods/functions | Yes | Args, Returns, Raises sections |
| Private methods (`_helper`) | Only if logic is non-obvious | Keep brief |
| Module-level | Optional | Only for complex modules |
| Test functions | No | Test name should be self-documenting |
| Views layer | No | GUI code is exempted |

**Google-style sections to use:**

| Section | When |
|---------|------|
| `Args:` | Function takes parameters |
| `Returns:` | Function returns a value |
| `Raises:` | Function raises exceptions |
| `Note:` | Important caveats or context |
| `Example:` | Complex or non-obvious usage |

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

Author: Prabhukumar Sivamorthy
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
| **Vertical Slice** | Self-contained feature owning all layers | `features/budget_goals/` (models, repo, service, controller, page) |
| **Strategy** | Multiple algorithms for same task | `StatementFormatters` (Citi, Discover, Default) |
| **Factory** | Object creation with selection logic | `create_statement_formatter()` |
| **Template Method** | Define algorithm skeleton, let subclasses override steps | `BaseStatementFormatter._bank_specific_formatting()` |
| **Repository** | Abstract data access | `BudgetGoalsRepository`, `TransactionDatabase`, `CsvStatementRepository` |
| **Protocol/Interface** | Decouple layers, enable testing | `core.protocols`: `StatementRepository`, `ColumnMappingProvider` |
| **Service** | Pure business logic functions | `budget_goals.service`, `ReportService`, `TransactionProcessor` |
| **Dependency Injection** | Loose coupling, testability | Controllers receive dependencies via constructor |
| **Observer** | Event-driven communication | Qt Signal/Slot (`upload_successful`, `refresh_requested`) |
| **Composition Root** | Single wiring location for all dependencies | `app_gui.py::_build_controller()` |
| **Data Transfer Object** | Pass data across layers immutably | `MonthlyReports`, `BudgetGoal` (frozen dataclasses) |

### Clean Code Principles

- **Single Responsibility Principle (SRP)** — every class and function does one thing
- **One class per file** — each module has a single public class or cohesive set of functions
- **DRY (Don't Repeat Yourself)** — extract duplicated logic into helpers or shared utilities
- **Layered architecture** — views → controllers → domain → infrastructure (no skipping layers)
- **Domain independence** — domain layer has no dependencies on infrastructure (use protocols)
- **Protocol-based abstractions** — define interfaces in domain, implement in infrastructure
- **Frozen dataclasses** for immutable configuration and DTOs
- **Pure functions** in domain where possible (no side effects)
- **Composition over inheritance** — prefer injecting collaborators over deep class hierarchies
- **Fail fast** — validate inputs at boundaries, raise domain exceptions early

### When Adding New Features

**ALWAYS use vertical slices** — This is the standard pattern in this codebase. See `features/budget_goals/`, `features/net_worth/`, etc. for examples.

1. Create `features/<name>/` directory with all required files
2. **models.py** — DTOs (frozen dataclasses) for data transfer between layers
3. **repository.py** — Database access using `core.database.get_connection()`
4. **service.py** — Pure business logic functions (no Qt/PySide6, no infrastructure)
5. **controller.py** — Thin facade that coordinates repository + service
6. **page.py** — Qt widget (view) that receives controller in `__init__`
7. **__init__.py** — Export public interfaces (controller, repository, models)
8. Wire controller in `app_gui.py` composition root at `run_app()`
9. Add unit tests: `tests/unit/test_<feature>_{models,repository,service,controller}.py`
10. Update `BudgetController` facade if feature interacts with reports/dashboards

**Pattern example (net_worth):**
```
features/net_worth/
├── __init__.py              # Export NetWorthRepository, NetWorthController
├── models.py                # Account, NetWorthSummary (frozen dataclasses)
├── repository.py            # CRUD operations on accounts table
├── service.py               # calculate_net_worth_summary(), etc.
├── controller.py            # NetWorthController (aggregates repo + service)
└── (no page.py if no UI)
```

**For changes to legacy (unmigrated) domain code:**

Legacy code still exists in `domain/` and `controller/` as backward-compat shims. If you must modify it:
1. First, check if a vertical slice feature already exists for this domain
2. If yes: Move the logic into the feature module
3. If no: Extract the feature into a new vertical slice
4. Keep shims in old locations for backward compatibility
5. Never add new code to legacy horizontal layers

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

**Follow Test-Driven Development (TDD).** Write tests before implementing features.

**TDD workflow:**
1. **Write test first** - Create failing test for the new feature/fix
2. **Implement code** - Write minimal code to make the test pass
3. **Refactor** - Clean up while keeping tests green
4. **Run unit tests** - All unit tests must pass before committing

**Test types:**

| Type | Purpose | Location | Scope |
|------|---------|----------|-------|
| **Unit** | Test individual functions/classes in isolation | `tests/unit/` | Single module, mocked dependencies |
| **Integration** | Test component interactions | `tests/integration/` | Multiple modules, real dependencies |
| **System** | Test end-to-end workflows | `tests/system/` | Full application, user scenarios |

```bash
# Run unit tests (REQUIRED before committing)
pytest tests/unit/ -q

# Run integration tests
pytest tests/integration/ -q

# Run system tests
pytest tests/system/ -q

# Run all tests
pytest -q

# Run with coverage
pytest --cov=src/budget_analyser
```

**Testing requirements:**
- Every new feature must have unit tests (required), integration/system tests as appropriate
- Every bug fix must have a regression test
- **All unit tests must pass before committing** (`pytest tests/unit/ -q`)
- Tests in `tests/` directory using pytest
- `tests/conftest.py` adds `src/` to PYTHONPATH
- CI runs on Linux/macOS/Windows across Python 3.10-3.12

**Test organization:**
```
tests/
├── unit/           # Fast, isolated tests (mock external dependencies)
│   ├── test_budget_goals_service.py      # Feature slice: service pure functions
│   ├── test_budget_goals_repository.py   # Feature slice: SQLite CRUD (tmp_path)
│   ├── test_budget_goals_controller.py   # Feature slice: controller integration
│   ├── test_budget_controller.py         # Legacy facade backward compat
│   ├── test_keyword_matching.py          # Domain business logic
│   ├── ... (other domain/controller tests)
├── integration/    # Component interaction tests (real DB, file I/O)
└── system/         # End-to-end workflow tests (full app scenarios)
```

**Naming conventions:**
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Group related tests in classes when appropriate
- Prefix test files with `test_`

**Test execution:**

| Stage | Tests Run | Purpose |
|-------|-----------|---------|
| **Before commit** | Unit tests only | Fast feedback, catch logic errors |
| **CI pipeline** | Unit → Integration → System | Full validation across all layers |

**Coverage focus:**

| Test Type | Focus Areas |
|-----------|-------------|
| **Unit** | Domain layer (business logic), controllers, pure functions |
| **Integration** | Database operations, file I/O, CSV parsing, JSON mappings |
| **System** | Critical user workflows (CSV import → categorization → reports) |

**GUI testing (for system tests):**
- Prefer controller-level system tests (faster, less flaky)
- Use `pytest-qt` for GUI tests only when necessary (critical UI flows)
- Keep GUI tests minimal - focus on user-facing critical paths
- Mock heavy dependencies (DB, file system) even in GUI tests when possible

## [RECENT-CHANGES] Latest Updates (Phase 3 Complete)

### Architecture Migration (Commit 647e2d2)
**All 11 features successfully migrated to vertical slices:**
- `budget_goals`, `net_worth`, `recurring`, `savings`, `forecasting`, `trends`, `export`, `payments`, `reporting`, `mappers`, `ingestion`, `settings`
- Core layer created with shared protocols, errors, database utilities
- 17 backward-compat shims in place for existing consumers
- 64 new tests added; all 453 unit tests passing

**Migration impact:**
- `app_gui.py` now creates feature repositories and wires BudgetController facade
- New code should import directly from feature modules, not facade
- Old imports via shims continue to work for backward compatibility

### Bug Fixes (Commit a44d457)
1. **Pandas deprecation fix** — Updated `pd.date_range(..., freq="M")` to `freq="ME"`
   - DatetimeIndex frequency changed in newer pandas versions
   - Period frequency still uses `freq="M"` (different system)
2. **BudgetController initialization** — Updated app_gui.py composition root
   - Changed from `BudgetController(budget_db=...)` to feature repository parameters
   - Wire `budget_goals_repo`, `net_worth_repo`, `recurring_repo` separately

## Skills

### PySide6 UI Designer (`.claude/skills/pyside6-ui-designer.md`)
Automatically applied when designing, building, or modifying any UI component. Enforces the project's design system: centralized tokens from `constants.py`, dual theme support, page structure via `ModernPageMixin`, icon system with fallbacks, and financial UI best practices. Always reference this skill for any views-layer work.

### Vertical Slices Pattern
When creating a new feature, follow the vertical slice structure already established in `features/budget_goals/`, `features/net_worth/`, etc. Each feature is self-contained with models, repository, service, controller, and optionally a view page.
