"""Recurring Transactions Page - Detect and manage recurring expenses."""

from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

if TYPE_CHECKING:
    from budget_analyser.controller.budget_controller import BudgetController
    from budget_analyser.controller.controllers import MonthlyReports


class RecurringPage(QtWidgets.QWidget):
    """Page for detecting and managing recurring transactions."""

    FREQUENCIES = [
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("yearly", "Yearly"),
    ]

    def __init__(
        self,
        reports: List["MonthlyReports"],
        budget_controller: "BudgetController",
        logger: logging.Logger
    ) -> None:
        super().__init__()
        self._reports = reports
        self._budget_controller = budget_controller
        self._logger = logger
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QtWidgets.QLabel("Recurring Transactions")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Description
        desc = QtWidgets.QLabel(
            "Track and manage recurring expenses like subscriptions, rent, and utilities. "
            "Auto-detect patterns in your transactions and get alerts for unusual changes."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Summary Cards Row
        cards_layout = QtWidgets.QHBoxLayout()

        self._monthly_card = self._create_summary_card("Monthly Fixed Expenses", "$0.00", "#ff6b6b")
        cards_layout.addWidget(self._monthly_card)

        self._yearly_card = self._create_summary_card("Yearly Projection", "$0.00", "#ffd93d")
        cards_layout.addWidget(self._yearly_card)

        self._count_card = self._create_summary_card("Tracked Items", "0", "#4d96ff")
        cards_layout.addWidget(self._count_card)

        layout.addLayout(cards_layout)

        # Main content splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel - Recurring Transactions List
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # Tracked recurring transactions
        tracked_header = QtWidgets.QLabel("Tracked Recurring Expenses")
        tracked_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(tracked_header)

        self._recurring_table = QtWidgets.QTableWidget()
        self._recurring_table.setColumnCount(5)
        self._recurring_table.setHorizontalHeaderLabels([
            "Description", "Amount", "Frequency", "Category", "Actions"
        ])
        self._recurring_table.horizontalHeader().setStretchLastSection(True)
        self._recurring_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for col in range(1, 4):
            self._recurring_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._recurring_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._recurring_table.setAlternatingRowColors(True)
        left_layout.addWidget(self._recurring_table)

        # Anomalies section
        anomalies_header = QtWidgets.QLabel("⚠️ Anomaly Alerts")
        anomalies_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b6b;")
        left_layout.addWidget(anomalies_header)

        self._anomalies_list = QtWidgets.QListWidget()
        self._anomalies_list.setMaximumHeight(120)
        self._anomalies_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ff6b6b;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
        """)
        left_layout.addWidget(self._anomalies_list)

        splitter.addWidget(left_panel)

        # Right panel - Add/Detect
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Auto-detect section
        detect_group = QtWidgets.QGroupBox("🔍 Auto-Detect Recurring")
        detect_layout = QtWidgets.QVBoxLayout(detect_group)

        detect_desc = QtWidgets.QLabel(
            "Scan your transaction history to find potential recurring expenses."
        )
        detect_desc.setWordWrap(True)
        detect_desc.setStyleSheet("color: #666;")
        detect_layout.addWidget(detect_desc)

        detect_btn = QtWidgets.QPushButton("Detect Recurring Transactions")
        detect_btn.setStyleSheet("background-color: #4d96ff; color: white; padding: 10px;")
        detect_btn.clicked.connect(self._on_detect_recurring)
        detect_layout.addWidget(detect_btn)

        self._detected_list = QtWidgets.QListWidget()
        self._detected_list.setMaximumHeight(150)
        self._detected_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        detect_layout.addWidget(self._detected_list)

        add_detected_btn = QtWidgets.QPushButton("Add Selected to Tracking")
        add_detected_btn.setStyleSheet("background-color: #6bcb77; color: white; padding: 8px;")
        add_detected_btn.clicked.connect(self._on_add_detected)
        detect_layout.addWidget(add_detected_btn)

        right_layout.addWidget(detect_group)

        # Manual add section
        add_group = QtWidgets.QGroupBox("➕ Add Manually")
        add_layout = QtWidgets.QFormLayout(add_group)

        self._desc_edit = QtWidgets.QLineEdit()
        self._desc_edit.setPlaceholderText("e.g., Netflix, Rent, Electric Bill")
        add_layout.addRow("Description:", self._desc_edit)

        self._amount_spin = QtWidgets.QDoubleSpinBox()
        self._amount_spin.setRange(0, 100000)
        self._amount_spin.setDecimals(2)
        self._amount_spin.setPrefix("$ ")
        self._amount_spin.setValue(0)
        add_layout.addRow("Expected Amount:", self._amount_spin)

        self._freq_combo = QtWidgets.QComboBox()
        for freq_id, freq_name in self.FREQUENCIES:
            self._freq_combo.addItem(freq_name, freq_id)
        self._freq_combo.setCurrentIndex(1)  # Default to monthly
        add_layout.addRow("Frequency:", self._freq_combo)

        self._category_edit = QtWidgets.QLineEdit()
        self._category_edit.setPlaceholderText("e.g., Subscriptions, Utilities")
        add_layout.addRow("Category:", self._category_edit)

        add_btn = QtWidgets.QPushButton("Add Recurring")
        add_btn.setStyleSheet("background-color: #6bcb77; color: white; padding: 8px;")
        add_btn.clicked.connect(self._on_add_recurring)
        add_layout.addRow("", add_btn)

        right_layout.addWidget(add_group)

        # Tips section
        tips_group = QtWidgets.QGroupBox("💡 Tips")
        tips_layout = QtWidgets.QVBoxLayout(tips_group)
        tips_text = QtWidgets.QLabel(
            "• Track subscriptions to avoid forgotten charges\n"
            "• Review recurring expenses quarterly\n"
            "• Cancel unused subscriptions to save money\n"
            "• Set alerts for price increases\n"
            "• Use this to predict next month's fixed costs"
        )
        tips_text.setStyleSheet("color: #666;")
        tips_layout.addWidget(tips_text)
        right_layout.addWidget(tips_group)

        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([550, 400])

        layout.addWidget(splitter)

    def _create_summary_card(self, title: str, value: str, color: str) -> QtWidgets.QFrame:
        """Create a summary card widget."""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)

        layout = QtWidgets.QVBoxLayout(card)

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)

        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(value_label)

        return card

    def _load_data(self) -> None:
        """Load all data."""
        self._refresh_table()
        self._refresh_summary()
        self._refresh_anomalies()

    def _refresh_table(self) -> None:
        """Refresh the recurring transactions table."""
        recurring = self._budget_controller.get_all_recurring_transactions(active_only=True)
        self._recurring_table.setRowCount(len(recurring))

        freq_names = dict(self.FREQUENCIES)

        for row, rec in enumerate(recurring):
            # Description
            desc_item = QtWidgets.QTableWidgetItem(rec.description)
            desc_item.setFlags(desc_item.flags() & ~QtCore.Qt.ItemIsEditable)
            desc_item.setData(QtCore.Qt.UserRole, rec.id)
            self._recurring_table.setItem(row, 0, desc_item)

            # Amount
            amount_item = QtWidgets.QTableWidgetItem(f"${rec.expected_amount:,.2f}")
            amount_item.setFlags(amount_item.flags() & ~QtCore.Qt.ItemIsEditable)
            amount_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._recurring_table.setItem(row, 1, amount_item)

            # Frequency
            freq_item = QtWidgets.QTableWidgetItem(freq_names.get(rec.frequency, rec.frequency))
            freq_item.setFlags(freq_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._recurring_table.setItem(row, 2, freq_item)

            # Category
            cat_item = QtWidgets.QTableWidgetItem(rec.category or "-")
            cat_item.setFlags(cat_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._recurring_table.setItem(row, 3, cat_item)

            # Delete button
            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(
                lambda checked, rid=rec.id, desc=rec.description: self._on_delete_recurring(rid, desc)
            )
            self._recurring_table.setCellWidget(row, 4, delete_btn)

    def _refresh_summary(self) -> None:
        """Refresh the summary cards."""
        expenses_df = self._get_all_expenses()
        summary = self._budget_controller.get_recurring_summary(expenses_df)

        # Update monthly card
        monthly_label = self._monthly_card.findChild(QtWidgets.QLabel, "value_label")
        if monthly_label:
            monthly_label.setText(f"${summary['monthly_total']:,.2f}")

        # Update yearly card
        yearly_label = self._yearly_card.findChild(QtWidgets.QLabel, "value_label")
        if yearly_label:
            yearly_label.setText(f"${summary['yearly_projection']:,.2f}")

        # Update count card
        count_label = self._count_card.findChild(QtWidgets.QLabel, "value_label")
        if count_label:
            count_label.setText(str(summary['count']))

    def _refresh_anomalies(self) -> None:
        """Refresh the anomalies list."""
        self._anomalies_list.clear()

        expenses_df = self._get_all_expenses()
        anomalies = self._budget_controller.check_recurring_anomalies(expenses_df)

        if not anomalies:
            item = QtWidgets.QListWidgetItem("✓ No anomalies detected")
            item.setForeground(QtGui.QColor("#6bcb77"))
            self._anomalies_list.addItem(item)
            return

        for anomaly in anomalies:
            text = (
                f"⚠️ {anomaly['description']}: "
                f"Expected ${anomaly['expected']:,.2f}, "
                f"Actual ${anomaly['actual']:,.2f} "
                f"({anomaly['difference_percent']:.1f}% change)"
            )
            item = QtWidgets.QListWidgetItem(text)
            item.setForeground(QtGui.QColor("#ff6b6b"))
            self._anomalies_list.addItem(item)

    def _get_all_expenses(self) -> "pd.DataFrame":
        """Get all expenses from reports."""
        import pandas as pd

        all_expenses = []
        for mr in self._reports:
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                all_expenses.append(mr.expenses)

        if not all_expenses:
            return pd.DataFrame()

        return pd.concat(all_expenses, ignore_index=True)

    def _on_detect_recurring(self) -> None:
        """Detect recurring transactions from history."""
        self._detected_list.clear()

        expenses_df = self._get_all_expenses()
        if expenses_df.empty:
            QtWidgets.QMessageBox.information(
                self, "No Data", "No transaction data available for detection."
            )
            return

        detected = self._budget_controller.detect_recurring_transactions(expenses_df)

        if not detected:
            QtWidgets.QMessageBox.information(
                self, "No Patterns Found",
                "No recurring patterns detected in your transactions."
            )
            return

        for item in detected:
            text = f"{item['description']} - ${item['avg_amount']:,.2f} ({item['occurrences']} times)"
            list_item = QtWidgets.QListWidgetItem(text)
            list_item.setData(QtCore.Qt.UserRole, item)
            self._detected_list.addItem(list_item)

        self._logger.info("Detected %d potential recurring transactions", len(detected))

    def _on_add_detected(self) -> None:
        """Add selected detected items to tracking."""
        selected = self._detected_list.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(
                self, "No Selection", "Please select items to add."
            )
            return

        added = 0
        for item in selected:
            data = item.data(QtCore.Qt.UserRole)
            if data:
                self._budget_controller.add_recurring_transaction(
                    description=data['description'],
                    expected_amount=data['avg_amount'],
                    frequency="monthly",
                    category=data.get('category', ''),
                    sub_category=data.get('sub_category', '')
                )
                added += 1

        self._logger.info("Added %d recurring transactions from detection", added)
        self._detected_list.clear()
        self._load_data()

        QtWidgets.QMessageBox.information(
            self, "Success", f"Added {added} recurring transaction(s) to tracking!"
        )

    def _on_add_recurring(self) -> None:
        """Add a recurring transaction manually."""
        description = self._desc_edit.text().strip()
        if not description:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a description."
            )
            return

        amount = self._amount_spin.value()
        if amount <= 0:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a valid amount."
            )
            return

        frequency = self._freq_combo.currentData()
        category = self._category_edit.text().strip()

        self._budget_controller.add_recurring_transaction(
            description=description,
            expected_amount=amount,
            frequency=frequency,
            category=category
        )

        self._logger.info("Added recurring: %s = $%.2f (%s)", description, amount, frequency)

        # Clear form
        self._desc_edit.clear()
        self._amount_spin.setValue(0)
        self._category_edit.clear()

        self._load_data()

        QtWidgets.QMessageBox.information(
            self, "Success", f"Recurring transaction '{description}' added!"
        )

    def _on_delete_recurring(self, recurring_id: int, description: str) -> None:
        """Delete a recurring transaction."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{description}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self._budget_controller.delete_recurring_transaction(recurring_id):
                self._logger.info("Deleted recurring: %s", description)
                self._load_data()
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Failed to delete recurring transaction."
                )
