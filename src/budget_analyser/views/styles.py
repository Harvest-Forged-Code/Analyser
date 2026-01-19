"""Shared styles for the PySide6 presentation layer.

Centralizes QSS used across the application and supports light/dark themes.
"""

from __future__ import annotations

from PySide6.QtGui import QFont, QFontDatabase


def _dark_theme() -> str:
    return """
    /* Global - Professional Typography */
    QWidget {
        font-size: 14px;
        color: #E2E4F0;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Window backgrounds - Clean Black */
    QMainWindow#dashboardWindow {
        background: #000000;
    }
    #loginWindow {
        background: #000000;
        color: #E5E7EB;
    }

    /* Header bar - Subtle Design */
    #headerBar {
        background: rgba(30, 30, 35, 0.8);
        border: 1px solid rgba(100, 100, 110, 0.2);
        border-radius: 18px;
        padding: 14px 20px;
    }
    #headerTitleLabel {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: -0.3px;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    }
    #headerSubtitleLabel {
        color: #9CA3AF;
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    #versionChip {
        color: #A78BFA;
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 5px 10px;
        font-weight: 600;
        font-size: 12px;
    }

    /* Sidebar - Subtle Accent */
    #sidebar {
        background: rgba(18, 18, 20, 0.95);
        border-radius: 18px;
        border: 1px solid rgba(100, 100, 110, 0.15);
    }
    #sidebar QLabel {
        color: #9CA3AF;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    #sidebar QLabel#navBrand {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: -0.3px;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
    }
    #sidebar QLabel#navTitle {
        color: #6B7280;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }
    #sidebar QPushButton {
        color: #D1D5DB;
        background: transparent;
        border: 1px solid transparent;
        padding: 11px 16px;
        border-radius: 14px;
        text-align: left;
        font-weight: 600;
        font-size: 13px;
        min-height: 0px;
    }
    #sidebar QPushButton:hover {
        background: rgba(139, 92, 246, 0.08);
        border-color: rgba(139, 92, 246, 0.15);
        color: #FFFFFF;
    }
    #sidebar QPushButton:checked {
        background: rgba(139, 92, 246, 0.15);
        color: #FFFFFF;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-left: 3px solid #8B5CF6;
        padding-left: 13px;
        font-weight: 700;
    }

    /* Search bar in sidebar */
    #sidebarSearchBar {
        background: rgba(17, 24, 39, 0.6);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 12px;
        padding: 10px 14px;
        color: #DDD6FE;
        font-size: 13px;
    }
    #sidebarSearchBar:focus {
        border: 1px solid rgba(168, 85, 247, 0.5);
        background: rgba(17, 24, 39, 0.8);
    }
    #sidebarSearchBar::placeholder {
        color: #6B7280;
    }

    /* Toggle sidebar button */
    QPushButton#toggleSidebar {
        background: rgba(139, 92, 246, 0.15);
        border: 1px solid rgba(168, 85, 247, 0.25);
        border-radius: 12px;
        padding: 8px 10px;
        color: #C4B5FD;
        font-size: 16px;
        min-width: 36px;
        max-width: 36px;
    }
    QPushButton#toggleSidebar:hover {
        background: rgba(139, 92, 246, 0.25);
        border-color: rgba(168, 85, 247, 0.4);
        color: #E9D5FF;
    }

    /* Content area - Clean & Modern */
    #content {
        background: transparent;
        border: none;
        border-radius: 0px;
    }

    /* Cards - Premium Design */
    #card {
        background: rgba(18, 18, 20, 0.95);
        border: 1px solid rgba(60, 60, 70, 0.3);
        border-radius: 18px;
    }
    QLabel#cardTitle {
        font-size: 11px;
        color: #A78BFA;
        letter-spacing: 0.8px;
        font-weight: 600;
        text-transform: uppercase;
    }
    QLabel#valueBig {
        font-size: 32px;
        font-weight: 700;
        color: #F5F3FF;
        letter-spacing: -1px;
    }

    /* Common text and tables - Professional Look */
    QLabel {
        color: #E2E4F0;
    }
    QTextEdit {
        background: rgba(18, 18, 20, 0.9);
        color: #E9D5FF;
        border: 1px solid rgba(60, 60, 70, 0.3);
        border-radius: 12px;
        padding: 8px;
        font-size: 13px;
    }
    QTableWidget {
        background: rgba(18, 18, 20, 0.9);
        color: #E2E4F0;
        gridline-color: rgba(60, 60, 70, 0.2);
        border: 1px solid rgba(60, 60, 70, 0.3);
        border-radius: 12px;
        selection-background-color: rgba(139, 92, 246, 0.15);
        alternate-background-color: rgba(25, 25, 28, 0.5);
        font-size: 13px;
    }
    QTableWidget::item:selected {
        background: rgba(139, 92, 246, 0.15);
        color: #FFFFFF;
        border-left: 3px solid #8B5CF6;
    }
    QHeaderView::section {
        background: rgba(25, 25, 28, 0.95);
        color: #DDD6FE;
        border: none;
        padding: 10px 12px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.5px;
    }

    /* Tree Widgets - Professional Typography */
    QTreeWidget {
        background: rgba(18, 18, 20, 0.9);
        color: #E2E4F0;
        border: 1px solid rgba(60, 60, 70, 0.3);
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        selection-background-color: rgba(139, 92, 246, 0.15);
        alternate-background-color: rgba(25, 25, 28, 0.5);
        outline: none;
    }
    QTreeWidget::item {
        padding: 8px 4px;
        border: none;
        color: #E2E4F0;
    }
    QTreeWidget::item:hover {
        background: rgba(139, 92, 246, 0.08);
        border-left: 3px solid rgba(139, 92, 246, 0.3);
    }
    QTreeWidget::item:selected {
        background: rgba(139, 92, 246, 0.15);
        color: #FFFFFF;
        border-left: 3px solid #8B5CF6;
    }
    QTreeWidget::item:selected:hover {
        background: rgba(139, 92, 246, 0.20);
        border-left: 3px solid #8B5CF6;
    }
    QTreeWidget::branch {
        background: transparent;
    }

    /* Modern dropdowns - Subtle Design */
    QComboBox {
        background: rgba(18, 18, 20, 0.9);
        color: #E9D5FF;
        border: 1px solid rgba(60, 60, 70, 0.4);
        border-radius: 10px;
        padding: 4px 30px 4px 8px;
        min-height: 30px;
        font-size: 13px;
        font-weight: 500;
    }
    QComboBox:hover {
        background: rgba(18, 18, 20, 0.95);
        border-color: rgba(139, 92, 246, 0.3);
    }
    QComboBox:focus {
        border: 1px solid rgba(139, 92, 246, 0.4);
        background: rgba(18, 18, 20, 1.0);
    }
    QComboBox:disabled {
        color: #6B7280;
        background: rgba(18, 18, 20, 0.6);
        border-color: rgba(60, 60, 70, 0.3);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid rgba(60, 60, 70, 0.4);
        background: transparent;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
        margin-right: 6px;
    }
    QComboBox:on {
        border-color: rgba(139, 92, 246, 0.4);
    }
    QComboBox QAbstractItemView {
        background-color: #000000;
        color: #E2E4F0;
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 6px;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        background-color: transparent;
        color: #E2E4F0;
        padding: 8px 12px;
        min-height: 30px;
        border-radius: 8px;
        margin: 2px 4px;
    }
    QComboBox QAbstractItemView::item:hover {
        background-color: rgba(139, 92, 246, 0.1);
        color: #FFFFFF;
    }
    QComboBox QAbstractItemView::item:selected {
        background-color: rgba(139, 92, 246, 0.15);
        color: #FFFFFF;
        border-left: 3px solid #8B5CF6;
    }

    QPushButton#themeToggle {
        background: transparent;
        border: none;
        font-size: 18px;
        padding: 8px;
        color: #C4B5FD;
    }
    QPushButton#themeToggle:hover {
        color: #E9D5FF;
    }

    /* Inputs and primary buttons - Professional Design */
    QLineEdit {
        background: rgba(18, 18, 20, 0.9);
        border: 1px solid rgba(60, 60, 70, 0.4);
        border-radius: 14px;
        padding: 12px 16px;
        color: #E9D5FF;
        selection-background-color: rgba(139, 92, 246, 0.4);
        font-size: 13px;
        font-weight: 500;
    }
    QLineEdit:focus {
        border: 1px solid rgba(139, 92, 246, 0.4);
        background: rgba(18, 18, 20, 1.0);
    }
    QLineEdit::placeholder {
        color: #6B7280;
    }

    QPushButton {
        background: rgba(139, 92, 246, 0.25);
        color: #FFFFFF;
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 10px;
        padding: 6px 12px;
        min-height: 30px;
        font-weight: 700;
        letter-spacing: 0.3px;
        font-size: 13px;
    }
    QPushButton:hover {
        background: rgba(139, 92, 246, 0.35);
        border-color: rgba(139, 92, 246, 0.4);
    }
    QPushButton:pressed {
        background: rgba(139, 92, 246, 0.45);
    }
    QPushButton:disabled {
        background-color: rgba(18, 18, 20, 0.7);
        color: #6B7280;
        border-color: rgba(60, 60, 70, 0.3);
    }

    /* Scroll bars - Custom styling */
    QScrollBar:vertical {
        background: transparent;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: rgba(100, 100, 110, 0.5);
        border-radius: 6px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(139, 92, 246, 0.4);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: transparent;
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: rgba(100, 100, 110, 0.5);
        border-radius: 6px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(139, 92, 246, 0.4);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    """


