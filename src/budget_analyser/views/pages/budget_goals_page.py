"""Budget Goals Page - Set and manage budget limits and earnings expectations."""

from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

if TYPE_CHECKING:
    from budget_analyser.controller.budget_controller import BudgetController, BudgetProgress
    from budget_analyser.controller.controllers import MonthlyReports


class BudgetGoalsPage(QtWidgets.QWidget):
    """Page for managing budget goals and viewing progress."""

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

        header = QtWidgets.QLabel("Budget Goals")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        desc = QtWidgets.QLabel(
            "Set monthly spending limits and expected earnings. "
            "Track progress separately for expenses and earnings."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        tabs = QtWidgets.QTabWidget()
        layout.addWidget(tabs)

        # ---------------- Expenses Tab ----------------
        expenses_tab = QtWidgets.QWidget()
        exp_layout = QtWidgets.QVBoxLayout(expenses_tab)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.setSpacing(12)

        exp_month_layout = QtWidgets.QHBoxLayout()
        exp_month_layout.addWidget(QtWidgets.QLabel("View Progress for:"))
        self._month_combo = QtWidgets.QComboBox()
        self._month_combo.setMinimumWidth(150)
        self._month_combo.currentIndexChanged.connect(self._on_month_changed)
        exp_month_layout.addWidget(self._month_combo)
        exp_month_layout.addStretch()
        exp_layout.addLayout(exp_month_layout)

        exp_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: Expense budgets list and form
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        left_header = QtWidgets.QLabel("Budget Limits")
        left_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(left_header)

        self._budgets_table = QtWidgets.QTableWidget()
        self._budgets_table.setColumnCount(4)
        self._budgets_table.setHorizontalHeaderLabels(["Category", "Month", "Monthly Limit", "Actions"])
        self._budgets_table.horizontalHeader().setStretchLastSection(True)
        self._budgets_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self._budgets_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self._budgets_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self._budgets_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._budgets_table.setAlternatingRowColors(True)
        left_layout.addWidget(self._budgets_table)

        form_group = QtWidgets.QGroupBox("Add/Update Budget")
        form_layout = QtWidgets.QFormLayout(form_group)

        self._category_combo = QtWidgets.QComboBox()
        self._category_combo.setEditable(True)
        self._category_combo.setMinimumWidth(200)
        form_layout.addRow("Category:", self._category_combo)

        self._budget_month_combo = QtWidgets.QComboBox()
        self._budget_month_combo.setEditable(True)
        form_layout.addRow("Month (YYYY-MM or ALL):", self._budget_month_combo)

        self._limit_spin = QtWidgets.QDoubleSpinBox()
        self._limit_spin.setRange(0, 1000000)
        self._limit_spin.setDecimals(2)
        self._limit_spin.setPrefix("$ ")
        self._limit_spin.setValue(500)
        form_layout.addRow("Monthly Limit:", self._limit_spin)

        btn_layout = QtWidgets.QHBoxLayout()
        self._save_btn = QtWidgets.QPushButton("Save Budget")
        self._save_btn.clicked.connect(self._on_save_budget)
        btn_layout.addWidget(self._save_btn)
        form_layout.addRow("", btn_layout)

        left_layout.addWidget(form_group)
        exp_splitter.addWidget(left_panel)

        # Right: Expense progress
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        right_header = QtWidgets.QLabel("Budget Progress")
        right_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        right_layout.addWidget(right_header)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)

        self._progress_widget = QtWidgets.QWidget()
        self._progress_layout = QtWidgets.QVBoxLayout(self._progress_widget)
        self._progress_layout.setAlignment(QtCore.Qt.AlignTop)
        scroll.setWidget(self._progress_widget)
        right_layout.addWidget(scroll)

        self._summary_label = QtWidgets.QLabel()
        self._summary_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 10px; border-radius: 5px;"
        )
        right_layout.addWidget(self._summary_label)

        exp_splitter.addWidget(right_panel)
        exp_splitter.setSizes([400, 500])

        exp_layout.addWidget(exp_splitter)
        tabs.addTab(expenses_tab, "Expenses")

        # ---------------- Earnings Tab ----------------
        earnings_tab = QtWidgets.QWidget()
        earn_layout = QtWidgets.QVBoxLayout(earnings_tab)
        earn_layout.setContentsMargins(0, 0, 0, 0)
        earn_layout.setSpacing(12)

        earn_month_layout = QtWidgets.QHBoxLayout()
        earn_month_layout.addWidget(QtWidgets.QLabel("View Earnings Progress for:"))
        self._earnings_progress_month_combo = QtWidgets.QComboBox()
        self._earnings_progress_month_combo.setMinimumWidth(150)
        self._earnings_progress_month_combo.currentIndexChanged.connect(self._on_earnings_month_changed)
        earn_month_layout.addWidget(self._earnings_progress_month_combo)
        earn_month_layout.addStretch()
        earn_layout.addLayout(earn_month_layout)

        earn_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left: Earnings expectations table and form
        earn_left = QtWidgets.QWidget()
        earn_left_layout = QtWidgets.QVBoxLayout(earn_left)
        earn_left_layout.setContentsMargins(0, 0, 10, 0)

        earnings_header = QtWidgets.QLabel("Earnings Expectations")
        earnings_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        earn_left_layout.addWidget(earnings_header)

        self._earnings_table = QtWidgets.QTableWidget()
        self._earnings_table.setColumnCount(4)
        self._earnings_table.setHorizontalHeaderLabels(["Sub-category", "Month", "Expected", "Actions"])
        self._earnings_table.horizontalHeader().setStretchLastSection(True)
        self._earnings_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self._earnings_table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self._earnings_table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self._earnings_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._earnings_table.setAlternatingRowColors(True)
        earn_left_layout.addWidget(self._earnings_table)

        earn_form_group = QtWidgets.QGroupBox("Add/Update Expected Earnings")
        earn_form_layout = QtWidgets.QFormLayout(earn_form_group)

        self._earnings_sub_combo = QtWidgets.QComboBox()
        self._earnings_sub_combo.setEditable(True)
        self._earnings_sub_combo.setMinimumWidth(200)
        earn_form_layout.addRow("Sub-category:", self._earnings_sub_combo)

        self._earnings_month_combo = QtWidgets.QComboBox()
        self._earnings_month_combo.setEditable(True)
        earn_form_layout.addRow("Month (YYYY-MM or ALL):", self._earnings_month_combo)

        self._earnings_expected_spin = QtWidgets.QDoubleSpinBox()
        self._earnings_expected_spin.setRange(0, 1000000)
        self._earnings_expected_spin.setDecimals(2)
        self._earnings_expected_spin.setPrefix("$ ")
        self._earnings_expected_spin.setValue(500)
        earn_form_layout.addRow("Expected Amount:", self._earnings_expected_spin)

        earn_btn_layout = QtWidgets.QHBoxLayout()
        self._earnings_save_btn = QtWidgets.QPushButton("Save Expected")
        self._earnings_save_btn.clicked.connect(self._on_save_earnings_goal)
        earn_btn_layout.addWidget(self._earnings_save_btn)
        earn_form_layout.addRow("", earn_btn_layout)

        earn_left_layout.addWidget(earn_form_group)
        earn_splitter.addWidget(earn_left)

        # Right: Earnings progress
        earn_right = QtWidgets.QWidget()
        earn_right_layout = QtWidgets.QVBoxLayout(earn_right)
        earn_right_layout.setContentsMargins(10, 0, 0, 0)

        earnings_prog_header = QtWidgets.QLabel("Earnings Progress")
        earnings_prog_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        earn_right_layout.addWidget(earnings_prog_header)

        self._earnings_progress_table = QtWidgets.QTableWidget()
        self._earnings_progress_table.setColumnCount(5)
        self._earnings_progress_table.setHorizontalHeaderLabels([
            "Sub-category", "Actual", "Expected", "Diff", "Diff %"
        ])
        self._earnings_progress_table.horizontalHeader().setStretchLastSection(True)
        self._earnings_progress_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for col in range(1, 5):
            self._earnings_progress_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._earnings_progress_table.setAlternatingRowColors(True)
        self._earnings_progress_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        earn_right_layout.addWidget(self._earnings_progress_table)

        self._earnings_summary_label = QtWidgets.QLabel()
        self._earnings_summary_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 10px; border-radius: 5px;"
        )
        earn_right_layout.addWidget(self._earnings_summary_label)

        earn_splitter.addWidget(earn_right)
        earn_splitter.setSizes([400, 500])

        earn_layout.addWidget(earn_splitter)
        tabs.addTab(earnings_tab, "Earnings")

    def _populate_months(self) -> None:
        """Populate month selectors from available data (includes ALL)."""
        months = set()
        for mr in self._reports:
            if hasattr(mr.month, 'strftime'):
                months.add(mr.month.strftime("%Y-%m"))
        self._months = sorted(months)

        def _set_month_options(combo: QtWidgets.QComboBox) -> None:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("ALL", "ALL")
            for m in self._months:
                combo.addItem(m, m)
            # Default to latest month if available, else ALL
            if self._months:
                combo.setCurrentIndex(combo.count() - 1)
            else:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

        _set_month_options(self._month_combo)
        _set_month_options(self._budget_month_combo)
        _set_month_options(self._earnings_month_combo)
        _set_month_options(self._earnings_progress_month_combo)

    def _populate_categories(self) -> None:
        """Populate category dropdown from existing data."""
        self._category_combo.clear()
        categories = set()
        
        for mr in self._reports:
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                if 'category' in mr.expenses.columns:
                    categories.update(mr.expenses['category'].dropna().unique())
        
        # Add standard categories
        standard = ["Needs", "Flexible", "Luxuries", "Savings", "Investments"]
        categories.update(standard)
        
        for cat in sorted(categories):
            if cat:
                self._category_combo.addItem(cat)

    def _populate_earnings_sub_categories(self) -> None:
        """Populate earnings sub-category dropdown from data and saved goals."""
        self._earnings_sub_combo.clear()
        subs = set()
        for mr in self._reports:
            if hasattr(mr, 'earnings') and not mr.earnings.empty:
                if 'sub_category' in mr.earnings.columns:
                    subs.update(mr.earnings['sub_category'].dropna().unique())
        try:
            for goal in self._budget_controller.get_all_earnings_goals():
                if goal.sub_category:
                    subs.add(goal.sub_category)
        except Exception:
            pass
        for sub in sorted(subs):
            self._earnings_sub_combo.addItem(str(sub))

    def _load_data(self) -> None:
        """Load all data."""
        self._populate_months()
        self._populate_categories()
        self._populate_earnings_sub_categories()
        self._refresh_budgets_table()
        self._refresh_progress()
        self._refresh_earnings_goals_table()
        self._refresh_earnings_progress()

    def _refresh_budgets_table(self) -> None:
        """Refresh the budget goals table."""
        budgets = self._budget_controller.get_all_budgets()
        self._budgets_table.setRowCount(len(budgets))

        for row, budget in enumerate(budgets):
            # Category
            cat_item = QtWidgets.QTableWidgetItem(budget.category)
            cat_item.setFlags(cat_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._budgets_table.setItem(row, 0, cat_item)

            month_item = QtWidgets.QTableWidgetItem(budget.year_month)
            month_item.setFlags(month_item.flags() & ~QtCore.Qt.ItemIsEditable)
            month_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._budgets_table.setItem(row, 1, month_item)

            # Monthly limit
            limit_item = QtWidgets.QTableWidgetItem(f"${budget.monthly_limit:,.2f}")
            limit_item.setFlags(limit_item.flags() & ~QtCore.Qt.ItemIsEditable)
            limit_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._budgets_table.setItem(row, 2, limit_item)

            # Delete button
            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(lambda checked, c=budget.category, m=budget.year_month: self._on_delete_budget(c, m))
            self._budgets_table.setCellWidget(row, 3, delete_btn)

    def _refresh_earnings_goals_table(self) -> None:
        """Refresh the earnings expectations table."""
        goals = self._budget_controller.get_all_earnings_goals()
        self._earnings_table.setRowCount(len(goals))

        for row, goal in enumerate(goals):
            sub_item = QtWidgets.QTableWidgetItem(goal.sub_category)
            sub_item.setFlags(sub_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._earnings_table.setItem(row, 0, sub_item)

            month_item = QtWidgets.QTableWidgetItem(goal.year_month)
            month_item.setFlags(month_item.flags() & ~QtCore.Qt.ItemIsEditable)
            month_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._earnings_table.setItem(row, 1, month_item)

            expected_item = QtWidgets.QTableWidgetItem(f"${goal.expected_amount:,.2f}")
            expected_item.setFlags(expected_item.flags() & ~QtCore.Qt.ItemIsEditable)
            expected_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._earnings_table.setItem(row, 2, expected_item)

            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setStyleSheet("background-color: #ff6b6b; color: white;")
            delete_btn.clicked.connect(lambda checked, s=goal.sub_category, m=goal.year_month: self._on_delete_earnings_goal(s, m))
            self._earnings_table.setCellWidget(row, 3, delete_btn)

    def _refresh_progress(self) -> None:
        """Refresh the budget progress display."""
        # Clear existing progress widgets
        while self._progress_layout.count():
            item = self._progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        year_month = self._month_combo.currentData()
        if year_month == "ALL" and self._months:
            year_month = self._months[-1]
        if not year_month:
            self._summary_label.setText("No data available")
            return

        # Get expenses for the selected month
        expenses_df = self._get_expenses_for_month(year_month)
        progress_list = self._budget_controller.calculate_budget_progress(expenses_df, year_month)

        if not progress_list:
            no_data = QtWidgets.QLabel("No budget goals set. Add budgets on the left panel.")
            no_data.setStyleSheet("color: #666; padding: 20px;")
            self._progress_layout.addWidget(no_data)
            self._summary_label.setText("")
            return

        # Create progress bars for each category
        total_budget = 0.0
        total_spent = 0.0
        over_budget_count = 0

        for progress in progress_list:
            self._add_progress_widget(progress)
            total_budget += progress.budget_limit
            total_spent += progress.spent
            if progress.status == "over":
                over_budget_count += 1

        self._progress_layout.addStretch()

        # Update summary
        remaining = total_budget - total_spent
        summary_text = (
            f"<b>Monthly Summary ({year_month})</b><br>"
            f"Total Budget: ${total_budget:,.2f}<br>"
            f"Total Spent: ${total_spent:,.2f}<br>"
            f"Remaining: ${remaining:,.2f}<br>"
        )
        if over_budget_count > 0:
            summary_text += f"<span style='color: red;'>⚠ {over_budget_count} categories over budget</span>"
        else:
            summary_text += "<span style='color: green;'>✓ All categories within budget</span>"

        self._summary_label.setText(summary_text)

    def _refresh_earnings_progress(self) -> None:
        """Refresh earnings progress table for the selected month."""
        year_month = self._earnings_progress_month_combo.currentData()
        if year_month == "ALL" and self._months:
            year_month = self._months[-1]

        df = self._get_earnings_for_month(year_month) if year_month else None
        expected_map = self._budget_controller.get_earnings_goal_map(year_month or "ALL")

        actual_by_sub: dict[str, float] = {}
        if df is not None and not df.empty:
            if "sub_category" in df.columns:
                grouped = df.groupby("sub_category")['amount'].sum()
                for sub, amt in grouped.items():
                    actual_by_sub[str(sub)] = float(amt)

        subs = set(actual_by_sub.keys()) | set(expected_map.keys())
        rows = []
        total_actual = 0.0
        total_expected = 0.0

        for sub in sorted(subs, key=lambda s: s.lower()):
            actual = actual_by_sub.get(sub, 0.0)
            expected = expected_map.get(sub, 0.0)
            diff = actual - expected
            diff_percent = (diff / expected * 100) if expected else (100.0 if actual > 0 else 0.0)
            rows.append((sub, actual, expected, diff, diff_percent))
            total_actual += actual
            total_expected += expected

        self._earnings_progress_table.setSortingEnabled(False)
        self._earnings_progress_table.setRowCount(0)
        for sub, actual, expected, diff, diff_pct in rows:
            r = self._earnings_progress_table.rowCount()
            self._earnings_progress_table.insertRow(r)
            items = [
                QtWidgets.QTableWidgetItem(sub),
                QtWidgets.QTableWidgetItem(f"${actual:,.2f}"),
                QtWidgets.QTableWidgetItem(f"${expected:,.2f}"),
                QtWidgets.QTableWidgetItem(f"${diff:,.2f}"),
                QtWidgets.QTableWidgetItem(f"{diff_pct:.1f}%"),
            ]
            for idx, item in enumerate(items):
                if idx > 0:
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                if idx in (3, 4):
                    color = QtGui.QColor("#16A34A" if diff >= 0 else "#DC2626")
                    item.setForeground(QtGui.QBrush(color))
                self._earnings_progress_table.setItem(r, idx, item)
        self._earnings_progress_table.setSortingEnabled(True)

        total_diff = total_actual - total_expected
        diff_color = "#16A34A" if total_diff >= 0 else "#DC2626"
        summary_text = (
            f"<b>Earnings Summary ({year_month or 'ALL'})</b><br>"
            f"Actual: ${total_actual:,.2f}<br>"
            f"Expected: ${total_expected:,.2f}<br>"
            f"<span style='color:{diff_color};'>Diff: ${total_diff:,.2f}</span>"
        )
        self._earnings_summary_label.setText(summary_text)

    def _add_progress_widget(self, progress: "BudgetProgress") -> None:
        """Add a progress widget for a budget category."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 10)

        # Header with category name and amounts
        header_layout = QtWidgets.QHBoxLayout()
        
        cat_label = QtWidgets.QLabel(f"<b>{progress.category}</b>")
        header_layout.addWidget(cat_label)
        
        header_layout.addStretch()
        
        amount_label = QtWidgets.QLabel(
            f"${progress.spent:,.2f} / ${progress.budget_limit:,.2f}"
        )
        header_layout.addWidget(amount_label)
        
        layout.addLayout(header_layout)

        # Progress bar
        progress_bar = QtWidgets.QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(min(int(progress.percentage), 100))
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{progress.percentage:.1f}%")

        # Color based on status
        if progress.status == "over":
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #ff6b6b;
                    border-radius: 4px;
                }
            """)
        elif progress.status == "warning":
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #ffd93d;
                    border-radius: 4px;
                }
            """)
        else:
            progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background-color: #6bcb77;
                    border-radius: 4px;
                }
            """)

        layout.addWidget(progress_bar)

        # Remaining amount
        if progress.remaining >= 0:
            remaining_text = f"${progress.remaining:,.2f} remaining"
            remaining_color = "#666"
        else:
            remaining_text = f"${abs(progress.remaining):,.2f} over budget!"
            remaining_color = "#ff6b6b"

        remaining_label = QtWidgets.QLabel(remaining_text)
        remaining_label.setStyleSheet(f"color: {remaining_color}; font-size: 12px;")
        layout.addWidget(remaining_label)

        self._progress_layout.addWidget(widget)

    def _get_expenses_for_month(self, year_month: str) -> "pd.DataFrame":
        """Get expenses DataFrame for a specific month."""
        import pandas as pd
        
        all_expenses = []
        for mr in self._reports:
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                all_expenses.append(mr.expenses)

        if not all_expenses:
            return pd.DataFrame()

        df = pd.concat(all_expenses, ignore_index=True)
        return df

    def _get_earnings_for_month(self, year_month: str | None) -> "pd.DataFrame":
        """Get earnings DataFrame for a specific month (or all)."""
        import pandas as pd

        frames = []
        for mr in self._reports:
            if hasattr(mr, 'earnings') and not mr.earnings.empty:
                frames.append(mr.earnings)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        if not year_month or year_month == "ALL":
            return df

        if "transaction_date" in df.columns:
            df = df.copy()
            df["year_month"] = pd.to_datetime(df["transaction_date"], errors="coerce").dt.strftime("%Y-%m")
            return df[df["year_month"] == year_month]
        return pd.DataFrame()

    def _on_month_changed(self, index: int) -> None:
        """Handle month selection change."""
        self._refresh_progress()

    def _on_earnings_month_changed(self, index: int) -> None:
        """Handle earnings progress month selection change."""
        self._refresh_earnings_progress()

    def _on_save_budget(self) -> None:
        """Save a new or updated budget goal."""
        category = self._category_combo.currentText().strip()
        if not category:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a category name."
            )
            return

        limit = self._limit_spin.value()
        if limit <= 0:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a valid budget limit."
            )
            return

        year_month = self._budget_month_combo.currentText().strip() or "ALL"
        self._budget_controller.set_budget(category, limit, year_month)
        self._logger.info("Saved budget: %s = $%.2f (%s)", category, limit, year_month)

        self._refresh_budgets_table()
        self._refresh_progress()
        self._refresh_earnings_progress()

        QtWidgets.QMessageBox.information(
            self, "Success", f"Budget for '{category}' saved successfully for {year_month}!"
        )

    def _on_delete_budget(self, category: str, year_month: str) -> None:
        """Delete a budget goal."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete the budget for '{category}' ({year_month})?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.delete_budget(category, year_month)
            self._logger.info("Deleted budget: %s (%s)", category, year_month)
            self._refresh_budgets_table()
            self._refresh_progress()
            self._refresh_earnings_progress()

    def _on_save_earnings_goal(self) -> None:
        """Save a new or updated earnings expectation."""
        sub_category = self._earnings_sub_combo.currentText().strip()
        if not sub_category:
            QtWidgets.QMessageBox.warning(self, "Error", "Please enter a sub-category name.")
            return

        expected = self._earnings_expected_spin.value()
        if expected < 0:
            QtWidgets.QMessageBox.warning(self, "Error", "Expected amount must be non-negative.")
            return

        year_month = self._earnings_month_combo.currentText().strip() or "ALL"
        self._budget_controller.set_earnings_goal(sub_category, expected, year_month)
        self._logger.info("Saved earnings expectation: %s = $%.2f (%s)", sub_category, expected, year_month)

        self._populate_earnings_sub_categories()
        self._refresh_earnings_goals_table()
        self._refresh_earnings_progress()

        QtWidgets.QMessageBox.information(
            self, "Success", f"Expected earnings for '{sub_category}' saved for {year_month}!"
        )

    def _on_delete_earnings_goal(self, sub_category: str, year_month: str) -> None:
        """Delete an earnings expectation."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete expected earnings for '{sub_category}' ({year_month})?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.delete_earnings_goal(sub_category, year_month)
            self._logger.info("Deleted earnings expectation: %s (%s)", sub_category, year_month)
            self._refresh_earnings_goals_table()
            self._refresh_earnings_progress()
