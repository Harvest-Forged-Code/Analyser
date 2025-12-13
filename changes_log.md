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

### Home page polish and Settings separation
- Home page UI tweaks:
  - Enforced equal widths for the Earnings and Expenses columns using explicit stretch factors and Expanding size policies.
  - Switched month labels to full names (January..December) via a shared controller utility.
- Controller layer:
  - Added presentation/controller/settings_controller.py (SettingsController) to keep Settings logic out of the view.
  - Refactored SettingsPage to be UI-only; it now delegates password and log-level actions to SettingsController.
