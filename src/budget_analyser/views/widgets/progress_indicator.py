"""Progress indicator widgets for budget tracking.

Provides horizontal progress bars and circular progress rings
for visualizing budget utilization and goal progress.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.views.constants import (
    COLOR_POSITIVE,
    COLOR_INCOME,
    COLOR_WARNING,
    COLOR_EXPENSE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    FONT_SIZE_CARD_VALUE,
    PROGRESS_BAR_HEIGHT,
    PROGRESS_BAR_HEIGHT_LARGE,
    BORDER_RADIUS_CARD,
    format_currency,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class ProgressStatus(Enum):
    """Status based on percentage thresholds."""

    HEALTHY = ("healthy", COLOR_POSITIVE)     # 0-70%
    GOOD = ("good", COLOR_INCOME)             # 71-90%
    WARNING = ("warning", COLOR_WARNING)      # 91-100%
    OVER = ("over", COLOR_EXPENSE)            # >100%

    def __init__(self, status_name: str, color: str) -> None:
        self.status_name = status_name
        self.color = color

    @classmethod
    def from_percentage(cls, pct: float) -> "ProgressStatus":
        """Get status from percentage value.

        Args:
            pct: Percentage (0-100+)

        Returns:
            Appropriate ProgressStatus
        """
        if pct <= 70:
            return cls.HEALTHY
        elif pct <= 90:
            return cls.GOOD
        elif pct <= 100:
            return cls.WARNING
        return cls.OVER


@dataclass(frozen=True)
class ProgressData:
    """Data for progress indicator."""

    current: float
    target: float
    label: str = ""
    format_as_currency: bool = True
    show_remaining: bool = True

    @property
    def percentage(self) -> float:
        """Calculate percentage completion."""
        if self.target <= 0:
            return 0.0
        return (self.current / self.target) * 100

    @property
    def remaining(self) -> float:
        """Calculate remaining amount."""
        return self.target - self.current

    @property
    def status(self) -> ProgressStatus:
        """Get status based on percentage."""
        return ProgressStatus.from_percentage(self.percentage)


class HorizontalProgressBar(QtWidgets.QWidget):
    """Budget utilization progress bar with status colors.

    Shows a horizontal bar with current/target values, percentage,
    and color-coded status indication.
    """

    clicked = QtCore.Signal()

    def __init__(
        self,
        data: ProgressData,
        *,
        height: int = PROGRESS_BAR_HEIGHT_LARGE,
        show_labels: bool = True,
        compact: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize progress bar.

        Args:
            data: Progress data
            height: Bar height in pixels
            show_labels: Whether to show text labels
            compact: Use compact single-line layout
            parent: Parent widget
        """
        super().__init__(parent)
        self._data = data
        self._bar_height = height
        self._show_labels = show_labels
        self._compact = compact
        self._init_ui()
        self.update_data(data)

    def _init_ui(self) -> None:
        """Initialize the UI."""
        if self._compact:
            self._init_compact_ui()
        else:
            self._init_full_ui()

    def _init_full_ui(self) -> None:
        """Initialize full two-line layout."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Top row: label and values
        if self._show_labels:
            top_row = QtWidgets.QHBoxLayout()
            top_row.setSpacing(8)

            self._label = QtWidgets.QLabel()
            self._label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {COLOR_TEXT_PRIMARY};
            """)
            top_row.addWidget(self._label)

            top_row.addStretch()

            self._values_label = QtWidgets.QLabel()
            self._values_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                color: {COLOR_TEXT_MUTED};
            """)
            top_row.addWidget(self._values_label)

            layout.addLayout(top_row)

        # Progress bar row
        bar_row = QtWidgets.QHBoxLayout()
        bar_row.setSpacing(12)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(self._bar_height)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        bar_row.addWidget(self._progress_bar, 1)

        self._percentage_label = QtWidgets.QLabel()
        self._percentage_label.setMinimumWidth(50)
        self._percentage_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        bar_row.addWidget(self._percentage_label)

        self._remaining_label = QtWidgets.QLabel()
        self._remaining_label.setMinimumWidth(100)
        self._remaining_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        bar_row.addWidget(self._remaining_label)

        layout.addLayout(bar_row)

    def _init_compact_ui(self) -> None:
        """Initialize compact single-line layout."""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        if self._show_labels:
            self._label = QtWidgets.QLabel()
            self._label.setStyleSheet(f"""
                font-size: {FONT_SIZE_BODY}px;
                font-weight: 600;
                color: {COLOR_TEXT_PRIMARY};
            """)
            self._label.setMinimumWidth(120)
            layout.addWidget(self._label)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(self._bar_height)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        layout.addWidget(self._progress_bar, 1)

        self._percentage_label = QtWidgets.QLabel()
        self._percentage_label.setMinimumWidth(45)
        self._percentage_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(self._percentage_label)

        self._remaining_label = QtWidgets.QLabel()
        self._remaining_label.setMinimumWidth(90)
        self._remaining_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(self._remaining_label)

        # Hidden in compact mode
        self._values_label = None

    def update_data(self, data: ProgressData) -> None:
        """Update with new data.

        Args:
            data: New progress data
        """
        self._data = data
        status = data.status

        # Update label
        if self._show_labels and hasattr(self, '_label'):
            self._label.setText(data.label)

        # Update values label (full mode only)
        if self._values_label and data.format_as_currency:
            self._values_label.setText(
                f"{format_currency(data.current)} / {format_currency(data.target)}"
            )

        # Update progress bar
        display_pct = min(int(data.percentage), 100)
        self._progress_bar.setValue(display_pct)

        # Update percentage label
        self._percentage_label.setText(f"{data.percentage:.0f}%")
        self._percentage_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            font-weight: 600;
            color: {status.color};
        """)

        # Update remaining label
        if data.show_remaining:
            remaining = data.remaining
            if data.format_as_currency:
                if remaining >= 0:
                    self._remaining_label.setText(f"{format_currency(remaining)} left")
                    self._remaining_label.setStyleSheet(f"""
                        font-size: {FONT_SIZE_CAPTION}px;
                        color: {COLOR_TEXT_MUTED};
                    """)
                else:
                    self._remaining_label.setText(f"{format_currency(abs(remaining))} over")
                    self._remaining_label.setStyleSheet(f"""
                        font-size: {FONT_SIZE_CAPTION}px;
                        font-weight: 600;
                        color: {COLOR_EXPENSE};
                    """)
            else:
                self._remaining_label.setText(f"{remaining:.0f} left")
        else:
            self._remaining_label.setText("")

        # Style progress bar
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(60, 60, 70, 0.3);
                border: none;
                border-radius: {self._bar_height // 2}px;
            }}
            QProgressBar::chunk {{
                background: {status.color};
                border-radius: {self._bar_height // 2}px;
            }}
        """)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle click."""
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CircularProgressRing(QtWidgets.QWidget):
    """Circular progress indicator for goal completion.

    Shows a ring that fills based on progress percentage with
    center text showing current value.
    """

    def __init__(
        self,
        data: ProgressData,
        *,
        size: int = 120,
        thickness: int = 12,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize circular progress.

        Args:
            data: Progress data
            size: Widget size (diameter) in pixels
            thickness: Ring thickness in pixels
            parent: Parent widget
        """
        super().__init__(parent)
        self._data = data
        self._size = size
        self._thickness = thickness
        self.setFixedSize(size, size)
        self.update_data(data)

    def update_data(self, data: ProgressData) -> None:
        """Update with new data.

        Args:
            data: New progress data
        """
        self._data = data
        self.update()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Paint the circular progress ring."""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Calculate dimensions
        rect = QtCore.QRectF(
            self._thickness / 2,
            self._thickness / 2,
            self._size - self._thickness,
            self._size - self._thickness,
        )

        # Draw background ring
        pen = QtGui.QPen(QtGui.QColor(60, 60, 70, 80))
        pen.setWidth(self._thickness)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)

        # Draw progress arc
        status = self._data.status
        progress_color = QtGui.QColor(status.color)
        pen = QtGui.QPen(progress_color)
        pen.setWidth(self._thickness)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        painter.setPen(pen)

        # Calculate arc span (starts from top, goes clockwise)
        percentage = min(self._data.percentage, 100)
        span_angle = int((percentage / 100) * 360 * 16)
        start_angle = 90 * 16  # Start from top
        painter.drawArc(rect, start_angle, -span_angle)

        # Draw center text
        painter.setPen(QtGui.QColor(COLOR_TEXT_PRIMARY))
        font = painter.font()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)

        center_rect = QtCore.QRectF(0, 0, self._size, self._size)

        # Main percentage text
        painter.drawText(
            center_rect,
            QtCore.Qt.AlignCenter,
            f"{self._data.percentage:.0f}%"
        )

        painter.end()


