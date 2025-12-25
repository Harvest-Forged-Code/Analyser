from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import EarningsStatsController
from budget_analyser.controller.budget_controller import BudgetController

import pandas as pd


# View mode constants
VIEW_MODE_MONTHLY = "Monthly"
VIEW_MODE_YEARLY = "Yearly"
VIEW_MODE_CUSTOM = "Custom Range"


class EarningsPage(QtWidgets.QWidget):
    """Earnings page with table view (Monthly/Yearly/Custom) plus transactions table."""

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger, budget_controller: BudgetController | None = None):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._budget_controller = budget_controller
        self._controller = EarningsStatsController(self._reports, self._logger, budget_controller=self._budget_controller)

        self._current_period = None  # type: ignore[var-annotated]
        self._current_year: Optional[int] = None
        self._current_view_mode = VIEW_MODE_MONTHLY
        self._current_sub_category: Optional[str] = None
        self._init_ui()

    # ---------------- UI ----------------
    def _init_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header: Title + View Mode + Date Selectors
        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Earnings")
        tf = title.font()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        header_row.addWidget(title)
        header_row.addStretch(1)

        # View Mode selector
        header_row.addWidget(QtWidgets.QLabel("View:"))
        self.view_mode_combo = QtWidgets.QComboBox()
        self.view_mode_combo.addItems([VIEW_MODE_MONTHLY, VIEW_MODE_YEARLY, VIEW_MODE_CUSTOM])
        header_row.addWidget(self.view_mode_combo)

        # Month selector (for Monthly mode)
        self.month_label = QtWidgets.QLabel("Month:")
        header_row.addWidget(self.month_label)
        self.month_combo = QtWidgets.QComboBox()
        header_row.addWidget(self.month_combo)

        # Year selector (for Yearly mode)
        self.year_label = QtWidgets.QLabel("Year:")
        header_row.addWidget(self.year_label)
        self.year_combo = QtWidgets.QComboBox()
        header_row.addWidget(self.year_combo)

        # Date range selectors (for Custom Range mode)
        self.from_label = QtWidgets.QLabel("From:")
        header_row.addWidget(self.from_label)
        self.from_date = QtWidgets.QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDisplayFormat("MM/dd/yyyy")
        header_row.addWidget(self.from_date)

        self.to_label = QtWidgets.QLabel("To:")
        header_row.addWidget(self.to_label)
        self.to_date = QtWidgets.QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDisplayFormat("MM/dd/yyyy")
        header_row.addWidget(self.to_date)

        # Apply button for custom range
        self.apply_btn = QtWidgets.QPushButton("Apply")
        header_row.addWidget(self.apply_btn)

        root.addLayout(header_row)

        # Middle: Summary table
        summary_card = QtWidgets.QWidget()
        summary_card.setObjectName("card")
        summary_layout = QtWidgets.QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)

        summary_header = QtWidgets.QHBoxLayout()
        summary_title = QtWidgets.QLabel("Earnings Breakdown")
        f = summary_title.font()
        f.setBold(True)
        summary_title.setFont(f)
        summary_header.addWidget(summary_title)
        summary_header.addStretch(1)
        # Note: Expected amounts are now set in the Budget Goals page
        summary_layout.addLayout(summary_header)

        self.summary_table = QtWidgets.QTableWidget(0, 6)
        self.summary_table.setHorizontalHeaderLabels([
            "Sub-category",
            "Actual",
            "% Total",
            "Expected",
            "Diff",
            "Diff %",
        ])
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.summary_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.summary_table.horizontalHeader().setStretchLastSection(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for col in range(1, 6):
            self.summary_table.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setDefaultSectionSize(26)
        self.summary_table.itemSelectionChanged.connect(self._on_summary_selection_changed)
        summary_layout.addWidget(self.summary_table)

        root.addWidget(summary_card)

        # Bottom: Transactions table
        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "From Account", "Sub-category"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(26)
        root.addWidget(self.table)

        # Populate months and years
        self._populate_months()
        self._populate_years()
        self._set_default_date_range()

        # Wire events
        self.view_mode_combo.currentTextChanged.connect(self._on_view_mode_changed)
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        self.apply_btn.clicked.connect(self._on_apply_custom_range)

        # Initial visibility and selection
        self._update_selector_visibility()
        if self.month_combo.count() > 0:
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)  # latest
        self._rebuild_summary()

    # ------------- Population helpers -------------
    def _populate_months(self) -> None:
        self.month_combo.clear()
        months = self._controller.available_months()
        for p in months:
            self.month_combo.addItem(self._controller.month_label(p), userData=p)

    def _populate_years(self) -> None:
        self.year_combo.clear()
        years = self._controller.available_years()
        for y in years:
            self.year_combo.addItem(str(y), userData=y)
        # Select latest year by default
        if self.year_combo.count() > 0:
            self.year_combo.setCurrentIndex(self.year_combo.count() - 1)

    def _set_default_date_range(self) -> None:
        """Set default date range based on available data."""
        months = self._controller.available_months()
        if months:
            # Default: first day of earliest month to last day of latest month
            earliest = months[0]
            latest = months[-1]
            from_date = date(earliest.year, earliest.month, 1)
            # Last day of latest month
            if latest.month == 12:
                to_date = date(latest.year, 12, 31)
            else:
                to_date = date(latest.year, latest.month + 1, 1) - __import__('datetime').timedelta(days=1)
            self.from_date.setDate(QtCore.QDate(from_date.year, from_date.month, from_date.day))
            self.to_date.setDate(QtCore.QDate(to_date.year, to_date.month, to_date.day))
        else:
            # Default to current year
            today = date.today()
            self.from_date.setDate(QtCore.QDate(today.year, 1, 1))
            self.to_date.setDate(QtCore.QDate(today.year, today.month, today.day))

    def _update_selector_visibility(self) -> None:
        """Show/hide date selectors based on current view mode."""
        mode = self.view_mode_combo.currentText()
        is_monthly = mode == VIEW_MODE_MONTHLY
        is_yearly = mode == VIEW_MODE_YEARLY
        is_custom = mode == VIEW_MODE_CUSTOM

        # Monthly selectors
        self.month_label.setVisible(is_monthly)
        self.month_combo.setVisible(is_monthly)

        # Yearly selectors
        self.year_label.setVisible(is_yearly)
        self.year_combo.setVisible(is_yearly)

        # Custom range selectors
        self.from_label.setVisible(is_custom)
        self.from_date.setVisible(is_custom)
        self.to_label.setVisible(is_custom)
        self.to_date.setVisible(is_custom)
        self.apply_btn.setVisible(is_custom)

    def _rebuild_summary(self) -> None:
        mode = self._current_view_mode
        rows = []
        actual_total = 0.0
        expected_total = 0.0

        if mode == VIEW_MODE_MONTHLY:
            if self._current_period is not None:
                rows, actual_total, expected_total = self._controller.table_for_month(self._current_period)
        elif mode == VIEW_MODE_YEARLY:
            if self._current_year is not None:
                rows, actual_total, expected_total = self._controller.table_for_year(self._current_year)
        elif mode == VIEW_MODE_CUSTOM:
            start = self.from_date.date().toPython()
            end = self.to_date.date().toPython()
            rows, actual_total, expected_total = self._controller.table_for_range(start, end)

        self._populate_summary_table(rows, actual_total, expected_total)
        self._select_default_row()

    def _populate_summary_table(self, rows, actual_total: float, expected_total: float) -> None:
        self.summary_table.setSortingEnabled(False)
        self.summary_table.setRowCount(0)
        self.summary_table.clearSelection()

        def _add_row(values, bold: bool = False, color: Optional[QtGui.QColor] = None, raw_name: Optional[str] = None):
            r = self.summary_table.rowCount()
            self.summary_table.insertRow(r)
            for c, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                if c == 0 and raw_name is not None:
                    # Store raw sub-category name as item data for later retrieval
                    item.setData(QtCore.Qt.UserRole, raw_name)
                if c in (1, 2, 3, 4, 5):
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                if bold:
                    f = item.font()
                    f.setBold(True)
                    item.setFont(f)
                if color is not None and c in (4, 5):
                    item.setForeground(QtGui.QBrush(color))
                self.summary_table.setItem(r, c, item)
            return r

        # Data rows with radio indicator (○ = unselected)
        for row in rows:
            diff_color = QtGui.QColor("#16A34A") if row.diff >= 0 else QtGui.QColor("#DC2626")
            raw_name = row.sub_category or "(Uncategorized)"
            _add_row([
                f"○ {raw_name}",
                self._fmt_currency(row.actual),
                self._fmt_percent(row.percent_of_total),
                self._fmt_currency(row.expected),
                self._fmt_currency(row.diff),
                self._fmt_percent(row.diff_percent),
            ], bold=False, color=diff_color, raw_name=raw_name)

        # Total row (no radio indicator)
        total_diff = actual_total - expected_total
        total_color = QtGui.QColor("#16A34A") if total_diff >= 0 else QtGui.QColor("#DC2626")
        total_row = _add_row([
            "TOTAL",
            self._fmt_currency(actual_total),
            self._fmt_percent(100.0 if rows else 0.0),
            self._fmt_currency(expected_total),
            self._fmt_currency(total_diff),
            self._fmt_percent((total_diff / expected_total * 100) if expected_total > 0 else None),
        ], bold=True, color=total_color, raw_name=None)

        self.summary_table.setSortingEnabled(True)
        self.summary_table.resizeColumnsToContents()
        # Prevent selecting the total row by default
        if total_row >= 0:
            self.summary_table.setRowHidden(total_row, False)

    def _refresh_table(self) -> None:
        mode = self._current_view_mode
        sub = self._current_sub_category

        # Get transactions based on view mode
        if mode == VIEW_MODE_MONTHLY:
            if self._current_period is None:
                self.table.setRowCount(0)
                return
            df = self._controller.transactions(self._current_period, sub_category=sub)
        elif mode == VIEW_MODE_YEARLY:
            if self._current_year is None:
                self.table.setRowCount(0)
                return
            df = self._controller.transactions_for_year(
                self._current_year, month=None, sub_category=sub
            )
        elif mode == VIEW_MODE_CUSTOM:
            start = self.from_date.date().toPython()
            end = self.to_date.date().toPython()
            df = self._controller.transactions_for_range(start, end, sub_category=sub)
        else:
            self.table.setRowCount(0)
            return

        # Sort by date desc if available
        if not df.empty and "transaction_date" in df.columns:
            try:
                df = df.sort_values(by="transaction_date", ascending=False)
            except Exception:  # pragma: no cover - defensive
                pass

        self._populate_table(df)

    def _populate_table(self, df: pd.DataFrame) -> None:
        """Populate the transactions table with the given DataFrame."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)
        for _, row in df.iterrows():
            r = self.table.rowCount()
            self.table.insertRow(r)
            date_str = self._fmt_date(row.get("transaction_date"))
            desc = str(row.get("description", ""))
            amt = float(row.get("amount", 0.0) or 0.0)
            facct = str(row.get("from_account", ""))
            subc = str(row.get("sub_category", "")) if row.get("sub_category") is not None else ""

            it0 = QtWidgets.QTableWidgetItem(date_str)
            it1 = QtWidgets.QTableWidgetItem(desc)
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(amt))
            it3 = QtWidgets.QTableWidgetItem(facct)
            it4 = QtWidgets.QTableWidgetItem(subc)

            it2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            self.table.setItem(r, 0, it0)
            self.table.setItem(r, 1, it1)
            self.table.setItem(r, 2, it2)
            self.table.setItem(r, 3, it3)
            self.table.setItem(r, 4, it4)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    # ------------- Events -------------
    def _on_view_mode_changed(self, mode: str) -> None:
        self._current_view_mode = mode
        self._logger.info("EarningsPage: View mode changed -> %s", mode)
        self._update_selector_visibility()

        # Trigger appropriate data load based on new mode
        if mode == VIEW_MODE_MONTHLY:
            if self._current_period is None and self.month_combo.count() > 0:
                self.month_combo.setCurrentIndex(self.month_combo.count() - 1)
            else:
                self._rebuild_summary()
                self._refresh_table()
        elif mode == VIEW_MODE_YEARLY:
            year_data = self.year_combo.currentData()
            if year_data is not None:
                self._current_year = year_data
            self._rebuild_summary()
            self._refresh_table()
        elif mode == VIEW_MODE_CUSTOM:
            self._rebuild_summary()
            self._refresh_table()

    def _on_month_changed(self, index: int) -> None:
        if self._current_view_mode != VIEW_MODE_MONTHLY:
            return
        period = self.month_combo.currentData()
        self._current_period = period
        self._logger.info("EarningsPage: Month changed -> %s", period)
        self._rebuild_summary()
        self._refresh_table()

    def _on_year_changed(self, index: int) -> None:
        if self._current_view_mode != VIEW_MODE_YEARLY:
            return
        year = self.year_combo.currentData()
        self._current_year = year
        self._logger.info("EarningsPage: Year changed -> %s", year)
        self._rebuild_summary()
        self._refresh_table()

    def _on_apply_custom_range(self) -> None:
        if self._current_view_mode != VIEW_MODE_CUSTOM:
            return
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        self._logger.info("EarningsPage: Custom range applied -> %s to %s", start, end)
        self._rebuild_summary()
        self._refresh_table()

    def _on_summary_selection_changed(self) -> None:
        selected_row = self.summary_table.currentRow()
        
        # Update radio indicators for all rows
        for row in range(self.summary_table.rowCount()):
            name_item = self.summary_table.item(row, 0)
            if name_item is None:
                continue
            raw_name = name_item.data(QtCore.Qt.UserRole)
            if raw_name is None:
                # This is the TOTAL row, skip it
                continue
            # Update indicator: ● for selected, ○ for others
            indicator = "●" if row == selected_row else "○"
            name_item.setText(f"{indicator} {raw_name}")
        
        # Set current sub-category from item data
        if selected_row < 0:
            self._current_sub_category = None
        else:
            name_item = self.summary_table.item(selected_row, 0)
            if name_item:
                raw_name = name_item.data(QtCore.Qt.UserRole)
                # If raw_name is None, it's the TOTAL row
                self._current_sub_category = raw_name
            else:
                self._current_sub_category = None
        
        self._refresh_table()

    # ------------- Helpers -------------
    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:  # pragma: no cover - defensive
            return str(value)

    @staticmethod
    def _fmt_percent(value: Optional[float]) -> str:
        if value is None:
            return "—"
        try:
            return f"{value:.1f}%"
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_date(value) -> str:
        try:
            # value can be pandas Timestamp/Period/str
            return str(getattr(value, "date", lambda: value)()) if hasattr(value, "date") else str(value)[:10]
        except Exception:  # pragma: no cover
            return str(value)[:10]

    def _select_default_row(self) -> None:
        # Select first data row (if any) - use item data to identify non-TOTAL rows
        if self.summary_table.rowCount() == 0:
            self._current_sub_category = None
            return
        for row in range(self.summary_table.rowCount()):
            name_item = self.summary_table.item(row, 0)
            if name_item:
                raw_name = name_item.data(QtCore.Qt.UserRole)
                if raw_name is not None:
                    # This is a data row (not TOTAL), select it
                    self.summary_table.selectRow(row)
                    # Selection change handler will update indicators and _current_sub_category
                    return
        self._current_sub_category = None

