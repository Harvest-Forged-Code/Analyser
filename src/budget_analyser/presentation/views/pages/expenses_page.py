from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from PySide6 import QtCore, QtWidgets

from budget_analyser.presentation.controllers import MonthlyReports
from budget_analyser.presentation.controller import ExpensesStatsController


class ExpensesPage(QtWidgets.QWidget):
    """Expenses page mirroring Earnings but with hierarchy:
    Expenses (root) -> Categories -> Sub-categories.

    Bottom table shows transactions filtered by current tree selection.
    UI-only; all computations live in ExpensesStatsController.
    """

    ROLE_NODE_KIND = QtCore.Qt.UserRole + 1  # 'root' | 'category' | 'sub'
    ROLE_CATEGORY = QtCore.Qt.UserRole + 2
    ROLE_SUB_CATEGORY = QtCore.Qt.UserRole + 3

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._controller = ExpensesStatsController(self._reports, self._logger)

        self._current_period = None  # type: ignore[var-annotated]
        self._init_ui()

    # ---------------- UI ----------------
    def _init_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Header: Title + Month combobox
        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Expenses")
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

        # Middle: Tree view (Expenses -> Categories -> Sub-categories)
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Expenses", "Amount"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        root.addWidget(self.tree)

        # Bottom: Transactions table
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "From Account", "Category", "Sub-category"]
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
        root_item = QtWidgets.QTreeWidgetItem(["Expenses", self._fmt_currency(total)])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        f = root_item.font(0)
        f.setBold(True)
        root_item.setFont(0, f)
        root_item.setFont(1, f)
        root_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        # Add categories and sub-categories
        for cat, cat_total, subs in self._controller.category_breakdown(self._current_period):
            cat_item = QtWidgets.QTreeWidgetItem([cat or "(Uncategorized)", self._fmt_currency(cat_total)])
            cat_item.setData(0, self.ROLE_NODE_KIND, "category")
            cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
            cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            for sub, amt in subs:
                sub_item = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(amt)])
                sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                cat_item.addChild(sub_item)
            root_item.addChild(cat_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _refresh_table(self) -> None:
        if self._current_period is None:
            self.table.setRowCount(0)
            return
        kind, cat, sub = self._current_selection()
        if kind == "root":
            df = self._controller.transactions(self._current_period)
        elif kind == "category":
            df = self._controller.transactions(self._current_period, category=cat)
        else:
            df = self._controller.transactions(self._current_period, category=cat, sub_category=sub)

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
            catv = str(row.get("category", "")) if row.get("category") is not None else ""
            subv = str(row.get("sub_category", "")) if row.get("sub_category") is not None else ""

            it0 = QtWidgets.QTableWidgetItem(date_str)
            it1 = QtWidgets.QTableWidgetItem(desc)
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(abs(amt)))  # show positive
            it3 = QtWidgets.QTableWidgetItem(facct)
            it4 = QtWidgets.QTableWidgetItem(catv)
            it5 = QtWidgets.QTableWidgetItem(subv)

            it2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            self.table.setItem(r, 0, it0)
            self.table.setItem(r, 1, it1)
            self.table.setItem(r, 2, it2)
            self.table.setItem(r, 3, it3)
            self.table.setItem(r, 4, it4)
            self.table.setItem(r, 5, it5)

        self.table.resizeColumnsToContents()
        self.table.setSortingEnabled(True)

    # ------------- Events -------------
    def _on_month_changed(self, index: int) -> None:
        period = self.month_combo.currentData()
        self._current_period = period
        self._logger.info("ExpensesPage: Month changed -> %s", period)
        self._rebuild_tree()
        self._refresh_table()

    def _on_tree_selection_changed(self) -> None:
        self._refresh_table()

    # ------------- Helpers -------------
    def _current_selection(self) -> Tuple[str, Optional[str], Optional[str]]:
        item = self.tree.currentItem()
        if item is None:
            return "root", None, None
        kind = item.data(0, self.ROLE_NODE_KIND) or "root"
        cat = item.data(0, self.ROLE_CATEGORY)
        sub = item.data(0, self.ROLE_SUB_CATEGORY)
        return str(kind), (str(cat) if cat else None), (str(sub) if sub else None)

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