class BudgetUtilizationCard(QtWidgets.QWidget):
    """Card showing budget utilization for a category.

    Combines category name, budget amounts, and progress bar
    in a card format suitable for the expenses page.
    """

    clicked = QtCore.Signal(str)  # Emits category name

    def __init__(
        self,
        category: str,
        budget: float,
        spent: float,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize budget utilization card.

        Args:
            category: Category name
            budget: Budget amount
            spent: Amount spent
            parent: Parent widget
        """
        super().__init__(parent)
        self._category = category
        self._budget = budget
        self._spent = spent
        self._init_ui()
        self._update_display()

    def _init_ui(self) -> None:
        """Initialize UI."""
        self.setObjectName("budgetUtilCard")
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#budgetUtilCard {{
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: {BORDER_RADIUS_CARD}px;
                padding: 16px;
            }}
            QWidget#budgetUtilCard:hover {{
                border-color: rgba(139, 92, 246, 0.4);
            }}
        """)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Top row: category and amounts
        top_row = QtWidgets.QHBoxLayout()
        top_row.setSpacing(12)

        self._category_label = QtWidgets.QLabel()
        self._category_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_BODY}px;
            font-weight: 600;
            color: {COLOR_TEXT_PRIMARY};
        """)
        top_row.addWidget(self._category_label)

        top_row.addStretch()

        self._amounts_label = QtWidgets.QLabel()
        self._amounts_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_BODY}px;
            color: {COLOR_TEXT_MUTED};
        """)
        top_row.addWidget(self._amounts_label)

        layout.addLayout(top_row)

        # Progress bar row
        bar_row = QtWidgets.QHBoxLayout()
        bar_row.setSpacing(12)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(PROGRESS_BAR_HEIGHT_LARGE)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        bar_row.addWidget(self._progress_bar, 1)

        self._status_label = QtWidgets.QLabel()
        self._status_label.setMinimumWidth(100)
        self._status_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        bar_row.addWidget(self._status_label)

        layout.addLayout(bar_row)

    def _update_display(self) -> None:
        """Update display values."""
        self._category_label.setText(self._category)

        # Calculate percentage
        pct = (self._spent / self._budget * 100) if self._budget > 0 else 0
        status = ProgressStatus.from_percentage(pct)
        remaining = self._budget - self._spent

        self._amounts_label.setText(
            f"{format_currency(self._spent)} / {format_currency(self._budget)}"
        )

        # Progress bar
        self._progress_bar.setValue(min(int(pct), 100))
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: rgba(60, 60, 70, 0.3);
                border: none;
                border-radius: 6px;
            }}
            QProgressBar::chunk {{
                background: {status.color};
                border-radius: 6px;
            }}
        """)

        # Status label
        if remaining >= 0:
            self._status_label.setText(f"{pct:.0f}% • {format_currency(remaining)} left")
            self._status_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_CAPTION}px;
                color: {COLOR_TEXT_MUTED};
            """)
        else:
            self._status_label.setText(f"{pct:.0f}% • {format_currency(abs(remaining))} over")
            self._status_label.setStyleSheet(f"""
                font-size: {FONT_SIZE_CAPTION}px;
                font-weight: 600;
                color: {COLOR_EXPENSE};
            """)

    def update_values(self, budget: float, spent: float) -> None:
        """Update budget and spent values.

        Args:
            budget: New budget amount
            spent: New spent amount
        """
        self._budget = budget
        self._spent = spent
        self._update_display()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle click."""
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self._category)
        super().mousePressEvent(event)


class BudgetUtilizationSection(QtWidgets.QWidget):
    """Section showing budget progress bars for all categories."""

    category_clicked = QtCore.Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize budget utilization section.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._bars: dict[str, HorizontalProgressBar] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self._layout = layout

    def update_budgets(
        self,
        allocations: list[tuple[str, float, float]],
    ) -> None:
        """Update all budget progress bars.

        Args:
            allocations: List of (category, budget, spent) tuples
        """
        # Clear existing
        for bar in self._bars.values():
            self._layout.removeWidget(bar)
            bar.deleteLater()
        self._bars.clear()

        # Add new bars
        for category, budget, spent in allocations:
            data = ProgressData(
                current=spent,
                target=budget,
                label=category,
                format_as_currency=True,
                show_remaining=True,
            )
            bar = HorizontalProgressBar(data, compact=True)
            bar.setCursor(QtCore.Qt.PointingHandCursor)
            bar.clicked.connect(lambda cat=category: self.category_clicked.emit(cat))
            self._bars[category] = bar
            self._layout.addWidget(bar)

    def clear(self) -> None:
        """Clear all bars."""
        for bar in self._bars.values():
            self._layout.removeWidget(bar)
            bar.deleteLater()
        self._bars.clear()