# Changes Log

This file tracks notable project changes made during development and refactoring.

## 2025-12-12

### Architecture & layout migration (in progress)
- Introduced `src/` + `tests/` directory scaffolding to migrate toward a strict layered architecture.
- Target package name: `budget_analyser`.
- Added `pyproject.toml` to support `src/` layout packaging.
- Added initial layered implementation under `src/budget_analyser/` including composition root (`python -m budget_analyser`).
- Added repo-shipped configuration `config/budget_analyser.ini` and mapper JSONs under `resources/mappers/`.
- Added pytest suite scaffold under `tests/` and migrated statement-formatter checks to `tests/unit/test_statement_formatter.py`.
- Moved legacy ad-hoc scripts out of pytest discovery:
  - `source/Unitests/test_statement_formatter.py` -> `scripts/manual/statement_formatter_smoke.py`
  - `source/Unitests/test_gui_login_flow.py` -> `scripts/manual/gui_login_flow.py`
  - `source/Unitests/test.py` -> `examples/qt_demo.py`

### Documentation pass
- Added/expanded module, class, and method docstrings (Purpose/Goal/Steps) across `src/budget_analyser/**`.
- Added inline comments describing key steps in the workflow and adapters.

### GUI modularization (PySide6)
- Split monolithic GUI module into single-class files to improve readability and reduce duplicate imports/object creation:
  - src/budget_analyser/presentation/views/login_window.py — LoginWindow
  - src/budget_analyser/presentation/views/dashboard_window.py — DashboardWindow
  - src/budget_analyser/presentation/views/app_gui.py — composition and run_app()
- Updated src/budget_analyser/__main__.py to import run_app from the new app_gui module.
- README updated with new run instructions and module layout.

### Presentation cleanup
- Removed legacy presentation-layer CLI module: src/budget_analyser/presentation/views/cli.py
- Removed legacy compatibility shim: src/budget_analyser/presentation/views/gui_pyside6.py
- Standard entrypoint: `python -m budget_analyser` (uses app_gui.run_app)

### UI polish
- Applied modern styling to the PySide6 Login window:
  - Dark gradient background with centered rounded "card" container.
  - Styled password field with focus highlight and improved placeholder.
  - Prominent accent-colored Login button with hover/pressed states.
  - Subtle drop shadow for depth and cleaner typography.

## 2025-12-13

### Modern Dashboard UI
- Introduced a centralized stylesheet (presentation/views/styles.py) to unify the dark theme and accent colors.
- Upgraded Dashboard shell (presentation/views/dashboard_window.py):
  - Added a header bar with title and current section subtitle.
  - Redesigned the left sidebar with rounded container, pill-style buttons, and hover/checked states.
  - Wrapped the central content area in a rounded container and added subtle drop shadows for depth.
  - Kept File → Exit menu and navigation behavior unchanged.
- Updated README to reflect the new look and header behavior in the dashboard.

### Login window style tweak
- Scoped a login-only stylesheet so styling applies only to the Login window.
- Increased the Login title size to improve readability (36px).
- Applied consistent input and button styles per the provided snippet (focus/hover/pressed states).

### Theme system and UI polish
- Added light/dark theme support with centralized styles and persistence:
  - New `app_stylesheet(theme)` in `presentation/views/styles.py` (dark and light variants).
  - Theme preference persisted in `config/budget_analyser.ini` under `[app] theme=dark|light` via `AppPreferences.get_theme/set_theme`.
  - Theme applied at startup in `views/app_gui.py` and can be toggled at runtime.
- Theme toggle buttons (🌙/☀️):
  - Login: button on the top-right of the login card.
  - Dashboard: button on the header bar’s right side.
- Navigation emojis added to sidebar items (🗓️, 💰, 🧾, ⬆️, 🧭, ⚙️).
- Yearly Summary page modernization:
  - Relies on global styles; removed heavy inline QSS.
  - Equal-width panels for earnings/expenses; improved tables with alternating rows and consistent row heights.

