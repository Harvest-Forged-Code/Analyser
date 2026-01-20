"""Unified Mapper Hub page (views layer).

Purpose:
    Consolidate all mapping interfaces into a single tabbed view:
    - Transaction Mapping (description -> sub-category)
    - Sub-category Mapping (sub-category -> category)
    - Cashflow Classification (category -> earnings/expenses)
    - Validation Report (mapping health check)

This provides a unified UX for all mapping operations.
"""

from __future__ import annotations

import logging
from typing import List, Callable, Any

from PySide6 import QtCore, QtWidgets

from budget_analyser.views.pages._page_base import ModernPageMixin


class ValidationReportTab(QtWidgets.QWidget):
    """Tab showing mapping validation results."""

    def __init__(
        self,
        validation_callback: Callable[[], dict] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._validation_callback = validation_callback
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 0)
        layout.setSpacing(16)

        # Refresh button
        btn_layout = QtWidgets.QHBoxLayout()
        self._refresh_btn = ModernPageMixin.create_action_button(
            "Run Validation", primary=True
        )
        self._refresh_btn.clicked.connect(self._run_validation)
        btn_layout.addWidget(self._refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Summary section
        summary_card, summary_layout = ModernPageMixin.create_card("VALIDATION SUMMARY")

        self._summary_label = QtWidgets.QLabel("Click 'Run Validation' to check your mappings.")
        self._summary_label.setWordWrap(True)
        self._summary_label.setStyleSheet("color: #6B7280; font-size: 14px;")
        summary_layout.addWidget(self._summary_label)

        layout.addWidget(summary_card)

        # Issues table
        issues_card, issues_layout = ModernPageMixin.create_card("ISSUES FOUND")

        self._issues_table = QtWidgets.QTableWidget(0, 4)
        self._issues_table.setHorizontalHeaderLabels([
            "Severity", "Type", "Message", "Details"
        ])
        self._issues_table.verticalHeader().setVisible(False)
        self._issues_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._issues_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._issues_table.horizontalHeader().setStretchLastSection(True)
        self._issues_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._issues_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._issues_table.setAlternatingRowColors(True)
        issues_layout.addWidget(self._issues_table)

        layout.addWidget(issues_card, 1)

    def _run_validation(self) -> None:
        """Run validation and update the display."""
        if self._validation_callback is None:
            self._summary_label.setText("Validation not configured.")
            return

        try:
            result = self._validation_callback()
            self._display_results(result)
        except Exception as e:
            self._summary_label.setText(f"Validation error: {e}")

    def _display_results(self, result: dict) -> None:
        """Display validation results."""
        # Update summary
        error_count = result.get("error_count", 0)
        warning_count = result.get("warning_count", 0)
        is_valid = result.get("is_valid", True)

        if is_valid:
            summary_text = "✅ No errors found. "
        else:
            summary_text = f"❌ Found {error_count} error(s). "

        if warning_count > 0:
            summary_text += f"⚠️ {warning_count} warning(s)."

        self._summary_label.setText(summary_text)

        # Update issues table
        self._issues_table.setRowCount(0)
        issues = result.get("issues", [])

        for issue in issues:
            row = self._issues_table.rowCount()
            self._issues_table.insertRow(row)

            severity = issue.get("severity", "info")
            severity_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")

            self._issues_table.setItem(
                row, 0, QtWidgets.QTableWidgetItem(f"{severity_icon} {severity.upper()}")
            )
            self._issues_table.setItem(
                row, 1, QtWidgets.QTableWidgetItem(issue.get("issue_type", ""))
            )
            self._issues_table.setItem(
                row, 2, QtWidgets.QTableWidgetItem(issue.get("message", ""))
            )

            details = issue.get("details", {})
            details_str = ", ".join(f"{k}: {v}" for k, v in details.items())
            self._issues_table.setItem(row, 3, QtWidgets.QTableWidgetItem(details_str))

        self._issues_table.resizeColumnsToContents()


class UnifiedMapperPage(QtWidgets.QWidget):
    """Unified mapper hub with tabbed interface."""

    def __init__(
        self,
        transaction_mapper_widget: QtWidgets.QWidget | None = None,
        sub_category_mapper_widget: QtWidgets.QWidget | None = None,
        cashflow_mapper_widget: QtWidgets.QWidget | None = None,
        validation_callback: Callable[[], dict] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        super().__init__()
        self._logger = logger or logging.getLogger("budget_analyser.gui")
        self._transaction_mapper = transaction_mapper_widget
        self._sub_category_mapper = sub_category_mapper_widget
        self._cashflow_mapper = cashflow_mapper_widget
        self._validation_callback = validation_callback
        self._init_ui()

    def _init_ui(self) -> None:
        # Scroll area
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        header = ModernPageMixin.create_page_header(
            title="Mapper Hub",
            subtitle="Manage all transaction categorization mappings in one place",
            icon="🗂️"
        )
        root.addWidget(header)

        # Tab widget
        self._tabs = QtWidgets.QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 12px;
                background-color: transparent;
                padding: 16px;
            }
            QTabBar::tab {
                background-color: rgba(18, 18, 20, 0.5);
                border: 1px solid rgba(60, 60, 70, 0.3);
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 4px;
                font-weight: 500;
                color: #9CA3AF;
            }
            QTabBar::tab:selected {
                background-color: transparent;
                color: #8B5CF6;
                font-weight: 600;
                border-color: rgba(139, 92, 246, 0.4);
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(139, 92, 246, 0.1);
                color: #FFFFFF;
            }
        """)

        # Add tabs
        if self._transaction_mapper:
            self._tabs.addTab(self._transaction_mapper, "📝 Transaction Mapping")
        else:
            placeholder = self._create_placeholder("Transaction Mapping")
            self._tabs.addTab(placeholder, "📝 Transaction Mapping")

        if self._sub_category_mapper:
            self._tabs.addTab(self._sub_category_mapper, "📂 Sub-category Mapping")
        else:
            placeholder = self._create_placeholder("Sub-category Mapping")
            self._tabs.addTab(placeholder, "📂 Sub-category Mapping")

        if self._cashflow_mapper:
            self._tabs.addTab(self._cashflow_mapper, "💰 Cashflow Classification")
        else:
            placeholder = self._create_placeholder("Cashflow Classification")
            self._tabs.addTab(placeholder, "💰 Cashflow Classification")

        # Validation tab
        validation_tab = ValidationReportTab(
            validation_callback=self._validation_callback
        )
        self._tabs.addTab(validation_tab, "✅ Validation Report")

        root.addWidget(self._tabs, 1)

    def _create_placeholder(self, name: str) -> QtWidgets.QWidget:
        """Create a placeholder widget for missing mapper."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        label = QtWidgets.QLabel(f"{name} not configured")
        label.setStyleSheet("color: #9CA3AF; font-size: 16px;")
        label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        return widget

    def set_current_tab(self, index: int) -> None:
        """Switch to a specific tab by index."""
        if 0 <= index < self._tabs.count():
            self._tabs.setCurrentIndex(index)

    def get_current_tab_index(self) -> int:
        """Get the current tab index."""
        return self._tabs.currentIndex()
