"""Dashboard window (PySide6).

Single responsibility:
    Provide the main application shell with:
      - Menu bar (File -> Exit)
      - Header bar with title/subtitle
      - Left side navigation panel (sections)
      - Central content area that updates based on selection

Modern UI:
    Applies a cohesive dark theme with rounded containers, subtle shadows,
    and improved spacing using a centralized QSS stylesheet.
"""

from __future__ import annotations

import logging
from functools import partial
from typing import Callable, List
from PySide6 import QtWidgets, QtGui, QtCore

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.views.pages import (
    YearlySummaryPage,
    EarningsPage,
    ExpensesPage,
    PaymentsPage,
    UploadPage,
    MapperPage,
    CashflowMapperPage,
    SubCategoryMapperPage,
    SettingsPage,
    BudgetGoalsPage,
    SavingsPage,
    NetWorthPage,
    RecurringPage,
)
from budget_analyser.views.styles import app_stylesheet
from budget_analyser.settings.preferences import AppPreferences
from budget_analyser.controller import SettingsController
from budget_analyser.controller import MapperController
from budget_analyser.controller import CashflowMapperController
from budget_analyser.controller import SubCategoryMapperController
from budget_analyser.controller import UploadController
from budget_analyser.controller.budget_controller import BudgetController
from budget_analyser.version import get_version, APP_NAME


