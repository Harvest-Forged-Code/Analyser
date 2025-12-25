"""Savings Rate Page - Track savings rate and financial health metrics."""

from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

if TYPE_CHECKING:
    from budget_analyser.controller.budget_controller import BudgetController, SavingsMetrics
    from budget_analyser.controller.controllers import MonthlyReports


class SavingsPage(QtWidgets.QWidget):
    """Page for tracking savings rate and financial health metrics."""

    def __init__(
        self,
        reports: List["MonthlyReports"],
        budget_controller: "BudgetController",
        logger: logging.Logger
    ) -> None:
        super().__init__()
        self._reports = reports
        self._budget_controller = budget_controller
        self._logger = logger
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QtWidgets.QLabel("Savings Rate Calculator")
        header.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(header)

        # Description
        desc = QtWidgets.QLabel(
            "Track your savings rate - a key indicator of financial health. "
            "Savings Rate = (Earnings - Expenses) / Earnings × 100"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Year selector
        year_layout = QtWidgets.QHBoxLayout()
        year_layout.addWidget(QtWidgets.QLabel("Select Year:"))
        self._year_combo = QtWidgets.QComboBox()
        self._year_combo.setMinimumWidth(120)
        self._year_combo.currentIndexChanged.connect(self._on_year_changed)
        year_layout.addWidget(self._year_combo)
        year_layout.addStretch()
        layout.addLayout(year_layout)

        # Summary Cards Row
        cards_layout = QtWidgets.QHBoxLayout()
        
        self._earnings_card = self._create_summary_card("Total Earnings", "$0.00", "#6bcb77")
        cards_layout.addWidget(self._earnings_card)
        
        self._expenses_card = self._create_summary_card("Total Expenses", "$0.00", "#ff6b6b")
        cards_layout.addWidget(self._expenses_card)
        
        self._savings_card = self._create_summary_card("Net Savings", "$0.00", "#4d96ff")
        cards_layout.addWidget(self._savings_card)
        
        self._rate_card = self._create_summary_card("Savings Rate", "0%", "#9b59b6")
        cards_layout.addWidget(self._rate_card)
        
        layout.addLayout(cards_layout)

        # Main content splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel - Monthly breakdown table
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        left_header = QtWidgets.QLabel("Monthly Breakdown")
        left_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        left_layout.addWidget(left_header)

        self._monthly_table = QtWidgets.QTableWidget()
        self._monthly_table.setColumnCount(5)
        self._monthly_table.setHorizontalHeaderLabels([
            "Month", "Earnings", "Expenses", "Savings", "Rate"
        ])
        self._monthly_table.horizontalHeader().setStretchLastSection(True)
        self._monthly_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        for col in range(1, 5):
            self._monthly_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._monthly_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._monthly_table.setAlternatingRowColors(True)
        left_layout.addWidget(self._monthly_table)

        splitter.addWidget(left_panel)

        # Right panel - Insights and Goals
        right_panel = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Insights section
        insights_group = QtWidgets.QGroupBox("📊 Insights")
        insights_layout = QtWidgets.QVBoxLayout(insights_group)
        
        self._insights_label = QtWidgets.QLabel()
        self._insights_label.setWordWrap(True)
        self._insights_label.setStyleSheet("padding: 10px;")
        insights_layout.addWidget(self._insights_label)
        
        right_layout.addWidget(insights_group)

        # Emergency Fund Progress
        emergency_group = QtWidgets.QGroupBox("🏦 Emergency Fund Progress")
        emergency_layout = QtWidgets.QVBoxLayout(emergency_group)
        
        self._emergency_label = QtWidgets.QLabel("Target: 3-6 months of expenses")
        self._emergency_label.setStyleSheet("color: #666;")
        emergency_layout.addWidget(self._emergency_label)
        
        self._emergency_progress = QtWidgets.QProgressBar()
        self._emergency_progress.setRange(0, 100)
        self._emergency_progress.setTextVisible(True)
        self._emergency_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #6bcb77;
                border-radius: 4px;
            }
        """)
        emergency_layout.addWidget(self._emergency_progress)
        
        self._emergency_detail = QtWidgets.QLabel()
        self._emergency_detail.setStyleSheet("color: #666; font-size: 12px;")
        emergency_layout.addWidget(self._emergency_detail)
        
        right_layout.addWidget(emergency_group)

        # Tips section
        tips_group = QtWidgets.QGroupBox("💡 Savings Tips")
        tips_layout = QtWidgets.QVBoxLayout(tips_group)
        tips_text = QtWidgets.QLabel(
            "• Aim for 20%+ savings rate for financial security\n"
            "• 50/30/20 rule: 50% needs, 30% wants, 20% savings\n"
            "• Build 3-6 months emergency fund first\n"
            "• Automate savings to 'pay yourself first'\n"
            "• Track spending to find areas to cut"
        )
        tips_text.setStyleSheet("color: #666;")
        tips_layout.addWidget(tips_text)
        right_layout.addWidget(tips_group)

        right_layout.addStretch()

        splitter.addWidget(right_panel)
        splitter.setSizes([500, 400])

        layout.addWidget(splitter)

    def _create_summary_card(self, title: str, value: str, color: str) -> QtWidgets.QFrame:
        """Create a summary card widget."""
        card = QtWidgets.QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 2px solid {color};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        
        layout = QtWidgets.QVBoxLayout(card)
        
        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 12px;")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title_label)
        
        value_label = QtWidgets.QLabel(value)
        value_label.setObjectName("value_label")
        value_label.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: bold;")
        value_label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(value_label)
        
        return card

    def _populate_years(self) -> None:
        """Populate year selector from available data."""
        self._year_combo.clear()
        years = set()
        
        for mr in self._reports:
            if hasattr(mr.month, 'year'):
                years.add(mr.month.year)
        
        for year in sorted(years, reverse=True):
            self._year_combo.addItem(str(year), year)

    def _load_data(self) -> None:
        """Load all data."""
        self._populate_years()
        self._refresh_data()

    def _refresh_data(self) -> None:
        """Refresh all data displays."""
        year = self._year_combo.currentData()
        if year is None:
            return

        # Get earnings and expenses DataFrames
        import pandas as pd
        
        all_earnings = []
        all_expenses = []
        
        for mr in self._reports:
            if hasattr(mr, 'earnings') and not mr.earnings.empty:
                all_earnings.append(mr.earnings)
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                all_expenses.append(mr.expenses)
        
        earnings_df = pd.concat(all_earnings, ignore_index=True) if all_earnings else pd.DataFrame()
        expenses_df = pd.concat(all_expenses, ignore_index=True) if all_expenses else pd.DataFrame()

        # Calculate metrics
        metrics = self._budget_controller.calculate_savings_metrics(earnings_df, expenses_df, year)
        monthly_data = self._budget_controller.calculate_monthly_savings(earnings_df, expenses_df, year)

        # Update summary cards
        self._update_card(self._earnings_card, f"${metrics.total_earnings:,.2f}")
        self._update_card(self._expenses_card, f"${metrics.total_expenses:,.2f}")
        self._update_card(self._savings_card, f"${metrics.net_savings:,.2f}")
        
        rate_text = f"{metrics.savings_rate:.1f}%"
        self._update_card(self._rate_card, rate_text)

        # Update monthly table
        self._monthly_table.setRowCount(12)
        for row, (month, earnings, expenses, savings, rate) in enumerate(monthly_data):
            # Month
            month_item = QtWidgets.QTableWidgetItem(month)
            month_item.setFlags(month_item.flags() & ~QtCore.Qt.ItemIsEditable)
            self._monthly_table.setItem(row, 0, month_item)
            
            # Earnings
            earn_item = QtWidgets.QTableWidgetItem(f"${earnings:,.2f}")
            earn_item.setFlags(earn_item.flags() & ~QtCore.Qt.ItemIsEditable)
            earn_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            if earnings > 0:
                earn_item.setForeground(QtGui.QColor("#6bcb77"))
            self._monthly_table.setItem(row, 1, earn_item)
            
            # Expenses
            exp_item = QtWidgets.QTableWidgetItem(f"${expenses:,.2f}")
            exp_item.setFlags(exp_item.flags() & ~QtCore.Qt.ItemIsEditable)
            exp_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            if expenses > 0:
                exp_item.setForeground(QtGui.QColor("#ff6b6b"))
            self._monthly_table.setItem(row, 2, exp_item)
            
            # Savings
            sav_item = QtWidgets.QTableWidgetItem(f"${savings:,.2f}")
            sav_item.setFlags(sav_item.flags() & ~QtCore.Qt.ItemIsEditable)
            sav_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            if savings >= 0:
                sav_item.setForeground(QtGui.QColor("#4d96ff"))
            else:
                sav_item.setForeground(QtGui.QColor("#ff6b6b"))
            self._monthly_table.setItem(row, 3, sav_item)
            
            # Rate
            rate_item = QtWidgets.QTableWidgetItem(f"{rate:.1f}%")
            rate_item.setFlags(rate_item.flags() & ~QtCore.Qt.ItemIsEditable)
            rate_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            if rate >= 20:
                rate_item.setForeground(QtGui.QColor("#6bcb77"))
            elif rate >= 0:
                rate_item.setForeground(QtGui.QColor("#ffd93d"))
            else:
                rate_item.setForeground(QtGui.QColor("#ff6b6b"))
            self._monthly_table.setItem(row, 4, rate_item)

        # Update insights
        self._update_insights(metrics)
        
        # Update emergency fund progress
        self._update_emergency_fund(metrics)

    def _update_card(self, card: QtWidgets.QFrame, value: str) -> None:
        """Update a summary card's value."""
        value_label = card.findChild(QtWidgets.QLabel, "value_label")
        if value_label:
            value_label.setText(value)

    def _update_insights(self, metrics: "SavingsMetrics") -> None:
        """Update the insights section."""
        insights = []
        
        # Savings rate assessment
        if metrics.savings_rate >= 30:
            insights.append("🌟 <b>Excellent!</b> Your savings rate is above 30%.")
        elif metrics.savings_rate >= 20:
            insights.append("✅ <b>Good job!</b> You're meeting the recommended 20% savings rate.")
        elif metrics.savings_rate >= 10:
            insights.append("⚠️ <b>Room for improvement.</b> Try to increase savings to 20%.")
        elif metrics.savings_rate > 0:
            insights.append("🔴 <b>Low savings rate.</b> Review expenses to find areas to cut.")
        else:
            insights.append("❌ <b>Negative savings.</b> You're spending more than you earn.")

        # Monthly average
        if metrics.monthly_average_savings > 0:
            insights.append(
                f"📈 Average monthly savings: <b>${metrics.monthly_average_savings:,.2f}</b>"
            )
        
        # Yearly projection
        yearly_projection = metrics.monthly_average_savings * 12
        if yearly_projection > 0:
            insights.append(
                f"📅 Projected yearly savings: <b>${yearly_projection:,.2f}</b>"
            )

        # Data coverage
        insights.append(f"📊 Based on <b>{metrics.months_of_data}</b> months of data")

        self._insights_label.setText("<br><br>".join(insights))

    def _update_emergency_fund(self, metrics: "SavingsMetrics") -> None:
        """Update emergency fund progress."""
        # Calculate monthly expenses average
        monthly_expenses = metrics.total_expenses / max(metrics.months_of_data, 1)
        
        # Target: 6 months of expenses
        target_6_months = monthly_expenses * 6
        target_3_months = monthly_expenses * 3
        
        # Assume current savings equals net_savings (simplified)
        # In a real app, this would come from account balances
        current_savings = max(metrics.net_savings, 0)
        
        if target_6_months > 0:
            progress_percent = min((current_savings / target_6_months) * 100, 100)
        else:
            progress_percent = 0
        
        self._emergency_progress.setValue(int(progress_percent))
        
        # Update color based on progress
        if progress_percent >= 100:
            color = "#6bcb77"  # Green - fully funded
        elif progress_percent >= 50:
            color = "#ffd93d"  # Yellow - 3 months covered
        else:
            color = "#ff6b6b"  # Red - below 3 months
        
        self._emergency_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #ccc;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        
        self._emergency_detail.setText(
            f"3-month target: ${target_3_months:,.2f} | "
            f"6-month target: ${target_6_months:,.2f}\n"
            f"Current savings: ${current_savings:,.2f} ({progress_percent:.1f}% of 6-month goal)"
        )

    def _on_year_changed(self, index: int) -> None:
        """Handle year selection change."""
        self._refresh_data()
