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
- `src/budget_analyser/infrastructure/` – INI config, CSV repository, JSON mappers.

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
- Logs (rotating):
  - macOS/Linux: `~/.budget_analyser/logs/gui_app.log`
  - Windows: `%USERPROFILE%\.budget_analyser\logs\gui_app.log`
  - Override via `BUDGET_ANALYSER_LOG_DIR`.

## Notes on data & signs
- Domain reporting enforces signs: Earnings shown as positive, Expenses as negative.
- “payment_confirmations” are excluded from Earnings; “payments_made” are excluded from Expenses in standard reports (still visible in Payments page).

## Troubleshooting
- Set log level to DEBUG in Settings to capture detailed pipeline diagnostics.
- If date parsing issues occur, the formatters coerce invalid dates to NaT; check the logs for column info and hints.

—

For a deeper dive (architecture diagrams, flows), see `documentation/` and the LaTeX PDF.
