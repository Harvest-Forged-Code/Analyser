"""Shared styles for the PySide6 presentation layer.

Centralizes QSS used across the application and supports light/dark themes.
"""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase


def _dark_theme() -> str:
    return """
    /* Global */
    QWidget { font-size: 14px; color: #E5E7EB; }

    /* Window backgrounds */
    QMainWindow#dashboardWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0B1220, stop:1 #0A1425);
    }
    #loginWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0B1220, stop:1 #111827);
        color: #E5E7EB;
    }

    /* Header bar */
    #headerBar {
        background-color: rgba(21, 28, 42, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 12px 18px;
    }
    #headerTitleLabel { color: #F8FAFC; font-size: 19px; font-weight: 700; letter-spacing: 0.4px; }
    #headerSubtitleLabel { color: #94A3B8; font-size: 13px; }
    #versionChip {
        color: #C7D2FE;
        background: rgba(99, 102, 241, 0.16);
        border: 1px solid rgba(99, 102, 241, 0.32);
        border-radius: 10px;
        padding: 4px 8px;
        font-weight: 600;
    }

    /* Sidebar */
    #sidebar {
        background-color: rgba(15, 23, 42, 0.94);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    #sidebar QLabel { color: #94A3B8; font-size: 12px; font-weight: 600; letter-spacing: 0.6px; }
    #sidebar QLabel#navBrand { color: #F8FAFC; font-size: 14px; font-weight: 800; letter-spacing: 0.5px; }
    #sidebar QLabel#navTitle { color: #A5B4C3; font-size: 11px; font-weight: 700; letter-spacing: 0.9px; }
    #sidebar QPushButton {
        color: #E5E7EB;
        background: transparent;
        border: 1px solid transparent;
        padding: 10px 14px;
        border-radius: 12px;
        text-align: left;
        font-weight: 600;
    }
    #sidebar QPushButton:hover {
        background-color: rgba(99, 102, 241, 0.10);
        border-color: rgba(99, 102, 241, 0.28);
    }
    #sidebar QPushButton:checked {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
        color: #F8FAFC;
        border-color: rgba(99, 102, 241, 0.7);
        border-left: 3px solid #A5B4FC;
        padding-left: 11px;
    }

    /* Content area */
    #content {
        background-color: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 18px;
    }

    /* Cards */
    #card { background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; }
    QLabel#cardTitle { font-size: 12px; color: #94A3B8; letter-spacing: 0.4px; }
    QLabel#valueBig { font-size: 30px; font-weight: 700; color: #E5E7EB; }

    /* Common text and tables */
    QLabel { color: #E5E7EB; }
    QTextEdit {
        background: #0D162A; color: #E6EDF3; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px;
    }
    QTableWidget {
        background: #0D162A; color: #E6EDF3; gridline-color: rgba(255, 255, 255, 0.08);
        border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px;
        selection-background-color: rgba(99, 102, 241, 0.30);
        alternate-background-color: #0F1B33;
    }
    QHeaderView::section { background: #111827; color: #E6EDF3; border: none; padding: 8px 10px; font-weight: 600; }

    /* Modern dropdowns */
    QComboBox {
        background: #1E2633;
        color: #ECF0F1;
        border: 1px solid rgba(255, 255, 255, 0.10);
        border-radius: 12px;
        padding: 8px 38px 8px 12px; /* space on right for arrow */
        min-height: 34px;
    }
    QComboBox:hover {
        background: #222C3B;
        border-color: rgba(255, 255, 255, 0.18);
    }
    QComboBox:focus {
        border: 1px solid #6366F1; /* accent */
        background: #222C3B;
    }
    QComboBox:disabled {
        color: #98A1B2;
        background: #252C37;
        border-color: rgba(255, 255, 255, 0.08);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid rgba(255, 255, 255, 0.08);
        background: transparent;
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
    }
    QComboBox::down-arrow {
        width: 12px; height: 12px;
        margin-right: 8px;
    }
    QComboBox:on { /* when popup is open */
        border-color: #6366F1;
    }
    QComboBox QAbstractItemView {
        background: #0F1626;
        color: #ECF0F1;
        border: 1px solid rgba(255, 255, 255, 0.12);
        selection-background-color: rgba(99,102,241,0.30);
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
        min-height: 26px;
    }

    QPushButton#themeToggle { background: transparent; border: none; font-size: 16px; padding: 6px; color: #E5E7EB; }

    /* Inputs and primary buttons */
    QLineEdit {
        background-color: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 12px 14px;
        color: #E6EDF3;
        selection-background-color: #6366F1;
    }
    QLineEdit:focus { border: 1px solid #6366F1; }

    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 10px 16px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6D6FF3, stop:1 #4B44E0); }
    QPushButton:pressed { background: #4338CA; }
    QPushButton:disabled { background-color: #2f3545; color: #98A1B2; }
    """


