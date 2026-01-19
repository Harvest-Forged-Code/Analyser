from __future__ import annotations

import logging
from typing import List

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import YearlySummaryStatsController
from budget_analyser.views.pages._page_base import ModernPageMixin


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
        self._controller = YearlySummaryStatsController(self._reports, self._logger)
        self._init_ui()

    def _init_ui(self) -> None:
        self.setObjectName("yearlySummaryPage")

        # Scroll area for content
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header with year selector
        header_container = QtWidgets.QWidget()
        header_layout = QtWidgets.QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(16)

        # Page header
        page_header = ModernPageMixin.create_page_header(
            title="Yearly Summary",
            subtitle="View your annual earnings and expenses breakdown by category",
            icon="📊"
        )
        header_layout.addWidget(page_header, 1)

        # Year selector
        year_container = QtWidgets.QWidget()
        year_layout = QtWidgets.QVBoxLayout(year_container)
        year_layout.setContentsMargins(0, 0, 0, 0)
        year_layout.setSpacing(8)

        year_label = ModernPageMixin.create_control_label("Year")
        year_layout.addWidget(year_label)

        self.year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.year_combo, min_height=44)
        self.year_combo.setMinimumWidth(120)
        year_layout.addWidget(self.year_combo)

        header_layout.addWidget(year_container)
        root.addWidget(header_container)

        # Two-column cards layout
        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(16)

        # Earnings card
        self.earn_card, earn_layout = ModernPageMixin.create_card("TOTAL EARNED")
        self.earn_card.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        self.earn_total = QtWidgets.QLabel("$0.00")
        self.earn_total.setObjectName("valueBig")
        self.earn_total.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #10B981;
            letter-spacing: -1px;
            margin-bottom: 8px;
        """)
        earn_layout.addWidget(self.earn_total)

        earn_subtitle_row = QtWidgets.QHBoxLayout()
        earn_subtitle_row.setSpacing(12)

        earn_subtitle = QtWidgets.QLabel("BY CATEGORY")
        earn_subtitle.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
            margin-top: 8px;
            margin-bottom: 8px;
        """)
        earn_subtitle_row.addWidget(earn_subtitle)
        earn_subtitle_row.addStretch(1)

        self.earn_toggle_btn = ModernPageMixin.create_action_button("⊟", primary=False)
        self.earn_toggle_btn.setMaximumWidth(40)
        self.earn_toggle_btn.setToolTip("Collapse All")
        self.earn_toggle_btn.clicked.connect(self._toggle_earn_tree)
        earn_subtitle_row.addWidget(self.earn_toggle_btn)

        earn_layout.addLayout(earn_subtitle_row)

        self.earn_tree = QtWidgets.QTreeWidget()
        self._earn_expanded = False
        self.earn_tree.setHeaderLabels(["Category", "Amount"])
        self.earn_tree.header().setStretchLastSection(False)
        self.earn_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.earn_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.earn_tree.setAlternatingRowColors(True)
        self.earn_tree.setRootIsDecorated(True)
        self.earn_tree.setIndentation(24)
        self.earn_tree.setUniformRowHeights(True)
        earn_layout.addWidget(self.earn_tree, 1)

        # Expenses card
        self.exp_card, exp_layout = ModernPageMixin.create_card("TOTAL SPENT")
        self.exp_card.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        self.exp_total = QtWidgets.QLabel("$0.00")
        self.exp_total.setObjectName("valueBig")
        self.exp_total.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            color: #EF4444;
            letter-spacing: -1px;
            margin-bottom: 8px;
        """)
        exp_layout.addWidget(self.exp_total)

        exp_subtitle_row = QtWidgets.QHBoxLayout()
        exp_subtitle_row.setSpacing(12)

        exp_subtitle = QtWidgets.QLabel("BY CATEGORY")
        exp_subtitle.setStyleSheet("""
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #8B5CF6;
            margin-top: 8px;
            margin-bottom: 8px;
        """)
        exp_subtitle_row.addWidget(exp_subtitle)
        exp_subtitle_row.addStretch(1)

        self.exp_toggle_btn = ModernPageMixin.create_action_button("⊟", primary=False)
        self.exp_toggle_btn.setMaximumWidth(40)
        self.exp_toggle_btn.setToolTip("Collapse All")
        self.exp_toggle_btn.clicked.connect(self._toggle_exp_tree)
        exp_subtitle_row.addWidget(self.exp_toggle_btn)

        exp_layout.addLayout(exp_subtitle_row)

        self.exp_tree = QtWidgets.QTreeWidget()
        self._exp_expanded = False
        self.exp_tree.setHeaderLabels(["Category", "Amount"])
        self.exp_tree.header().setStretchLastSection(False)
        self.exp_tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.exp_tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.exp_tree.setAlternatingRowColors(True)
        self.exp_tree.setRootIsDecorated(True)
        self.exp_tree.setIndentation(24)
        self.exp_tree.setUniformRowHeights(True)
        exp_layout.addWidget(self.exp_tree, 1)

        cards_row.addWidget(self.earn_card, 1)
        cards_row.addWidget(self.exp_card, 1)
        root.addLayout(cards_row, 1)

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
                # Format category name with proper title case
                category_name = str(node.name).title() if node.name else "Uncategorized"

                top = QtWidgets.QTreeWidgetItem([
                    category_name,
                    self._fmt_currency(float(node.amount))
                ])
                top.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                # Style top-level category - bold, larger font
                f = top.font(0)
                f.setBold(True)
                f.setPointSize(14)
                top.setFont(0, f)

                # Amount font for category
                f_amt = top.font(1)
                f_amt.setBold(True)
                f_amt.setPointSize(14)
                top.setFont(1, f_amt)

                # Children: sub-categories
                for sub, amt in node.children:
                    sub_name = sub.title() if sub else "Uncategorized"
                    child = QtWidgets.QTreeWidgetItem([
                        sub_name,
                        self._fmt_currency(float(amt))
                    ])
                    child.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                    # Style sub-category - regular weight, normal size
                    f_sub = child.font(0)
                    f_sub.setPointSize(13)
                    child.setFont(0, f_sub)
                    child.setFont(1, f_sub)

                    top.addChild(child)
                tree.addTopLevelItem(top)
            tree.expandAll()

        fill_tree(self.earn_tree, earn_nodes or [])
        fill_tree(self.exp_tree, exp_nodes or [])

        # Reset toggle states after populating
        self._earn_expanded = True
        self._exp_expanded = True
        self.earn_toggle_btn.setText("⊟")
        self.earn_toggle_btn.setToolTip("Collapse All")
        self.exp_toggle_btn.setText("⊟")
        self.exp_toggle_btn.setToolTip("Collapse All")

    def _toggle_earn_tree(self) -> None:
        """Toggle expand/collapse state of earnings tree."""
        if self._earn_expanded:
            self.earn_tree.collapseAll()
            self.earn_toggle_btn.setText("⊞")
            self.earn_toggle_btn.setToolTip("Expand All")
            self._earn_expanded = False
        else:
            self.earn_tree.expandAll()
            self.earn_toggle_btn.setText("⊟")
            self.earn_toggle_btn.setToolTip("Collapse All")
            self._earn_expanded = True

    def _toggle_exp_tree(self) -> None:
        """Toggle expand/collapse state of expenses tree."""
        if self._exp_expanded:
            self.exp_tree.collapseAll()
            self.exp_toggle_btn.setText("⊞")
            self.exp_toggle_btn.setToolTip("Expand All")
            self._exp_expanded = False
        else:
            self.exp_tree.expandAll()
            self.exp_toggle_btn.setText("⊟")
            self.exp_toggle_btn.setToolTip("Collapse All")
            self._exp_expanded = True
