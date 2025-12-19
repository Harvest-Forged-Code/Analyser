# Budget Analyser

[![CI – unit tests](https://github.com/OWNER/REPO/actions/workflows/tests.yml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/tests.yml)

Modern, cross‑platform budget analysis app built with PySide6 and pandas. It processes bank statements, categorizes transactions using JSON keyword mappings, and presents reports in a polished GUI with light/dark themes.

## Highlights
- Fullscreen login with password validation (default 123456; configurable in Settings).
- Modern Dashboard with emoji navigation and a header bar that reflects the active section.
- Yearly Summary with Category → Sub‑category trees for Earnings and Expenses, plus a 12‑month table.
- Earnings and Expenses pages with month selector, hierarchical trees, and a transactions table bound to selection.
- Payments Reconciliation page comparing “payments made” vs “payment confirmations” per month (excluded from standard reports).
- Mapper page with a filterable table of unmapped transactions (Date | Description | Amount) to quickly add mappings.
- Settings page to change password and logging level; theme toggle in Login and Dashboard header with persistence.
- Robust logging to a rotating per‑user log file; deep diagnostics for data loading and mapping.

## Architecture (SRC layout)
Layered, testable architecture with one behavior class per file:
- Views: Qt widgets only (no business logic).
- Controller: Pure‑Python controllers that prepare data for views.
- Domain: Statement formatting, transaction processing, reporting services.
- Infrastructure: INI/JSON adapters, CSV repository.
- Settings: Configuration code (settings.py, preferences.py).
- Data: Application data files (config, mappers, statements).

Entrypoint: `python -m budget_analyser` → Login → Dashboard.

Key modules:
- `src/budget_analyser/views/app_gui.py` – composition, logging, theme, and flow control.
- `src/budget_analyser/views/dashboard_window.py` – shell (menu, header, nav, stacked pages).
- `src/budget_analyser/views/pages/` – Yearly Summary, Earnings, Expenses, Payments, Mapper, Settings, Upload.
- `src/budget_analyser/controller/` – Yearly/Earnings/Expenses/Payments/Settings controllers.
- `src/budget_analyser/domain/` – statement formatters, transaction processing, reporting.
- `src/budget_analyser/infrastructure/` – INI config, CSV repository, JSON mappers, SQLite database.

## Implementation Flow

The application follows a **DB-centric architecture** where all reports are generated from the SQLite database. CSV files are processed and ingested into the database, which serves as the single source of truth.

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        APPLICATION STARTUP                          │
│  1. Load Settings (INI config, paths, preferences)                  │
│  2. Build controllers with injected dependencies                    │
│  3. Show LoginWindow                                                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                          [Login Success]
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CHECK DATA AVAILABILITY                          │
│  - If DB has data → Generate reports from DB                        │
│  - If no DB data AND CSVs present → Ingest CSVs to DB → Reports     │
│  - If no DB data AND no CSVs → Restricted mode (Upload page only)   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CSV INGESTION PIPELINE                           │
│  (TransactionIngestionService)                                      │
└─────────────────────────────────────────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 1. LOAD CSV   │       │ 2. FORMAT       │       │ 3. CATEGORIZE   │
│ Raw bank      │  ──►  │ Per-bank        │  ──►  │ Keyword-based   │
│ statements    │       │ formatters      │       │ mapping         │
└───────────────┘       └─────────────────┘       └─────────────────┘
                                                          │
                                                          ▼
                                                  ┌─────────────────┐
                                                  │ 4. PERSIST      │
                                                  │ Insert to SQLite│
                                                  │ (deduplicated)  │
                                                  └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    REPORT GENERATION                                │
│  (BackendController.run_from_database)                              │
│  - Load transactions from DB                                        │
│  - Group by month                                                   │
│  - Generate: Earnings, Expenses, Category/SubCategory pivots        │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DASHBOARD WINDOW                               │
│  - Earnings, Expenses, Category breakdowns, Yearly summaries        │
│  - Upload page for adding new statements → Ingest → Update DB       │
│  - Mapper page for managing category mappings                       │
│  - Payments reconciliation page                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Key Data Structures

- **MonthlyReports**: Container for one month's data (earnings, expenses, category pivots, transactions).
- **Canonical Transaction Schema**: `transaction_date`, `description`, `amount`, `from_account`, `sub_category`, `category`, `c_or_d`.

### Supported Banks

Bank-specific formatters handle different CSV column layouts:
- **Citi** (custom formatter)
- **Discover** (custom formatter)
- **Chase**, **Bilt** (default formatter)

Column mappings are configured in `budget_analyser.ini`.

## Install
Prerequisites: Python 3.10–3.12 recommended.

```
pip install -r requirements.txt
```

## Run the app (GUI)
```
python -m budget_analyser
```

Login with `123456` (unless changed in Settings). Use the 🌙/☀️ toggle on Login or Dashboard to switch themes (persisted).

## Run tests
```
pytest -q
```

CI runs the full unit test suite on Linux/macOS/Windows across Python 3.10–3.12 via GitHub Actions (`.github/workflows/tests.yml`).

## Configuration & logs
- Config INI: `src/budget_analyser/data/config/budget_analyser.ini` (stores logging level, password hash, theme, column mappings).
- Statement dir: `src/budget_analyser/data/statements` (default; override via env var in `src/budget_analyser/settings/settings.py`).
- JSON mappings: `src/budget_analyser/data/mappers/*.json`.
- Database: `src/budget_analyser/data/budget_analyser.db` (SQLite; stores processed transactions).
- Logs (rotating): `src/budget_analyser/data/logs/gui_app.log` (override via `BUDGET_ANALYSER_LOG_DIR`).

## Notes on data & signs
- Domain reporting enforces signs: Earnings shown as positive, Expenses as negative.
- “payment_confirmations” are excluded from Earnings; “payments_made” are excluded from Expenses in standard reports (still visible in Payments page).

## Troubleshooting
- Set log level to DEBUG in Settings to capture detailed pipeline diagnostics.
- If date parsing issues occur, the formatters coerce invalid dates to NaT; check the logs for column info and hints.

—

For a deeper dive (architecture diagrams, flows), see `documentation/` and the LaTeX PDF.
