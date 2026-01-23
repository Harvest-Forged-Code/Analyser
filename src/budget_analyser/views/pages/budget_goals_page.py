"""Budget Goals Page - Set and manage budget limits and earnings expectations.

Redesigned with tabs: Set Goals and Manage Goals.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import List, TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.views.pages._page_base import ModernPageMixin
from budget_analyser.views.widgets.kpi_card import KPICard, KPICardData
from budget_analyser.views.widgets.progress_indicator import (
    HorizontalProgressBar,
    ProgressData,
)
from budget_analyser.views.constants import (
    COLOR_PRIMARY,
    COLOR_POSITIVE,
    COLOR_EXPENSE,
    COLOR_WARNING,
    COLOR_INCOME,
    format_currency,
    format_year_month,
    MONTH_NAMES_SHORT,
)

if TYPE_CHECKING:
    from budget_analyser.controller.budget_controller import BudgetController, BudgetProgress
    from budget_analyser.controller.controllers import MonthlyReports
    import pandas as pd


class BudgetGoalsPage(QtWidgets.QWidget):
    """Page for managing budget goals with tabs for setting and managing goals.

    Features:
    - Tab 1: Set Goals - KPI cards, budget allocation, earnings expectations
    - Tab 2: Manage Goals - View, edit, delete, and apply goals to year
    """

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
        self._months: list[str] = []
        self._available_years: list[int] = []
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self._tab_widget = QtWidgets.QTabWidget()
        self._tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: rgba(60, 60, 70, 0.4);
                color: #9CA3AF;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background: rgba(139, 92, 246, 0.3);
                color: #F5F3FF;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(60, 60, 70, 0.6);
            }
        """)

        # Tab 1: Set Goals
        set_goals_tab = self._create_set_goals_tab()
        self._tab_widget.addTab(set_goals_tab, "Set Goals")

        # Tab 2: Manage Goals
        manage_goals_tab = self._create_manage_goals_tab()
        self._tab_widget.addTab(manage_goals_tab, "Manage Goals")

        main_layout.addWidget(self._tab_widget)

    def _create_set_goals_tab(self) -> QtWidgets.QWidget:
        """Create the Set Goals tab with existing functionality."""
        scroll, container = ModernPageMixin.create_scroll_area()

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        header = ModernPageMixin.create_page_header(
            title="Budget Goals",
            subtitle="Set targets and track your progress toward financial goals",
            icon="🎯"
        )
        root.addWidget(header)

        # KPI Cards Section
        kpi_section = self._create_kpi_section()
        root.addWidget(kpi_section)

        # Month selector
        month_section = self._create_month_selector()
        root.addWidget(month_section)

        # Budget Allocation Section
        budget_section = self._create_budget_section()
        root.addWidget(budget_section)

        # Earnings Expectations Section
        earnings_section = self._create_earnings_section()
        root.addWidget(earnings_section)

        return scroll

    def _create_manage_goals_tab(self) -> QtWidgets.QWidget:
        """Create the Manage Goals tab for viewing and editing existing goals."""
        scroll, container = ModernPageMixin.create_scroll_area()

        root = QtWidgets.QVBoxLayout(container)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(24)

        # Header
        header = ModernPageMixin.create_page_header(
            title="Manage Goals",
            subtitle="View, edit, and manage your budget and earnings goals",
            icon="📋"
        )
        root.addWidget(header)

        # Year and Month filter
        filter_card, filter_layout = ModernPageMixin.create_card("FILTER")
        filter_row, filter_row_layout = ModernPageMixin.create_controls_row()

        year_label = ModernPageMixin.create_control_label("Year:")
        filter_row_layout.addWidget(year_label)

        self._manage_year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._manage_year_combo, min_height=40)
        self._manage_year_combo.setMinimumWidth(120)
        self._manage_year_combo.currentIndexChanged.connect(self._refresh_manage_tables)
        filter_row_layout.addWidget(self._manage_year_combo)

        month_label = ModernPageMixin.create_control_label("Month:")
        filter_row_layout.addWidget(month_label)

        self._manage_month_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._manage_month_combo, min_height=40)
        self._manage_month_combo.setMinimumWidth(140)
        self._manage_month_combo.currentIndexChanged.connect(self._refresh_manage_tables)
        filter_row_layout.addWidget(self._manage_month_combo)

        filter_row_layout.addStretch()
        filter_layout.addWidget(filter_row)
        root.addWidget(filter_card)

        # Budget Goals Section
        budget_card, budget_layout = ModernPageMixin.create_card("BUDGET GOALS")

        self._manage_budget_table = QtWidgets.QTableWidget()
        self._manage_budget_table.setColumnCount(4)
        self._manage_budget_table.setHorizontalHeaderLabels([
            "Category", "Month", "Limit", "Actions"
        ])
        self._manage_budget_table.verticalHeader().setVisible(False)
        self._manage_budget_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._manage_budget_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._manage_budget_table.horizontalHeader().setStretchLastSection(True)
        self._manage_budget_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        for col in range(1, 3):
            self._manage_budget_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._manage_budget_table.setAlternatingRowColors(True)
        self._manage_budget_table.verticalHeader().setDefaultSectionSize(48)
        budget_layout.addWidget(self._manage_budget_table)

        root.addWidget(budget_card)

        # Earnings Goals Section
        earnings_card, earnings_layout = ModernPageMixin.create_card("EARNINGS GOALS")

        self._manage_earnings_table = QtWidgets.QTableWidget()
        self._manage_earnings_table.setColumnCount(4)
        self._manage_earnings_table.setHorizontalHeaderLabels([
            "Sub-category", "Month", "Expected", "Actions"
        ])
        self._manage_earnings_table.verticalHeader().setVisible(False)
        self._manage_earnings_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._manage_earnings_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._manage_earnings_table.horizontalHeader().setStretchLastSection(True)
        self._manage_earnings_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        for col in range(1, 3):
            self._manage_earnings_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._manage_earnings_table.setAlternatingRowColors(True)
        self._manage_earnings_table.verticalHeader().setDefaultSectionSize(48)
        earnings_layout.addWidget(self._manage_earnings_table)

        root.addWidget(earnings_card)

        return scroll

    def _create_kpi_section(self) -> QtWidgets.QWidget:
        """Create KPI summary cards row."""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Total Budget Card
        self._total_budget_card = KPICard(KPICardData(
            title="TOTAL BUDGET",
            value="$0.00",
            accent_color=COLOR_PRIMARY,
        ))
        layout.addWidget(self._total_budget_card)

        # Remaining Card
        self._remaining_card = KPICard(KPICardData(
            title="REMAINING",
            value="$0.00",
            accent_color=COLOR_POSITIVE,
        ))
        layout.addWidget(self._remaining_card)

        # Categories On Track Card
        self._on_track_card = KPICard(KPICardData(
            title="ON TRACK",
            value="0 of 0",
            accent_color=COLOR_POSITIVE,
        ))
        layout.addWidget(self._on_track_card)

        # Total Earnings Card
        self._earnings_card = KPICard(KPICardData(
            title="EARNINGS VS EXPECTED",
            value="$0.00",
            accent_color=COLOR_INCOME,
        ))
        layout.addWidget(self._earnings_card)

        return container

    def _create_month_selector(self) -> QtWidgets.QWidget:
        """Create month selector card."""
        card, card_layout = ModernPageMixin.create_card("SELECT PERIOD")

        row, row_layout = ModernPageMixin.create_controls_row()

        label = ModernPageMixin.create_control_label("View Progress for:")
        row_layout.addWidget(label)

        self._month_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._month_combo, min_height=44)
        self._month_combo.setMinimumWidth(200)
        self._month_combo.currentIndexChanged.connect(self._on_month_changed)
        row_layout.addWidget(self._month_combo)

        row_layout.addStretch()

        card_layout.addWidget(row)

        return card

    def _create_budget_section(self) -> QtWidgets.QWidget:
        """Create budget allocation section."""
        card, card_layout = ModernPageMixin.create_card("BUDGET ALLOCATION")

        # Progress list container
        self._budget_progress_container = QtWidgets.QWidget()
        self._budget_progress_layout = QtWidgets.QVBoxLayout(self._budget_progress_container)
        self._budget_progress_layout.setContentsMargins(0, 0, 0, 0)
        self._budget_progress_layout.setSpacing(12)
        card_layout.addWidget(self._budget_progress_container)

        # Summary row
        summary_container = QtWidgets.QWidget()
        summary_container.setStyleSheet("""
            background: rgba(139, 92, 246, 0.1);
            border-radius: 12px;
            padding: 16px;
        """)
        summary_layout = QtWidgets.QHBoxLayout(summary_container)
        summary_layout.setContentsMargins(16, 12, 16, 12)

        self._budget_summary_label = QtWidgets.QLabel()
        self._budget_summary_label.setStyleSheet("""
            font-size: 13px;
            color: #E2E4F0;
        """)
        summary_layout.addWidget(self._budget_summary_label)

        summary_layout.addStretch()

        card_layout.addWidget(summary_container)

        # Add Budget Form (collapsible)
        form_card = self._create_budget_form()
        card_layout.addWidget(form_card)

        return card

    def _create_budget_form(self) -> QtWidgets.QWidget:
        """Create add/edit budget form with apply to year option."""
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            background: rgba(60, 60, 70, 0.2);
            border-radius: 12px;
        """)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QtWidgets.QLabel("ADD / UPDATE BUDGET")
        header.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #9CA3AF;
        """)
        layout.addWidget(header)

        # Form row 1 - Category and Apply to Year checkbox
        form_row1 = QtWidgets.QHBoxLayout()
        form_row1.setSpacing(16)

        # Category
        cat_container = QtWidgets.QVBoxLayout()
        cat_label = ModernPageMixin.create_control_label("Category")
        cat_container.addWidget(cat_label)
        self._category_combo = QtWidgets.QComboBox()
        self._category_combo.setEditable(True)
        ModernPageMixin.style_combo_box(self._category_combo, min_height=40)
        self._category_combo.setMinimumWidth(180)
        cat_container.addWidget(self._category_combo)
        form_row1.addLayout(cat_container)

        # Apply to Year checkbox
        self._budget_apply_year_checkbox = QtWidgets.QCheckBox("Apply to all months in year")
        self._budget_apply_year_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E2E4F0;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self._budget_apply_year_checkbox.stateChanged.connect(self._on_budget_apply_year_changed)
        form_row1.addWidget(self._budget_apply_year_checkbox, alignment=QtCore.Qt.AlignBottom)

        form_row1.addStretch()
        layout.addLayout(form_row1)

        # Form row 2 - Month/Year and Limit
        form_row2 = QtWidgets.QHBoxLayout()
        form_row2.setSpacing(16)

        # Year (shown when checkbox is checked)
        year_container = QtWidgets.QVBoxLayout()
        self._budget_year_label = ModernPageMixin.create_control_label("Year")
        year_container.addWidget(self._budget_year_label)
        self._budget_year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._budget_year_combo, min_height=40)
        self._budget_year_combo.setMinimumWidth(100)
        year_container.addWidget(self._budget_year_combo)
        self._budget_year_widget = QtWidgets.QWidget()
        self._budget_year_widget.setLayout(year_container)
        self._budget_year_widget.hide()
        form_row2.addWidget(self._budget_year_widget)

        # Month (shown when checkbox is unchecked)
        month_container = QtWidgets.QVBoxLayout()
        self._budget_month_label = ModernPageMixin.create_control_label("Month")
        month_container.addWidget(self._budget_month_label)
        self._budget_month_combo = QtWidgets.QComboBox()
        self._budget_month_combo.setEditable(True)
        ModernPageMixin.style_combo_box(self._budget_month_combo, min_height=40)
        self._budget_month_combo.setMinimumWidth(140)
        month_container.addWidget(self._budget_month_combo)
        self._budget_month_widget = QtWidgets.QWidget()
        self._budget_month_widget.setLayout(month_container)
        form_row2.addWidget(self._budget_month_widget)

        # Limit
        limit_container = QtWidgets.QVBoxLayout()
        limit_label = ModernPageMixin.create_control_label("Monthly Limit")
        limit_container.addWidget(limit_label)
        self._limit_spin = QtWidgets.QDoubleSpinBox()
        self._limit_spin.setRange(0, 1000000)
        self._limit_spin.setDecimals(2)
        self._limit_spin.setPrefix("$ ")
        self._limit_spin.setValue(500)
        self._limit_spin.setMinimumHeight(40)
        limit_container.addWidget(self._limit_spin)
        form_row2.addLayout(limit_container)

        # Save button
        self._save_btn = ModernPageMixin.create_action_button("Save Budget", primary=False)
        self._save_btn.clicked.connect(self._on_save_budget)
        form_row2.addWidget(self._save_btn, alignment=QtCore.Qt.AlignBottom)

        form_row2.addStretch()

        layout.addLayout(form_row2)

        return container

    def _create_earnings_section(self) -> QtWidgets.QWidget:
        """Create earnings expectations section."""
        card, card_layout = ModernPageMixin.create_card("EARNINGS EXPECTATIONS")

        # Table
        self._earnings_table = QtWidgets.QTableWidget()
        self._earnings_table.setColumnCount(6)
        self._earnings_table.setHorizontalHeaderLabels([
            "Sub-category", "Month", "Actual", "Expected", "Diff", "Actions"
        ])
        self._earnings_table.verticalHeader().setVisible(False)
        self._earnings_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self._earnings_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self._earnings_table.horizontalHeader().setStretchLastSection(True)
        self._earnings_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch
        )
        for col in range(1, 5):
            self._earnings_table.horizontalHeader().setSectionResizeMode(
                col, QtWidgets.QHeaderView.ResizeToContents
            )
        self._earnings_table.setAlternatingRowColors(True)
        self._earnings_table.verticalHeader().setDefaultSectionSize(40)
        card_layout.addWidget(self._earnings_table)

        # Summary
        self._earnings_summary_label = QtWidgets.QLabel()
        self._earnings_summary_label.setStyleSheet("""
            background: rgba(14, 165, 233, 0.1);
            border-radius: 12px;
            padding: 16px;
            font-size: 13px;
            color: #E2E4F0;
        """)
        card_layout.addWidget(self._earnings_summary_label)

        # Add Earnings Form
        form_card = self._create_earnings_form()
        card_layout.addWidget(form_card)

        return card

    def _create_earnings_form(self) -> QtWidgets.QWidget:
        """Create add/edit earnings expectation form with apply to year option."""
        container = QtWidgets.QWidget()
        container.setStyleSheet("""
            background: rgba(60, 60, 70, 0.2);
            border-radius: 12px;
        """)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Header
        header = QtWidgets.QLabel("ADD / UPDATE EXPECTED EARNINGS")
        header.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
            color: #9CA3AF;
        """)
        layout.addWidget(header)

        # Form row 1 - Sub-category and Apply to Year checkbox
        form_row1 = QtWidgets.QHBoxLayout()
        form_row1.setSpacing(16)

        # Sub-category
        sub_container = QtWidgets.QVBoxLayout()
        sub_label = ModernPageMixin.create_control_label("Sub-category")
        sub_container.addWidget(sub_label)
        self._earnings_sub_combo = QtWidgets.QComboBox()
        self._earnings_sub_combo.setEditable(True)
        ModernPageMixin.style_combo_box(self._earnings_sub_combo, min_height=40)
        self._earnings_sub_combo.setMinimumWidth(180)
        sub_container.addWidget(self._earnings_sub_combo)
        form_row1.addLayout(sub_container)

        # Apply to Year checkbox
        self._earnings_apply_year_checkbox = QtWidgets.QCheckBox("Apply to all months in year")
        self._earnings_apply_year_checkbox.setStyleSheet("""
            QCheckBox {
                color: #E2E4F0;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self._earnings_apply_year_checkbox.stateChanged.connect(
            self._on_earnings_apply_year_changed
        )
        form_row1.addWidget(self._earnings_apply_year_checkbox, alignment=QtCore.Qt.AlignBottom)

        form_row1.addStretch()
        layout.addLayout(form_row1)

        # Form row 2 - Month/Year and Amount
        form_row2 = QtWidgets.QHBoxLayout()
        form_row2.setSpacing(16)

        # Year (shown when checkbox is checked)
        year_container = QtWidgets.QVBoxLayout()
        self._earnings_year_label = ModernPageMixin.create_control_label("Year")
        year_container.addWidget(self._earnings_year_label)
        self._earnings_year_combo = QtWidgets.QComboBox()
        ModernPageMixin.style_combo_box(self._earnings_year_combo, min_height=40)
        self._earnings_year_combo.setMinimumWidth(100)
        year_container.addWidget(self._earnings_year_combo)
        self._earnings_year_widget = QtWidgets.QWidget()
        self._earnings_year_widget.setLayout(year_container)
        self._earnings_year_widget.hide()
        form_row2.addWidget(self._earnings_year_widget)

        # Month (shown when checkbox is unchecked)
        month_container = QtWidgets.QVBoxLayout()
        self._earnings_month_label = ModernPageMixin.create_control_label("Month")
        month_container.addWidget(self._earnings_month_label)
        self._earnings_month_combo = QtWidgets.QComboBox()
        self._earnings_month_combo.setEditable(True)
        ModernPageMixin.style_combo_box(self._earnings_month_combo, min_height=40)
        self._earnings_month_combo.setMinimumWidth(140)
        month_container.addWidget(self._earnings_month_combo)
        self._earnings_month_widget = QtWidgets.QWidget()
        self._earnings_month_widget.setLayout(month_container)
        form_row2.addWidget(self._earnings_month_widget)

        # Expected amount
        amount_container = QtWidgets.QVBoxLayout()
        amount_label = ModernPageMixin.create_control_label("Expected Amount")
        amount_container.addWidget(amount_label)
        self._earnings_expected_spin = QtWidgets.QDoubleSpinBox()
        self._earnings_expected_spin.setRange(0, 1000000)
        self._earnings_expected_spin.setDecimals(2)
        self._earnings_expected_spin.setPrefix("$ ")
        self._earnings_expected_spin.setValue(500)
        self._earnings_expected_spin.setMinimumHeight(40)
        amount_container.addWidget(self._earnings_expected_spin)
        form_row2.addLayout(amount_container)

        # Save button
        self._earnings_save_btn = ModernPageMixin.create_action_button(
            "Save Expected", primary=False
        )
        self._earnings_save_btn.clicked.connect(self._on_save_earnings_goal)
        form_row2.addWidget(self._earnings_save_btn, alignment=QtCore.Qt.AlignBottom)

        form_row2.addStretch()

        layout.addLayout(form_row2)

        return container

    def _on_budget_apply_year_changed(self, state: int) -> None:
        """Toggle between month and year selection for budget form."""
        apply_to_year = state == QtCore.Qt.Checked
        self._budget_month_widget.setVisible(not apply_to_year)
        self._budget_year_widget.setVisible(apply_to_year)

    def _on_earnings_apply_year_changed(self, state: int) -> None:
        """Toggle between month and year selection for earnings form."""
        apply_to_year = state == QtCore.Qt.Checked
        self._earnings_month_widget.setVisible(not apply_to_year)
        self._earnings_year_widget.setVisible(apply_to_year)

    def _populate_months(self) -> None:
        """Populate month selectors from available data."""
        months = set()
        years = set()
        for mr in self._reports:
            if hasattr(mr.month, 'strftime'):
                months.add(mr.month.strftime("%Y-%m"))
                years.add(mr.month.year)
        self._months = sorted(months)
        self._available_years = sorted(years)

        # Add current year if not present
        current_year = datetime.now().year
        if current_year not in self._available_years:
            self._available_years.append(current_year)
            self._available_years.sort()

        def _set_month_options(combo: QtWidgets.QComboBox) -> None:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("ALL", "ALL")
            for m in self._months:
                combo.addItem(format_year_month(m), m)  # Display "Jan 2026", store "2026-01"
            if self._months:
                combo.setCurrentIndex(combo.count() - 1)
            else:
                combo.setCurrentIndex(0)
            combo.blockSignals(False)

        def _set_year_options(combo: QtWidgets.QComboBox) -> None:
            combo.blockSignals(True)
            combo.clear()
            for y in self._available_years:
                combo.addItem(str(y), y)
            if self._available_years:
                combo.setCurrentIndex(combo.count() - 1)
            combo.blockSignals(False)

        _set_month_options(self._month_combo)
        _set_month_options(self._budget_month_combo)
        _set_month_options(self._earnings_month_combo)

        _set_year_options(self._budget_year_combo)
        _set_year_options(self._earnings_year_combo)

        # Manage tab year filter
        self._manage_year_combo.blockSignals(True)
        self._manage_year_combo.clear()
        self._manage_year_combo.addItem("All Years", None)
        for y in self._available_years:
            self._manage_year_combo.addItem(str(y), y)
        self._manage_year_combo.blockSignals(False)

        # Manage tab month filter
        self._manage_month_combo.blockSignals(True)
        self._manage_month_combo.clear()
        self._manage_month_combo.addItem("All Months", None)
        for i, name in enumerate(MONTH_NAMES_SHORT):
            self._manage_month_combo.addItem(name, i + 1)  # 1-12
        self._manage_month_combo.blockSignals(False)

    def _populate_categories(self) -> None:
        """Populate category dropdown from existing data."""
        self._category_combo.clear()
        categories = set()

        for mr in self._reports:
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                if 'category' in mr.expenses.columns:
                    categories.update(mr.expenses['category'].dropna().unique())

        standard = ["Needs", "Flexible", "Luxuries", "Savings", "Investments"]
        categories.update(standard)

        for cat in sorted(categories):
            if cat:
                self._category_combo.addItem(cat)

    def _populate_earnings_sub_categories(self) -> None:
        """Populate earnings sub-category dropdown."""
        self._earnings_sub_combo.clear()
        subs = set()
        for mr in self._reports:
            if hasattr(mr, 'earnings') and not mr.earnings.empty:
                if 'sub_category' in mr.earnings.columns:
                    subs.update(mr.earnings['sub_category'].dropna().unique())
        try:
            for goal in self._budget_controller.get_all_earnings_goals():
                if goal.sub_category:
                    subs.add(goal.sub_category)
        except Exception:
            pass
        for sub in sorted(subs):
            self._earnings_sub_combo.addItem(str(sub))

    def _load_data(self) -> None:
        """Load all data."""
        self._populate_months()
        self._populate_categories()
        self._populate_earnings_sub_categories()
        self._refresh_budget_progress()
        self._refresh_earnings_table()
        self._refresh_manage_tables()
        self._update_kpi_cards()

    def _refresh_budget_progress(self) -> None:
        """Refresh the budget progress display."""
        # Clear existing
        while self._budget_progress_layout.count():
            item = self._budget_progress_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        year_month = self._month_combo.currentData()
        if year_month == "ALL" and self._months:
            year_month = self._months[-1]
        if not year_month:
            self._budget_summary_label.setText("No data available")
            return

        expenses_df = self._get_expenses_for_month(year_month)
        progress_list = self._budget_controller.calculate_budget_progress(expenses_df, year_month)

        if not progress_list:
            no_data = QtWidgets.QLabel(
                "No budget goals set yet. Use the form below to add budget limits."
            )
            no_data.setStyleSheet("color: #9CA3AF; padding: 20px;")
            no_data.setAlignment(QtCore.Qt.AlignCenter)
            self._budget_progress_layout.addWidget(no_data)
            self._budget_summary_label.setText("")
            return

        total_budget = 0.0
        total_spent = 0.0
        over_budget_count = 0
        on_track_count = 0

        for progress in progress_list:
            self._add_budget_progress_row(progress)
            total_budget += progress.budget_limit
            total_spent += progress.spent
            if progress.status == "over":
                over_budget_count += 1
            else:
                on_track_count += 1

        remaining = total_budget - total_spent
        pct_used = (total_spent / total_budget * 100) if total_budget > 0 else 0

        summary_parts = [
            f"<b>Total Budget:</b> {format_currency(total_budget)}",
            f"<b>Total Spent:</b> {format_currency(total_spent)}",
            f"<b>Remaining:</b> {format_currency(remaining)}",
        ]
        if over_budget_count > 0:
            summary_parts.append(
                f"<span style='color: #F97316;'>⚠ {over_budget_count} over budget</span>"
            )
        else:
            summary_parts.append(
                f"<span style='color: #10B981;'>✓ All categories on track</span>"
            )

        self._budget_summary_label.setText(" • ".join(summary_parts))

        # Update KPI cards
        self._total_budget_card.update_data(KPICardData(
            title="TOTAL BUDGET",
            value=format_currency(total_budget),
            progress_percent=pct_used,
            comparison_text=f"{pct_used:.0f}% used",
            accent_color=COLOR_PRIMARY,
        ))

        remaining_color = COLOR_POSITIVE if remaining >= 0 else COLOR_EXPENSE
        self._remaining_card.update_data(KPICardData(
            title="REMAINING",
            value=format_currency(remaining),
            comparison_text=f"of {format_currency(total_budget)} budget",
            accent_color=remaining_color,
            value_color=remaining_color,
        ))

        total_categories = on_track_count + over_budget_count
        self._on_track_card.update_data(KPICardData(
            title="ON TRACK",
            value=f"{on_track_count} of {total_categories}",
            comparison_text="categories within budget",
            accent_color=COLOR_POSITIVE if over_budget_count == 0 else COLOR_WARNING,
        ))

    def _add_budget_progress_row(self, progress: "BudgetProgress") -> None:
        """Add a budget progress row."""
        row = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(row)
        row_layout.setContentsMargins(0, 4, 0, 4)
        row_layout.setSpacing(16)

        # Category label
        cat_label = QtWidgets.QLabel(progress.category)
        cat_label.setStyleSheet("""
            font-size: 14px;
            font-weight: 600;
            color: #F5F3FF;
        """)
        cat_label.setMinimumWidth(120)
        row_layout.addWidget(cat_label)

        # Progress bar
        data = ProgressData(
            current=progress.spent,
            target=progress.budget_limit,
            label="",
            format_as_currency=True,
            show_remaining=True,
        )
        progress_bar = HorizontalProgressBar(data, compact=True, show_labels=False)
        row_layout.addWidget(progress_bar, 1)

        # Delete button
        delete_btn = QtWidgets.QPushButton("×")
        delete_btn.setFixedSize(28, 28)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                border: none;
                border-radius: 14px;
                color: #EF4444;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.4);
            }
        """)
        delete_btn.setCursor(QtCore.Qt.PointingHandCursor)
        delete_btn.clicked.connect(
            lambda: self._on_delete_budget(
                progress.category, self._month_combo.currentData() or "ALL"
            )
        )
        row_layout.addWidget(delete_btn)

        self._budget_progress_layout.addWidget(row)

    def _refresh_earnings_table(self) -> None:
        """Refresh earnings expectations table."""
        year_month = self._month_combo.currentData()
        if year_month == "ALL" and self._months:
            year_month = self._months[-1]

        df = self._get_earnings_for_month(year_month) if year_month else None
        expected_map = self._budget_controller.get_earnings_goal_map(year_month or "ALL")
        goals = self._budget_controller.get_all_earnings_goals()

        actual_by_sub: dict[str, float] = {}
        if df is not None and not df.empty:
            if "sub_category" in df.columns:
                grouped = df.groupby("sub_category")['amount'].sum()
                for sub, amt in grouped.items():
                    actual_by_sub[str(sub)] = float(amt)

        subs = set(actual_by_sub.keys()) | set(expected_map.keys())

        rows = []
        total_actual = 0.0
        total_expected = 0.0

        for sub in sorted(subs, key=lambda s: s.lower()):
            actual = actual_by_sub.get(sub, 0.0)
            expected = expected_map.get(sub, 0.0)
            diff = actual - expected

            # Find goal month
            goal_month = "ALL"
            for g in goals:
                if g.sub_category == sub:
                    goal_month = g.year_month
                    break

            rows.append((sub, goal_month, actual, expected, diff))
            total_actual += actual
            total_expected += expected

        self._earnings_table.setSortingEnabled(False)
        self._earnings_table.setRowCount(0)

        for sub, month, actual, expected, diff in rows:
            r = self._earnings_table.rowCount()
            self._earnings_table.insertRow(r)

            # Sub-category
            sub_item = QtWidgets.QTableWidgetItem(sub)
            self._earnings_table.setItem(r, 0, sub_item)

            # Month - formatted as "Jan 2026"
            display_month = format_year_month(month)
            month_item = QtWidgets.QTableWidgetItem(display_month)
            month_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._earnings_table.setItem(r, 1, month_item)

            # Actual
            actual_item = QtWidgets.QTableWidgetItem(format_currency(actual))
            actual_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._earnings_table.setItem(r, 2, actual_item)

            # Expected
            expected_item = QtWidgets.QTableWidgetItem(format_currency(expected))
            expected_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._earnings_table.setItem(r, 3, expected_item)

            # Diff
            diff_item = QtWidgets.QTableWidgetItem(format_currency(diff, show_sign=True))
            diff_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            diff_color = QtGui.QColor(COLOR_POSITIVE if diff >= 0 else COLOR_EXPENSE)
            diff_item.setForeground(QtGui.QBrush(diff_color))
            self._earnings_table.setItem(r, 4, diff_item)

            # Delete button
            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(239, 68, 68, 0.2);
                    border: 1px solid rgba(239, 68, 68, 0.3);
                    border-radius: 6px;
                    color: #EF4444;
                    padding: 4px 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: rgba(239, 68, 68, 0.3);
                }
            """)
            delete_btn.clicked.connect(
                lambda checked, s=sub, m=month: self._on_delete_earnings_goal(s, m)
            )
            self._earnings_table.setCellWidget(r, 5, delete_btn)

        self._earnings_table.setSortingEnabled(True)

        # Update summary
        total_diff = total_actual - total_expected
        diff_color = COLOR_POSITIVE if total_diff >= 0 else COLOR_EXPENSE

        self._earnings_summary_label.setText(
            f"<b>Total Actual:</b> {format_currency(total_actual)} • "
            f"<b>Total Expected:</b> {format_currency(total_expected)} • "
            f"<b style='color: {diff_color};'>Diff: {format_currency(total_diff, show_sign=True)}"
            f"</b>"
        )

        # Update KPI card
        self._earnings_card.update_data(KPICardData(
            title="EARNINGS VS EXPECTED",
            value=format_currency(total_diff, show_sign=True),
            comparison_text=f"Actual: {format_currency(total_actual)}",
            accent_color=COLOR_INCOME if total_diff >= 0 else COLOR_EXPENSE,
            value_color=COLOR_INCOME if total_diff >= 0 else COLOR_EXPENSE,
        ))

    def _refresh_manage_tables(self) -> None:
        """Refresh the manage goals tables."""
        selected_year = self._manage_year_combo.currentData()
        selected_month = self._manage_month_combo.currentData()  # 1-12 or None

        def _matches_filter(year_month: str) -> bool:
            """Check if goal matches year and month filters."""
            if year_month == "ALL":
                return selected_year is None and selected_month is None

            if selected_year is not None:
                if not year_month.startswith(str(selected_year)):
                    return False

            if selected_month is not None:
                try:
                    goal_month = int(year_month.split("-")[1])
                    if goal_month != selected_month:
                        return False
                except (ValueError, IndexError):
                    return False

            return True

        # Refresh budget goals table - sorted by month for grouping
        budget_goals = self._budget_controller.get_all_budgets()
        # Sort by year_month for grouping
        sorted_budget_goals = sorted(
            budget_goals,
            key=lambda g: (g.year_month if g.year_month != "ALL" else "0000-00", g.category)
        )

        self._manage_budget_table.setSortingEnabled(False)
        self._manage_budget_table.setRowCount(0)

        for goal in sorted_budget_goals:
            if not _matches_filter(goal.year_month):
                continue

            r = self._manage_budget_table.rowCount()
            self._manage_budget_table.insertRow(r)

            # Category
            cat_item = QtWidgets.QTableWidgetItem(goal.category)
            self._manage_budget_table.setItem(r, 0, cat_item)

            # Month - formatted as "Jan 2026"
            display_month = format_year_month(goal.year_month)
            month_item = QtWidgets.QTableWidgetItem(display_month)
            month_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._manage_budget_table.setItem(r, 1, month_item)

            # Limit
            limit_item = QtWidgets.QTableWidgetItem(format_currency(goal.monthly_limit))
            limit_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._manage_budget_table.setItem(r, 2, limit_item)

            # Actions
            actions_widget = self._create_budget_actions_widget(goal)
            self._manage_budget_table.setCellWidget(r, 3, actions_widget)

        self._manage_budget_table.setSortingEnabled(True)

        # Refresh earnings goals table - sorted by month for grouping
        earnings_goals = self._budget_controller.get_all_earnings_goals()
        sorted_earnings_goals = sorted(
            earnings_goals,
            key=lambda g: (g.year_month if g.year_month != "ALL" else "0000-00", g.sub_category)
        )

        self._manage_earnings_table.setSortingEnabled(False)
        self._manage_earnings_table.setRowCount(0)

        for goal in sorted_earnings_goals:
            if not _matches_filter(goal.year_month):
                continue

            r = self._manage_earnings_table.rowCount()
            self._manage_earnings_table.insertRow(r)

            # Sub-category
            sub_item = QtWidgets.QTableWidgetItem(goal.sub_category)
            self._manage_earnings_table.setItem(r, 0, sub_item)

            # Month - formatted as "Jan 2026"
            display_month = format_year_month(goal.year_month)
            month_item = QtWidgets.QTableWidgetItem(display_month)
            month_item.setTextAlignment(QtCore.Qt.AlignCenter)
            self._manage_earnings_table.setItem(r, 1, month_item)

            # Expected
            expected_item = QtWidgets.QTableWidgetItem(format_currency(goal.expected_amount))
            expected_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            self._manage_earnings_table.setItem(r, 2, expected_item)

            # Actions
            actions_widget = self._create_earnings_actions_widget(goal)
            self._manage_earnings_table.setCellWidget(r, 3, actions_widget)

        self._manage_earnings_table.setSortingEnabled(True)

    def _create_budget_actions_widget(self, goal) -> QtWidgets.QWidget:
        """Create actions widget for budget goal row."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        button_style = """
            QPushButton {
                background: rgba(99, 102, 241, 0.2);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 4px;
                color: #A5B4FC;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.3);
            }
        """

        delete_style = """
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                color: #EF4444;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """

        # Edit button
        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.setStyleSheet(button_style)
        edit_btn.clicked.connect(
            lambda: self._on_edit_budget_goal(goal.category, goal.year_month, goal.monthly_limit)
        )
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.setStyleSheet(delete_style)
        delete_btn.clicked.connect(
            lambda: self._on_delete_budget(goal.category, goal.year_month)
        )
        layout.addWidget(delete_btn)

        # Apply to Year button (only show for specific months)
        if goal.year_month != "ALL" and "-" in goal.year_month:
            apply_btn = QtWidgets.QPushButton("Apply to Year")
            apply_btn.setStyleSheet(button_style)
            apply_btn.clicked.connect(
                lambda: self._on_apply_budget_to_year(
                    goal.category, goal.monthly_limit, goal.year_month
                )
            )
            layout.addWidget(apply_btn)

        layout.addStretch()
        return widget

    def _create_earnings_actions_widget(self, goal) -> QtWidgets.QWidget:
        """Create actions widget for earnings goal row."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)

        button_style = """
            QPushButton {
                background: rgba(99, 102, 241, 0.2);
                border: 1px solid rgba(99, 102, 241, 0.3);
                border-radius: 4px;
                color: #A5B4FC;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(99, 102, 241, 0.3);
            }
        """

        delete_style = """
            QPushButton {
                background: rgba(239, 68, 68, 0.2);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 4px;
                color: #EF4444;
                padding: 4px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.3);
            }
        """

        # Edit button
        edit_btn = QtWidgets.QPushButton("Edit")
        edit_btn.setStyleSheet(button_style)
        edit_btn.clicked.connect(
            lambda: self._on_edit_earnings_goal(
                goal.sub_category, goal.year_month, goal.expected_amount
            )
        )
        layout.addWidget(edit_btn)

        # Delete button
        delete_btn = QtWidgets.QPushButton("Delete")
        delete_btn.setStyleSheet(delete_style)
        delete_btn.clicked.connect(
            lambda: self._on_delete_earnings_goal(goal.sub_category, goal.year_month)
        )
        layout.addWidget(delete_btn)

        # Apply to Year button (only show for specific months)
        if goal.year_month != "ALL" and "-" in goal.year_month:
            apply_btn = QtWidgets.QPushButton("Apply to Year")
            apply_btn.setStyleSheet(button_style)
            apply_btn.clicked.connect(
                lambda: self._on_apply_earnings_to_year(
                    goal.sub_category, goal.expected_amount, goal.year_month
                )
            )
            layout.addWidget(apply_btn)

        layout.addStretch()
        return widget

    def _on_edit_budget_goal(self, category: str, year_month: str, limit: float) -> None:
        """Edit a budget goal by populating the form."""
        self._tab_widget.setCurrentIndex(0)  # Switch to Set Goals tab

        # Set form values
        idx = self._category_combo.findText(category)
        if idx >= 0:
            self._category_combo.setCurrentIndex(idx)
        else:
            self._category_combo.setEditText(category)

        self._budget_apply_year_checkbox.setChecked(False)
        idx = self._budget_month_combo.findData(year_month)
        if idx >= 0:
            self._budget_month_combo.setCurrentIndex(idx)
        else:
            self._budget_month_combo.setEditText(year_month)

        self._limit_spin.setValue(limit)

    def _on_edit_earnings_goal(
        self, sub_category: str, year_month: str, expected: float
    ) -> None:
        """Edit an earnings goal by populating the form."""
        self._tab_widget.setCurrentIndex(0)  # Switch to Set Goals tab

        # Set form values
        idx = self._earnings_sub_combo.findText(sub_category)
        if idx >= 0:
            self._earnings_sub_combo.setCurrentIndex(idx)
        else:
            self._earnings_sub_combo.setEditText(sub_category)

        self._earnings_apply_year_checkbox.setChecked(False)
        idx = self._earnings_month_combo.findData(year_month)
        if idx >= 0:
            self._earnings_month_combo.setCurrentIndex(idx)
        else:
            self._earnings_month_combo.setEditText(year_month)

        self._earnings_expected_spin.setValue(expected)

    def _on_apply_budget_to_year(
        self, category: str, limit: float, year_month: str
    ) -> None:
        """Apply a budget goal to all months in its year."""
        try:
            year = int(year_month.split("-")[0])
        except (ValueError, IndexError):
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Cannot determine year from: {year_month}"
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Apply to Year",
            f"Apply budget '{category}' = {format_currency(limit)} to all 12 months of {year}?\n\n"
            "This will create or update budget entries for each month.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.set_budget_for_year(category, limit, year)
            self._logger.info(
                "Applied budget to year: %s = $%.2f for %d", category, limit, year
            )
            self._refresh_budget_progress()
            self._refresh_manage_tables()
            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Budget for '{category}' applied to all months of {year}!"
            )

    def _on_apply_earnings_to_year(
        self, sub_category: str, expected: float, year_month: str
    ) -> None:
        """Apply an earnings goal to all months in its year."""
        try:
            year = int(year_month.split("-")[0])
        except (ValueError, IndexError):
            QtWidgets.QMessageBox.warning(
                self, "Error", f"Cannot determine year from: {year_month}"
            )
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Apply to Year",
            f"Apply expected earnings '{sub_category}' = {format_currency(expected)} "
            f"to all 12 months of {year}?\n\n"
            "This will create or update earnings entries for each month.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.set_earnings_goal_for_year(sub_category, expected, year)
            self._logger.info(
                "Applied earnings goal to year: %s = $%.2f for %d", sub_category, expected, year
            )
            self._refresh_earnings_table()
            self._refresh_manage_tables()
            QtWidgets.QMessageBox.information(
                self, "Success",
                f"Expected earnings for '{sub_category}' applied to all months of {year}!"
            )

    def _update_kpi_cards(self) -> None:
        """Update all KPI cards."""
        pass

    def _get_expenses_for_month(self, year_month: str) -> "pd.DataFrame":
        """Get expenses DataFrame for a specific month."""
        import pandas as pd

        all_expenses = []
        for mr in self._reports:
            if hasattr(mr, 'expenses') and not mr.expenses.empty:
                all_expenses.append(mr.expenses)

        if not all_expenses:
            return pd.DataFrame()

        df = pd.concat(all_expenses, ignore_index=True)
        return df

    def _get_earnings_for_month(self, year_month: str | None) -> "pd.DataFrame":
        """Get earnings DataFrame for a specific month."""
        import pandas as pd

        frames = []
        for mr in self._reports:
            if hasattr(mr, 'earnings') and not mr.earnings.empty:
                frames.append(mr.earnings)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        if not year_month or year_month == "ALL":
            return df

        if "transaction_date" in df.columns:
            df = df.copy()
            df["year_month"] = pd.to_datetime(
                df["transaction_date"], errors="coerce"
            ).dt.strftime("%Y-%m")
            return df[df["year_month"] == year_month]
        return pd.DataFrame()

    def _on_month_changed(self, index: int) -> None:
        """Handle month selection change."""
        self._refresh_budget_progress()
        self._refresh_earnings_table()

    def _on_save_budget(self) -> None:
        """Save a new or updated budget goal."""
        category = self._category_combo.currentText().strip()
        if not category:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a category name."
            )
            return

        limit = self._limit_spin.value()
        if limit <= 0:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a valid budget limit."
            )
            return

        apply_to_year = self._budget_apply_year_checkbox.isChecked()

        if apply_to_year:
            year = self._budget_year_combo.currentData()
            if year is None:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Please select a year."
                )
                return

            self._budget_controller.set_budget_for_year(category, limit, year)
            self._logger.info(
                "Saved budget for year: %s = $%.2f (%d)", category, limit, year
            )
            message = f"Budget for '{category}' saved for all months of {year}!"
        else:
            year_month = self._budget_month_combo.currentText().strip() or "ALL"
            self._budget_controller.set_budget(category, limit, year_month)
            self._logger.info("Saved budget: %s = $%.2f (%s)", category, limit, year_month)
            message = f"Budget for '{category}' saved for {year_month}!"

        self._refresh_budget_progress()
        self._refresh_manage_tables()

        QtWidgets.QMessageBox.information(self, "Success", message)

    def _on_delete_budget(self, category: str, year_month: str) -> None:
        """Delete a budget goal."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete budget for '{category}' ({year_month})?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.delete_budget(category, year_month)
            self._logger.info("Deleted budget: %s (%s)", category, year_month)
            self._refresh_budget_progress()
            self._refresh_manage_tables()

    def _on_save_earnings_goal(self) -> None:
        """Save earnings expectation."""
        sub_category = self._earnings_sub_combo.currentText().strip()
        if not sub_category:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Please enter a sub-category name."
            )
            return

        expected = self._earnings_expected_spin.value()
        if expected < 0:
            QtWidgets.QMessageBox.warning(
                self, "Error", "Expected amount must be non-negative."
            )
            return

        apply_to_year = self._earnings_apply_year_checkbox.isChecked()

        if apply_to_year:
            year = self._earnings_year_combo.currentData()
            if year is None:
                QtWidgets.QMessageBox.warning(
                    self, "Error", "Please select a year."
                )
                return

            self._budget_controller.set_earnings_goal_for_year(sub_category, expected, year)
            self._logger.info(
                "Saved earnings goal for year: %s = $%.2f (%d)",
                sub_category, expected, year
            )
            message = f"Expected earnings for '{sub_category}' saved for all months of {year}!"
        else:
            year_month = self._earnings_month_combo.currentText().strip() or "ALL"
            self._budget_controller.set_earnings_goal(sub_category, expected, year_month)
            self._logger.info(
                "Saved earnings expectation: %s = $%.2f (%s)",
                sub_category, expected, year_month
            )
            message = f"Expected earnings for '{sub_category}' saved for {year_month}!"

        self._populate_earnings_sub_categories()
        self._refresh_earnings_table()
        self._refresh_manage_tables()

        QtWidgets.QMessageBox.information(self, "Success", message)

    def _on_delete_earnings_goal(self, sub_category: str, year_month: str) -> None:
        """Delete an earnings expectation."""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete expected earnings for '{sub_category}' ({year_month})?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )

        if reply == QtWidgets.QMessageBox.Yes:
            self._budget_controller.delete_earnings_goal(sub_category, year_month)
            self._logger.info("Deleted earnings expectation: %s (%s)", sub_category, year_month)
            self._refresh_earnings_table()
            self._refresh_manage_tables()
