"""Shared styles for the PySide6 presentation layer.

This module centralizes QSS used across the Dashboard to keep visuals
consistent and easy to tune.
"""

from __future__ import annotations


def dashboard_stylesheet() -> str:
    """Return the QSS for the Dashboard shell and common widgets.

    Scope:
        - QMainWindow#dashboardWindow
        - #headerBar, #sidebar, #content containers
        - Buttons inside sidebar
        - Common tables and labels
    """
    return (
        """
        QMainWindow#dashboardWindow { background-color: #0F172A; }

        /* Header bar */
        #headerBar {
            background-color: rgba(22, 27, 34, 0.88);
            border: 1px solid rgba(240, 246, 252, 0.08);
            border-radius: 12px;
            padding: 10px 14px;
        }
        #headerTitleLabel {
            color: #F0F6FC;
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 0.3px;
        }
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
        #sidebar QPushButton:checked {
            background-color: #2D81FF;
            color: #FFFFFF;
        }

        /* Content area */
        #content {
            background-color: rgba(22, 27, 34, 0.88);
            border: 1px solid rgba(240, 246, 252, 0.08);
            border-radius: 14px;
        }

        /* Common text and tables */
        QLabel { color: #E6EDF3; }
        QTextEdit {
            background: #0B1220;
            color: #E6EDF3;
            border: 1px solid rgba(240, 246, 252, 0.08);
            border-radius: 8px;
        }
        QTableWidget {
            background: #0B1220;
            color: #E6EDF3;
            gridline-color: rgba(240, 246, 252, 0.08);
            border: 1px solid rgba(240, 246, 252, 0.08);
            border-radius: 8px;
        }
        QHeaderView::section {
            background: #111827;
            color: #E6EDF3;
            border: none;
            padding: 6px 8px;
        }
        QTableWidget::item:selected { background: rgba(45, 129, 255, 0.22); }
        """
    )
