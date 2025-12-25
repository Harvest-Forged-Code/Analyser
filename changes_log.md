# Changes Log

This file tracks notable project changes made during development and refactoring.

## 2025-12-25

### Cashflow Mapping
- Added `cashflow_to_category.json` to centrally map earnings and expense categories for reporting.
- Wired settings and JSON loaders to expose the new cashflow mapping path with environment overrides and startup diagnostics.
- Updated `ReportService` to consume the cashflow mapping (including expense categories regardless of sign) and refreshed unit coverage for earnings/refund handling.

### Cashflow Mapping UI & Navigation
- Added an in-app Cashflow Mapping page with drag/drop lists to assign categories to Earnings or Expenses, plus quick move buttons, add-category controls, and save/reset actions backed by the JSON mapping store.
- Introduced a cashflow mapping controller and store for editing the earnings/expenses grouping without touching files manually.
- Wired the new page into the Data navigation group and menubar, and removed the redundant "MENU" label from the sidebar for a cleaner look.

### Yearly Summary UI
- Removed the monthly summary table from the Yearly Summary page and simplified the stats controller/DTOs accordingly, keeping only the yearly totals and category trees.

### Earnings Page
- Reworked Earnings page into a table view showing sub-categories with actuals, percent of total, expected amounts, differences, and diff percentages.
- Added an expected-amounts dialog backed by earnings goals so users can set per-sub-category expectations (monthly or global) and see differences reflected immediately.

### Budget Goals & Earnings Expectations
- Centralized all expected amount management in the Budget Goals page with month-specific inputs for both expenses and earnings.
- Added earnings expectations table/form and progress view alongside existing budget limits, with support for "ALL" defaults and month overrides.
- Updated in-app summaries to use the selected month while respecting month-specific overrides for both earnings and expense budgets.

### Budget Goals UI
- Split the Budget Goals page into two tabs (Expenses and Earnings) with dedicated month selectors, tables/forms, and progress sections for each side.
- Kept progress summaries and controls organized per tab to improve clarity between spending limits and expected income.

### Mapping Save Refresh
- Mapping pages (description mapper, cashflow mapper, sub-category mapper) now trigger an in-app report refresh after saving.
- Dashboard shows a progress dialog while reloading mappings, regenerating reports, and updating all report-driven pages so changes take effect immediately.

### Sub-category Mapping UI
- Added an in-app Sub-category Mapping page to move sub-categories between categories, add new ones, and save changes to `sub_category_to_category.json`.
- Introduced a dedicated controller for sub-category grouping built on the existing JSON mapping store.
- Wired the new page into the Data navigation group and menubar alongside Mapper and Cashflow Mapping.

## 2025-12-24

### UI/UX Refresh
- Introduced modernized light and dark palettes with consistent typography, rounded surfaces, and gradient backgrounds across the app.
- Restyled the dashboard header with a version chip and refreshed branded sidebar navigation with wider, more legible buttons.
- Polished the login experience with a branded badge, helper copy, and enlarged, theme-aware controls for a professional feel.

### Navigation Reorganization
- Grouped sidebar navigation into Reports, Goals, Automation, and Data clusters for faster scanning.
- Moved Settings into the menubar alongside report/data shortcuts for quick page access without cluttering the sidebar.

### Earnings & Expenses Categorization
- Earnings now count only transactions categorized as `Income` or `Unplanned_income`, keeping other positive entries out of earnings totals.
- Refunded money is treated as an expense reduction so refunds no longer inflate earnings and instead lower overall expenses.

### High-Priority Financial Features Integration
Completed integration of four major financial tracking features into the dashboard:

#### Budget Goals & Tracking
- Budget limits per category with monthly targets (e.g., Groceries: $500)
- Progress bars showing spending vs budget: "Groceries: $350/$500 (70%)"
- Color-coded status: Green (<80%), Yellow (80-100%), Red (>100%)
- Alerts when approaching or exceeding budget limits
- Full CRUD operations for budget goals

#### Savings Rate Calculator
- Savings Rate formula: (Earnings - Expenses) / Earnings × 100
- Monthly and yearly savings rate display with color-coded indicators
- Monthly breakdown table with earnings, expenses, savings, and rate
- Emergency fund progress tracking (3-6 months of expenses target)
- Financial health insights and savings tips

#### Net Worth Tracking
- Track bank accounts (checking, savings)
- Track investment accounts
- Track debts/liabilities (credit cards, loans)
- Calculate and display net worth (Assets - Liabilities)
- Quick balance update functionality

