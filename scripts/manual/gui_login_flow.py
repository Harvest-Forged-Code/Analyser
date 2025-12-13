"""GUI login flow verification script.

Validates that:
- After successful login, the login window is closed.
- The dashboard window is opened and maximized.

Run:
    QT_QPA_PLATFORM=offscreen python source/test_gui_login_flow.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    try:
        from PyQt6 import QtCore, QtTest, QtWidgets
    except Exception:
        print("PyQt6 is required to run this script. Install requirements with: pip install -r requirements.txt")
        raise

    # Keep imports aligned with source/app.py (login.py uses local imports).
    base_dir = Path(__file__).resolve().parent
    view_dir = base_dir / "view"
    if str(view_dir) not in sys.path:
        sys.path.insert(0, str(view_dir))

    import importlib

    login_mod = importlib.import_module("login")
    Ui_Widget = getattr(login_mod, "Ui_Widget")

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    login_widget = QtWidgets.QWidget()
    ui = Ui_Widget()
    ui.setupUi(login_widget)
    login_widget.show()

    # Perform login
    ui.entered_password.setText("password")
    QtTest.QTest.mouseClick(ui.login_buttons, QtCore.Qt.MouseButton.LeftButton)
    app.processEvents()

    dashboard = getattr(ui, "dashboard", None)
    failures: list[str] = []

    if dashboard is None:
        failures.append("Dashboard window was not created.")
    else:
        if not dashboard.isVisible():
            failures.append("Dashboard window is not visible after login.")
        if not dashboard.isMaximized():
            failures.append("Dashboard window is not maximized.")

    if login_widget.isVisible():
        failures.append("Login window is still visible after successful login.")

    # Cleanup
    if dashboard is not None:
        dashboard.close()
    login_widget.close()
    app.processEvents()

    if failures:
        print("FAIL")
        for msg in failures:
            print(f"- {msg}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
