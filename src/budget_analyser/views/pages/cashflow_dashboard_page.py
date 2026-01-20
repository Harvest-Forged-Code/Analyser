"""Unified Cashflow Dashboard page (views layer).

Purpose:
    Provide a unified view of earnings and expenses with:
    - Summary cards (Total Income, Total Expenses, Net Savings, Savings Rate)
    - Monthly cashflow chart (income vs expenses with net line)
    - Category breakdown charts
    - Quick filters (This month, Last 3 months, This year)

This page combines data from earnings and expenses into a single dashboard.
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.views.pages._page_base import ModernPageMixin

import pandas as pd


# Filter presets
FILTER_THIS_MONTH = "This Month"
FILTER_LAST_3_MONTHS = "Last 3 Months"
FILTER_LAST_6_MONTHS = "Last 6 Months"
FILTER_THIS_YEAR = "This Year"
FILTER_LAST_YEAR = "Last Year"
FILTER_ALL_TIME = "All Time"


class SummaryCard(QtWidgets.QFrame):
    """A summary metric card widget."""

    def __init__(
        self,
        title: str,
        value: str = "$0.00",
        subtitle: str = "",
        icon: str = "",
        color: str = "#8B5CF6",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._setup_ui(title, value, subtitle, icon, color)

    def _setup_ui(
        self, title: str, value: str, subtitle: str, icon: str, color: str
    ) -> None:
        self.setFrameStyle(QtWidgets.QFrame.Shape.StyledPanel)
        self.setObjectName("card")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # Header with icon and title
        header = QtWidgets.QHBoxLayout()

        if icon:
            icon_label = QtWidgets.QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 24px; color: {color};")
            header.addWidget(icon_label)

        title_label = QtWidgets.QLabel(title.upper())
        title_label.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #6B7280;
            letter-spacing: 0.5px;
        """)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Value
        self._value_label = QtWidgets.QLabel(value)
        self._value_label.setStyleSheet(f"""
            font-size: 28px;
            font-weight: 700;
            color: {color};
        """)
        layout.addWidget(self._value_label)

        # Subtitle
        if subtitle:
            self._subtitle_label = QtWidgets.QLabel(subtitle)
            self._subtitle_label.setStyleSheet("""
                font-size: 12px;
                color: #9CA3AF;
            """)
            layout.addWidget(self._subtitle_label)
        else:
            self._subtitle_label = None

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        self._value_label.setText(value)

    def set_subtitle(self, subtitle: str) -> None:
        """Update the subtitle text."""
        if self._subtitle_label:
            self._subtitle_label.setText(subtitle)


