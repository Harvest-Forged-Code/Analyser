"""Shared styles for the PySide6 presentation layer.

Centralizes QSS used across the application and supports light/dark themes.
"""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase


def _dark_theme() -> str:
    return """
    /* Global */
    QWidget { font-size: 13px; }

    /* Window backgrounds */
    QMainWindow#dashboardWindow { background-color: #0F172A; }
    #loginWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0F172A, stop:1 #0B1220); color: #E6EDF3; }

    /* Header bar */
    #headerBar {
        background-color: rgba(22, 27, 34, 0.88);
        border: 1px solid rgba(240, 246, 252, 0.08);
        border-radius: 12px;
        padding: 10px 14px;
    }
    #headerTitleLabel { color: #F0F6FC; font-size: 18px; font-weight: 600; letter-spacing: 0.3px; }
    #headerSubtitleLabel { color: #9DA7B1; }

    /* Sidebar */
    #sidebar {
        background-color: #111827;
        border-radius: 14px;
        border: 1px solid rgba(240, 246, 252, 0.06);
    }
    #sidebar QLabel { color: #CBD5E1; }
    #sidebar QPushButton {
        color: #E5E7EB;
        background: transparent;
        border: none;
        padding: 10px 12px;
        border-radius: 10px;
        text-align: left;
    }
    #sidebar QPushButton:hover { background-color: rgba(45, 129, 255, 0.12); }
    #sidebar QPushButton:checked { background-color: #2D81FF; color: #FFFFFF; }

    /* Content area */
    #content {
        background-color: rgba(22, 27, 34, 0.88);
        border: 1px solid rgba(240, 246, 252, 0.08);
        border-radius: 14px;
    }

    /* Cards */
    #card { background-color: rgba(22, 27, 34, 0.88); border: 1px solid rgba(240,246,252,0.08); border-radius: 14px; }
    QLabel#cardTitle { font-size: 13px; color: #9DA7B1; }
    QLabel#valueBig { font-size: 28px; font-weight: 600; color: #F0F6FC; }

    /* Common text and tables */
    QLabel { color: #E6EDF3; }
    QTextEdit {
        background: #0B1220; color: #E6EDF3; border: 1px solid rgba(240, 246, 252, 0.08); border-radius: 8px;
    }
    QTableWidget {
        background: #0B1220; color: #E6EDF3; gridline-color: rgba(240, 246, 252, 0.08);
        border: 1px solid rgba(240, 246, 252, 0.08); border-radius: 8px;
        selection-background-color: rgba(45,129,255,0.22);
        alternate-background-color: #0E1626;
    }
    QHeaderView::section { background: #111827; color: #E6EDF3; border: none; padding: 6px 8px; }

    /* Modern dropdowns */
    QComboBox {
        background: #2C3440;
        color: #ECF0F1;
        border: 1px solid rgba(240, 246, 252, 0.12);
        border-radius: 10px;
        padding: 6px 36px 6px 10px; /* space on right for arrow */
        min-height: 30px;
    }
    QComboBox:hover {
        background: #2A313D;
        border-color: rgba(240, 246, 252, 0.20);
    }
    QComboBox:focus {
        border: 1px solid #2D81FF; /* accent */
        background: #2A313D;
    }
    QComboBox:disabled {
        color: #98A1B2;
        background: #252C37;
        border-color: rgba(240, 246, 252, 0.10);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid rgba(240, 246, 252, 0.10);
        background: transparent;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }
    QComboBox::down-arrow {
        width: 12px; height: 12px;
        margin-right: 8px;
    }
    QComboBox:on { /* when popup is open */
        border-color: #2D81FF;
    }
    QComboBox QAbstractItemView {
        background: #0E1626;
        color: #ECF0F1;
        border: 1px solid rgba(240, 246, 252, 0.12);
        selection-background-color: rgba(45,129,255,0.22);
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
        min-height: 26px;
    }

    QPushButton#themeToggle { background: transparent; border: none; font-size: 16px; padding: 6px; }

    /* Inputs and primary buttons */
    QLineEdit {
        background-color: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(240, 246, 252, 0.12);
        border-radius: 10px;
        padding: 10px 12px;
        color: #E6EDF3;
        selection-background-color: #2D81FF;
    }
    QLineEdit:focus { border: 1px solid #2D81FF; }

    QPushButton {
        background-color: #2D81FF;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 8px 14px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #3B8BFF; }
    QPushButton:pressed { background-color: #1F66E5; }
    QPushButton:disabled { background-color: #2f3545; color: #98A1B2; }
    """


