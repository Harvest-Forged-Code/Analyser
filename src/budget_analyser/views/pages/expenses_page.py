from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import ExpensesStatsController
from budget_analyser.views.pages._page_base import ModernPageMixin

import pandas as pd


# View mode constants
VIEW_MODE_MONTHLY = "Monthly"
VIEW_MODE_YEARLY = "Yearly"
VIEW_MODE_CUSTOM = "Custom Range"


class ExpensesPage(QtWidgets.QWidget):
    """Expenses page with view mode selector (Monthly/Yearly/Custom Range),
    hierarchy: Expenses (root) -> Categories -> Sub-categories.

    Bottom table shows transactions filtered by current tree selection.
    UI-only; all computations live in ExpensesStatsController.
    """

    ROLE_NODE_KIND = QtCore.Qt.UserRole + 1  # 'root' | 'category' | 'sub' | 'month'
    ROLE_CATEGORY = QtCore.Qt.UserRole + 2
    ROLE_SUB_CATEGORY = QtCore.Qt.UserRole + 3
    ROLE_MONTH = QtCore.Qt.UserRole + 4  # For yearly view month nodes

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._controller = ExpensesStatsController(self._reports, self._logger)

        self._current_period = None  # type: ignore[var-annotated]
        self._current_year: Optional[int] = None
        self._current_view_mode = VIEW_MODE_MONTHLY
        self._init_ui()

    # ---------------- UI ----------------
    def _init_ui(self) -> None:
        # Scroll area for content
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header with page title
        page_header = ModernPageMixin.create_page_header(
            title="Expenses",
            subtitle="Track and analyze your expense categories and transactions",
            icon="🧾"
        )
        root.addWidget(page_header)

        # Filters card
        filters_card, filters_layout = ModernPageMixin.create_card("FILTERS")

        # View Mode selector row
        view_row_container, view_row = ModernPageMixin.create_controls_row()

        view_label = ModernPageMixin.create_control_label("View Mode")
        view_row.addWidget(view_label)

        self.view_mode_combo = QtWidgets.QComboBox()
        self.view_mode_combo.addItems([VIEW_MODE_MONTHLY, VIEW_MODE_YEARLY, VIEW_MODE_CUSTOM])
        ModernPageMixin.style_combo_box(self.view_mode_combo, min_height=44)
        self.view_mode_combo.setMinimumWidth(160)
        view_row.addWidget(self.view_mode_combo)
        view_row.addStretch(1)

        filters_layout.addWidget(view_row_container)

        # Monthly selector container
        self._monthly_container = QtWidgets.QWidget()
        monthly_layout = QtWidgets.QVBoxLayout(self._monthly_container)
        monthly_layout.setContentsMargins(0, 0, 0, 0)
        monthly_layout.setSpacing(8)

        self.month_label = ModernPageMixin.create_control_label("Month")
        monthly_layout.addWidget(self.month_label)

        self.month_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.month_combo, min_height=44)
        monthly_layout.addWidget(self.month_combo)

        filters_layout.addWidget(self._monthly_container)

        # Yearly selector container
        self._yearly_container = QtWidgets.QWidget()
        yearly_layout = QtWidgets.QVBoxLayout(self._yearly_container)
        yearly_layout.setContentsMargins(0, 0, 0, 0)
        yearly_layout.setSpacing(8)

        self.year_label = ModernPageMixin.create_control_label("Year")
        yearly_layout.addWidget(self.year_label)

        self.year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.year_combo, min_height=44)
        self.year_combo.setMinimumWidth(120)
        yearly_layout.addWidget(self.year_combo)

        filters_layout.addWidget(self._yearly_container)

        # Custom range selector container
        self._custom_container = QtWidgets.QWidget()
        custom_layout = QtWidgets.QVBoxLayout(self._custom_container)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(16)

        # From date
        from_container = QtWidgets.QWidget()
        from_layout = QtWidgets.QVBoxLayout(from_container)
        from_layout.setContentsMargins(0, 0, 0, 0)
        from_layout.setSpacing(8)

        self.from_label = ModernPageMixin.create_control_label("From Date")
        from_layout.addWidget(self.from_label)

        self.from_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.from_date, min_height=44)
        from_layout.addWidget(self.from_date)

        custom_layout.addWidget(from_container)

        # To date
        to_container = QtWidgets.QWidget()
        to_layout = QtWidgets.QVBoxLayout(to_container)
        to_layout.setContentsMargins(0, 0, 0, 0)
        to_layout.setSpacing(8)

        self.to_label = ModernPageMixin.create_control_label("To Date")
        to_layout.addWidget(self.to_label)

        self.to_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.to_date, min_height=44)
        to_layout.addWidget(self.to_date)

        custom_layout.addWidget(to_container)

        # Apply button
        self.apply_btn = ModernPageMixin.create_action_button("Apply", primary=True)
        self.apply_btn.setMinimumHeight(48)
        custom_layout.addWidget(self.apply_btn)

        filters_layout.addWidget(self._custom_container)

        root.addWidget(filters_card)

        # Tree card
        tree_card, tree_layout = ModernPageMixin.create_card("EXPENSE BREAKDOWN")
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Expenses", "Amount"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setIndentation(24)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        tree_layout.addWidget(self.tree, 1)
        root.addWidget(tree_card, 1)

        # Transactions table card
        table_card, table_layout = ModernPageMixin.create_card("TRANSACTIONS")
        self.table = QtWidgets.QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Date", "Description", "Amount", "From Account", "Category", "Sub-category"]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(34)
        table_layout.addWidget(self.table, 1)
        root.addWidget(table_card, 1)

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
                to_date = date(latest.year, latest.month + 1, 1) - timedelta(days=1)
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

        # Show/hide entire containers
        self._monthly_container.setVisible(is_monthly)
        self._yearly_container.setVisible(is_yearly)
        self._custom_container.setVisible(is_custom)

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
        """Build tree for monthly view: Expenses -> Categories -> Sub-categories."""
        if self._current_period is None:
            return
        total = self._controller.total_for_month(self._current_period)
        root_item = QtWidgets.QTreeWidgetItem(["Expenses", self._fmt_currency(total)])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        # Add categories and sub-categories
        for cat, cat_total, subs in self._controller.category_breakdown(self._current_period):
            cat_name = cat.title() if cat else "Uncategorized"
            cat_item = QtWidgets.QTreeWidgetItem([cat_name, self._fmt_currency(cat_total)])
            cat_item.setData(0, self.ROLE_NODE_KIND, "category")
            cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
            cat_item.setData(0, self.ROLE_MONTH, None)
            cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            # Style category item - bold, larger font
            cat_font = cat_item.font(0)
            cat_font.setBold(True)
            cat_font.setPointSize(14)
            cat_item.setFont(0, cat_font)
            cat_item.setFont(1, cat_font)

            for sub, amt in subs:
                sub_name = sub.title() if sub else "Uncategorized"
                sub_item = QtWidgets.QTreeWidgetItem([sub_name, self._fmt_currency(amt)])
                sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                sub_item.setData(0, self.ROLE_MONTH, None)
                sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                # Style sub-category - regular weight
                sub_font = sub_item.font(0)
                sub_font.setPointSize(13)
                sub_item.setFont(0, sub_font)
                sub_item.setFont(1, sub_font)

                cat_item.addChild(sub_item)
            root_item.addChild(cat_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_yearly(self) -> None:
        """Build tree for yearly view: Year Total -> Month -> Categories -> Sub-categories."""
        if self._current_year is None:
            return
        year_total = self._controller.total_for_year(self._current_year)
        root_item = QtWidgets.QTreeWidgetItem([f"Expenses {self._current_year}", self._fmt_currency(year_total)])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        # Add month nodes
        for period, month_total, cat_breakdown in self._controller.year_breakdown(self._current_year):
            month_label = self._controller.month_label(period)
            month_item = QtWidgets.QTreeWidgetItem([month_label, self._fmt_currency(month_total)])
            month_item.setData(0, self.ROLE_NODE_KIND, "month")
            month_item.setData(0, self.ROLE_MONTH, period)
            month_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            # Bold month items
            font = month_item.font(0)
            font.setBold(True)
            font.setPointSize(14)
            month_item.setFont(0, font)
            month_item.setFont(1, font)

            # Add category children
            for cat, cat_total, subs in cat_breakdown:
                cat_name = cat.title() if cat else "Uncategorized"
                cat_item = QtWidgets.QTreeWidgetItem([cat_name, self._fmt_currency(cat_total)])
                cat_item.setData(0, self.ROLE_NODE_KIND, "category")
                cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
                cat_item.setData(0, self.ROLE_MONTH, period)
                cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                # Style category
                cat_font = cat_item.font(0)
                cat_font.setBold(True)
                cat_font.setPointSize(14)
                cat_item.setFont(0, cat_font)
                cat_item.setFont(1, cat_font)

                for sub, amt in subs:
                    sub_name = sub.title() if sub else "Uncategorized"
                    sub_item = QtWidgets.QTreeWidgetItem([sub_name, self._fmt_currency(amt)])
                    sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                    sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                    sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                    sub_item.setData(0, self.ROLE_MONTH, period)
                    sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                    # Style sub-category
                    sub_font = sub_item.font(0)
                    sub_font.setPointSize(13)
                    sub_item.setFont(0, sub_font)
                    sub_item.setFont(1, sub_font)

                    cat_item.addChild(sub_item)

                month_item.addChild(cat_item)

            root_item.addChild(month_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_custom(self) -> None:
        """Build tree for custom range view: Total -> Categories -> Sub-categories."""
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        total = self._controller.total_for_range(start, end)
        root_item = QtWidgets.QTreeWidgetItem(["Expenses", self._fmt_currency(total)])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        # Add categories and sub-categories
        for cat, cat_total, subs in self._controller.category_breakdown_for_range(start, end):
            cat_name = cat.title() if cat else "Uncategorized"
            cat_item = QtWidgets.QTreeWidgetItem([cat_name, self._fmt_currency(cat_total)])
            cat_item.setData(0, self.ROLE_NODE_KIND, "category")
            cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
            cat_item.setData(0, self.ROLE_MONTH, None)
            cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            # Style category
            cat_font = cat_item.font(0)
            cat_font.setBold(True)
            cat_font.setPointSize(14)
            cat_item.setFont(0, cat_font)
            cat_item.setFont(1, cat_font)

            for sub, amt in subs:
                sub_name = sub.title() if sub else "Uncategorized"
                sub_item = QtWidgets.QTreeWidgetItem([sub_name, self._fmt_currency(amt)])
                sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                sub_item.setData(0, self.ROLE_MONTH, None)
                sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                # Style sub-category
                sub_font = sub_item.font(0)
                sub_font.setPointSize(13)
                sub_item.setFont(0, sub_font)
                sub_item.setFont(1, sub_font)

                cat_item.addChild(sub_item)
            root_item.addChild(cat_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _style_root_item(self, item: QtWidgets.QTreeWidgetItem) -> None:
        """Apply bold styling to root tree item."""
        font = item.font(0)
        font.setBold(True)
        font.setPointSize(15)
        item.setFont(0, font)
        item.setFont(1, font)
        item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _refresh_table(self) -> None:
        mode = self._current_view_mode
        kind, cat, sub = self._current_selection()
        month = self._current_month_from_tree()

        # Get transactions based on view mode
        if mode == VIEW_MODE_MONTHLY:
            if self._current_period is None:
                self.table.setRowCount(0)
                return
            if kind == "root":
                df = self._controller.transactions(self._current_period)
            elif kind == "category":
                df = self._controller.transactions(self._current_period, category=cat)
            else:
                df = self._controller.transactions(self._current_period, category=cat, sub_category=sub)
        elif mode == VIEW_MODE_YEARLY:
            if self._current_year is None:
                self.table.setRowCount(0)
                return
            if kind == "root":
                df = self._controller.transactions_for_year(self._current_year)
            elif kind == "month":
                df = self._controller.transactions_for_year(self._current_year, month=month)
            elif kind == "category":
                df = self._controller.transactions_for_year(
                    self._current_year, month=month, category=cat
                )
            else:
                df = self._controller.transactions_for_year(
                    self._current_year, month=month, category=cat, sub_category=sub
                )
        elif mode == VIEW_MODE_CUSTOM:
            start = self.from_date.date().toPython()
            end = self.to_date.date().toPython()
            if kind == "root":
                df = self._controller.transactions_for_range(start, end)
            elif kind == "category":
                df = self._controller.transactions_for_range(start, end, category=cat)
            else:
                df = self._controller.transactions_for_range(start, end, category=cat, sub_category=sub)
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
    def _on_view_mode_changed(self, mode: str) -> None:
        self._current_view_mode = mode
        self._logger.info("ExpensesPage: View mode changed -> %s", mode)
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
        self._logger.info("ExpensesPage: Month changed -> %s", period)
        self._rebuild_tree()
        self._refresh_table()

    def _on_year_changed(self, index: int) -> None:
        if self._current_view_mode != VIEW_MODE_YEARLY:
            return
        year = self.year_combo.currentData()
        self._current_year = year
        self._logger.info("ExpensesPage: Year changed -> %s", year)
        self._rebuild_tree()
        self._refresh_table()

    def _on_apply_custom_range(self) -> None:
        if self._current_view_mode != VIEW_MODE_CUSTOM:
            return
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        self._logger.info("ExpensesPage: Custom range applied -> %s to %s", start, end)
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