class CashflowDashboardPage(QtWidgets.QWidget):
    """Unified cashflow dashboard combining earnings and expenses."""

    def __init__(
        self,
        reports: List[MonthlyReports],
        logger: logging.Logger,
    ) -> None:
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._current_filter = FILTER_LAST_3_MONTHS
        self._init_ui()
        self._refresh_data()

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
            title="Cashflow Dashboard",
            subtitle="Overview of your income, expenses, and savings",
            icon="📊"
        )
        root.addWidget(header)

        # Filter bar
        filter_card, filter_layout = ModernPageMixin.create_card("QUICK FILTERS")
        filter_layout.setDirection(QtWidgets.QBoxLayout.Direction.LeftToRight)

        self._filter_buttons = {}
        for filter_name in [
            FILTER_THIS_MONTH,
            FILTER_LAST_3_MONTHS,
            FILTER_LAST_6_MONTHS,
            FILTER_THIS_YEAR,
            FILTER_ALL_TIME,
        ]:
            btn = QtWidgets.QPushButton(filter_name)
            btn.setCheckable(True)
            btn.setChecked(filter_name == self._current_filter)
            btn.clicked.connect(lambda checked, f=filter_name: self._on_filter_clicked(f))
            self._style_filter_button(btn)
            filter_layout.addWidget(btn)
            self._filter_buttons[filter_name] = btn

        filter_layout.addStretch()
        root.addWidget(filter_card)

        # Summary cards row
        cards_row = QtWidgets.QHBoxLayout()
        cards_row.setSpacing(16)

        self._income_card = SummaryCard(
            title="Total Income",
            icon="💰",
            color="#10B981",
        )
        cards_row.addWidget(self._income_card)

        self._expenses_card = SummaryCard(
            title="Total Expenses",
            icon="💸",
            color="#EF4444",
        )
        cards_row.addWidget(self._expenses_card)

        self._savings_card = SummaryCard(
            title="Net Savings",
            icon="🏦",
            color="#3B82F6",
        )
        cards_row.addWidget(self._savings_card)

        self._rate_card = SummaryCard(
            title="Savings Rate",
            icon="📈",
            color="#8B5CF6",
        )
        cards_row.addWidget(self._rate_card)

        root.addLayout(cards_row)

        # Charts row
        charts_row = QtWidgets.QHBoxLayout()
        charts_row.setSpacing(16)

        # Monthly trend chart
        trend_card, trend_layout = ModernPageMixin.create_card("MONTHLY TREND")
        self._trend_chart_placeholder = QtWidgets.QLabel("Monthly trend chart")
        self._trend_chart_placeholder.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._trend_chart_placeholder.setMinimumHeight(250)
        self._trend_chart_placeholder.setStyleSheet("""
            background-color: transparent;
            border: 1px dashed rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            color: #9CA3AF;
        """)

        # Try to use pyqtgraph chart
        try:
            from budget_analyser.views.widgets.charts import BarChartWidget
            self._trend_chart = BarChartWidget()
            self._trend_chart.setMinimumHeight(250)
            self._trend_chart.set_dark_mode(True)
            trend_layout.addWidget(self._trend_chart)
        except ImportError:
            trend_layout.addWidget(self._trend_chart_placeholder)
            self._trend_chart = None

        charts_row.addWidget(trend_card, 2)

        # Category breakdown
        breakdown_card, breakdown_layout = ModernPageMixin.create_card("EXPENSE BREAKDOWN")
        self._breakdown_placeholder = QtWidgets.QLabel("Category breakdown chart")
        self._breakdown_placeholder.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._breakdown_placeholder.setMinimumHeight(250)
        self._breakdown_placeholder.setStyleSheet("""
            background-color: transparent;
            border: 1px dashed rgba(139, 92, 246, 0.3);
            border-radius: 8px;
            color: #9CA3AF;
        """)

        try:
            from budget_analyser.views.widgets.charts import PieChartWidget
            self._breakdown_chart = PieChartWidget(donut=True)
            self._breakdown_chart.setMinimumHeight(250)
            self._breakdown_chart.set_dark_mode(True)
            breakdown_layout.addWidget(self._breakdown_chart)
        except ImportError:
            breakdown_layout.addWidget(self._breakdown_placeholder)
            self._breakdown_chart = None

        charts_row.addWidget(breakdown_card, 1)

        root.addLayout(charts_row)

        # Detailed table
        table_card, table_layout = ModernPageMixin.create_card("MONTHLY SUMMARY")

        self._table = QtWidgets.QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            "Month", "Income", "Expenses", "Net Savings", "Savings Rate"
        ])
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(34)

        table_layout.addWidget(self._table)
        root.addWidget(table_card, 1)

    def _style_filter_button(self, btn: QtWidgets.QPushButton) -> None:
        """Style a filter button."""
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(18, 18, 20, 0.8);
                border: 1px solid rgba(60, 60, 70, 0.4);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 500;
                color: #9CA3AF;
            }
            QPushButton:hover {
                background-color: rgba(139, 92, 246, 0.1);
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: rgba(139, 92, 246, 0.25);
                border-color: rgba(139, 92, 246, 0.4);
                color: #FFFFFF;
            }
        """)

    def _on_filter_clicked(self, filter_name: str) -> None:
        """Handle filter button click."""
        self._current_filter = filter_name

        # Update button states
        for name, btn in self._filter_buttons.items():
            btn.setChecked(name == filter_name)

        self._refresh_data()

    def _get_date_range(self) -> tuple[date, date]:
        """Get date range based on current filter."""
        today = date.today()

        if self._current_filter == FILTER_THIS_MONTH:
            start = date(today.year, today.month, 1)
            end = today
        elif self._current_filter == FILTER_LAST_3_MONTHS:
            start = today - timedelta(days=90)
            end = today
        elif self._current_filter == FILTER_LAST_6_MONTHS:
            start = today - timedelta(days=180)
            end = today
        elif self._current_filter == FILTER_THIS_YEAR:
            start = date(today.year, 1, 1)
            end = today
        elif self._current_filter == FILTER_LAST_YEAR:
            start = date(today.year - 1, 1, 1)
            end = date(today.year - 1, 12, 31)
        else:  # All time
            start = date(2000, 1, 1)
            end = today

        return start, end

    def _refresh_data(self) -> None:
        """Refresh all data based on current filter."""
        start_date, end_date = self._get_date_range()

        # Collect data from reports
        total_income = 0.0
        total_expenses = 0.0
        monthly_data: dict[str, dict[str, float]] = {}
        category_totals: dict[str, float] = {}

        for report in self._reports:
            if report.transactions is None or report.transactions.empty:
                continue

            df = report.transactions

            # Filter by date range
            if "transaction_date" in df.columns:
                df["_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
                mask = (df["_date"].dt.date >= start_date) & (df["_date"].dt.date <= end_date)
                df = df[mask]

            if df.empty:
                continue

            month_key = str(report.month)

            # Calculate income and expenses
            income = df[df["amount"] > 0]["amount"].sum()
            expenses = abs(df[df["amount"] < 0]["amount"].sum())

            total_income += income
            total_expenses += expenses

            monthly_data[month_key] = {
                "income": income,
                "expenses": expenses,
                "savings": income - expenses,
            }

            # Category breakdown (expenses only)
            if "category" in df.columns:
                expense_df = df[df["amount"] < 0]
                for cat, amt in expense_df.groupby("category")["amount"].sum().items():
                    cat_str = str(cat) if cat else "Uncategorized"
                    category_totals[cat_str] = category_totals.get(cat_str, 0) + abs(amt)

        # Update summary cards
        net_savings = total_income - total_expenses
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

        self._income_card.set_value(f"${total_income:,.2f}")
        self._expenses_card.set_value(f"${total_expenses:,.2f}")
        self._savings_card.set_value(f"${net_savings:,.2f}")
        self._rate_card.set_value(f"{savings_rate:.1f}%")

        # Update charts
        self._update_trend_chart(monthly_data)
        self._update_breakdown_chart(category_totals)

        # Update table
        self._update_table(monthly_data)

    def _update_trend_chart(self, monthly_data: dict[str, dict[str, float]]) -> None:
        """Update the monthly trend chart."""
        if self._trend_chart is None:
            return

        if not monthly_data:
            return

        # Sort by month
        sorted_months = sorted(monthly_data.keys())
        months = [m[-5:] for m in sorted_months]  # Show MM-YY format
        income_values = [monthly_data[m]["income"] for m in sorted_months]
        expense_values = [monthly_data[m]["expenses"] for m in sorted_months]

        self._trend_chart.set_grouped_data(
            categories=months,
            series_data={
                "Income": income_values,
                "Expenses": expense_values,
            },
            colors={
                "Income": "#10B981",
                "Expenses": "#EF4444",
            },
        )

    def _update_breakdown_chart(self, category_totals: dict[str, float]) -> None:
        """Update the category breakdown chart."""
        if self._breakdown_chart is None:
            return

        if not category_totals:
            return

        # Sort by value and take top categories
        sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        top_cats = sorted_cats[:8]  # Top 8 categories

        labels = [c[0] for c in top_cats]
        values = [c[1] for c in top_cats]

        self._breakdown_chart.set_data(labels=labels, values=values)

    def _update_table(self, monthly_data: dict[str, dict[str, float]]) -> None:
        """Update the monthly summary table."""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        sorted_months = sorted(monthly_data.keys(), reverse=True)

        for month in sorted_months:
            data = monthly_data[month]
            row = self._table.rowCount()
            self._table.insertRow(row)

            income = data["income"]
            expenses = data["expenses"]
            savings = data["savings"]
            rate = (savings / income * 100) if income > 0 else 0

            self._table.setItem(row, 0, QtWidgets.QTableWidgetItem(month))

            income_item = QtWidgets.QTableWidgetItem(f"${income:,.2f}")
            income_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            income_item.setForeground(QtGui.QBrush(QtGui.QColor("#10B981")))
            self._table.setItem(row, 1, income_item)

            expense_item = QtWidgets.QTableWidgetItem(f"${expenses:,.2f}")
            expense_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            expense_item.setForeground(QtGui.QBrush(QtGui.QColor("#EF4444")))
            self._table.setItem(row, 2, expense_item)

            savings_item = QtWidgets.QTableWidgetItem(f"${savings:,.2f}")
            savings_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            color = QtGui.QColor("#10B981") if savings >= 0 else QtGui.QColor("#EF4444")
            savings_item.setForeground(QtGui.QBrush(color))
            self._table.setItem(row, 3, savings_item)

            rate_item = QtWidgets.QTableWidgetItem(f"{rate:.1f}%")
            rate_item.setTextAlignment(
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, 4, rate_item)

        self._table.resizeColumnsToContents()
        self._table.setSortingEnabled(True)