class DashboardWindow(QtWidgets.QMainWindow):
    """Main dashboard window with navigation sidebar and content pages."""

    # Signal emitted when user requests to reload data after uploading CSVs
    reload_requested = QtCore.Signal()

    # Page indices
    PAGE_YEARLY_SUMMARY = 0
    PAGE_EARNINGS = 1
    PAGE_EXPENSES = 2
    PAGE_PAYMENTS = 3
    PAGE_BUDGET_GOALS = 4
    PAGE_SAVINGS = 5
    PAGE_NET_WORTH = 6
    PAGE_RECURRING = 7
    PAGE_UPLOAD = 8
    PAGE_MAPPER = 9
    PAGE_CASHFLOW_MAPPER = 10
    PAGE_SUB_CATEGORY_MAPPER = 11
    PAGE_SETTINGS = 12

    def __init__(
        self,
        reports: List[MonthlyReports],
        logger: logging.Logger,
        prefs: AppPreferences,
        mapper_controller: MapperController,
        sub_category_mapper_controller: SubCategoryMapperController,
        cashflow_mapper_controller: CashflowMapperController,
        upload_controller: UploadController,
        budget_controller: BudgetController,
        *,
        refresh_reports_fn: Callable[[], List[MonthlyReports]] | None = None,
        csv_missing: bool = False,
    ):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._prefs = prefs
        self._mapper_controller = mapper_controller
        self._sub_category_mapper_controller = sub_category_mapper_controller
        self._cashflow_mapper_controller = cashflow_mapper_controller
        self._upload_controller = upload_controller
        self._budget_controller = budget_controller
        self._csv_missing = csv_missing
        self._refresh_reports_fn = refresh_reports_fn
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle(f"{APP_NAME} v{get_version()} - Dashboard")
        self.setObjectName("dashboardWindow")

        # App stylesheet is applied at QApplication level; no per-window stylesheet here.

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        exit_action = QtGui.QAction("Exit", self)
        # Use platform standard Quit shortcut (Cmd+Q on macOS, Ctrl+Q elsewhere)
        exit_action.setShortcuts([QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Quit)])
        exit_action.triggered.connect(self._on_exit)
        file_menu.addAction(exit_action)

        # Navigation menus
        reports_menu = menubar.addMenu("&Reports")
        data_menu = menubar.addMenu("&Data")
        settings_menu = menubar.addMenu("&Settings")

        def add_nav_action(menu: QtWidgets.QMenu, text: str, index: int) -> None:
            action = QtGui.QAction(text, self)
            action.triggered.connect(partial(self._navigate_to, index))
            menu.addAction(action)

        add_nav_action(reports_menu, "Yearly Summary", self.PAGE_YEARLY_SUMMARY)
        add_nav_action(reports_menu, "Earnings", self.PAGE_EARNINGS)
        add_nav_action(reports_menu, "Expenses", self.PAGE_EXPENSES)
        add_nav_action(reports_menu, "Payments", self.PAGE_PAYMENTS)
        add_nav_action(reports_menu, "Budget Goals", self.PAGE_BUDGET_GOALS)
        add_nav_action(reports_menu, "Savings", self.PAGE_SAVINGS)
        add_nav_action(reports_menu, "Net Worth", self.PAGE_NET_WORTH)
        add_nav_action(reports_menu, "Recurring", self.PAGE_RECURRING)

        add_nav_action(data_menu, "Upload", self.PAGE_UPLOAD)
        add_nav_action(data_menu, "Mapper", self.PAGE_MAPPER)
        add_nav_action(data_menu, "Cashflow Mapping", self.PAGE_CASHFLOW_MAPPER)
        add_nav_action(data_menu, "Sub-category Mapping", self.PAGE_SUB_CATEGORY_MAPPER)

        add_nav_action(settings_menu, "Open Settings", self.PAGE_SETTINGS)

        # Central widget with vertical layout (header bar + content row)
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        vroot = QtWidgets.QVBoxLayout(central)
        vroot.setContentsMargins(12, 12, 12, 12)
        vroot.setSpacing(12)

        # Header bar
        header = QtWidgets.QWidget()
        header.setObjectName("headerBar")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(8)

        title_lbl = QtWidgets.QLabel(APP_NAME)
        title_lbl.setObjectName("headerTitleLabel")
        header_layout.addWidget(title_lbl)

        version_chip = QtWidgets.QLabel(f"v{get_version()}")
        version_chip.setObjectName("versionChip")
        header_layout.addWidget(version_chip)

        header_layout.addStretch(1)

        self._subtitle = QtWidgets.QLabel("Yearly Summary")
        self._subtitle.setObjectName("headerSubtitleLabel")
        header_layout.addWidget(self._subtitle)

        # Theme toggle button on the right
        header_layout.addStretch(1)
        self._theme_btn = QtWidgets.QPushButton()
        self._theme_btn.setObjectName("themeToggle")
        self._update_theme_button()
        self._theme_btn.clicked.connect(self._on_toggle_theme)
        header_layout.addWidget(self._theme_btn, alignment=QtCore.Qt.AlignRight)

        # Subtle shadow for header
        h_shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=22, xOffset=0, yOffset=10)
        h_shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        header.setGraphicsEffect(h_shadow)

        vroot.addWidget(header)

        # Content row: sidebar + content container
        row = QtWidgets.QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        # Sidebar with navigation buttons
        sidebar = QtWidgets.QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QtWidgets.QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 14, 14, 14)
        sidebar_layout.setSpacing(10)

        brand = QtWidgets.QLabel(APP_NAME)
        brand.setObjectName("navBrand")
        brand.setAlignment(QtCore.Qt.AlignCenter)
        bf = brand.font()
        bf.setPointSize(14)
        bf.setBold(True)
        brand.setFont(bf)
        sidebar_layout.addWidget(brand)

        self._btn_group = QtWidgets.QButtonGroup(self)
        self._btn_group.setExclusive(True)

        def make_btn(text: str) -> QtWidgets.QPushButton:
            btn = QtWidgets.QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(40)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            return btn

        self._section_names = {
            self.PAGE_YEARLY_SUMMARY: "🗓️ Yearly Summary",
            self.PAGE_EARNINGS: "💰 Earnings",
            self.PAGE_EXPENSES: "🧾 Expenses",
            self.PAGE_PAYMENTS: "🔁 Payments",
            self.PAGE_BUDGET_GOALS: "🎯 Budget Goals",
            self.PAGE_SAVINGS: "💵 Savings",
            self.PAGE_NET_WORTH: "📊 Net Worth",
            self.PAGE_RECURRING: "🔄 Recurring",
            self.PAGE_UPLOAD: "⬆️ Upload",
            self.PAGE_MAPPER: "🧭 Mapper",
            self.PAGE_CASHFLOW_MAPPER: "💹 Cashflow Mapping",
            self.PAGE_SUB_CATEGORY_MAPPER: "🗂️ Sub-category Mapping",
            self.PAGE_SETTINGS: "⚙️ Settings",
        }

        self._buttons: list[QtWidgets.QPushButton] = []

        grouped_sections = [
            (
                "Reports",
                [
                    (self._section_names[self.PAGE_YEARLY_SUMMARY], self.PAGE_YEARLY_SUMMARY),
                    (self._section_names[self.PAGE_EARNINGS], self.PAGE_EARNINGS),
                    (self._section_names[self.PAGE_EXPENSES], self.PAGE_EXPENSES),
                    (self._section_names[self.PAGE_PAYMENTS], self.PAGE_PAYMENTS),
                ],
            ),
            (
                "Goals",
                [
                    (self._section_names[self.PAGE_BUDGET_GOALS], self.PAGE_BUDGET_GOALS),
                    (self._section_names[self.PAGE_SAVINGS], self.PAGE_SAVINGS),
                    (self._section_names[self.PAGE_NET_WORTH], self.PAGE_NET_WORTH),
                ],
            ),
            (
                "Automation",
                [
                    (self._section_names[self.PAGE_RECURRING], self.PAGE_RECURRING),
                ],
            ),
            (
                "Data",
                [
                    (self._section_names[self.PAGE_UPLOAD], self.PAGE_UPLOAD),
                    (self._section_names[self.PAGE_MAPPER], self.PAGE_MAPPER),
                    (self._section_names[self.PAGE_CASHFLOW_MAPPER], self.PAGE_CASHFLOW_MAPPER),
                    (self._section_names[self.PAGE_SUB_CATEGORY_MAPPER], self.PAGE_SUB_CATEGORY_MAPPER),
                ],
            ),
        ]

        for group_title, items in grouped_sections:
            group_label = QtWidgets.QLabel(group_title.upper())
            group_label.setObjectName("navTitle")
            group_label.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            sidebar_layout.addWidget(group_label)

            for name, idx in items:
                btn = make_btn(name)
                self._btn_group.addButton(btn, idx)
                sidebar_layout.addWidget(btn)
                self._buttons.append(btn)

            sidebar_layout.addSpacing(6)

        sidebar_layout.addStretch(1)
        sidebar.setFixedWidth(220)

        # Shadow for sidebar
        s_shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=24, xOffset=0, yOffset=10)
        s_shadow.setColor(QtGui.QColor(0, 0, 0, 160))
        sidebar.setGraphicsEffect(s_shadow)

        # Content container with stacked pages
        content = QtWidgets.QWidget()
        content.setObjectName("content")
        content_v = QtWidgets.QVBoxLayout(content)
        content_v.setContentsMargins(12, 12, 12, 12)
        content_v.setSpacing(0)

        # Stacked content area
        self._stack = QtWidgets.QStackedWidget()
        # Create pages once and keep strong references
        # Build controllers for pages that need them
        settings_controller = SettingsController(self._logger, self._prefs)

        self._upload_page = UploadPage(self._logger, self._upload_controller)
        self._mapper_page = MapperPage(self._logger, self._mapper_controller)
        self._cashflow_mapper_page = CashflowMapperPage(self._logger, self._cashflow_mapper_controller)
        self._sub_category_mapper_page = SubCategoryMapperPage(
            self._logger, self._sub_category_mapper_controller
        )
        self._pages = [
            YearlySummaryPage(self._reports, self._logger),
            EarningsPage(self._reports, self._logger, self._budget_controller),
            ExpensesPage(self._reports, self._logger),
            PaymentsPage(self._reports, self._logger),
            BudgetGoalsPage(self._reports, self._budget_controller, self._logger),
            SavingsPage(self._reports, self._budget_controller, self._logger),
            NetWorthPage(self._budget_controller, self._logger),
            RecurringPage(self._reports, self._budget_controller, self._logger),
            self._upload_page,
            self._mapper_page,
            self._cashflow_mapper_page,
            self._sub_category_mapper_page,
            SettingsPage(self._logger, settings_controller),
        ]
        for page in self._pages:
            self._stack.addWidget(page)
        content_v.addWidget(self._stack)

        # Connect upload page success signal to dashboard reload signal
        self._upload_page.upload_successful.connect(self.reload_requested.emit)

        # Connect mapping saves to refresh workflow
        self._mapper_page.refresh_requested.connect(self._on_mapping_saved)
        self._cashflow_mapper_page.refresh_requested.connect(self._on_mapping_saved)
        self._sub_category_mapper_page.refresh_requested.connect(self._on_mapping_saved)

        # Shadow for content
        c_shadow = QtWidgets.QGraphicsDropShadowEffect(blurRadius=28, xOffset=0, yOffset=12)
        c_shadow.setColor(QtGui.QColor(0, 0, 0, 140))
        content.setGraphicsEffect(c_shadow)

        # Compose row
        row.addWidget(sidebar)
        row.addWidget(content, 1)
        vroot.addLayout(row)

        # Wire navigation
        self._btn_group.idClicked.connect(self._on_nav_clicked)

        # Apply restricted mode if CSVs are missing
        if self._csv_missing:
            self._apply_restricted_mode()
        else:
            # Default selection: Yearly Summary
            self._navigate_to(self.PAGE_YEARLY_SUMMARY)

    def _apply_restricted_mode(self) -> None:
        """Apply restricted mode: disable all pages except Upload and Settings."""
        self._logger.info("Applying restricted mode - CSVs missing")
        restricted_pages = {self.PAGE_UPLOAD, self.PAGE_SETTINGS}
        for btn in self._buttons:
            idx = self._btn_group.id(btn)
            if idx not in restricted_pages:
                btn.setEnabled(False)
                btn.setToolTip("Upload all required CSV files first")

        # Navigate to Upload page
        self._navigate_to(self.PAGE_UPLOAD)

    def enable_all_pages(self) -> None:
        """Enable all navigation pages (called after CSVs are uploaded)."""
        self._logger.info("Enabling all navigation pages")
        self._csv_missing = False
        for btn in self._buttons:
            btn.setEnabled(True)
            btn.setToolTip("")

    def _on_exit(self) -> None:
        self._logger.info("Exit action triggered from File menu")
        QtWidgets.QApplication.instance().quit()

    def _on_nav_clicked(self, index: int) -> None:
        self._logger.info("Navigating to section index: %s", index)
        self._navigate_to(index)

    def _on_toggle_theme(self) -> None:
        # Toggle theme and persist
        current = self._prefs.get_theme()
        new_theme = "light" if current == "dark" else "dark"
        self._prefs.set_theme(new_theme)
        app = QtWidgets.QApplication.instance()
        if app is not None:
            app.setStyleSheet(app_stylesheet(new_theme))
        self._update_theme_button()

    def _update_theme_button(self) -> None:
        # Show icon that indicates target theme upon click
        cur = self._prefs.get_theme()
        self._theme_btn.setText("☀️" if cur == "dark" else "🌙")

    def _navigate_to(self, index: int) -> None:
        """Navigate to a page by index and update subtitle/button states."""
        self._stack.setCurrentIndex(index)
        name = self._section_names.get(index, "")
        if name:
            self._subtitle.setText(name)
        btn = self._btn_group.button(index)
        if btn is not None:
            btn.setChecked(True)
        else:
            for other_btn in self._buttons:
                other_btn.setChecked(False)

    def _on_mapping_saved(self) -> None:
        self._refresh_reports_with_progress()

    def _refresh_reports_with_progress(self) -> None:
        if self._refresh_reports_fn is None:
            QtWidgets.QMessageBox.information(
                self,
                "Refresh unavailable",
                "Reports refresh is not configured for this session. Please restart the app to see the latest mappings.",
            )
            return

        dlg = QtWidgets.QProgressDialog("Refreshing reports...", None, 0, 3, self)
        dlg.setWindowTitle("Refreshing Reports")
        dlg.setWindowModality(QtCore.Qt.ApplicationModal)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        dlg.show()

        try:
            dlg.setLabelText("Reloading latest mappings...")
            dlg.setValue(1)
            QtWidgets.QApplication.processEvents()
            self._mapper_controller.reload()
            self._cashflow_mapper_controller.reload()
            self._sub_category_mapper_controller.reload()

            dlg.setLabelText("Rebuilding reports...")
            dlg.setValue(2)
            QtWidgets.QApplication.processEvents()
            reports = self._refresh_reports_fn()

            dlg.setLabelText("Updating pages...")
            dlg.setValue(3)
            QtWidgets.QApplication.processEvents()
            self._rebuild_pages(reports)

            QtWidgets.QMessageBox.information(
                self,
                "Reports refreshed",
                "Reports were regenerated using the latest mappings.",
            )
        except Exception as exc:  # pragma: no cover
            dlg.close()
            QtWidgets.QMessageBox.critical(
                self,
                "Refresh failed",
                f"Failed to refresh reports:\n{exc}",
            )
            return

        dlg.close()

    def _rebuild_pages(self, reports: List[MonthlyReports]) -> None:
        self._reports = reports or []
        current_index = self._stack.currentIndex()

        replacements = [
            (
                self.PAGE_YEARLY_SUMMARY,
                YearlySummaryPage(self._reports, self._logger),
            ),
            (
                self.PAGE_EARNINGS,
                EarningsPage(self._reports, self._logger, self._budget_controller),
            ),
            (
                self.PAGE_EXPENSES,
                ExpensesPage(self._reports, self._logger),
            ),
            (
                self.PAGE_PAYMENTS,
                PaymentsPage(self._reports, self._logger),
            ),
            (
                self.PAGE_BUDGET_GOALS,
                BudgetGoalsPage(self._reports, self._budget_controller, self._logger),
            ),
            (
                self.PAGE_SAVINGS,
                SavingsPage(self._reports, self._budget_controller, self._logger),
            ),
            (
                self.PAGE_NET_WORTH,
                NetWorthPage(self._budget_controller, self._logger),
            ),
            (
                self.PAGE_RECURRING,
                RecurringPage(self._reports, self._budget_controller, self._logger),
            ),
        ]

        for idx, widget in replacements:
            self._replace_page(idx, widget)

        if 0 <= current_index < self._stack.count():
            self._navigate_to(current_index)
        else:
            self._navigate_to(self.PAGE_YEARLY_SUMMARY)

    def _replace_page(self, index: int, widget: QtWidgets.QWidget) -> None:
        old_widget = self._stack.widget(index)
        if old_widget is not None:
            self._stack.removeWidget(old_widget)
            old_widget.deleteLater()
        self._stack.insertWidget(index, widget)
        if len(self._pages) > index:
            self._pages[index] = widget
