"""Earnings page with KPI cards, donut chart, and transaction tables.

Provides income tracking by sub-category with budget comparison.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.controller import EarningsStatsController
from budget_analyser.controller.budget_controller import BudgetController
from budget_analyser.views.pages._page_base import ModernPageMixin
from budget_analyser.views.widgets.kpi_card import KPICard, KPICardData
from budget_analyser.views.widgets.charts import PieChartWidget
from budget_analyser.views.constants import (
    COLOR_INCOME,
    COLOR_POSITIVE,
    COLOR_EXPENSE,
    COLOR_PRIMARY,
    INCOME_CHART_COLORS,
    format_currency,
    format_percentage,
)

import pandas as pd


# View mode constants
VIEW_MODE_MONTHLY = "Monthly"
VIEW_MODE_YEARLY = "Yearly"
VIEW_MODE_CUSTOM = "Custom Range"


class EarningsPage(QtWidgets.QWidget):
    """Earnings page with KPI cards, donut chart, and transaction tables."""

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
        self._controller = EarningsStatsController(
            self._reports, self._logger, budget_controller=self._budget_controller
        )

        self._current_period = None
        self._current_year: Optional[int] = None
        self._current_view_mode = VIEW_MODE_MONTHLY
        self._current_sub_category: Optional[str] = None
        self._last_rows = []
        self._last_actual_total = 0.0
        self._last_expected_total = 0.0
        self._init_ui()

    def _init_ui(self) -> None:
        # Scroll area
        scroll, container = ModernPageMixin.create_scroll_area()

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        header = ModernPageMixin.create_page_header(
            title="Earnings",
            subtitle="Track income by sub-category with budget comparison",
            icon="💰"
        )
        root.addWidget(header)

        # KPI Cards Section
        kpi_section = self._create_kpi_section()
        root.addWidget(kpi_section)

        # Filters card
        filters_card = self._create_filters_section()
        root.addWidget(filters_card)

        # Earnings breakdown section (chart + table)
        breakdown_section = self._create_breakdown_section()
        root.addWidget(breakdown_section)

        # Transactions card
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

        # Initial visibility and selection
        self._update_selector_visibility()
        if self.month_combo.count() > 0:
            self.month_combo.setCurrentIndex(self.month_combo.count() - 1)
        self._rebuild_summary()

    def _create_kpi_section(self) -> QtWidgets.QWidget:
        """Create KPI summary cards row."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Total Income Card
        self._total_income_card = KPICard(KPICardData(
            title="TOTAL INCOME",
            value="$0.00",
            accent_color=COLOR_INCOME,
        ))
        layout.addWidget(self._total_income_card)

        # VS Expected Card
        self._vs_expected_card = KPICard(KPICardData(
            title="VS EXPECTED",
            value="$0.00",
        ))
        layout.addWidget(self._vs_expected_card)

        # Top Source Card
        self._top_source_card = KPICard(KPICardData(
            title="TOP SOURCE",
            value="--",
            accent_color=COLOR_PRIMARY,
        ))
        layout.addWidget(self._top_source_card)

        return container

    def _create_filters_section(self) -> QtWidgets.QWidget:
        """Create filters card."""
        filters_card, filters_layout = ModernPageMixin.create_card("FILTERS")

        # View Mode
        view_label = ModernPageMixin.create_control_label("View Mode")
        filters_layout.addWidget(view_label)

        self.view_mode_combo = QtWidgets.QComboBox()
        self.view_mode_combo.addItems([VIEW_MODE_MONTHLY, VIEW_MODE_YEARLY, VIEW_MODE_CUSTOM])
        ModernPageMixin.style_combo_box(self.view_mode_combo)
        filters_layout.addWidget(self.view_mode_combo)

        # Date selection container
        self._date_selection = QtWidgets.QWidget()
        date_layout = QtWidgets.QVBoxLayout(self._date_selection)
        date_layout.setContentsMargins(0, 16, 0, 0)
        date_layout.setSpacing(12)

        # Monthly selectors
        self._monthly_container = QtWidgets.QWidget()
        monthly_layout = QtWidgets.QVBoxLayout(self._monthly_container)
        monthly_layout.setContentsMargins(0, 0, 0, 0)
        monthly_layout.setSpacing(8)

        self.month_label = ModernPageMixin.create_control_label("Select Month")
        monthly_layout.addWidget(self.month_label)

        self.month_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.month_combo)
        monthly_layout.addWidget(self.month_combo)

        date_layout.addWidget(self._monthly_container)

        # Yearly selectors
        self._yearly_container = QtWidgets.QWidget()
        yearly_layout = QtWidgets.QVBoxLayout(self._yearly_container)
        yearly_layout.setContentsMargins(0, 0, 0, 0)
        yearly_layout.setSpacing(8)

        self.year_label = ModernPageMixin.create_control_label("Select Year")
        yearly_layout.addWidget(self.year_label)

        self.year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self.year_combo)
        yearly_layout.addWidget(self.year_combo)

        date_layout.addWidget(self._yearly_container)

        # Custom range selectors
        self._custom_container = QtWidgets.QWidget()
        custom_layout = QtWidgets.QVBoxLayout(self._custom_container)
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.setSpacing(8)

        date_range_label = ModernPageMixin.create_control_label("Date Range")
        custom_layout.addWidget(date_range_label)

        date_range_row = QtWidgets.QWidget()
        date_range_layout = QtWidgets.QHBoxLayout(date_range_row)
        date_range_layout.setContentsMargins(0, 0, 0, 0)
        date_range_layout.setSpacing(12)

        self.from_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.from_date)
        date_range_layout.addWidget(self.from_date, 1)

        to_label = QtWidgets.QLabel("to")
        to_label.setStyleSheet("color: #8B5CF6; font-weight: 600;")
        date_range_layout.addWidget(to_label)

        self.to_date = QtWidgets.QDateEdit()
        ModernPageMixin.style_date_edit(self.to_date)
        date_range_layout.addWidget(self.to_date, 1)

        self.apply_btn = ModernPageMixin.create_action_button("Apply", primary=False)
        date_range_layout.addWidget(self.apply_btn)

        custom_layout.addWidget(date_range_row)
        date_layout.addWidget(self._custom_container)

        filters_layout.addWidget(self._date_selection)

        return filters_card

    def _create_breakdown_section(self) -> QtWidgets.QWidget:
        """Create earnings breakdown section with chart and table."""
        card, card_layout = ModernPageMixin.create_card("EARNINGS BREAKDOWN")

        # Content container with chart and table side by side
        content = QtWidgets.QWidget()
        content_layout = QtWidgets.QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(24)

        # Donut chart
        chart_container = QtWidgets.QWidget()
        chart_layout = QtWidgets.QVBoxLayout(chart_container)
        chart_layout.setContentsMargins(0, 0, 0, 0)
        chart_layout.setSpacing(8)

        chart_title = QtWidgets.QLabel("INCOME DISTRIBUTION")
        chart_title.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #9CA3AF;
        """)
        chart_layout.addWidget(chart_title)

        self._income_chart = PieChartWidget(donut=True)
        self._income_chart.setMinimumSize(220, 220)
        self._income_chart.setMaximumSize(280, 280)
        chart_layout.addWidget(self._income_chart)
        chart_layout.addStretch()

        content_layout.addWidget(chart_container)

        # Summary table
        table_container = QtWidgets.QWidget()
        table_layout = QtWidgets.QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        self.summary_table = QtWidgets.QTableWidget(0, 6)
        self.summary_table.setHorizontalHeaderLabels([
            "Sub-category", "Actual", "% Total", "Expected", "Diff", "Diff %"
        ])
        self.summary_table.verticalHeader().setVisible(False)
        self.summary_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.summary_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.summary_table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.summary_table.horizontalHeader().setStretchLastSection(False)
        self.summary_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        for col in range(1, 6):
            self.summary_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.verticalHeader().setDefaultSectionSize(34)
        self.summary_table.itemSelectionChanged.connect(self._on_summary_selection_changed)
        table_layout.addWidget(self.summary_table)

        content_layout.addWidget(table_container, 1)

        card_layout.addWidget(content)

        return card

    def _create_transactions_section(self) -> QtWidgets.QWidget:
        """Create transactions table card."""
        transactions_card, transactions_layout = ModernPageMixin.create_card("TRANSACTIONS")

        self.table = QtWidgets.QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Amount", "From Account", "Sub-category"
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(32)
        transactions_layout.addWidget(self.table)

        return transactions_card

    def _update_kpi_cards(self) -> None:
        """Update KPI cards with current data."""
        rows = self._last_rows
        actual_total = self._last_actual_total
        expected_total = self._last_expected_total

        # Total Income Card
        diff = actual_total - expected_total
        diff_pct = (diff / expected_total * 100) if expected_total > 0 else 0

        trend_direction = "up" if diff >= 0 else "down"
        trend_value = format_percentage(abs(diff_pct), show_sign=False)

        self._total_income_card.update_data(KPICardData(
            title="TOTAL INCOME",
            value=format_currency(actual_total),
            trend_value=trend_value if expected_total > 0 else None,
            trend_direction=trend_direction,
            comparison_text=f"Expected: {format_currency(expected_total)}" if expected_total > 0 else None,
            accent_color=COLOR_INCOME,
        ))

        # VS Expected Card
        vs_color = COLOR_POSITIVE if diff >= 0 else COLOR_EXPENSE
        pct_of_expected = (actual_total / expected_total * 100) if expected_total > 0 else 0

        self._vs_expected_card.update_data(KPICardData(
            title="VS EXPECTED",
            value=format_currency(diff, show_sign=True) if expected_total > 0 else "--",
            progress_percent=pct_of_expected if expected_total > 0 else None,
            comparison_text=f"{pct_of_expected:.0f}% of target" if expected_total > 0 else "No budget set",
            accent_color=vs_color,
            value_color=vs_color,
        ))

        # Top Source Card
        if rows:
            top_row = max(rows, key=lambda r: r.actual)
            top_pct = (top_row.actual / actual_total * 100) if actual_total > 0 else 0
            self._top_source_card.update_data(KPICardData(
                title="TOP SOURCE",
                value=top_row.sub_category or "Uncategorized",
                trend_value=f"{top_pct:.0f}%",
                trend_direction="neutral",
                comparison_text=f"{format_currency(top_row.actual)} this period",
                accent_color=COLOR_PRIMARY,
            ))
        else:
            self._top_source_card.update_data(KPICardData(
                title="TOP SOURCE",
                value="--",
                comparison_text="No income data",
                accent_color=COLOR_PRIMARY,
            ))

    def _update_income_chart(self) -> None:
        """Update the income distribution donut chart."""
        rows = self._last_rows

        if not rows:
            self._income_chart.set_data([], [])
            return

        labels = []
        values = []
        colors = []

        for i, row in enumerate(rows):
            if row.actual > 0:
                labels.append(row.sub_category or "Uncategorized")
                values.append(row.actual)
                colors.append(INCOME_CHART_COLORS[i % len(INCOME_CHART_COLORS)])

        self._income_chart.set_data(labels, values, colors=colors)

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

    def _rebuild_summary(self) -> None:
        mode = self._current_view_mode
        rows = []
        actual_total = 0.0
        expected_total = 0.0

        if mode == VIEW_MODE_MONTHLY:
            if self._current_period is not None:
                rows, actual_total, expected_total = self._controller.table_for_month(
                    self._current_period
                )
        elif mode == VIEW_MODE_YEARLY:
            if self._current_year is not None:
                rows, actual_total, expected_total = self._controller.table_for_year(
                    self._current_year
                )
        elif mode == VIEW_MODE_CUSTOM:
            start = self.from_date.date().toPython()
            end = self.to_date.date().toPython()
            rows, actual_total, expected_total = self._controller.table_for_range(start, end)

        # Store for KPI updates
        self._last_rows = rows
        self._last_actual_total = actual_total
        self._last_expected_total = expected_total

        self._populate_summary_table(rows, actual_total, expected_total)
        self._update_kpi_cards()
        self._update_income_chart()
        self._select_default_row()

    def _populate_summary_table(
        self, rows, actual_total: float, expected_total: float
    ) -> None:
        self.summary_table.setSortingEnabled(False)
        self.summary_table.setRowCount(0)
        self.summary_table.clearSelection()

        def _add_row(
            values, bold: bool = False, color: Optional[QtGui.QColor] = None,
            raw_name: Optional[str] = None, color_indicator: str | None = None
        ):
            r = self.summary_table.rowCount()
            self.summary_table.insertRow(r)
            for c, text in enumerate(values):
                item = QtWidgets.QTableWidgetItem(text)
                if c == 0 and raw_name is not None:
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

        # Data rows with color indicator
        for i, row in enumerate(rows):
            diff_color = QtGui.QColor("#10B981") if row.diff >= 0 else QtGui.QColor("#EF4444")
            raw_name = row.sub_category or "(Uncategorized)"
            chart_color = INCOME_CHART_COLORS[i % len(INCOME_CHART_COLORS)]
            _add_row([
                f"● {raw_name}",
                self._fmt_currency(row.actual),
                self._fmt_percent(row.percent_of_total),
                self._fmt_currency(row.expected),
                self._fmt_currency(row.diff),
                self._fmt_percent(row.diff_percent),
            ], bold=False, color=diff_color, raw_name=raw_name, color_indicator=chart_color)

        # Total row
        total_diff = actual_total - expected_total
        total_color = QtGui.QColor("#10B981") if total_diff >= 0 else QtGui.QColor("#EF4444")
        _add_row([
            "TOTAL",
            self._fmt_currency(actual_total),
            self._fmt_percent(100.0 if rows else 0.0),
            self._fmt_currency(expected_total),
            self._fmt_currency(total_diff),
            self._fmt_percent((total_diff / expected_total * 100) if expected_total > 0 else None),
        ], bold=True, color=total_color, raw_name=None)

        self.summary_table.setSortingEnabled(True)
        self.summary_table.resizeColumnsToContents()

    def _refresh_table(self) -> None:
        mode = self._current_view_mode
        sub = self._current_sub_category

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

    def _on_view_mode_changed(self, mode: str) -> None:
        self._current_view_mode = mode
        self._logger.info("EarningsPage: View mode changed -> %s", mode)
        self._update_selector_visibility()

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

        # Update selection indicators
        for row in range(self.summary_table.rowCount()):
            name_item = self.summary_table.item(row, 0)
            if name_item is None:
                continue
            raw_name = name_item.data(QtCore.Qt.UserRole)
            if raw_name is None:
                continue
            indicator = "●" if row == selected_row else "○"
            name_item.setText(f"{indicator} {raw_name}")

        # Set current sub-category
        if selected_row < 0:
            self._current_sub_category = None
        else:
            name_item = self.summary_table.item(selected_row, 0)
            if name_item:
                raw_name = name_item.data(QtCore.Qt.UserRole)
                self._current_sub_category = raw_name
            else:
                self._current_sub_category = None

        self._refresh_table()

    @staticmethod
    def _fmt_currency(value: float) -> str:
        try:
            return f"${value:,.2f}"
        except Exception:
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
            return str(getattr(value, "date", lambda: value)()) if hasattr(value, "date") else str(value)[:10]
        except Exception:
            return str(value)[:10]

    def _select_default_row(self) -> None:
        if self.summary_table.rowCount() == 0:
            self._current_sub_category = None
            return
        for row in range(self.summary_table.rowCount()):
            name_item = self.summary_table.item(row, 0)
            if name_item:
                raw_name = name_item.data(QtCore.Qt.UserRole)
                if raw_name is not None:
                    self.summary_table.selectRow(row)
                    return
        self._current_sub_category = None
