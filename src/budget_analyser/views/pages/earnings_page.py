from __future__ import annotations

import logging
from typing import List, Optional

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import EarningsStatsController


class EarningsPage(QtWidgets.QWidget):
    """Earnings page with month selector, tree (total -> sub-categories),
    and a transactions table bound to the current selection.

    UI-only: all data comes from EarningsStatsController.
    """

    ROLE_SUB_CATEGORY = QtCore.Qt.UserRole + 1

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._controller = EarningsStatsController(self._reports, self._logger)

        self._current_period = None  # type: ignore[var-annotated]
        self._init_ui()

    # ---------------- UI ----------------
    def _init_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header: Title + Month combobox
        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Earnings")
        tf = title.font()
        tf.setPointSize(16)
        tf.setBold(True)
        title.setFont(tf)
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(QtWidgets.QLabel("Month:"))
        self.month_combo = QtWidgets.QComboBox()
        header_row.addWidget(self.month_combo)
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

        # Populate months and wire events
        self._populate_months()
        self.month_combo.currentIndexChanged.connect(self._on_month_changed)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)

        # Initial selection
        if self.month_combo.count() > 0:
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)  # latest

    # ------------- Population helpers -------------
    def _populate_months(self) -> None:
        self.month_combo.clear()
        months = self._controller.available_months()
        for p in months:
            self.month_combo.addItem(self._controller.month_label(p), userData=p)

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        if self._current_period is None:
            return
        total = self._controller.total_for_month(self._current_period)
        root_item = QtWidgets.QTreeWidgetItem([f"Earnings", self._fmt_currency(total)])
        # Mark root with sub_category=None
        root_item.setData(0, self.ROLE_SUB_CATEGORY, None)
        # Bold root
        font = root_item.font(0)
        font.setBold(True)
        root_item.setFont(0, font)
        root_item.setFont(1, font)

        for sub, amt in self._controller.subcategory_totals(self._current_period):
            child = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(amt)])
            child.setData(0, self.ROLE_SUB_CATEGORY, sub)
            # Right-align amount
            child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            root_item.addChild(child)

        # Right-align root amount
        root_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _refresh_table(self) -> None:
        if self._current_period is None:
            self.table.setRowCount(0)
            return
        sub = self._current_sub_category()
        df = self._controller.transactions(self._current_period, sub_category=sub)
        # Sort by date desc if available
        if not df.empty and "transaction_date" in df.columns:
            try:
                df = df.sort_values(by="transaction_date", ascending=False)
            except Exception:  # pragma: no cover - defensive
                pass

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
    def _on_month_changed(self, index: int) -> None:
        period = self.month_combo.currentData()
        self._current_period = period
        self._logger.info("EarningsPage: Month changed -> %s", period)
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
