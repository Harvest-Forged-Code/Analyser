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