#### Recurring Transaction Detection
- Auto-detect recurring patterns from transaction history
- Track subscriptions, rent, utilities with expected amounts
- Support for weekly, monthly, quarterly, yearly frequencies
- Anomaly alerts for unusual changes in recurring amounts
- Predict next month's fixed expenses
- Manual add and manage recurring transactions

### Dashboard Navigation Updates
- Added four new navigation items: Budget Goals, Savings, Net Worth, Recurring
- Updated page indices and navigation structure
- Integrated BudgetController for all new financial features
- Created budget_goals.db for persistent storage of budget data

### New Files
- `src/budget_analyser/views/pages/recurring_page.py` - Recurring transactions UI (448 lines)

### Modified Files
- `src/budget_analyser/views/pages/__init__.py` - Export new pages
- `src/budget_analyser/views/dashboard_window.py` - Integrate new pages and navigation
- `src/budget_analyser/views/app_gui.py` - Create BudgetController and pass to dashboard

## 2025-12-21

### Tag-based versioning and automated releases
- Implemented semantic versioning (`Major.Minor.Patch`) with tag-based version management:
  - Patch version auto-increments on every push to `main` branch via GitHub Actions.
  - Minor and Major versions are updated manually by creating Git tags.
  - Developer mode (`eng_ver = 0` in `pyproject.toml`) disables auto-increment for local development.
- Added `src/budget_analyser/version.py` module with:
  - `get_version()` function that reads version from Git tags, package metadata, or pyproject.toml.
  - PyInstaller frozen environment detection (`_is_frozen()`) to read version from bundled VERSION file.
  - Helper functions: `get_version_tuple()`, `get_full_version_string()`, `is_dev_mode()`.

### Automated build and release workflow
- Created `.github/workflows/release.yml` for automated builds on push to `main`:
  - Calculates next version from Git tags and creates new tag.
  - Generates changelog from commit messages since last tag.
  - Builds Windows executable (.exe) using PyInstaller.
  - Builds macOS Intel (.zip) on `macos-13` runner.
  - Builds macOS Apple Silicon (.zip) on `macos-latest` runner.
  - Creates GitHub Release with all artifacts and changelog.
- VERSION file is created during build and bundled with PyInstaller to ensure correct version display in built apps.

### App icon integration
- Added app icons in `assets/` directory:
  - `icon.png` - Original PNG source.
  - `icon.ico` - Windows icon format.
  - `icon.icns` - macOS icon format.
- Icons are embedded in built executables via PyInstaller `--icon` flag.

### macOS Gatekeeper bypass documentation
- Added detailed instructions for bypassing macOS Gatekeeper warning ("Apple could not verify..."):
  - Updated README.md with new "macOS Installation (Gatekeeper Bypass)" section explaining:
    - Why the warning appears (unsigned app, no Apple Developer certificate)
    - Step-by-step instructions: Right-click → Open → Open
    - Alternative Terminal method: `xattr -d com.apple.quarantine`
  - Updated `.github/workflows/release.yml` release notes with:
    - The exact warning message users will see
    - Detailed bypass instructions
    - Terminal alternative command
    - Explanation linking to source code for verification

### Documentation updates
- Updated README.md:
  - Added Downloads section with links to latest releases for all platforms.
  - Added Build and Release badge.
  - Updated Python version requirement to 3.11+.
  - Added Versioning section explaining semantic versioning and developer mode.
  - Updated CI badge URLs to point to correct repository.

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
 
## 2025-12-16

### Documentation alignment with current SRC implementation
- Overhauled `documentation/README.md` to serve as a documentation hub reflecting the SRC layout, run/test commands, config, logs, and how to rebuild docs/diagrams.
- Refreshed `documentation/uml/README.md` to describe the Presentation (views/controllers), Domain, and Infrastructure packages; updated generation instructions; removed legacy references to `main_be.py` and old UI classes.
- Updated LaTeX manual `documentation/LaTeX/budget_analyser_documentation.tex`:
  - Replaced legacy run commands (`source/main_be.py`, `source/view/login.py`) with the standard entrypoint `python -m budget_analyser`.
  - Corrected default password to `123456` and clarified theme toggle behavior.
  - Rewrote the Project Structure section to match `src/budget_analyser/**` packages and added config/resources/tests/scripts entries.
- Cross-checked top-level `README.md` and environment variables against code (logging dir, statement dir, config and mapper paths). No changes required.
