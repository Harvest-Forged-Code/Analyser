"""Expenses page with KPI cards, budget utilization, donut chart, and transaction tables.

Provides expense tracking by category with budget comparison and visual breakdowns.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional, Tuple

from PySide6 import QtCore, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import ExpensesStatsController
from budget_analyser.controller.budget_controller import BudgetController
from budget_analyser.views.pages._page_base import ModernPageMixin
from budget_analyser.views.widgets.kpi_card import KPICard, KPICardData
from budget_analyser.views.widgets.charts import PieChartWidget
from budget_analyser.views.widgets.progress_indicator import (
    BudgetUtilizationSection,
)
from budget_analyser.views.constants import (
    COLOR_EXPENSE,
    COLOR_POSITIVE,
    COLOR_PRIMARY,
    EXPENSE_CHART_COLORS,
    format_currency,
    format_percentage,
)

import pandas as pd


# View mode constants
VIEW_MODE_MONTHLY = "Monthly"
VIEW_MODE_YEARLY = "Yearly"
VIEW_MODE_CUSTOM = "Custom Range"


class ExpensesPage(QtWidgets.QWidget):
    """Expenses page with KPI cards, budget utilization, and category breakdown.

    UI features:
    - KPI cards: Total Spent, VS Budget, Top Category
    - Budget utilization progress bars per category
    - Donut chart for expense distribution
    - Hierarchical tree: Expenses -> Categories -> Sub-categories
    - Transactions table filtered by selection
    """

    ROLE_NODE_KIND = QtCore.Qt.UserRole + 1  # 'root' | 'category' | 'sub' | 'month'
    ROLE_CATEGORY = QtCore.Qt.UserRole + 2
    ROLE_SUB_CATEGORY = QtCore.Qt.UserRole + 3
    ROLE_MONTH = QtCore.Qt.UserRole + 4

    def __init__(
        self,
        reports: List[MonthlyReports],
        logger: logging.Logger,
        budget_controller: BudgetController | None = None
    ):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._budget_controller = budget_controller
        self._controller = ExpensesStatsController(self._reports, self._logger)

        self._current_period = None
        self._current_year: Optional[int] = None
        self._current_view_mode = VIEW_MODE_MONTHLY
        self._last_total = 0.0
        self._last_category_breakdown = []
        self._init_ui()

    def _init_ui(self) -> None:
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        page_header = ModernPageMixin.create_page_header(
            title="Expenses",
            subtitle="Track and analyze your expense categories and transactions",
            icon="🧾"
        )
        root.addWidget(page_header)

        # KPI Cards Section
        kpi_section = self._create_kpi_section()
        root.addWidget(kpi_section)

        # Budget Utilization Section
        budget_section = self._create_budget_utilization_section()
        root.addWidget(budget_section)

        # Filters card
        filters_card = self._create_filters_section()
        root.addWidget(filters_card)

        # Expense breakdown section (chart + tree)
        breakdown_section = self._create_breakdown_section()
        root.addWidget(breakdown_section, 1)

        # Transactions table card
        transactions_card = self._create_transactions_section()
        root.addWidget(transactions_card, 1)

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
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)

    def _create_kpi_section(self) -> QtWidgets.QWidget:
        """Create KPI summary cards row."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Total Spent Card
        self._total_spent_card = KPICard(KPICardData(
            title="TOTAL SPENT",
            value="$0.00",
            accent_color=COLOR_EXPENSE,
            value_color=COLOR_EXPENSE,
        ))
        layout.addWidget(self._total_spent_card)

        # VS Budget Card
        self._vs_budget_card = KPICard(KPICardData(
            title="VS BUDGET",
            value="--",
        ))
        layout.addWidget(self._vs_budget_card)

        # Top Category Card
        self._top_category_card = KPICard(KPICardData(
            title="TOP CATEGORY",
            value="--",
            accent_color=COLOR_PRIMARY,
        ))
        layout.addWidget(self._top_category_card)

        return container

    def _create_budget_utilization_section(self) -> QtWidgets.QWidget:
        """Create budget utilization progress bars section."""
        card, card_layout = ModernPageMixin.create_card("BUDGET UTILIZATION")

        self._budget_utilization = BudgetUtilizationSection()
        self._budget_utilization.category_clicked.connect(self._on_budget_category_clicked)
        card_layout.addWidget(self._budget_utilization)

        return card

    def _create_filters_section(self) -> QtWidgets.QWidget:
        """Create filters card."""
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
        custom_layout = QtWidgets.QHBoxLayout(self._custom_container)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(12)

        from_label = ModernPageMixin.create_control_label("From")
        custom_layout.addWidget(from_label)

        self.from_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.from_date, min_height=44)
        custom_layout.addWidget(self.from_date)

        to_label = QtWidgets.QLabel("to")
        to_label.setStyleSheet("color: #8B5CF6; font-weight: 600;")
        custom_layout.addWidget(to_label)

        self.to_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.to_date, min_height=44)
        custom_layout.addWidget(self.to_date)

        self.apply_btn = ModernPageMixin.create_action_button("Apply", primary=False)
        custom_layout.addWidget(self.apply_btn)

        custom_layout.addStretch()

        filters_layout.addWidget(self._custom_container)

        return filters_card

    def _create_breakdown_section(self) -> QtWidgets.QWidget:
        """Create expense breakdown section with chart and tree."""
        card, card_layout = ModernPageMixin.create_card("EXPENSE BREAKDOWN")

        # Content container with chart and tree side by side
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)

        # Donut chart
        chart_container = QtWidgets.QWidget()
        chart_layout = QtWidgets.QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(8)

        chart_title = QtWidgets.QLabel("SPENDING BY CATEGORY")
        chart_title.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #9CA3AF;
        """)
        chart_layout.addWidget(chart_title)

        self._expense_chart = PieChartWidget(donut=True)
        self._expense_chart.setMinimumSize(220, 220)
        self._expense_chart.setMaximumSize(280, 280)
        chart_layout.addWidget(self._expense_chart)
        chart_layout.addStretch()

        content_layout.addWidget(chart_container)

        # Tree widget
        tree_container = QtWidgets.QWidget()
        tree_layout = QtWidgets.QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)

        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Expenses", "Amount", "% Total"])
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setIndentation(24)
        self.tree.setUniformRowHeights(True)
        self.tree.setAlternatingRowColors(True)
        tree_layout.addWidget(self.tree)

        content_layout.addWidget(tree_container, 1)

        card_layout.addWidget(content)

        return card

    def _create_transactions_section(self) -> QtWidgets.QWidget:
        """Create transactions table card."""
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
        table_layout.addWidget(self.table)

        return table_card

    def _update_kpi_cards(self) -> None:
        """Update KPI cards with current data."""
        total = self._last_total
        breakdown = self._last_category_breakdown

        # Total Spent Card
        self._total_spent_card.update_data(KPICardData(
            title="TOTAL SPENT",
            value=format_currency(total),
            accent_color=COLOR_EXPENSE,
            value_color=COLOR_EXPENSE,
        ))

        # VS Budget Card - compare against budget goals
        total_budget = self._get_total_budget_for_period()
        if total_budget > 0:
            diff = total_budget - total
            pct_used = (total / total_budget * 100) if total_budget > 0 else 0
            vs_color = COLOR_POSITIVE if diff >= 0 else COLOR_EXPENSE
            self._vs_budget_card.update_data(KPICardData(
                title="VS BUDGET",
                value=format_currency(diff, show_sign=True),
                progress_percent=min(pct_used, 100),
                comparison_text=f"{pct_used:.0f}% of {format_currency(total_budget)} budget",
                accent_color=vs_color,
                value_color=vs_color,
            ))
        else:
            self._vs_budget_card.update_data(KPICardData(
                title="VS BUDGET",
                value="--",
                comparison_text="No budget set",
                accent_color=COLOR_POSITIVE,
            ))

        # Top Category Card
        if breakdown:
            top_cat = max(breakdown, key=lambda x: x[1])
            top_pct = (top_cat[1] / total * 100) if total > 0 else 0
            self._top_category_card.update_data(KPICardData(
                title="TOP CATEGORY",
                value=(top_cat[0] or "Uncategorized").title(),
                trend_value=f"{top_pct:.0f}%",
                trend_direction="neutral",
                comparison_text=f"{format_currency(top_cat[1])} this period",
                accent_color=COLOR_PRIMARY,
            ))
        else:
            self._top_category_card.update_data(KPICardData(
                title="TOP CATEGORY",
                value="--",
                comparison_text="No expense data",
                accent_color=COLOR_PRIMARY,
            ))

    def _update_expense_chart(self) -> None:
        """Update the expense distribution donut chart."""
        breakdown = self._last_category_breakdown

        if not breakdown:
            self._expense_chart.set_data([], [])
            return

        labels = []
        values = []
        colors = []

        for i, (cat, cat_total, _) in enumerate(breakdown):
            if cat_total > 0:
                labels.append((cat or "Uncategorized").title())
                values.append(cat_total)
                colors.append(EXPENSE_CHART_COLORS[i % len(EXPENSE_CHART_COLORS)])

        self._expense_chart.set_data(labels, values, colors=colors)

    def _get_total_budget_for_period(self) -> float:
        """Get total budget for the current period from BudgetController."""
        if self._budget_controller is None:
            return 0.0

        year_month = self._get_current_year_month()
        if not year_month:
            return 0.0

        total_budget = 0.0
        budgets = self._budget_controller.get_all_budgets()

        for budget in budgets:
            # Match specific month or "ALL"
            if budget.year_month == year_month or budget.year_month == "ALL":
                # Prefer month-specific over "ALL"
                total_budget += budget.monthly_limit

        return total_budget

    def _get_budget_for_category(self, category: str) -> float:
        """Get budget limit for a specific category."""
        if self._budget_controller is None:
            return 0.0

        year_month = self._get_current_year_month()
        if not year_month:
            return 0.0

        budget = self._budget_controller.get_budget(category, year_month)
        return budget.monthly_limit if budget else 0.0

    def _get_current_year_month(self) -> str | None:
        """Get current year-month string based on view mode."""
        mode = self._current_view_mode
        if mode == VIEW_MODE_MONTHLY and self._current_period is not None:
            return self._current_period.strftime("%Y-%m")
        elif mode == VIEW_MODE_YEARLY and self._current_year is not None:
            # For yearly view, we can't use month-specific budgets directly
            # Return None to indicate we need to aggregate
            return None
        return None

    def _update_budget_utilization(self) -> None:
        """Update budget utilization progress bars using actual budget goals."""
        breakdown = self._last_category_breakdown
        total = self._last_total

        if not breakdown or total <= 0:
            self._budget_utilization.clear()
            return

        if self._budget_controller is None:
            # Fallback: show spending without budget comparison
            allocations = []
            for cat, cat_total, _ in sorted(breakdown, key=lambda x: x[1], reverse=True)[:5]:
                cat_name = (cat or "Uncategorized").title()
                allocations.append((cat_name, 0.0, cat_total))
            self._budget_utilization.update_budgets(allocations)
            return

        # Get budget data for each category
        allocations = []
        for cat, cat_total, _ in sorted(breakdown, key=lambda x: x[1], reverse=True)[:5]:
            cat_name = (cat or "Uncategorized").title()
            budget_limit = self._get_budget_for_category(cat or "")
            allocations.append((cat_name, budget_limit, cat_total))

        self._budget_utilization.update_budgets(allocations)

    def _on_budget_category_clicked(self, category: str) -> None:
        """Handle click on budget utilization category."""
        self._logger.info("Budget category clicked: %s", category)
        # Could navigate to filter tree by this category

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
        if self.year_combo.count() > 0:
            self.year_combo.setCurrentIndex(self.year_combo.count() - 1)

    def _set_default_date_range(self) -> None:
        """Set default date range based on available data."""
        months = self._controller.available_months()
        if months:
            earliest = months[0]
            latest = months[-1]
            from_date = date(earliest.year, earliest.month, 1)
            if latest.month == 12:
                to_date = date(latest.year, 12, 31)
            else:
                to_date = date(latest.year, latest.month + 1, 1) - timedelta(days=1)
            self.from_date.setDate(QtCore.QDate(from_date.year, from_date.month, from_date.day))
            self.to_date.setDate(QtCore.QDate(to_date.year, to_date.month, to_date.day))
        else:
            today = date.today()
            self.from_date.setDate(QtCore.QDate(today.year, 1, 1))
            self.to_date.setDate(QtCore.QDate(today.year, today.month, today.day))

    def _update_selector_visibility(self) -> None:
        """Show/hide date selectors based on current view mode."""
        mode = self.view_mode_combo.currentText()
        self._monthly_container.setVisible(mode == VIEW_MODE_MONTHLY)
        self._yearly_container.setVisible(mode == VIEW_MODE_YEARLY)
        self._custom_container.setVisible(mode == VIEW_MODE_CUSTOM)

    def _rebuild_tree(self) -> None:
        self.tree.clear()
        mode = self._current_view_mode

        if mode == VIEW_MODE_MONTHLY:
            self._rebuild_tree_monthly()
        elif mode == VIEW_MODE_YEARLY:
            self._rebuild_tree_yearly()
        elif mode == VIEW_MODE_CUSTOM:
            self._rebuild_tree_custom()

        # Update KPI cards and charts after tree rebuild
        self._update_kpi_cards()
        self._update_expense_chart()
        self._update_budget_utilization()

    def _rebuild_tree_monthly(self) -> None:
        """Build tree for monthly view."""
        if self._current_period is None:
            return
        total = self._controller.total_for_month(self._current_period)
        breakdown = list(self._controller.category_breakdown(self._current_period))

        self._last_total = total
        self._last_category_breakdown = breakdown

        root_item = QtWidgets.QTreeWidgetItem(["Expenses", self._fmt_currency(total), "100%"])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        for i, (cat, cat_total, subs) in enumerate(breakdown):
            cat_name = (cat or "Uncategorized").title()
            cat_pct = (cat_total / total * 100) if total > 0 else 0
            cat_item = QtWidgets.QTreeWidgetItem([
                f"● {cat_name}",
                self._fmt_currency(cat_total),
                f"{cat_pct:.1f}%"
            ])
            cat_item.setData(0, self.ROLE_NODE_KIND, "category")
            cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
            cat_item.setData(0, self.ROLE_MONTH, None)
            cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            cat_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            cat_font = cat_item.font(0)
            cat_font.setBold(True)
            cat_font.setPointSize(14)
            cat_item.setFont(0, cat_font)
            cat_item.setFont(1, cat_font)
            cat_item.setFont(2, cat_font)

            for sub, amt in subs:
                sub_name = (sub or "Uncategorized").title()
                sub_pct = (amt / total * 100) if total > 0 else 0
                sub_item = QtWidgets.QTreeWidgetItem([
                    sub_name,
                    self._fmt_currency(amt),
                    f"{sub_pct:.1f}%"
                ])
                sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                sub_item.setData(0, self.ROLE_MONTH, None)
                sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                sub_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                sub_font = sub_item.font(0)
                sub_font.setPointSize(13)
                sub_item.setFont(0, sub_font)
                sub_item.setFont(1, sub_font)
                sub_item.setFont(2, sub_font)

                cat_item.addChild(sub_item)
            root_item.addChild(cat_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_yearly(self) -> None:
        """Build tree for yearly view."""
        if self._current_year is None:
            return
        year_total = self._controller.total_for_year(self._current_year)

        # Aggregate category breakdown for the year
        all_breakdown = {}
        for period, _, cat_breakdown in self._controller.year_breakdown(self._current_year):
            for cat, cat_total, subs in cat_breakdown:
                if cat not in all_breakdown:
                    all_breakdown[cat] = [0.0, {}]
                all_breakdown[cat][0] += cat_total
                for sub, amt in subs:
                    if sub not in all_breakdown[cat][1]:
                        all_breakdown[cat][1][sub] = 0.0
                    all_breakdown[cat][1][sub] += amt

        breakdown = [
            (cat, data[0], list(data[1].items()))
            for cat, data in all_breakdown.items()
        ]
        breakdown.sort(key=lambda x: x[1], reverse=True)

        self._last_total = year_total
        self._last_category_breakdown = breakdown

        root_item = QtWidgets.QTreeWidgetItem([
            f"Expenses {self._current_year}",
            self._fmt_currency(year_total),
            "100%"
        ])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        # Add month nodes
        for period, month_total, cat_breakdown in self._controller.year_breakdown(self._current_year):
            month_label = self._controller.month_label(period)
            month_pct = (month_total / year_total * 100) if year_total > 0 else 0
            month_item = QtWidgets.QTreeWidgetItem([
                month_label,
                self._fmt_currency(month_total),
                f"{month_pct:.1f}%"
            ])
            month_item.setData(0, self.ROLE_NODE_KIND, "month")
            month_item.setData(0, self.ROLE_MONTH, period)
            month_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            month_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            font = month_item.font(0)
            font.setBold(True)
            font.setPointSize(14)
            month_item.setFont(0, font)
            month_item.setFont(1, font)
            month_item.setFont(2, font)

            for cat, cat_total, subs in cat_breakdown:
                cat_name = (cat or "Uncategorized").title()
                cat_pct = (cat_total / month_total * 100) if month_total > 0 else 0
                cat_item = QtWidgets.QTreeWidgetItem([
                    f"● {cat_name}",
                    self._fmt_currency(cat_total),
                    f"{cat_pct:.1f}%"
                ])
                cat_item.setData(0, self.ROLE_NODE_KIND, "category")
                cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
                cat_item.setData(0, self.ROLE_MONTH, period)
                cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                cat_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                cat_font = cat_item.font(0)
                cat_font.setBold(True)
                cat_font.setPointSize(14)
                cat_item.setFont(0, cat_font)
                cat_item.setFont(1, cat_font)
                cat_item.setFont(2, cat_font)

                for sub, amt in subs:
                    sub_name = (sub or "Uncategorized").title()
                    sub_pct = (amt / month_total * 100) if month_total > 0 else 0
                    sub_item = QtWidgets.QTreeWidgetItem([
                        sub_name,
                        self._fmt_currency(amt),
                        f"{sub_pct:.1f}%"
                    ])
                    sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                    sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                    sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                    sub_item.setData(0, self.ROLE_MONTH, period)
                    sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    sub_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                    sub_font = sub_item.font(0)
                    sub_font.setPointSize(13)
                    sub_item.setFont(0, sub_font)
                    sub_item.setFont(1, sub_font)
                    sub_item.setFont(2, sub_font)

                    cat_item.addChild(sub_item)

                month_item.addChild(cat_item)

            root_item.addChild(month_item)

        self.tree.addTopLevelItem(root_item)
        self.tree.expandItem(root_item)
        self.tree.setCurrentItem(root_item)

    def _rebuild_tree_custom(self) -> None:
        """Build tree for custom range view."""
        start = self.from_date.date().toPython()
        end = self.to_date.date().toPython()
        total = self._controller.total_for_range(start, end)
        breakdown = list(self._controller.category_breakdown_for_range(start, end))

        self._last_total = total
        self._last_category_breakdown = breakdown

        root_item = QtWidgets.QTreeWidgetItem(["Expenses", self._fmt_currency(total), "100%"])
        root_item.setData(0, self.ROLE_NODE_KIND, "root")
        root_item.setData(0, self.ROLE_MONTH, None)
        self._style_root_item(root_item)

        for cat, cat_total, subs in breakdown:
            cat_name = (cat or "Uncategorized").title()
            cat_pct = (cat_total / total * 100) if total > 0 else 0
            cat_item = QtWidgets.QTreeWidgetItem([
                f"● {cat_name}",
                self._fmt_currency(cat_total),
                f"{cat_pct:.1f}%"
            ])
            cat_item.setData(0, self.ROLE_NODE_KIND, "category")
            cat_item.setData(0, self.ROLE_CATEGORY, cat or "")
            cat_item.setData(0, self.ROLE_MONTH, None)
            cat_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            cat_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

            cat_font = cat_item.font(0)
            cat_font.setBold(True)
            cat_font.setPointSize(14)
            cat_item.setFont(0, cat_font)
            cat_item.setFont(1, cat_font)
            cat_item.setFont(2, cat_font)

            for sub, amt in subs:
                sub_name = (sub or "Uncategorized").title()
                sub_pct = (amt / total * 100) if total > 0 else 0
                sub_item = QtWidgets.QTreeWidgetItem([
                    sub_name,
                    self._fmt_currency(amt),
                    f"{sub_pct:.1f}%"
                ])
                sub_item.setData(0, self.ROLE_NODE_KIND, "sub")
                sub_item.setData(0, self.ROLE_CATEGORY, cat or "")
                sub_item.setData(0, self.ROLE_SUB_CATEGORY, sub or "")
                sub_item.setData(0, self.ROLE_MONTH, None)
                sub_item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                sub_item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

                sub_font = sub_item.font(0)
                sub_font.setPointSize(13)
                sub_item.setFont(0, sub_font)
                sub_item.setFont(1, sub_font)
                sub_item.setFont(2, sub_font)

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
        item.setFont(2, font)
        item.setTextAlignment(1, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        item.setTextAlignment(2, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _refresh_table(self) -> None:
        mode = self._current_view_mode
        kind, cat, sub = self._current_selection()
        month = self._current_month_from_tree()

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

        if not df.empty and "transaction_date" in df.columns:
            try:
                df = df.sort_values(by="transaction_date", ascending=False)
            except Exception:
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
            it2 = QtWidgets.QTableWidgetItem(self._fmt_currency(abs(amt)))
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

    def _on_view_mode_changed(self, mode: str) -> None:
        self._current_view_mode = mode
        self._logger.info("ExpensesPage: View mode changed -> %s", mode)
        self._update_selector_visibility()

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

    def _current_selection(self) -> Tuple[str, Optional[str], Optional[str]]:
        item = self.tree.currentItem()
        if item is None:
            return "root", None, None
        kind = item.data(0, self.ROLE_NODE_KIND) or "root"
        cat = item.data(0, self.ROLE_CATEGORY)
        sub = item.data(0, self.ROLE_SUB_CATEGORY)
        return str(kind), (str(cat) if cat else None), (str(sub) if sub else None)

    def _current_month_from_tree(self) -> Optional[pd.Period]:
        """Get the month period from the currently selected tree item."""
        item = self.tree.currentItem()
        if item is None:
            return None
        return item.data(0, self.ROLE_MONTH)

    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:
            return str(value)

    @staticmethod
    def _fmt_date(value) -> str:
        try:
            return str(getattr(value, "date", lambda: value)()) if hasattr(value, "date") else str(value)[:10]
        except Exception:
            return str(value)[:10]
