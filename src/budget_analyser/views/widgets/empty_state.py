"""Empty state widgets for displaying when no data is available.

Purpose:
    Provides user-friendly empty state messages throughout the UI:
    - Contextual messages based on the current view
    - Optional action buttons to guide users
    - Consistent visual design across the application

Examples:
    - Mapper: "All transactions mapped! Great job."
    - Budget Goals: "No budget goals set. Click here to create your first budget."
    - Expenses: "No data found. Upload bank statements to get started."
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6 import QtCore, QtWidgets, QtGui


@dataclass(frozen=True)
class EmptyStateConfig:
    """Configuration for an empty state display."""

    icon: str  # Emoji or icon text
    title: str  # Main message
    subtitle: str = ""  # Secondary message
    action_text: str = ""  # Button text (empty = no button)
    is_success: bool = False  # True for positive states (e.g., "All done!")


class EmptyStateWidget(QtWidgets.QWidget):
    """A reusable empty state component with icon, title, and optional action."""

    action_clicked = QtCore.Signal()

    def __init__(
        self,
        config: EmptyStateConfig,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the empty state UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(32, 48, 32, 48)
        layout.setSpacing(16)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Icon
        icon_label = QtWidgets.QLabel(self._config.icon)
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 48px;")
        layout.addWidget(icon_label)

        # Title
        title_label = QtWidgets.QLabel(self._config.title)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)

        if self._config.is_success:
            title_color = "#059669"  # Green for success
        else:
            title_color = "#374151"

        title_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {title_color};
        """)
        layout.addWidget(title_label)

        # Subtitle
        if self._config.subtitle:
            subtitle_label = QtWidgets.QLabel(self._config.subtitle)
            subtitle_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet("""
                font-size: 14px;
                color: #6B7280;
            """)
            layout.addWidget(subtitle_label)

        # Action button
        if self._config.action_text:
            layout.addSpacing(8)
            action_btn = QtWidgets.QPushButton(self._config.action_text)
            action_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8B5CF6;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 24px;
                    font-size: 14px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #7C3AED;
                }
                QPushButton:pressed {
                    background-color: #6D28D9;
                }
            """)
            action_btn.clicked.connect(self.action_clicked.emit)

            # Center the button
            btn_layout = QtWidgets.QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(action_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

        layout.addStretch()

    def update_config(self, config: EmptyStateConfig) -> None:
        """Update the empty state configuration."""
        self._config = config
        # Clear and rebuild
        layout = self.layout()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._init_ui()


# Pre-defined empty state configurations
class EmptyStates:
    """Collection of pre-defined empty state configurations."""

    # Transactions
    NO_TRANSACTIONS = EmptyStateConfig(
        icon="📭",
        title="No transactions found",
        subtitle="Upload bank statements to get started with tracking your finances.",
        action_text="Upload Statements",
    )

    NO_TRANSACTIONS_FOR_FILTER = EmptyStateConfig(
        icon="🔍",
        title="No matching transactions",
        subtitle="Try adjusting your filters to see more results.",
        action_text="Clear Filters",
    )

    # Mapper states
    ALL_TRANSACTIONS_MAPPED = EmptyStateConfig(
        icon="✅",
        title="All transactions mapped!",
        subtitle="Great job! All your transactions have been categorized.",
        is_success=True,
    )

    NO_UNMAPPED_TRANSACTIONS = EmptyStateConfig(
        icon="🎉",
        title="No unmapped transactions",
        subtitle="All transactions are already categorized. Nice work!",
        is_success=True,
    )

    NO_MAPPING_RULES = EmptyStateConfig(
        icon="📝",
        title="No mapping rules defined",
        subtitle="Create rules to automatically categorize your transactions.",
        action_text="Add Rule",
    )

    # Budget states
    NO_BUDGET_GOALS = EmptyStateConfig(
        icon="🎯",
        title="No budget goals set",
        subtitle="Set spending limits for categories to stay on track.",
        action_text="Create Budget Goal",
    )

    BUDGET_ON_TRACK = EmptyStateConfig(
        icon="💚",
        title="Budget on track!",
        subtitle="You're within your spending limits. Keep it up!",
        is_success=True,
    )

    # Earnings/Expenses
    NO_EARNINGS = EmptyStateConfig(
        icon="💰",
        title="No earnings recorded",
        subtitle="Upload statements containing income to track your earnings.",
        action_text="Upload Statements",
    )

    NO_EXPENSES = EmptyStateConfig(
        icon="💸",
        title="No expenses recorded",
        subtitle="Upload bank statements to start tracking your spending.",
        action_text="Upload Statements",
    )

    # Reports
    NO_REPORT_DATA = EmptyStateConfig(
        icon="📊",
        title="No data for this period",
        subtitle="Select a different date range or upload more statements.",
        action_text="Change Date Range",
    )

    REPORT_LOADING = EmptyStateConfig(
        icon="⏳",
        title="Loading report data...",
        subtitle="Please wait while we crunch the numbers.",
    )

    # Categories
    NO_CATEGORIES = EmptyStateConfig(
        icon="📂",
        title="No categories defined",
        subtitle="Categories help organize your transactions for better insights.",
        action_text="Add Category",
    )

    # Search results
    NO_SEARCH_RESULTS = EmptyStateConfig(
        icon="🔎",
        title="No results found",
        subtitle="Try different search terms or check your spelling.",
    )

    # Payments
    NO_PAYMENTS = EmptyStateConfig(
        icon="💳",
        title="No payment transactions",
        subtitle="Payments will appear here once they're categorized.",
    )

    NO_UNMATCHED_PAYMENTS = EmptyStateConfig(
        icon="✨",
        title="All payments matched!",
        subtitle="All payment transactions have been paired successfully.",
        is_success=True,
    )

    # Validation
    NO_VALIDATION_ISSUES = EmptyStateConfig(
        icon="✅",
        title="No issues found",
        subtitle="Your mappings are correctly configured.",
        is_success=True,
    )

    # Charts
    NO_CHART_DATA = EmptyStateConfig(
        icon="📈",
        title="Not enough data for chart",
        subtitle="More transactions are needed to generate meaningful visualizations.",
    )

    # Settings
    NO_ACCOUNTS = EmptyStateConfig(
        icon="🏦",
        title="No accounts configured",
        subtitle="Add accounts to organize your transactions by source.",
        action_text="Add Account",
    )


class ConditionalEmptyState(QtWidgets.QStackedWidget):
    """Widget that switches between content and empty state based on data."""

    action_clicked = QtCore.Signal()

    def __init__(
        self,
        content_widget: QtWidgets.QWidget,
        empty_config: EmptyStateConfig,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._content_widget = content_widget
        self._empty_widget = EmptyStateWidget(empty_config)
        self._empty_widget.action_clicked.connect(self.action_clicked.emit)

        self.addWidget(content_widget)
        self.addWidget(self._empty_widget)

        # Start with empty state
        self.show_empty()

    def show_content(self) -> None:
        """Show the content widget."""
        self.setCurrentWidget(self._content_widget)

    def show_empty(self) -> None:
        """Show the empty state."""
        self.setCurrentWidget(self._empty_widget)

    def set_has_data(self, has_data: bool) -> None:
        """Switch based on whether data is available."""
        if has_data:
            self.show_content()
        else:
            self.show_empty()

    def update_empty_config(self, config: EmptyStateConfig) -> None:
        """Update the empty state configuration."""
        self._empty_widget.update_config(config)


class TableWithEmptyState(QtWidgets.QWidget):
    """A table widget with built-in empty state handling."""

    action_clicked = QtCore.Signal()

    def __init__(
        self,
        empty_config: EmptyStateConfig,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._empty_config = empty_config
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create table
        self._table = QtWidgets.QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self._table.horizontalHeader().setStretchLastSection(True)

        # Create empty state
        self._empty_state = EmptyStateWidget(self._empty_config)
        self._empty_state.action_clicked.connect(self.action_clicked.emit)

        # Stack them
        self._stack = QtWidgets.QStackedWidget()
        self._stack.addWidget(self._table)
        self._stack.addWidget(self._empty_state)

        layout.addWidget(self._stack)

        # Start with empty state
        self._stack.setCurrentWidget(self._empty_state)

    def table(self) -> QtWidgets.QTableWidget:
        """Get the underlying table widget."""
        return self._table

    def set_row_count(self, count: int) -> None:
        """Set row count and update empty state visibility."""
        self._table.setRowCount(count)
        if count > 0:
            self._stack.setCurrentWidget(self._table)
        else:
            self._stack.setCurrentWidget(self._empty_state)

    def update_empty_config(self, config: EmptyStateConfig) -> None:
        """Update the empty state configuration."""
        self._empty_config = config
        self._empty_state.update_config(config)
