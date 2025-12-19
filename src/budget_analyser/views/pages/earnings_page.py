from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import EarningsStatsController

import pandas as pd


# View mode constants
VIEW_MODE_MONTHLY = "Monthly"
VIEW_MODE_YEARLY = "Yearly"
VIEW_MODE_CUSTOM = "Custom Range"


class EarningsPage(QtWidgets.QWidget):
    """Earnings page with view mode selector (Monthly/Yearly/Custom Range),
    tree (total -> sub-categories), and a transactions table bound to the current selection.

    UI-only: all data comes from EarningsStatsController.
    """

    ROLE_SUB_CATEGORY = QtCore.Qt.UserRole + 1
    ROLE_MONTH = QtCore.Qt.UserRole + 2  # For yearly view month nodes

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._controller = EarningsStatsController(self._reports, self._logger)

        self._current_period = None  # type: ignore[var-annotated]
        self._current_year: Optional[int] = None
        self._current_view_mode = VIEW_MODE_MONTHLY
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

        # Middle: Tree view (Total -> sub-categories)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Earnings", "Amount"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        root.addWidget(self.tree)

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
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)

        # Initial visibility and selection
        self._update_selector_visibility()
        if self.month_combo.count() > 0:
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)  # latest

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

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        mode = self._current_view_mode

        if mode == VIEW_MODE_MONTHLY:
            self._rebuild_tree_monthly()
        elif mode == VIEW_MODE_YEARLY:
            self._rebuild_tree_yearly()
        elif mode == VIEW_MODE_CUSTOM:
            self._rebuild_tree_custom()

    def _rebuild_tree_monthly(self) -> None:
        """Build tree for monthly view: Earnings -> Sub-categories."""
        if self._current_period is None:
            return
        total = self._controller.total_for_month(self._current_period)
        root_item = QtWidgets.QTreeWidgetItem(["Earnings", self._fmt_currency(total)])
        root_item.setData(0, self.ROLE_SUB_CATEGORY, None)
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        for sub, amt in self._controller.subcategory_totals(self._current_period):
            child = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(amt)])
            child.setData(0, self.ROLE_SUB_CATEGORY, sub)
            child.setData(0, self.ROLE_MONTH, None)
            child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            root_item.addChild(child)

        root_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_yearly(self) -> None:
        """Build tree for yearly view: Year Total -> Month -> Sub-categories."""
        if self._current_year is None:
            return
        year_total = self._controller.total_for_year(self._current_year)
        root_item = QtWidgets.QTreeWidgetItem([f"Earnings {self._current_year}", self._fmt_currency(year_total)])
        root_item.setData(0, self.ROLE_SUB_CATEGORY, None)
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        # Add month nodes
        for period, month_total, subcats in self._controller.year_breakdown(self._current_year):
            month_label = self._controller.month_label(period)
            month_item = QtWidgets.QTreeWidgetItem([month_label, self._fmt_currency(month_total)])
            month_item.setData(0, self.ROLE_SUB_CATEGORY, None)
            month_item.setData(0, self.ROLE_MONTH, period)
            month_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            # Bold month items
            font = month_item.font(0)
            font.setBold(True)
            month_item.setFont(0, font)

            # Add sub-category children
            for sub, amt in subcats:
                child = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(amt)])
                child.setData(0, self.ROLE_SUB_CATEGORY, sub)
                child.setData(0, self.ROLE_MONTH, period)
                child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                month_item.addChild(child)

            root_item.addChild(month_item)

        root_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_custom(self) -> None:
        """Build tree for custom range view: Total -> Sub-categories."""
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        total = self._controller.total_for_range(start, end)
        root_item = QtWidgets.QTreeWidgetItem(["Earnings", self._fmt_currency(total)])
        root_item.setData(0, self.ROLE_SUB_CATEGORY, None)
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        for sub, amt in self._controller.subcategory_totals_for_range(start, end):
            child = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(amt)])
            child.setData(0, self.ROLE_SUB_CATEGORY, sub)
            child.setData(0, self.ROLE_MONTH, None)
            child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            root_item.addChild(child)

        root_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _style_root_item(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """Apply bold styling to root tree item."""
        font = item.font(0)
        font.setBold(True)
        item.setFont(0, font)
        item.setFont(1, font)

    def _refresh_table(self) -> None:
        mode = self._current_view_mode
        sub = self._current_sub_category()
        month = self._current_month_from_tree()

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
                self._current_year, month=month, sub_category=sub
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
                self._rebuild_tree()
                self._refresh_table()
        elif mode == VIEW_MODE_YEARLY:
            year_data = self.year_combo.currentData()
            if year_data is not None:
                self._current_year = year_data
            self._rebuild_tree()
            self._refresh_table()
        elif mode == VIEW_MODE_CUSTOM:
            self._rebuild_tree()
            self._refresh_table()

    def _on_month_changed(self, index: int) -> None:
        if self._current_view_mode != VIEW_MODE_MONTHLY:
            return
        period = self.month_combo.currentData()
        self._current_period = period
        self._logger.info("EarningsPage: Month changed -> %s", period)
        self._rebuild_tree()
        self._refresh_table()

    def _on_year_changed(self, index: int) -> None:
        if self._current_view_mode != VIEW_MODE_YEARLY:
            return
        year = self.year_combo.currentData()
        self._current_year = year
        self._logger.info("EarningsPage: Year changed -> %s", year)
        self._rebuild_tree()
        self._refresh_table()

    def _on_apply_custom_range(self) -> None:
        if self._current_view_mode != VIEW_MODE_CUSTOM:
            return
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        self._logger.info("EarningsPage: Custom range applied -> %s to %s", start, end)
        self._rebuild_tree()
        self._refresh_table()

    def _on_tree_selection_changed(self) -> None:
        self._refresh_table()

    # ------------- Helpers -------------
    def _current_sub_category(self) -> Optional[str]:
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, self.ROLE_SUB_CATEGORY)

    def _current_month_from_tree(self) -> Optional[pd.Period]:
        """Get the month period from the currently selected tree item (for yearly view)."""
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, self.ROLE_MONTH)

    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:  # pragma: no cover - defensive
            return str(value)

    @staticmethod
    def _fmt_date(value) -> str:
        try:
            # value can be pandas Timestamp/Period/str
            return str(getattr(value, "date", lambda: value)()) if hasattr(value, "date") else str(value)[:10]
        except Exception:  # pragma: no cover
            return str(value)[:10]
