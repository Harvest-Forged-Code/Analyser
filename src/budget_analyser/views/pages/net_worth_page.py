"""Net Worth Page - Track assets, liabilities, and net worth."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

if TYPE_CHECKING:
    from budget_analyser.controller.budget_controller import BudgetController


class NetWorthPage(QtWidgets.QWidget):
    """Page for tracking net worth through accounts management."""

    ACCOUNT_TYPES = [
        ("checking", "Checking Account"),
        ("savings", "Savings Account"),
        ("investment", "Investment Account"),
        ("credit_card", "Credit Card"),
        ("loan", "Loan"),
        ("other", "Other"),
    ]

    def __init__(
        self,
        budget_controller: "BudgetController",
        logger: logging.Logger
    ) -> None:
        super().__init__()
        self._budget_controller = budget_controller
        self._logger = logger
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QtWidgets.QLabel("Net Worth Tracker")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Description
        desc = QtWidgets.QLabel(
            "Track your financial accounts to monitor your net worth over time. "
            "Add all your bank accounts, investments, credit cards, and loans."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Net Worth Summary Cards
        summary_layout = QtWidgets.QHBoxLayout()
        
        self._assets_card = self._create_summary_card("Total Assets", "$0.00", "#6bcb77")
        summary_layout.addWidget(self._assets_card)
        
        self._liabilities_card = self._create_summary_card("Total Liabilities", "$0.00", "#ff6b6b")
        summary_layout.addWidget(self._liabilities_card)
        
        self._net_worth_card = self._create_summary_card("Net Worth", "$0.00", "#4d96ff")
        summary_layout.addWidget(self._net_worth_card)
        
        layout.addLayout(summary_layout)

        # Main content splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel - Accounts List
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        # Assets section
        assets_header = QtWidgets.QLabel("Assets")
        assets_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #6bcb77;")
        left_layout.addWidget(assets_header)

        self._assets_table = self._create_accounts_table()
        left_layout.addWidget(self._assets_table)

        # Liabilities section
        liab_header = QtWidgets.QLabel("Liabilities")
        liab_header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff6b6b;")
        left_layout.addWidget(liab_header)

        self._liabilities_table = self._create_accounts_table()
        left_layout.addWidget(self._liabilities_table)

        splitter.addWidget(left_panel)

        # Right panel - Add/Edit Account Form
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        form_group = QtWidgets.QGroupBox("Add New Account")
        form_layout = QtWidgets.QFormLayout(form_group)

        self._name_edit = QtWidgets.QLineEdit()
        self._name_edit.setPlaceholderText("e.g., Chase Checking, Fidelity 401k")
        form_layout.addRow("Account Name:", self._name_edit)

        self._type_combo = QtWidgets.QComboBox()
        for type_id, type_name in self.ACCOUNT_TYPES:
            self._type_combo.addItem(type_name, type_id)
        form_layout.addRow("Account Type:", self._type_combo)

        self._balance_spin = QtWidgets.QDoubleSpinBox()
        self._balance_spin.setRange(-10000000, 10000000)
        self._balance_spin.setDecimals(2)
        self._balance_spin.setPrefix("$ ")
        self._balance_spin.setValue(0)
        form_layout.addRow("Current Balance:", self._balance_spin)

        self._notes_edit = QtWidgets.QTextEdit()
        self._notes_edit.setMaximumHeight(80)
        self._notes_edit.setPlaceholderText("Optional notes about this account...")
        form_layout.addRow("Notes:", self._notes_edit)

        btn_layout = QtWidgets.QHBoxLayout()
        self._add_btn = QtWidgets.QPushButton("Add Account")
        self._add_btn.setStyleSheet("background-color: #6bcb77; color: white; padding: 8px 16px;")
        self._add_btn.clicked.connect(self._on_add_account)
        btn_layout.addWidget(self._add_btn)

        self._clear_btn = QtWidgets.QPushButton("Clear Form")
        self._clear_btn.clicked.connect(self._clear_form)
        btn_layout.addWidget(self._clear_btn)
        form_layout.addRow("", btn_layout)

        right_layout.addWidget(form_group)

        # Quick Update Section
        update_group = QtWidgets.QGroupBox("Quick Balance Update")
        update_layout = QtWidgets.QFormLayout(update_group)

        self._update_account_combo = QtWidgets.QComboBox()
        update_layout.addRow("Select Account:", self._update_account_combo)

        self._update_balance_spin = QtWidgets.QDoubleSpinBox()
        self._update_balance_spin.setRange(-10000000, 10000000)
        self._update_balance_spin.setDecimals(2)
        self._update_balance_spin.setPrefix("$ ")
        update_layout.addRow("New Balance:", self._update_balance_spin)

        update_btn = QtWidgets.QPushButton("Update Balance")
        update_btn.setStyleSheet("background-color: #4d96ff; color: white; padding: 8px 16px;")
        update_btn.clicked.connect(self._on_update_balance)
        update_layout.addRow("", update_btn)

        right_layout.addWidget(update_group)

        # Tips section
        tips_group = QtWidgets.QGroupBox("💡 Tips")
        tips_layout = QtWidgets.QVBoxLayout(tips_group)
        tips_text = QtWidgets.QLabel(
            "• Update balances monthly for accurate tracking\n"
            "• Include all accounts: checking, savings, investments\n"
            "• Don't forget credit cards and loans as liabilities\n"
            "• Net Worth = Assets - Liabilities\n"
            "• Aim to increase net worth over time"
        )
        tips_text.setStyleSheet("color: #666;")
        tips_layout.addWidget(tips_text)
        right_layout.addWidget(tips_group)

        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter)

    def _create_summary_card(self, title: str, value: str, color: str) -> QtWidgets.QFrame:
        """Create a summary card widget."""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 14px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card

    def _create_accounts_table(self) -> QtWidgets.QTableWidget:
        """Create an accounts table widget."""
        table = QtWidgets.QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Account", "Type", "Balance", "Actions"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.setMaximumHeight(200)
        return table

    def _load_data(self) -> None:
        """Load all account data."""
        self._refresh_tables()
        self._refresh_summary()
        self._refresh_account_combo()

    def _refresh_tables(self) -> None:
        """Refresh the assets and liabilities tables."""
        accounts = self._budget_controller.get_all_accounts()
        
        asset_types = {"checking", "savings", "investment", "other"}
        liability_types = {"credit_card", "loan"}
        
        assets = [a for a in accounts if a.account_type in asset_types]
        liabilities = [a for a in accounts if a.account_type in liability_types]
        
        self._populate_table(self._assets_table, assets)
        self._populate_table(self._liabilities_table, liabilities)

    def _populate_table(self, table: QtWidgets.QTableWidget, accounts: list) -> None:
        """Populate a table with accounts."""
        table.setRowCount(len(accounts))
        
        type_names = dict(self.ACCOUNT_TYPES)
        
        for row, account in enumerate(accounts):
            # Account name
            name_item = QtWidgets.QTableWidgetItem(account.name)
            name_item.setFlags(name_item.flags() & ~QtCore.Qt.ItemIsEditable)
            name_item.setData(QtCore.Qt.UserRole, account.id)
            table.setItem(row, 0, name_item)
            
            # Type
            type_item = QtWidgets.QTableWidgetItem(type_names.get(account.account_type, account.account_type))
            type_item.setFlags(type_item.flags() & ~QtCore.Qt.ItemIsEditable)
            table.setItem(row, 1, type_item)
            
            # Balance
            balance_item = QtWidgets.QTableWidgetItem(f"${account.balance:,.2f}")
            balance_item.setFlags(balance_item.flags() & ~QtCore.Qt.ItemIsEditable)
            balance_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            table.setItem(row, 2, balance_item)
            
            # Delete button
            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(lambda checked, aid=account.id, name=account.name: self._on_delete_account(aid, name))
            table.setCellWidget(row, 3, delete_btn)

    def _refresh_summary(self) -> None:
        """Refresh the net worth summary cards."""
        summary = self._budget_controller.get_net_worth_summary()
        
        # Update assets card
        assets_label = self._assets_card.findChild(QtWidgets.QLabel, "value_label")
        if assets_label:
            assets_label.setText(f"${summary.total_assets:,.2f}")
        
        # Update liabilities card
        liab_label = self._liabilities_card.findChild(QtWidgets.QLabel, "value_label")
        if liab_label:
            liab_label.setText(f"${summary.total_liabilities:,.2f}")
        
        # Update net worth card
        nw_label = self._net_worth_card.findChild(QtWidgets.QLabel, "value_label")
        if nw_label:
            nw_label.setText(f"${summary.net_worth:,.2f}")

    def _refresh_account_combo(self) -> None:
        """Refresh the account dropdown for quick updates."""
        self._update_account_combo.clear()
        accounts = self._budget_controller.get_all_accounts()
        
        for account in accounts:
            self._update_account_combo.addItem(
                f"{account.name} (${account.balance:,.2f})",
                account.id
            )

    def _clear_form(self) -> None:
        """Clear the add account form."""
        self._name_edit.clear()
        self._type_combo.setCurrentIndex(0)
        self._balance_spin.setValue(0)
        self._notes_edit.clear()

    def _on_add_account(self) -> None:
        """Add a new account."""
        name = self._name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter an account name."
            )
            return
        
        account_type = self._type_combo.currentData()
        balance = self._balance_spin.value()
        notes = self._notes_edit.toPlainText().strip()
        
        try:
            self._budget_controller.add_account(name, account_type, balance, notes)
            self._logger.info("Added account: %s (%s) = $%.2f", name, account_type, balance)
            
            self._clear_form()
            self._load_data()
            
            QtWidgets.QMessageBox.information(
                self, "Success", f"Account '{name}' added successfully!"
            )
        except Exception as e:
            self._logger.error("Failed to add account: %s", e)
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Failed to add account: {e}"
            )

    def _on_update_balance(self) -> None:
        """Update an account's balance."""
        account_id = self._update_account_combo.currentData()
        if account_id is None:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please select an account to update."
            )
            return
        
        new_balance = self._update_balance_spin.value()
        
        if self._budget_controller.update_account_balance(account_id, new_balance):
            self._logger.info("Updated account %d balance to $%.2f", account_id, new_balance)
            self._load_data()
            QtWidgets.QMessageBox.information(
                self, "Success", "Balance updated successfully!"
            )
        else:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Failed to update balance."
            )

    def _on_delete_account(self, account_id: int, account_name: str) -> None:
        """Delete an account."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{account_name}'?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            if self._budget_controller.delete_account(account_id):
                self._logger.info("Deleted account: %s", account_name)
                self._load_data()
            else:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Failed to delete account."
                )
