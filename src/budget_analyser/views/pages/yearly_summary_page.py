from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import YearlySummaryStatsController


class YearlySummaryPage(QtWidgets.QWidget):
    """Modern Yearly Summary page with yearly overview.

    Features:
      - Year selector
      - Two cards: Earnings (left) and Expenses (right)
        - Each card shows the yearly total and a tree widget:
          Category (top level) -> Sub-categories (children) with right-aligned amounts
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
        earn_layout.addWidget(QtWidgets.QLabel("By Category"))
        self.earn_tree = QtWidgets.QTreeWidget()
        self.earn_tree.setHeaderLabels(["Category / Sub-category", "Amount"])
        self.earn_tree.header().setStretchLastSection(False)
        self.earn_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.earn_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        earn_layout.addWidget(self.earn_tree)

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
        exp_layout.addWidget(QtWidgets.QLabel("By Category"))
        self.exp_tree = QtWidgets.QTreeWidget()
        self.exp_tree.setHeaderLabels(["Category / Sub-category", "Amount"])
        self.exp_tree.header().setStretchLastSection(False)
        self.exp_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.exp_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        exp_layout.addWidget(self.exp_tree)

        two_col.addWidget(self.earn_card, 1)
        two_col.addWidget(self.exp_card, 1)
        # Explicitly enforce equal stretch for both columns across platforms
        two_col.setStretch(0, 1)
        two_col.setStretch(1, 1)
        root.addLayout(two_col)

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
            self._populate_category_trees([], [])

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

        # Fill category trees
        breakdown = self._controller.get_category_breakdown(year)
        self._populate_category_trees(breakdown.earnings, breakdown.expenses)

    # ------------------------ HELPERS ------------------------
    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:  # fallback
            return str(value)


    def _populate_category_trees(self, earn_nodes, exp_nodes) -> None:
        # Helper to fill a tree with CategoryNode structures
        def fill_tree(tree: QtWidgets.QTreeWidget, nodes) -> None:
            tree.clear()
            for node in nodes:
                top = QtWidgets.QTreeWidgetItem([str(node.name), self._fmt_currency(float(node.amount))])
                top.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                # Bold top-level category
                f = top.font(0)
                f.setBold(True)
                top.setFont(0, f)
                top.setFont(1, f)
                # Children: sub-categories
                for sub, amt in node.children:
                    child = QtWidgets.QTreeWidgetItem([sub or "(Uncategorized)", self._fmt_currency(float(amt))])
                    child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    top.addChild(child)
                tree.addTopLevelItem(top)
            tree.expandAll()

        fill_tree(self.earn_tree, earn_nodes or [])
        fill_tree(self.exp_tree, exp_nodes or [])
