# Changes Log

This file tracks notable project changes made during development and refactoring.

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