def _light_theme() -> str:
    return """
    QWidget { font-size: 14px; color: #0F172A; }

    QMainWindow#dashboardWindow {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFC, stop:1 #E8EDF5);
    }
    #loginWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #F8FAFC, stop:1 #E2E8F0); color: #0F172A; }

    #headerBar {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 12px 18px;
    }
    #headerTitleLabel { color: #111827; font-size: 19px; font-weight: 700; letter-spacing: 0.2px; }
    #headerSubtitleLabel { color: #475569; font-size: 13px; }
    #versionChip {
        color: #4338CA;
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.32);
        border-radius: 10px;
        padding: 4px 8px;
        font-weight: 600;
    }

    #sidebar { background-color: #FFFFFF; border-radius: 16px; border: 1px solid #E2E8F0; }
    #sidebar QLabel { color: #475569; font-size: 12px; font-weight: 700; letter-spacing: 0.6px; }
    #sidebar QLabel#navBrand { color: #111827; font-size: 14px; font-weight: 800; letter-spacing: 0.5px; }
    #sidebar QLabel#navTitle { color: #475569; font-size: 11px; font-weight: 700; letter-spacing: 0.9px; }
    #sidebar QPushButton { color: #0F172A; background: transparent; border: 1px solid transparent; padding: 10px 14px; border-radius: 12px; text-align: left; font-weight: 600; }
    #sidebar QPushButton:hover { background-color: #EEF2FF; border-color: rgba(99, 102, 241, 0.32); }
    #sidebar QPushButton:checked { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5); color: #FFFFFF; border-color: rgba(99, 102, 241, 0.72); border-left: 3px solid #C7D2FE; padding-left: 11px; }

    #content { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; }

    #card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 18px; }
    QLabel#cardTitle { font-size: 12px; color: #6B7280; letter-spacing: 0.4px; }
    QLabel#valueBig { font-size: 30px; font-weight: 700; color: #0F172A; }

    QTextEdit { background: #FFFFFF; color: #0F172A; border: 1px solid #E2E8F0; border-radius: 10px; }
    QTableWidget { background: #FFFFFF; color: #0F172A; gridline-color: #E2E8F0; border: 1px solid #E2E8F0; border-radius: 10px; alternate-background-color: #F8FAFC; }
    QHeaderView::section { background: #F1F5F9; color: #0F172A; border: none; padding: 8px 10px; font-weight: 600; }

    /* Modern dropdowns */
    QComboBox {
        background: #FFFFFF;
        color: #0F172A;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 8px 38px 8px 12px;
        min-height: 34px;
    }
    QComboBox:hover {
        background: #F8FAFC;
        border-color: #CBD5E1;
    }
    QComboBox:focus {
        border: 1px solid #6366F1;
        background: #FFFFFF;
    }
    QComboBox:disabled {
        color: #6E7781;
        background: #F8FAFC;
        border-color: #E5EAF0;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid #E2E8F0;
        background: transparent;
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
    }
    QComboBox::down-arrow {
        width: 12px; height: 12px;
        margin-right: 8px;
    }
    QComboBox:on {
        border-color: #6366F1;
    }
    QComboBox QAbstractItemView {
        background: #FFFFFF;
        color: #0F172A;
        border: 1px solid #E2E8F0;
        selection-background-color: rgba(99,102,241,0.18);
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 6px 10px;
        min-height: 26px;
    }

    QPushButton#themeToggle { background: transparent; border: none; font-size: 16px; padding: 6px; color: #475569; }

    /* Inputs and primary buttons */
    QLineEdit {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 14px;
        color: #0F172A;
        selection-background-color: #6366F1;
    }
    QLineEdit:focus { border: 1px solid #6366F1; }

    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366F1, stop:1 #4F46E5);
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 10px 16px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6D6FF3, stop:1 #4B44E0); }
    QPushButton:pressed { background: #4338CA; }
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