### Home page polish and Settings separation
- Home page UI tweaks:
  - Enforced equal widths for the Earnings and Expenses columns using explicit stretch factors and Expanding size policies.
  - Switched month labels to full names (January..December) via a shared controller utility.
- Controller layer:
  - Added presentation/controller/settings_controller.py (SettingsController) to keep Settings logic out of the view.
  - Refactored SettingsPage to be UI-only; it now delegates password and log-level actions to SettingsController.

### Continuous Integration (CI) for unit tests
- Added cross-platform GitHub Actions workflow `.github/workflows/tests.yml` that runs pytest on Ubuntu, macOS, and Windows across Python 3.10–3.12.
- Ensured headless Qt by setting `QT_QPA_PLATFORM=offscreen` and `PYTHONPATH=src` in the workflow.
- Updated existing `.github/workflows/pylint.yml` to set environment variables and run tests during lint job.

### Documentation refresh to match SRC implementation
- README.md rewritten to reflect the current architecture (SRC layout), controllers/views separation, new pages (Payments, Mapper table), theme system, logging, and CI badge.
- LaTeX documentation updated (documentation/LaTeX/budget_analyser_documentation.tex):
  - Added a "Current Implementation (SRC layout)" section with directory overview and composition root.
  - Documented controllers vs views, dashboard pages, domain sign normalization, logging/diagnostics, platform independence, and CI.

### Modern dropdown styling (all pages)
- Updated theme-aware QComboBox styling in presentation/views/styles.py for both dark and light themes:
  - Rounded corners (10px), refined borders, comfortable padding, and min-height for touch-friendly targets.
  - Hover and focus states with accent-colored border (#2D81FF); disabled state readability improvements.
  - Styled drop-down subcontrol with a subtle left divider; adjusted arrow spacing.
  - Popup list (QAbstractItemView) with themed background, visible border, and improved selection color.

### Font and Login polish
- Replaced missing Windows-only font "Segoe UI" with a cross-platform font stack to eliminate Qt font aliasing warning and speed up startup. (presentation/views/styles.py)
- Login window tweaks (presentation/views/login_window.py):
  - Made the theme toggle button fully transparent (no blue background) and compact.
  - Theme-aware login styles so the title/subtitle and inputs have proper contrast in light theme (title now dark for light BG).

### Diagnostics and logging improvements
- Switched GUI logging to RotatingFileHandler (5 MB, 3 backups) to prevent unbounded log growth. (views/app_gui.py)
- Added pipeline diagnostics in BackendController:
  - INFO: pipeline start/end with account count, total transactions, months, and duration.
  - DEBUG: per-account raw/ formatted shapes and columns; merged transactions shape; rich context on failures. (presentation/backend_controller.py)
- JSON mapping provider now logs mapping file paths and key counts; warns on empty mappings. (infrastructure/json_mappings.py)
- Formatter error messages now include the account name and present columns, with a short remediation hint for missing amount columns. (domain/statement_formatters/base_statement_formatter.py)
- README updated with log location, rotation, env override, and how to enable DEBUG.

### Domain reporting sign normalization
- Ensured final report tables enforce signs consistently in the domain layer:
  - Earnings amounts are normalized to positive values.
  - Expenses amounts are normalized to negative values.
- Implemented in `domain/reporting.py` (ReportService.earnings/expenses) with defensive copies to avoid mutating source frames.
- Added unit test `tests/unit/test_reporting_signs.py` to validate normalization and immutability.

### Mapper page UX enhancement
- Unmapped items are now shown as transaction rows (Date, Description, Amount) instead of a plain list of descriptions.
- Added controller API `MapperController.list_unmapped_transactions()` to provide the data in a UI-agnostic way.
- Updated `presentation/views/pages/mapper_page.py` to render a filterable, multi-select table and to map selected rows based on their descriptions.
