"""Custom chart tooltip widget.

Provides styled tooltips for chart data points.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor

from budget_analyser.views.constants import (
    COLOR_PRIMARY,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    FONT_SIZE_BODY,
    FONT_SIZE_CAPTION,
    BORDER_RADIUS_CARD,
)

if TYPE_CHECKING:
    pass


class ChartTooltip(QWidget):
    """Custom tooltip widget for chart data points.

    Displays a styled tooltip with title, value, and optional subtitle
    that follows the application's design language.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize chart tooltip.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui()
        self.hide()

    def _init_ui(self) -> None:
        """Initialize the UI layout."""
        self.setObjectName("chartTooltip")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(
            Qt.WindowType.ToolTip |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )

        # Apply styling
        self.setStyleSheet(f"""
            QWidget#chartTooltip {{
                background: rgba(18, 18, 20, 0.95);
                border: 1px solid rgba(139, 92, 246, 0.3);
                border-radius: {BORDER_RADIUS_CARD // 2}px;
                padding: 8px 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        # Title label
        self._title_label = QLabel()
        self._title_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            font-weight: 600;
            color: {COLOR_PRIMARY};
            letter-spacing: 0.5px;
        """)
        layout.addWidget(self._title_label)

        # Value label
        self._value_label = QLabel()
        self._value_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {COLOR_TEXT_PRIMARY};
            letter-spacing: -0.5px;
        """)
        layout.addWidget(self._value_label)

        # Subtitle label
        self._subtitle_label = QLabel()
        self._subtitle_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            color: {COLOR_TEXT_MUTED};
        """)
        layout.addWidget(self._subtitle_label)

        # Add shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)

    def show_at(
        self,
        position: QPoint,
        *,
        title: str = "",
        value: str = "",
        subtitle: str = "",
    ) -> None:
        """Show tooltip at the specified position.

        Args:
            position: Screen position for the tooltip
            title: Tooltip title text
            value: Main value text
            subtitle: Optional subtitle text
        """
        self._title_label.setText(title.upper())
        self._title_label.setVisible(bool(title))

        self._value_label.setText(value)
        self._value_label.setVisible(bool(value))

        self._subtitle_label.setText(subtitle)
        self._subtitle_label.setVisible(bool(subtitle))

        # Adjust position to avoid going off-screen
        self.adjustSize()
        tooltip_size = self.sizeHint()

        # Offset to position tooltip above and to the right of cursor
        offset_x = 10
        offset_y = -tooltip_size.height() - 10

        adjusted_pos = QPoint(
            position.x() + offset_x,
            position.y() + offset_y
        )

        self.move(adjusted_pos)
        self.show()
        self.raise_()

    def hide_tooltip(self) -> None:
        """Hide the tooltip."""
        self.hide()

    def set_accent_color(self, color: str) -> None:
        """Set the accent color for the tooltip.

        Args:
            color: Hex color string
        """
        self._title_label.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            font-weight: 600;
            color: {color};
            letter-spacing: 0.5px;
        """)

        self.setStyleSheet(f"""
            QWidget#chartTooltip {{
                background: rgba(18, 18, 20, 0.95);
                border: 1px solid {color}4D;
                border-radius: {BORDER_RADIUS_CARD // 2}px;
                padding: 8px 12px;
            }}
        """)


class ChartLegendItem(QWidget):
    """Single legend item for charts."""

    def __init__(
        self,
        label: str,
        color: str,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize legend item.

        Args:
            label: Legend text
            color: Color indicator (hex string)
            parent: Parent widget
        """
        super().__init__(parent)
        self._init_ui(label, color)

    def _init_ui(self, label: str, color: str) -> None:
        """Initialize UI."""
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Color indicator
        color_box = QLabel()
        color_box.setFixedSize(12, 12)
        color_box.setStyleSheet(f"""
            background: {color};
            border-radius: 3px;
        """)
        layout.addWidget(color_box)

        # Label
        label_widget = QLabel(label)
        label_widget.setStyleSheet(f"""
            font-size: {FONT_SIZE_CAPTION}px;
            color: {COLOR_TEXT_MUTED};
        """)
        layout.addWidget(label_widget)

        layout.addStretch()
