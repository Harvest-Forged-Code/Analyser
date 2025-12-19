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
from typing import List
from PySide6 import QtWidgets, QtGui, QtCore

from budget_analyser.controller.controllers import MonthlyReports
from budget_analyser.views.pages import (
    YearlySummaryPage,
    EarningsPage,
    ExpensesPage,
    PaymentsPage,
    UploadPage,
    MapperPage,
    SettingsPage,
)
from budget_analyser.views.styles import app_stylesheet
from budget_analyser.settings.preferences import AppPreferences
from budget_analyser.controller import SettingsController
from budget_analyser.controller import MapperController
from budget_analyser.controller import UploadController


class DashboardWindow(QtWidgets.QMainWindow):
    """Main dashboard window with navigation sidebar and content pages."""

    # Signal emitted when user requests to reload data after uploading CSVs
    reload_requested = QtCore.Signal()

    # Page indices
    PAGE_YEARLY_SUMMARY = 0
    PAGE_EARNINGS = 1
    PAGE_EXPENSES = 2
    PAGE_PAYMENTS = 3
    PAGE_UPLOAD = 4
    PAGE_MAPPER = 5
    PAGE_SETTINGS = 6

    def __init__(
        self,
        reports: List[MonthlyReports],
        logger: logging.Logger,
        prefs: AppPreferences,
        mapper_controller: MapperController,
        upload_controller: UploadController,
        *,
        csv_missing: bool = False,
    ):
        super().__init__()
        self._reports = reports
        self._logger = logger
        self._prefs = prefs
        self._mapper_controller = mapper_controller
        self._upload_controller = upload_controller
        self._csv_missing = csv_missing
        self._init_ui()

    def _init_ui(self) -> None:
        self.setWindowTitle("Budget Analyser - Dashboard")
        self.setObjectName("dashboardWindow")

        # App stylesheet is applied at QApplication level; no per-window stylesheet here.

        # Menu bar: File -> Exit
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        exit_action = QtGui.QAction("Exit", self)
        # Use platform standard Quit shortcut (Cmd+Q on macOS, Ctrl+Q elsewhere)
        exit_action.setShortcuts([QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.Quit)])
        exit_action.triggered.connect(self._on_exit)
        file_menu.addAction(exit_action)

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

        title_lbl = QtWidgets.QLabel("Budget Analyser")
        title_lbl.setObjectName("headerTitleLabel")
        header_layout.addWidget(title_lbl)

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
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(8)

        nav_label = QtWidgets.QLabel("Navigation")
        nf = nav_label.font()
        nf.setPointSize(12)
        nf.setBold(True)
        nav_label.setFont(nf)
        sidebar_layout.addWidget(nav_label)

        self._btn_group = QtWidgets.QButtonGroup(self)
        self._btn_group.setExclusive(True)

        def make_btn(text: str) -> QtWidgets.QPushButton:
            btn = QtWidgets.QPushButton(text)
            btn.setCheckable(True)
            btn.setMinimumHeight(36)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            return btn

        # Define sections (name, index)
        sections = [
            ("🗓️ Yearly Summary", 0),
            ("💰 Earnings", 1),
            ("🧾 Expenses", 2),
            ("🔁 Payments", 3),
            ("⬆️ Upload", 4),
            ("🧭 Mapper", 5),
            ("⚙️ Settings", 6),
        ]
        self._section_names = {idx: name for name, idx in sections}

        self._buttons: list[QtWidgets.QPushButton] = []
        for name, idx in sections:
            btn = make_btn(name)
            self._btn_group.addButton(btn, idx)
            sidebar_layout.addWidget(btn)
            self._buttons.append(btn)

        sidebar_layout.addStretch(1)
        sidebar.setFixedWidth(200)

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
        self._pages = [
            YearlySummaryPage(self._reports, self._logger),
            EarningsPage(self._reports, self._logger),
            ExpensesPage(self._reports, self._logger),
            PaymentsPage(self._reports, self._logger),
            self._upload_page,
            MapperPage(self._logger, self._mapper_controller),
            SettingsPage(self._logger, settings_controller),
        ]
        for page in self._pages:
            self._stack.addWidget(page)
        content_v.addWidget(self._stack)

        # Connect upload page success signal to dashboard reload signal
        self._upload_page.upload_successful.connect(self.reload_requested.emit)

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
            self._buttons[0].setChecked(True)
            self._stack.setCurrentIndex(0)
            self._subtitle.setText(self._section_names[0])

    def _apply_restricted_mode(self) -> None:
        """Apply restricted mode: disable all pages except Upload and Settings."""
        self._logger.info("Applying restricted mode - CSVs missing")
        # Disable all navigation buttons except Upload and Settings
        restricted_pages = {self.PAGE_UPLOAD, self.PAGE_SETTINGS}
        for idx, btn in enumerate(self._buttons):
            if idx not in restricted_pages:
                btn.setEnabled(False)
                btn.setToolTip("Upload all required CSV files first")

        # Navigate to Upload page
        self._buttons[self.PAGE_UPLOAD].setChecked(True)
        self._stack.setCurrentIndex(self.PAGE_UPLOAD)
        self._subtitle.setText(self._section_names[self.PAGE_UPLOAD])

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
        self._stack.setCurrentIndex(index)
        # Update subtitle to reflect current section
        name = self._section_names.get(index, "")
        if name:
            self._subtitle.setText(name)

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
