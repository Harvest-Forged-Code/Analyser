"""Goal Card widget for savings goal visualization.

Provides a card component for displaying savings goals with
progress indicators, status, and action buttons.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.views.constants import (
    COLOR_PRIMARY,
    COLOR_POSITIVE,
    COLOR_WARNING,
    COLOR_EXPENSE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_MUTED,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    FONT_SIZE_SECTION_TITLE,
    GOAL_CARD_MIN_WIDTH,
    GOAL_CARD_MIN_HEIGHT,
    BORDER_RADIUS_CARD,
    PROGRESS_BAR_HEIGHT_LARGE,
    SHADOW_BLUR_RADIUS,
    SHADOW_BLUR_RADIUS_HOVER,
    SHADOW_OFFSET_Y,
    SHADOW_OFFSET_Y_HOVER,
    format_currency,
)
from budget_analyser.views.animations import (
    create_card_shadow,
    ShadowAnimator,
    DURATION_FAST,
)
from budget_analyser.views.icons import AppIcon, get_icon, is_icon_available

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class GoalStatus(Enum):
    """Goal tracking status."""

    ON_TRACK = ("on_track", COLOR_POSITIVE, AppIcon.STATUS_ON_TRACK, "On Track", "✓")
    AT_RISK = ("at_risk", COLOR_WARNING, AppIcon.STATUS_AT_RISK, "At Risk", "⚠")
    BEHIND = ("behind", COLOR_EXPENSE, AppIcon.STATUS_BEHIND, "Behind", "!")
    COMPLETED = ("completed", "#FFD700", AppIcon.STATUS_COMPLETED, "Completed", "★")
    PAUSED = ("paused", COLOR_MUTED, AppIcon.STATUS_PAUSED, "Paused", "⏸")

    def __init__(
        self,
        status_id: str,
        color: str,
        icon: AppIcon,
        label: str,
        fallback_icon: str,
    ) -> None:
        self.status_id = status_id
        self.color = color
        self.app_icon = icon
        self.label = label
        self.fallback_icon = fallback_icon

    @classmethod
    def from_string(cls, status: str) -> "GoalStatus":
        """Get status from string identifier.

        Args:
            status: Status string (on_track, at_risk, behind, completed, paused)

        Returns:
            Matching GoalStatus
        """
        for member in cls:
            if member.status_id == status:
                return member
        return cls.ON_TRACK


@dataclass(frozen=True)
class GoalData:
    """Data for savings goal card."""

    goal_id: str
    name: str
    icon: str = "🎯"
    target_amount: float = 0.0
    current_amount: float = 0.0
    monthly_contribution: float = 0.0
    target_date: date | None = None
    status: str = "on_track"
    amount_this_month: float = 0.0

    @property
    def percentage(self) -> float:
        """Calculate completion percentage."""
        if self.target_amount <= 0:
            return 0.0
        return (self.current_amount / self.target_amount) * 100

    @property
    def remaining(self) -> float:
        """Calculate remaining amount."""
        return max(0, self.target_amount - self.current_amount)

    @property
    def months_remaining(self) -> int | None:
        """Estimate months to completion."""
        if self.monthly_contribution <= 0:
            return None
        remaining = self.remaining
        if remaining <= 0:
            return 0
        return int(remaining / self.monthly_contribution) + 1

    @property
    def goal_status(self) -> GoalStatus:
        """Get GoalStatus enum from status string."""
        return GoalStatus.from_string(self.status)


class GoalCard(QtWidgets.QWidget):
    """Savings goal card with progress visualization.

    Displays a savings goal with progress bar, status indicator,
    and action buttons for top-up, edit, and history.
    """

    top_up_clicked = QtCore.Signal(str)  # goal_id
    edit_clicked = QtCore.Signal(str)    # goal_id
    history_clicked = QtCore.Signal(str)  # goal_id

    def __init__(
        self,
        data: GoalData,
        *,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize goal card.

        Args:
            data: Goal data
            compact: Use compact layout
            parent: Parent widget
        """
        super().__init__(parent)
        self._data = data
        self._compact = compact
        self._shadow: QtWidgets.QGraphicsDropShadowEffect | None = None
        self._shadow_animator: ShadowAnimator | None = None
        self._hover_animation: QtCore.QParallelAnimationGroup | None = None
        self._init_ui()
        self._setup_shadow()
        self.update_data(data)

    def _init_ui(self) -> None:
        """Initialize UI."""
        self.setObjectName("goalCard")
        self.setMinimumWidth(GOAL_CARD_MIN_WIDTH)
        if not self._compact:
            self.setMinimumHeight(GOAL_CARD_MIN_HEIGHT)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self._apply_base_styles()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header: Icon and name
        header_row = QtWidgets.QHBoxLayout()
        header_row.setSpacing(12)

        self._icon_label = QtWidgets.QLabel()
        self._icon_label.setStyleSheet("font-size: 24px;")
        header_row.addWidget(self._icon_label)

        self._name_label = QtWidgets.QLabel()
        self._name_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {COLOR_TEXT_PRIMARY};
        """)
        header_row.addWidget(self._name_label, 1)

        # Status badge
        self._status_badge = QtWidgets.QLabel()
        self._status_badge.setAlignment(QtCore.Qt.AlignCenter)
        header_row.addWidget(self._status_badge)

        layout.addLayout(header_row)

        # Target amount
        self._target_label = QtWidgets.QLabel()
        self._target_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            color: {COLOR_TEXT_MUTED};
        """)
        layout.addWidget(self._target_label)

        # Progress bar
        progress_row = QtWidgets.QHBoxLayout()
        progress_row.setSpacing(12)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(PROGRESS_BAR_HEIGHT_LARGE)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        progress_row.addWidget(self._progress_bar, 1)

        self._percentage_label = QtWidgets.QLabel()
        self._percentage_label.setMinimumWidth(50)
        self._percentage_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        progress_row.addWidget(self._percentage_label)

        layout.addLayout(progress_row)

        # Progress details
        details_row = QtWidgets.QHBoxLayout()
        details_row.setSpacing(8)

        self._saved_label = QtWidgets.QLabel()
        self._saved_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_BODY}px;
            font-weight: 600;
            color: {COLOR_TEXT_PRIMARY};
        """)
        details_row.addWidget(self._saved_label)

        details_row.addStretch()

        self._eta_label = QtWidgets.QLabel()
        self._eta_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            color: {COLOR_TEXT_MUTED};
        """)
        details_row.addWidget(self._eta_label)

        layout.addLayout(details_row)

        # Additional info (non-compact only)
        if not self._compact:
            info_container = QtWidgets.QWidget()
            info_container.setStyleSheet(f"""
                background: rgba(60, 60, 70, 0.2);
                border-radius: 8px;
            """)
            info_layout = QtWidgets.QHBoxLayout(info_container)
            info_layout.setContentsMargins(12, 8, 12, 8)
            info_layout.setSpacing(16)

            # This month contribution
            month_col = QtWidgets.QVBoxLayout()
            month_col.setSpacing(2)

            month_title = QtWidgets.QLabel("This Month")
            month_title.setStyleSheet(f"""
                font-size: {FONT_SIZE_CAPTION}px;
                color: {COLOR_TEXT_MUTED};
            """)
            month_col.addWidget(month_title)

            self._month_amount_label = QtWidgets.QLabel()
            self._month_amount_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {COLOR_TEXT_PRIMARY};
            """)
            month_col.addWidget(self._month_amount_label)

            info_layout.addLayout(month_col)

            # Monthly contribution
            contrib_col = QtWidgets.QVBoxLayout()
            contrib_col.setSpacing(2)

            contrib_title = QtWidgets.QLabel("Monthly Target")
            contrib_title.setStyleSheet(f"""
                font-size: {FONT_SIZE_CAPTION}px;
                color: {COLOR_TEXT_MUTED};
            """)
            contrib_col.addWidget(contrib_title)

            self._contrib_label = QtWidgets.QLabel()
            self._contrib_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {COLOR_TEXT_PRIMARY};
            """)
            contrib_col.addWidget(self._contrib_label)

            info_layout.addLayout(contrib_col)

            # Remaining
            remaining_col = QtWidgets.QVBoxLayout()
            remaining_col.setSpacing(2)

            remaining_title = QtWidgets.QLabel("Remaining")
            remaining_title.setStyleSheet(f"""
                font-size: {FONT_SIZE_CAPTION}px;
                color: {COLOR_TEXT_MUTED};
            """)
            remaining_col.addWidget(remaining_title)

            self._remaining_label = QtWidgets.QLabel()
            self._remaining_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {COLOR_TEXT_PRIMARY};
            """)
            remaining_col.addWidget(self._remaining_label)

            info_layout.addLayout(remaining_col)

            layout.addWidget(info_container)

        # Action buttons
        button_row = QtWidgets.QHBoxLayout()
        button_row.setSpacing(8)

        self._top_up_btn = QtWidgets.QPushButton("Top Up")
        self._top_up_btn.setObjectName("goalActionBtn")
        self._top_up_btn.clicked.connect(
            lambda: self.top_up_clicked.emit(self._data.goal_id)
        )
        button_row.addWidget(self._top_up_btn)

        self._edit_btn = QtWidgets.QPushButton("Edit")
        self._edit_btn.setObjectName("goalActionBtnSecondary")
        self._edit_btn.clicked.connect(
            lambda: self.edit_clicked.emit(self._data.goal_id)
        )
        button_row.addWidget(self._edit_btn)

        if not self._compact:
            self._history_btn = QtWidgets.QPushButton("History")
            self._history_btn.setObjectName("goalActionBtnSecondary")
            self._history_btn.clicked.connect(
                lambda: self.history_clicked.emit(self._data.goal_id)
            )
            button_row.addWidget(self._history_btn)

        button_row.addStretch()

        layout.addLayout(button_row)

    def _apply_base_styles(self) -> None:
        """Apply base styles."""
        self.setStyleSheet(f"""
            QWidget#goalCard {{
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: {BORDER_RADIUS_CARD}px;
            }}
            QWidget#goalCard:hover {{
                border-color: rgba(139, 92, 246, 0.4);
            }}
            QPushButton#goalActionBtn {{
                background: rgba(139, 92, 246, 0.2);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                color: {COLOR_PRIMARY};
            }}
            QPushButton#goalActionBtn:hover {{
                background: rgba(139, 92, 246, 0.3);
            }}
            QPushButton#goalActionBtnSecondary {{
                background: rgba(60, 60, 70, 0.3);
                border: 1px solid rgba(60, 60, 70, 0.5);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                color: {COLOR_TEXT_MUTED};
            }}
            QPushButton#goalActionBtnSecondary:hover {{
                background: rgba(60, 60, 70, 0.5);
                color: {COLOR_TEXT_PRIMARY};
            }}
        """)

    def update_data(self, data: GoalData) -> None:
        """Update card with new data.

        Args:
            data: New goal data
        """
        self._data = data
        status = data.goal_status

        # Update header
        self._icon_label.setText(data.icon)
        self._name_label.setText(data.name)

        # Update status badge with icon (or fallback to text)
        # Create a horizontal layout for icon + text if not already set up
        if not hasattr(self, '_status_icon_label'):
            self._status_icon_label = QtWidgets.QLabel()
            self._status_text_label = QtWidgets.QLabel()

            badge_layout = QtWidgets.QHBoxLayout(self._status_badge)
            badge_layout.setContentsMargins(8, 4, 8, 4)
            badge_layout.setSpacing(4)
            badge_layout.addWidget(self._status_icon_label)
            badge_layout.addWidget(self._status_text_label)

        # Try to use icon, fall back to emoji
        if is_icon_available(status.app_icon):
            status_icon = get_icon(status.app_icon, color=status.color, size=14)
            if not status_icon.isNull():
                status_pixmap = status_icon.pixmap(QtCore.QSize(14, 14))
                if not status_pixmap.isNull():
                    self._status_icon_label.setPixmap(status_pixmap)
                else:
                    self._status_icon_label.setText(status.fallback_icon)
            else:
                self._status_icon_label.setText(status.fallback_icon)
        else:
            self._status_icon_label.setText(status.fallback_icon)

        self._status_text_label.setText(status.label)
        self._status_text_label.setStyleSheet(f"""
            color: {status.color};
            font-size: {FONT_SIZE_CAPTION}px;
            font-weight: 600;
        """)
        self._status_badge.setStyleSheet(f"""
            background: {status.color}33;
            border-radius: 4px;
        """)

        # Update target
        self._target_label.setText(f"Target: {format_currency(data.target_amount)}")

        # Update progress
        pct = data.percentage
        self._progress_bar.setValue(min(int(pct), 100))

        # Progress bar color based on status
        bar_color = status.color if status != GoalStatus.COMPLETED else COLOR_POSITIVE
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(60, 60, 70, 0.3);
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: {bar_color};
                border-radius: 6px;
            }}
        """)

        self._percentage_label.setText(f"{pct:.0f}%")
        self._percentage_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {bar_color};
        """)

        # Update saved amount
        self._saved_label.setText(f"{format_currency(data.current_amount)} saved")

        # Update ETA
        if data.target_date:
            self._eta_label.setText(
                f"Est. completion: {data.target_date.strftime('%b %Y')}"
            )
        elif data.months_remaining is not None:
            if data.months_remaining == 0:
                self._eta_label.setText("Goal reached!")
            else:
                self._eta_label.setText(f"~{data.months_remaining} months remaining")
        else:
            self._eta_label.setText("")

        # Update info section (non-compact only)
        if not self._compact:
            self._month_amount_label.setText(format_currency(data.amount_this_month))
            self._contrib_label.setText(format_currency(data.monthly_contribution))
            self._remaining_label.setText(format_currency(data.remaining))

        # Update button state
        if status == GoalStatus.COMPLETED:
            if is_icon_available(AppIcon.STATUS_COMPLETED):
                completed_icon = get_icon(AppIcon.STATUS_COMPLETED, color="#FFD700", size=16)
                if not completed_icon.isNull():
                    self._top_up_btn.setIcon(completed_icon)
                    self._top_up_btn.setText("Completed")
                else:
                    self._top_up_btn.setText("Completed ★")
            else:
                self._top_up_btn.setText("Completed ★")
            self._top_up_btn.setEnabled(False)
        else:
            self._top_up_btn.setText("Top Up")
            self._top_up_btn.setIcon(QtGui.QIcon())
            self._top_up_btn.setEnabled(True)

    def _setup_shadow(self) -> None:
        """Set up drop shadow effect with animation support."""
        self._shadow = create_card_shadow(
            blur_radius=SHADOW_BLUR_RADIUS,
            y_offset=SHADOW_OFFSET_Y,
        )
        self.setGraphicsEffect(self._shadow)
        self._shadow_animator = ShadowAnimator(self._shadow, self)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse enter for hover state with shadow animation."""
        # Stop any running animation
        if self._hover_animation is not None:
            self._hover_animation.stop()

        # Animate shadow elevation
        if self._shadow_animator is not None:
            self._hover_animation = self._shadow_animator.animate_hover_enter(
                target_blur=SHADOW_BLUR_RADIUS_HOVER,
                target_offset=SHADOW_OFFSET_Y_HOVER,
                duration=DURATION_FAST,
            )
            self._hover_animation.start()

        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse leave for hover state with shadow animation."""
        # Stop any running animation
        if self._hover_animation is not None:
            self._hover_animation.stop()

        # Animate shadow back to normal
        if self._shadow_animator is not None:
            self._hover_animation = self._shadow_animator.animate_hover_leave(
                target_blur=SHADOW_BLUR_RADIUS,
                target_offset=SHADOW_OFFSET_Y,
                duration=DURATION_FAST,
            )
            self._hover_animation.start()

        super().leaveEvent(event)


class SavingsGoalsGrid(QtWidgets.QWidget):
    """Grid layout for savings goal cards."""

    add_goal_clicked = QtCore.Signal()
    goal_top_up_clicked = QtCore.Signal(str)
    goal_edit_clicked = QtCore.Signal(str)
    goal_history_clicked = QtCore.Signal(str)

    def __init__(
        self,
        columns: int = 2,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize goals grid.

        Args:
            columns: Number of columns
            parent: Parent widget
        """
        super().__init__(parent)
        self._columns = columns
        self._cards: list[GoalCard] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with add button
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(12)

        title = QtWidgets.QLabel("SAVINGS GOALS")
        title.setStyleSheet(f"""
            font-size: {FONT_SIZE_SECTION_TITLE}px;
            font-weight: 700;
            letter-spacing: 1px;
            color: {COLOR_PRIMARY};
        """)
        header.addWidget(title)

        header.addStretch()

        add_btn = QtWidgets.QPushButton("+ Add Goal")
        add_btn.setObjectName("addGoalBtn")
        add_btn.setStyleSheet(f"""
            QPushButton#addGoalBtn {{
                background: rgba(139, 92, 246, 0.15);
                border: 1px solid rgba(139, 92, 246, 0.25);
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: 600;
                color: {COLOR_PRIMARY};
            }}
            QPushButton#addGoalBtn:hover {{
                background: rgba(139, 92, 246, 0.25);
            }}
        """)
        add_btn.clicked.connect(self.add_goal_clicked.emit)
        header.addWidget(add_btn)

        layout.addLayout(header)
        layout.addSpacing(16)

        # Grid container
        self._grid_container = QtWidgets.QWidget()
        self._grid_layout = QtWidgets.QGridLayout(self._grid_container)
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(16)

        layout.addWidget(self._grid_container)

        # Empty state
        self._empty_state = QtWidgets.QLabel(
            "No savings goals yet. Click '+ Add Goal' to create one."
        )
        self._empty_state.setAlignment(QtCore.Qt.AlignCenter)
        self._empty_state.setStyleSheet(f"""
            color: {COLOR_TEXT_MUTED};
            font-size: {FONT_SIZE_BODY}px;
            padding: 40px;
        """)
        self._empty_state.hide()
        layout.addWidget(self._empty_state)

    def update_goals(self, goals: list[GoalData]) -> None:
        """Update the goals display.

        Args:
            goals: List of goal data
        """
        # Clear existing cards
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()

        if not goals:
            self._grid_container.hide()
            self._empty_state.show()
            return

        self._empty_state.hide()
        self._grid_container.show()

        # Add new cards
        for i, goal_data in enumerate(goals):
            card = GoalCard(goal_data)
            card.top_up_clicked.connect(self.goal_top_up_clicked.emit)
            card.edit_clicked.connect(self.goal_edit_clicked.emit)
            card.history_clicked.connect(self.goal_history_clicked.emit)

            row = i // self._columns
            col = i % self._columns
            self._grid_layout.addWidget(card, row, col)
            self._cards.append(card)

    def clear(self) -> None:
        """Clear all cards."""
        for card in self._cards:
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        self._grid_container.hide()
        self._empty_state.show()