def _light_theme() -> str:
    return """
    /* Global - Professional Typography */
    QWidget {
        font-size: 14px;
        color: #1E1B4B;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Window backgrounds - Clean White */
    QMainWindow#dashboardWindow {
        background: #FFFFFF;
    }
    #loginWindow {
        background: #FFFFFF;
        color: #1E1B4B;
    }

    /* Header bar - Subtle Design */
    #headerBar {
        background: rgba(248, 248, 250, 0.9);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 18px;
        padding: 14px 20px;
    }
    #headerTitleLabel {
        color: #3B0764;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: -0.3px;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
    }
    #headerSubtitleLabel {
        color: #6B21A8;
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.3px;
    }
    #versionChip {
        color: #8B5CF6;
        background: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.2);
        border-radius: 12px;
        padding: 5px 10px;
        font-weight: 600;
        font-size: 12px;
    }

    /* Sidebar - Subtle Design */
    #sidebar {
        background: rgba(248, 248, 250, 0.95);
        border-radius: 18px;
        border: 1px solid rgba(139, 92, 246, 0.12);
    }
    #sidebar QLabel {
        color: #7C3AED;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    #sidebar QLabel#navBrand {
        color: #3B0764;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: -0.3px;
        font-family: -apple-system, "SF Pro Display", "Segoe UI", sans-serif;
    }
    #sidebar QLabel#navTitle {
        color: #9333EA;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
    }
    #sidebar QPushButton {
        color: #5B21B6;
        background: transparent;
        border: 1px solid transparent;
        padding: 11px 16px;
        border-radius: 14px;
        text-align: left;
        font-weight: 600;
        font-size: 13px;
        min-height: 0px;
    }
    #sidebar QPushButton:hover {
        background: rgba(139, 92, 246, 0.08);
        border-color: rgba(139, 92, 246, 0.2);
        color: #3B0764;
    }
    #sidebar QPushButton:checked {
        background: rgba(139, 92, 246, 0.15);
        color: #3B0764;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-left: 3px solid #8B5CF6;
        padding-left: 13px;
        font-weight: 700;
    }

    /* Search bar in sidebar */
    #sidebarSearchBar {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 12px;
        padding: 10px 14px;
        color: #3B0764;
        font-size: 13px;
    }
    #sidebarSearchBar:focus {
        border: 1px solid rgba(139, 92, 246, 0.5);
        background: #FFFFFF;
    }
    #sidebarSearchBar::placeholder {
        color: #9CA3AF;
    }

    /* Toggle sidebar button */
    QPushButton#toggleSidebar {
        background: rgba(139, 92, 246, 0.1);
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 12px;
        padding: 8px 10px;
        color: #7C3AED;
        font-size: 16px;
        min-width: 36px;
        max-width: 36px;
    }
    QPushButton#toggleSidebar:hover {
        background: rgba(139, 92, 246, 0.2);
        border-color: rgba(139, 92, 246, 0.4);
        color: #6B21A8;
    }

    /* Content area - Clean & Modern */
    #content {
        background: transparent;
        border: none;
        border-radius: 0px;
    }

    /* Cards - Premium Design */
    #card {
        background: #FFFFFF;
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 18px;
    }
    QLabel#cardTitle {
        font-size: 11px;
        color: #7C3AED;
        letter-spacing: 0.8px;
        font-weight: 600;
        text-transform: uppercase;
    }
    QLabel#valueBig {
        font-size: 32px;
        font-weight: 700;
        color: #3B0764;
        letter-spacing: -1px;
    }

    /* Common text and tables - Professional Look */
    QLabel {
        color: #1E1B4B;
    }
    QTextEdit {
        background: #FFFFFF;
        color: #3B0764;
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        padding: 8px;
        font-size: 13px;
    }
    QTableWidget {
        background: #FFFFFF;
        color: #1E1B4B;
        gridline-color: rgba(139, 92, 246, 0.08);
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        selection-background-color: rgba(139, 92, 246, 0.15);
        alternate-background-color: rgba(250, 245, 255, 0.5);
        font-size: 13px;
    }
    QTableWidget::item:selected {
        background: rgba(139, 92, 246, 0.15);
        color: #3B0764;
        border-left: 3px solid #8B5CF6;
    }
    QHeaderView::section {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(233, 213, 255, 0.6), stop:1 rgba(196, 181, 253, 0.6));
        color: #5B21B6;
        border: none;
        padding: 10px 12px;
        font-weight: 700;
        font-size: 12px;
        letter-spacing: 0.5px;
    }

    /* Tree Widgets - Professional Typography */
    QTreeWidget {
        background: #FFFFFF;
        color: #1E1B4B;
        border: 1px solid rgba(139, 92, 246, 0.15);
        border-radius: 12px;
        font-size: 14px;
        font-weight: 500;
        selection-background-color: rgba(139, 92, 246, 0.15);
        alternate-background-color: rgba(250, 245, 255, 0.5);
        outline: none;
    }
    QTreeWidget::item {
        padding: 8px 4px;
        border: none;
        color: #1E1B4B;
    }
    QTreeWidget::item:hover {
        background: rgba(139, 92, 246, 0.08);
        border-left: 3px solid rgba(139, 92, 246, 0.3);
    }
    QTreeWidget::item:selected {
        background: rgba(139, 92, 246, 0.15);
        color: #3B0764;
        border-left: 3px solid #8B5CF6;
    }
    QTreeWidget::item:selected:hover {
        background: rgba(139, 92, 246, 0.20);
        border-left: 3px solid #8B5CF6;
    }
    QTreeWidget::branch {
        background: transparent;
    }

    /* Modern dropdowns - Royal Violet Theme */
    QComboBox {
        background: #FFFFFF;
        color: #3B0764;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 10px;
        padding: 4px 30px 4px 8px;
        min-height: 30px;
        font-size: 13px;
        font-weight: 500;
    }
    QComboBox:hover {
        background: rgba(250, 245, 255, 0.8);
        border-color: rgba(139, 92, 246, 0.4);
    }
    QComboBox:focus {
        border: 1px solid rgba(139, 92, 246, 0.6);
        background: #FFFFFF;
    }
    QComboBox:disabled {
        color: #9CA3AF;
        background: rgba(250, 245, 255, 0.4);
        border-color: rgba(139, 92, 246, 0.1);
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 28px;
        border-left: 1px solid rgba(139, 92, 246, 0.15);
        background: transparent;
        border-top-right-radius: 10px;
        border-bottom-right-radius: 10px;
    }
    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
        margin-right: 6px;
    }
    QComboBox:on {
        border-color: rgba(139, 92, 246, 0.6);
    }
    QComboBox QAbstractItemView {
        background: #FFFFFF;
        color: #1F2937;
        border: 1px solid rgba(139, 92, 246, 0.3);
        border-radius: 12px;
        padding: 6px;
        selection-background-color: rgba(139, 92, 246, 0.15);
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px;
        min-height: 30px;
        border-radius: 8px;
        margin: 2px 4px;
    }
    QComboBox QAbstractItemView::item:hover {
        background: rgba(139, 92, 246, 0.1);
        color: #5B21B6;
    }
    QComboBox QAbstractItemView::item:selected {
        background: rgba(139, 92, 246, 0.15);
        color: #5B21B6;
        border-left: 3px solid #8B5CF6;
    }

    QPushButton#themeToggle {
        background: transparent;
        border: none;
        font-size: 18px;
        padding: 8px;
        color: #7C3AED;
    }
    QPushButton#themeToggle:hover {
        color: #6B21A8;
    }

    /* Inputs and primary buttons - Professional Design */
    QLineEdit {
        background: #FFFFFF;
        border: 1px solid rgba(139, 92, 246, 0.25);
        border-radius: 14px;
        padding: 12px 16px;
        color: #3B0764;
        selection-background-color: rgba(139, 92, 246, 0.4);
        font-size: 13px;
        font-weight: 500;
    }
    QLineEdit:focus {
        border: 1px solid rgba(139, 92, 246, 0.5);
        background: #FFFFFF;
    }
    QLineEdit::placeholder {
        color: #9CA3AF;
    }

    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #9333EA, stop:1 #7C3AED);
        color: #FFFFFF;
        border: none;
        border-radius: 10px;
        padding: 6px 12px;
        min-height: 30px;
        font-weight: 700;
        letter-spacing: 0.3px;
        font-size: 13px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #A855F7, stop:1 #8B5CF6);
    }
    QPushButton:pressed {
        background: #7C3AED;
    }
    QPushButton:disabled {
        background-color: rgba(250, 245, 255, 0.5);
        color: #9CA3AF;
    }

    /* Scroll bars - Custom styling */
    QScrollBar:vertical {
        background: rgba(250, 245, 255, 0.6);
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 6px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: rgba(139, 92, 246, 0.5);
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    QScrollBar:horizontal {
        background: rgba(250, 245, 255, 0.6);
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }
    QScrollBar::handle:horizontal {
        background: rgba(139, 92, 246, 0.3);
        border-radius: 6px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: rgba(139, 92, 246, 0.5);
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
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