def _light_theme() -> str:
    return """
    QWidget { font-size: 13px; color: #1F2328; }

    QMainWindow#dashboardWindow { background-color: #F6F8FA; }
    #loginWindow { background: #F6F8FA; color: #1F2328; }

    #headerBar {
        background-color: #FFFFFF;
        border: 1px solid #D0D7DE;
        border-radius: 12px;
        padding: 10px 14px;
    }
    #headerTitleLabel { color: #24292F; font-size: 18px; font-weight: 600; }
    #headerSubtitleLabel { color: #57606A; }

    #sidebar { background-color: #FFFFFF; border-radius: 14px; border: 1px solid #D0D7DE; }
    #sidebar QLabel { color: #57606A; }
    #sidebar QPushButton { color: #24292F; background: transparent; border: none; padding: 10px 12px; border-radius: 10px; text-align: left; }
    #sidebar QPushButton:hover { background-color: #E7F0FE; }
    #sidebar QPushButton:checked { background-color: #2D81FF; color: #FFFFFF; }

    #content { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 14px; }

    #card { background-color: #FFFFFF; border: 1px solid #D0D7DE; border-radius: 14px; }
    QLabel#cardTitle { font-size: 13px; color: #6E7781; }
    QLabel#valueBig { font-size: 28px; font-weight: 700; color: #24292F; }

    QTextEdit { background: #FFFFFF; color: #1F2328; border: 1px solid #D0D7DE; border-radius: 8px; }
    QTableWidget { background: #FFFFFF; color: #1F2328; gridline-color: #D0D7DE; border: 1px solid #D0D7DE; border-radius: 8px; alternate-background-color: #F6F8FA; }
    QHeaderView::section { background: #F6F8FA; color: #1F2328; border: none; padding: 6px 8px; }

    /* Modern dropdowns */
    QComboBox {
        background: #FFFFFF;
        color: #1F2328;
        border: 1px solid #D0D7DE;
        border-radius: 10px;
        padding: 6px 36px 6px 10px;
        min-height: 30px;
    }
    QComboBox:hover {
        background: #F6F8FA;
        border-color: #C7CDD3;
    }
    QComboBox:focus {
        border: 1px solid #2D81FF;
        background: #FFFFFF;
    }
    QComboBox:disabled {
        color: #6E7781;
        background: #F6F8FA;
        border-color: #E5EAF0;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid #D0D7DE;
        background: transparent;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }
    QComboBox::down-arrow {
        width: 12px; height: 12px;
        margin-right: 8px;
    }
    QComboBox:on {
        border-color: #2D81FF;
    }
    QComboBox QAbstractItemView {
        background: #FFFFFF;
        color: #1F2328;
        border: 1px solid #D0D7DE;
        selection-background-color: rgba(45,129,255,0.18);
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
        min-height: 26px;
    }

    QPushButton#themeToggle { background: transparent; border: none; font-size: 16px; padding: 6px; }

    /* Inputs and primary buttons */
    QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #D0D7DE;
        border-radius: 10px;
        padding: 10px 12px;
        color: #1F2328;
        selection-background-color: #2D81FF;
    }
    QLineEdit:focus { border: 1px solid #2D81FF; }

    QPushButton {
        background-color: #2D81FF;
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 8px 14px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #3B8BFF; }
    QPushButton:pressed { background-color: #1F66E5; }
    QPushButton:disabled { background-color: #E5EAF0; color: #6E7781; }
    """


def app_stylesheet(theme: str) -> str:
    """Return app-wide QSS for the given theme ('dark'|'light')."""
    return _dark_theme() if theme.lower() == "dark" else _light_theme()


def dashboard_stylesheet() -> str:  # Backward-compatible alias (dark default)
    return _dark_theme()


def select_app_font() -> QFont:
    """Select a platform-available UI font to avoid aliasing warnings.

    Strategy:
    - Prefer widely available, modern sans-serif families.
    - Return the first family present on the current system.
    - Fallback to Qt default if none are found.
    """
    candidates = [
        "Noto Sans",
        "DejaVu Sans",
        "Segoe UI",
        "Helvetica Neue",
        "Helvetica",
        "Arial",
        "Tahoma",
        "Sans Serif",
    ]
    available = set(QFontDatabase.families())
    for family in candidates:
        if family in available:
            f = QFont(family)
            # Set a sensible default point size similar to previous QSS value
            f.setPointSize(10)  # roughly ~13px depending on DPI
            return f
    # Fallback to system default
    f = QFont()
    f.setPointSize(10)
    return f
