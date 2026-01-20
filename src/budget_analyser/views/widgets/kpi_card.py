"""KPI Card widget for displaying key financial metrics.

Provides a reusable card component showing summary metrics with
optional trend indicators, progress bars, and comparisons.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6 import QtWidgets, QtCore, QtGui

from budget_analyser.views.constants import (
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_INCOME,
    COLOR_EXPENSE,
    COLOR_POSITIVE,
    FONT_SIZE_CARD_VALUE,
    FONT_SIZE_SECTION_TITLE,
    FONT_SIZE_CAPTION,
    KPI_CARD_MIN_HEIGHT,
    KPI_CARD_MIN_WIDTH,
    BORDER_RADIUS_CARD,
    PROGRESS_BAR_HEIGHT,
    get_trend_color,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class KPICardData:
    """Data transfer object for KPI card."""

    title: str
    value: str
    trend_value: str | None = None
    trend_direction: str = "neutral"  # "up", "down", "neutral"
    progress_percent: float | None = None
    comparison_text: str | None = None
    accent_color: str = COLOR_PRIMARY
    value_color: str | None = None


class KPICard(QtWidgets.QWidget):
    """Reusable KPI summary card widget.

    Displays a key metric with optional trend indicator, progress bar,
    and comparison text. Used across Earnings, Expenses, and Budget pages.
    """

    clicked = QtCore.Signal()

    def __init__(
        self,
        data: KPICardData,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize KPI card.

        Args:
            data: Card data including title, value, and optional elements
            parent: Parent widget
        """
        super().__init__(parent)
        self._data = data
        self._hovered = False
        self._init_ui()
        self.update_data(data)

    def _init_ui(self) -> None:
        """Initialize the UI layout."""
        self.setObjectName("kpiCard")
        self.setMinimumHeight(KPI_CARD_MIN_HEIGHT)
        self.setMinimumWidth(KPI_CARD_MIN_WIDTH)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)

        # Title row
        self._title_label = QtWidgets.QLabel()
        self._title_label.setObjectName("kpiTitle")
        layout.addWidget(self._title_label)

        # Value row with trend
        value_row = QtWidgets.QHBoxLayout()
        value_row.setSpacing(12)

        self._value_label = QtWidgets.QLabel()
        self._value_label.setObjectName("kpiValue")
        value_row.addWidget(self._value_label)

        value_row.addStretch()

        # Trend container
        self._trend_container = QtWidgets.QWidget()
        trend_layout = QtWidgets.QHBoxLayout(self._trend_container)
        trend_layout.setContentsMargins(0, 0, 0, 0)
        trend_layout.setSpacing(4)

        self._trend_arrow = QtWidgets.QLabel()
        self._trend_arrow.setObjectName("kpiTrendArrow")
        trend_layout.addWidget(self._trend_arrow)

        self._trend_label = QtWidgets.QLabel()
        self._trend_label.setObjectName("kpiTrend")
        trend_layout.addWidget(self._trend_label)

        value_row.addWidget(self._trend_container)
        layout.addLayout(value_row)

        # Progress bar (optional)
        self._progress_container = QtWidgets.QWidget()
        progress_layout = QtWidgets.QHBoxLayout(self._progress_container)
        progress_layout.setContentsMargins(0, 4, 0, 0)
        progress_layout.setSpacing(8)

        self._progress_bar = QtWidgets.QProgressBar()
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(PROGRESS_BAR_HEIGHT)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        progress_layout.addWidget(self._progress_bar, 1)

        self._progress_label = QtWidgets.QLabel()
        self._progress_label.setObjectName("kpiProgressLabel")
        progress_layout.addWidget(self._progress_label)

        layout.addWidget(self._progress_container)

        # Comparison text (optional)
        self._comparison_label = QtWidgets.QLabel()
        self._comparison_label.setObjectName("kpiComparison")
        self._comparison_label.setWordWrap(True)
        layout.addWidget(self._comparison_label)

        layout.addStretch()
        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply styles to the card."""
        accent = self._data.accent_color
        value_color = self._data.value_color or COLOR_TEXT_PRIMARY
        trend_color = get_trend_color(self._data.trend_direction)

        # Determine progress bar color
        progress_color = accent
        if self._data.progress_percent is not None:
            if self._data.progress_percent > 100:
                progress_color = COLOR_EXPENSE
            elif self._data.progress_percent > 90:
                progress_color = COLOR_EXPENSE
            elif self._data.progress_percent > 70:
                progress_color = COLOR_INCOME

        self.setStyleSheet(f"""
            QWidget#kpiCard {{
                background: {COLOR_CARD_BG};
                border: 1px solid {COLOR_CARD_BORDER};
                border-radius: {BORDER_RADIUS_CARD}px;
            }}
            QWidget#kpiCard:hover {{
                border-color: rgba(139, 92, 246, 0.4);
            }}
            QLabel#kpiTitle {{
                font-size: {FONT_SIZE_SECTION_TITLE}px;
                font-weight: 700;
                letter-spacing: 1px;
                color: {accent};
            }}
            QLabel#kpiValue {{
                font-size: {FONT_SIZE_CARD_VALUE}px;
                font-weight: 700;
                color: {value_color};
                letter-spacing: -0.5px;
            }}
            QLabel#kpiTrendArrow {{
                font-size: 14px;
                color: {trend_color};
            }}
            QLabel#kpiTrend {{
                font-size: 14px;
                font-weight: 600;
                color: {trend_color};
            }}
            QLabel#kpiProgressLabel {{
                font-size: {FONT_SIZE_CAPTION}px;
                font-weight: 600;
                color: {COLOR_TEXT_MUTED};
            }}
            QLabel#kpiComparison {{
                font-size: {FONT_SIZE_CAPTION}px;
                color: {COLOR_TEXT_MUTED};
            }}
            QProgressBar {{
                background: rgba(60, 60, 70, 0.3);
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background: {progress_color};
                border-radius: 4px;
            }}
        """)

    def update_data(self, data: KPICardData) -> None:
        """Update card with new data.

        Args:
            data: New card data
        """
        self._data = data

        # Update title
        self._title_label.setText(data.title.upper())

        # Update value
        self._value_label.setText(data.value)

        # Update trend
        if data.trend_value:
            self._trend_container.setVisible(True)
            arrow = "▲" if data.trend_direction == "up" else (
                "▼" if data.trend_direction == "down" else ""
            )
            self._trend_arrow.setText(arrow)
            self._trend_label.setText(data.trend_value)
        else:
            self._trend_container.setVisible(False)

        # Update progress bar
        if data.progress_percent is not None:
            self._progress_container.setVisible(True)
            # Cap display at 100 but show actual value
            display_value = min(int(data.progress_percent), 100)
            self._progress_bar.setValue(display_value)
            self._progress_label.setText(f"{data.progress_percent:.0f}%")
        else:
            self._progress_container.setVisible(False)

        # Update comparison
        if data.comparison_text:
            self._comparison_label.setVisible(True)
            self._comparison_label.setText(data.comparison_text)
        else:
            self._comparison_label.setVisible(False)

        self._apply_styles()

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Handle mouse press for click detection."""
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse enter for hover state."""
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Handle mouse leave for hover state."""
        self._hovered = False
        self.update()
        super().leaveEvent(event)


class KPICardRow(QtWidgets.QWidget):
    """Container for a row of KPI cards with consistent spacing."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize KPI card row.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._cards: list[KPICard] = []

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        self._layout = layout

    def add_card(self, data: KPICardData) -> KPICard:
        """Add a KPI card to the row.

        Args:
            data: Card data

        Returns:
            The created KPICard widget
        """
        card = KPICard(data)
        self._cards.append(card)
        self._layout.addWidget(card)
        return card

    def update_card(self, index: int, data: KPICardData) -> None:
        """Update a specific card's data.

        Args:
            index: Card index
            data: New card data
        """
        if 0 <= index < len(self._cards):
            self._cards[index].update_data(data)

    def get_card(self, index: int) -> KPICard | None:
        """Get card at index.

        Args:
            index: Card index

        Returns:
            KPICard or None if index out of range
        """
        if 0 <= index < len(self._cards):
            return self._cards[index]
        return None

    def clear(self) -> None:
        """Remove all cards."""
        for card in self._cards:
            self._layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()