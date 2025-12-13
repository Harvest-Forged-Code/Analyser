"""Compatibility shim for GUI app.

This module now delegates to the modularized GUI components:
    - views/login_window.py (LoginWindow)
    - views/dashboard_window.py (DashboardWindow)
    - views/app_gui.py (run_app and composition)

Kept for backward compatibility so external imports keep working:
    from budget_analyser.presentation.views.gui_pyside6 import run_app
"""

from __future__ import annotations

from budget_analyser.presentation.views.app_gui import run_app  # re-export

if __name__ == "__main__":
    raise SystemExit(run_app())
