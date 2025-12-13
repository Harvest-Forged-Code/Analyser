from __future__ import annotations

import logging
from typing import Dict, List, Tuple

from PySide6 import QtCore, QtWidgets

from budget_analyser.presentation.controllers import MonthlyReports
from budget_analyser.presentation.controller import YearlySummaryStatsController


class YearlySummaryPage(QtWidgets.QWidget):
    """Modern Yearly Summary page with yearly overview.

    Features:
      - Year selector
      - Two columns: total Earnings (left) and total Expenses (right) with sub-categories
      - Monthly summary table (12 months: Month, Earnings, Expenses) with zeros for missing data
    """

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        # Controller handles all data aggregation and caching
        self._controller = YearlySummaryStatsController(self._reports, self._logger)

        self._init_ui()

    # ------------------------ UI SETUP ------------------------
    def _init_ui(self) -> None:
        self.setObjectName("yearlySummaryPage")

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Header row: title + year selector to the right
        header_row = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Yearly Summary")
        title.setObjectName("headerTitle")
        tf = title.font()
        tf.setPointSize(18)
        tf.setBold(True)
        title.setFont(tf)
        header_row.addWidget(title)
        header_row.addStretch(1)
        header_row.addWidget(QtWidgets.QLabel("Year:"))
        self.year_combo = QtWidgets.QComboBox()
        header_row.addWidget(self.year_combo)
        root.addLayout(header_row)

        # Two columns row: Earnings (left) and Expenses (right)
        two_col = QtWidgets.QHBoxLayout()

        # Earnings card
        self.earn_card = QtWidgets.QFrame()
        self.earn_card.setObjectName("card")
        # Ensure the card expands horizontally so both columns share width equally
        self.earn_card.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        earn_layout = QtWidgets.QVBoxLayout(self.earn_card)
        earn_layout.setContentsMargins(14, 14, 14, 14)
        earn_title = QtWidgets.QLabel("Total Earned")
        earn_title.setObjectName("cardTitle")
        self.earn_total = QtWidgets.QLabel("")
        self.earn_total.setObjectName("valueBig")
        earn_layout.addWidget(earn_title)
        earn_layout.addWidget(self.earn_total)
        earn_layout.addSpacing(6)
        earn_layout.addWidget(QtWidgets.QLabel("Sub-categories"))
        self.earn_table = QtWidgets.QTableWidget(0, 2)
        self.earn_table.setHorizontalHeaderLabels(["Sub-category", "Amount"])
        self.earn_table.horizontalHeader().setStretchLastSection(True)
        self.earn_table.verticalHeader().setVisible(False)
        self.earn_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.earn_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.earn_table.setAlternatingRowColors(True)
        self.earn_table.verticalHeader().setDefaultSectionSize(26)
        earn_layout.addWidget(self.earn_table)

        # Expenses card
        self.exp_card = QtWidgets.QFrame()
        self.exp_card.setObjectName("card")
        # Ensure the card expands horizontally so both columns share width equally
        self.exp_card.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        exp_layout = QtWidgets.QVBoxLayout(self.exp_card)
        exp_layout.setContentsMargins(14, 14, 14, 14)
        exp_title = QtWidgets.QLabel("Total Spent")
        exp_title.setObjectName("cardTitle")
        self.exp_total = QtWidgets.QLabel("")
        self.exp_total.setObjectName("valueBig")
        exp_layout.addWidget(exp_title)
        exp_layout.addWidget(self.exp_total)
        exp_layout.addSpacing(6)
        exp_layout.addWidget(QtWidgets.QLabel("Sub-categories"))
        self.exp_table = QtWidgets.QTableWidget(0, 2)
        self.exp_table.setHorizontalHeaderLabels(["Sub-category", "Amount"])
        self.exp_table.horizontalHeader().setStretchLastSection(True)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.exp_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.exp_table.setAlternatingRowColors(True)
        self.exp_table.verticalHeader().setDefaultSectionSize(26)
        exp_layout.addWidget(self.exp_table)

        two_col.addWidget(self.earn_card, 1)
        two_col.addWidget(self.exp_card, 1)
        # Explicitly enforce equal stretch for both columns across platforms
        two_col.setStretch(0, 1)
        two_col.setStretch(1, 1)
        root.addLayout(two_col)

        # Monthly summary table (12 months)
        monthly_card = QtWidgets.QFrame()
        monthly_card.setObjectName("card")
        monthly_layout = QtWidgets.QVBoxLayout(monthly_card)
        monthly_layout.setContentsMargins(14, 14, 14, 14)
        monthly_layout.addWidget(QtWidgets.QLabel("Monthly Summary"))
        self.month_table = QtWidgets.QTableWidget(12, 3)
        self.month_table.setHorizontalHeaderLabels(["Month", "Earnings", "Expenses"])
        self.month_table.verticalHeader().setVisible(False)
        self.month_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.month_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.month_table.horizontalHeader().setStretchLastSection(True)
        self.month_table.setAlternatingRowColors(True)
        self.month_table.verticalHeader().setDefaultSectionSize(26)
        monthly_layout.addWidget(self.month_table)
        root.addWidget(monthly_card)

        # Populate years and wire signals
        years = self._controller.available_years()
        if years:
            for y in years:
                self.year_combo.addItem(str(y), userData=y)
            # Select latest year by default
            self.year_combo.setCurrentIndex(len(years) - 1)
            self.year_combo.currentIndexChanged.connect(self._on_year_changed)
            self._refresh_year(years[-1])
        else:
            # No data message
            self.earn_total.setText("$0.00")
            self.exp_total.setText("$0.00")
            self._populate_month_table([(m, 0.0, 0.0) for m in self._controller.month_names()])
            # Ensure standard formatting for zero totals
            self.earn_total.setText("$0.00")
            self.exp_total.setText("$0.00")

    # ------------------------ DATA & EVENTS ------------------------
    def _on_year_changed(self, index: int) -> None:
        year = self.year_combo.currentData()
        if isinstance(year, int):
            self._logger.info("YearlySummaryPage: Year changed -> %s", year)
            self._refresh_year(year)

    def _refresh_year(self, year: int) -> None:
        data = self._controller.get_yearly_stats(year)
        # Set totals
        self.earn_total.setText(self._fmt_currency(data.total_earnings))
        self.exp_total.setText(self._fmt_currency(data.total_expenses))

        # Fill sub-category tables
        self._populate_kv_table(self.earn_table, data.earn_subcats)  # list[Tuple[str, float]]
        self._populate_kv_table(self.exp_table, data.exp_subcats)    # list[Tuple[str, float]]

        # Fill monthly table
        self._populate_month_table(data.monthly_rows)  # list[Tuple[str, float, float]]

    # ------------------------ HELPERS ------------------------
    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:  # fallback
            return str(value)


    def _populate_kv_table(self, table: QtWidgets.QTableWidget, rows: List[Tuple[str, float]]):
        table.setRowCount(0)
        table.setSortingEnabled(False)
        for sub, amt in rows:
            r = table.rowCount()
            table.insertRow(r)
            item0 = QtWidgets.QTableWidgetItem(sub or "(Uncategorized)")
            item1 = QtWidgets.QTableWidgetItem(self._fmt_currency(float(amt)))
            # Align amount to right
            item1.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            table.setItem(r, 0, item0)
            table.setItem(r, 1, item1)
        table.setSortingEnabled(True)
        table.sortItems(1, QtCore.Qt.DescendingOrder)
        table.resizeColumnsToContents()

    def _populate_month_table(self, rows: List[Tuple[str, float, float]]):
        self.month_table.setSortingEnabled(False)
        self.month_table.clearContents()
        self.month_table.setRowCount(12)
        for r, (name, earn, exp) in enumerate(rows):
            it0 = QtWidgets.QTableWidgetItem(name)
            it1 = QtWidgets.QTableWidgetItem(self._fmt_currency(float(earn)))
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(float(exp)))
            it1.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            it2.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self.month_table.setItem(r, 0, it0)
            self.month_table.setItem(r, 1, it1)
            self.month_table.setItem(r, 2, it2)
        self.month_table.resizeColumnsToContents()
