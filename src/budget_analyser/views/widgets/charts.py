"""Chart widgets using pyqtgraph (views layer).

Purpose:
    Provide reusable chart widgets for visualizing financial data:
    - Line charts for trends over time
    - Bar charts for category comparisons
    - Pie/Donut charts for distribution
    - Sparklines for inline mini-charts

All widgets support light/dark themes and are Qt-native for seamless integration.
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except ImportError:
    PYQTGRAPH_AVAILABLE = False

from budget_analyser.views.constants import COLOR_PRIMARY, COLOR_TEXT_MUTED


# Color palette for charts (works in both light and dark themes)
CHART_COLORS = [
    "#4e79a7",  # Blue
    "#f28e2b",  # Orange
    "#e15759",  # Red
    "#76b7b2",  # Teal
    "#59a14f",  # Green
    "#edc948",  # Yellow
    "#b07aa1",  # Purple
    "#ff9da7",  # Pink
    "#9c755f",  # Brown
    "#bab0ac",  # Gray
]


def get_chart_color(index: int) -> str:
    """Get a chart color by index, cycling through the palette."""
    return CHART_COLORS[index % len(CHART_COLORS)]


class CurrencyAxisItem(pg.AxisItem):
    """Custom axis item for currency formatting.

    Displays values as formatted currency (e.g., $1,234).
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize currency axis."""
        super().__init__(*args, **kwargs)
        self._prefix = "$"
        self._show_cents = False

    def set_prefix(self, prefix: str) -> None:
        """Set currency prefix.

        Args:
            prefix: Currency symbol (e.g., "$", "€")
        """
        self._prefix = prefix

    def set_show_cents(self, show: bool) -> None:
        """Set whether to show cents.

        Args:
            show: Whether to show decimal places
        """
        self._show_cents = show

    def tickStrings(self, values, scale, spacing):
        """Format tick values as currency."""
        strings = []
        for v in values:
            if abs(v) >= 1_000_000:
                # Format as millions
                formatted = f"{self._prefix}{v / 1_000_000:.1f}M"
            elif abs(v) >= 1_000:
                # Format as thousands
                formatted = f"{self._prefix}{v / 1_000:.0f}K"
            elif self._show_cents:
                formatted = f"{self._prefix}{v:,.2f}"
            else:
                formatted = f"{self._prefix}{v:,.0f}"
            strings.append(formatted)
        return strings


class DateAxisItem(pg.AxisItem):
    """Custom axis item for date formatting.

    Displays numeric indices as formatted dates.
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initialize date axis."""
        super().__init__(*args, **kwargs)
        self._date_labels: list[str] = []
        self._format = "short"  # "short" for "Jan", "full" for "January 2024"

    def set_date_labels(self, labels: list[str]) -> None:
        """Set the date labels to use.

        Args:
            labels: List of date strings corresponding to x indices
        """
        self._date_labels = labels

    def set_format(self, fmt: str) -> None:
        """Set date format.

        Args:
            fmt: "short" or "full"
        """
        self._format = fmt

    def tickStrings(self, values, scale, spacing):
        """Format tick values as dates."""
        strings = []
        for v in values:
            idx = int(round(v))
            if 0 <= idx < len(self._date_labels):
                strings.append(self._date_labels[idx])
            else:
                strings.append("")
        return strings


class ChartWidget(QWidget):
    """Base class for chart widgets."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = ""
        self._dark_mode = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the widget UI."""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Title label
        self._title_label = QLabel("")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title_label.setVisible(False)
        self.layout.addWidget(self._title_label)

    def set_title(self, title: str) -> None:
        """Set the chart title."""
        self._title = title
        self._title_label.setText(title)
        self._title_label.setVisible(bool(title))

    def set_dark_mode(self, dark: bool) -> None:
        """Switch between light and dark mode."""
        self._dark_mode = dark
        self._apply_theme()

    def _apply_theme(self) -> None:
        """Apply the current theme to the chart."""
        pass  # Subclasses implement


class LineChartWidget(ChartWidget):
    """Line chart widget for time-series data."""

    # Signal emitted when hovering over data point (x_index, y_value, screen_pos)
    point_hovered = Signal(int, float, QPointF)
    hover_left = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plot_widget: pg.PlotWidget | None = None
        self._series: list = []
        self._crosshair_v: pg.InfiniteLine | None = None
        self._crosshair_h: pg.InfiniteLine | None = None
        self._crosshair_enabled = False
        self._x_data: list = []
        self._y_data: list = []
        self._init_plot()

    def _init_plot(self) -> None:
        """Initialize the pyqtgraph plot widget."""
        if not PYQTGRAPH_AVAILABLE:
            label = QLabel("pyqtgraph not installed")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(label)
            return

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#000000")
        self._plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self._plot_widget.setMouseEnabled(x=True, y=False)

        # Style the axes
        self._plot_widget.getAxis("bottom").setPen(pg.mkPen(color="#666666", width=1))
        self._plot_widget.getAxis("left").setPen(pg.mkPen(color="#666666", width=1))

        self.layout.addWidget(self._plot_widget)

    def enable_crosshair(self, enabled: bool = True) -> None:
        """Enable or disable crosshair on hover.

        Args:
            enabled: Whether to show crosshair
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        self._crosshair_enabled = enabled

        if enabled:
            self._setup_crosshair()
        else:
            self._remove_crosshair()

    def _setup_crosshair(self) -> None:
        """Set up crosshair lines for hover interaction."""
        if self._plot_widget is None:
            return

        # Vertical crosshair line
        self._crosshair_v = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen(color=COLOR_PRIMARY, width=1, style=Qt.PenStyle.DashLine)
        )
        self._crosshair_v.setVisible(False)
        self._plot_widget.addItem(self._crosshair_v)

        # Horizontal crosshair line
        self._crosshair_h = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen(color=COLOR_PRIMARY, width=1, style=Qt.PenStyle.DashLine)
        )
        self._crosshair_h.setVisible(False)
        self._plot_widget.addItem(self._crosshair_h)

        # Connect mouse move signal
        self._plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _remove_crosshair(self) -> None:
        """Remove crosshair lines."""
        if self._plot_widget is None:
            return

        if self._crosshair_v is not None:
            self._plot_widget.removeItem(self._crosshair_v)
            self._crosshair_v = None

        if self._crosshair_h is not None:
            self._plot_widget.removeItem(self._crosshair_h)
            self._crosshair_h = None

    def _on_mouse_moved(self, pos) -> None:
        """Handle mouse movement for crosshair update."""
        if self._plot_widget is None:
            return

        # Check if mouse is within plot area
        if self._plot_widget.sceneBoundingRect().contains(pos):
            mouse_point = self._plot_widget.plotItem.vb.mapSceneToView(pos)
            x = mouse_point.x()
            y = mouse_point.y()

            # Update crosshair position
            if self._crosshair_v is not None:
                self._crosshair_v.setPos(x)
                self._crosshair_v.setVisible(True)

            if self._crosshair_h is not None:
                self._crosshair_h.setPos(y)
                self._crosshair_h.setVisible(True)

            # Find nearest data point and emit signal
            if self._x_data and self._y_data:
                x_idx = int(round(x))
                if 0 <= x_idx < len(self._y_data):
                    y_val = self._y_data[x_idx]
                    screen_pos = self._plot_widget.mapToGlobal(
                        self._plot_widget.mapFromScene(pos.toPoint())
                    )
                    self.point_hovered.emit(x_idx, y_val, QPointF(screen_pos))
        else:
            # Hide crosshair when outside plot
            if self._crosshair_v is not None:
                self._crosshair_v.setVisible(False)
            if self._crosshair_h is not None:
                self._crosshair_h.setVisible(False)
            self.hover_left.emit()

    def set_data(
        self,
        x_values: Sequence[float] | Sequence[str],
        y_values: Sequence[float],
        *,
        label: str = "",
        color: str | None = None,
    ) -> None:
        """Set data for a single line.

        Args:
            x_values: X-axis values (numeric or string labels).
            y_values: Y-axis values.
            label: Optional series label.
            color: Optional line color.
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        self.clear()

        color = color or get_chart_color(0)
        pen = pg.mkPen(color=color, width=2)

        # Convert string labels to numeric if needed
        if x_values and isinstance(x_values[0], str):
            x_numeric = list(range(len(x_values)))
            self._plot_widget.getAxis("bottom").setTicks([
                [(i, str(v)) for i, v in enumerate(x_values)]
            ])
        else:
            x_numeric = list(x_values)

        # Store data for crosshair interaction
        self._x_data = x_numeric
        self._y_data = list(y_values)

        plot_item = self._plot_widget.plot(
            x_numeric,
            list(y_values),
            pen=pen,
            name=label,
        )
        self._series.append(plot_item)

    def add_series(
        self,
        x_values: Sequence[float] | Sequence[str],
        y_values: Sequence[float],
        *,
        label: str = "",
        color: str | None = None,
    ) -> None:
        """Add an additional data series.

        Args:
            x_values: X-axis values.
            y_values: Y-axis values.
            label: Optional series label.
            color: Optional line color.
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        color = color or get_chart_color(len(self._series))
        pen = pg.mkPen(color=color, width=2)

        # Convert string labels to numeric if needed
        if x_values and isinstance(x_values[0], str):
            x_numeric = list(range(len(x_values)))
        else:
            x_numeric = list(x_values)

        plot_item = self._plot_widget.plot(
            x_numeric,
            list(y_values),
            pen=pen,
            name=label,
        )
        self._series.append(plot_item)

    def clear(self) -> None:
        """Clear all data from the chart."""
        if self._plot_widget is not None:
            self._plot_widget.clear()
            self._series.clear()
            self._x_data = []
            self._y_data = []

            # Re-add crosshairs if enabled
            if self._crosshair_enabled:
                self._setup_crosshair()

    def set_axis_labels(self, x_label: str = "", y_label: str = "") -> None:
        """Set axis labels."""
        if self._plot_widget is not None:
            self._plot_widget.setLabel("bottom", x_label)
            self._plot_widget.setLabel("left", y_label)

    def use_currency_axis(self, prefix: str = "$", show_cents: bool = False) -> None:
        """Configure the Y-axis to display currency values.

        Args:
            prefix: Currency symbol
            show_cents: Whether to show decimal places
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        currency_axis = CurrencyAxisItem(orientation='left')
        currency_axis.set_prefix(prefix)
        currency_axis.set_show_cents(show_cents)

        self._plot_widget.setAxisItems({'left': currency_axis})

    def _apply_theme(self) -> None:
        """Apply theme to the plot widget."""
        if self._plot_widget is None:
            return

        if self._dark_mode:
            self._plot_widget.setBackground("#1e1e1e")
            axis_color = "#cccccc"
        else:
            self._plot_widget.setBackground("w")
            axis_color = "#666666"

        self._plot_widget.getAxis("bottom").setPen(pg.mkPen(color=axis_color, width=1))
        self._plot_widget.getAxis("left").setPen(pg.mkPen(color=axis_color, width=1))


class BarChartWidget(ChartWidget):
    """Bar chart widget for category comparisons."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._plot_widget: pg.PlotWidget | None = None
        self._bar_items: list = []
        self._init_plot()

    def _init_plot(self) -> None:
        """Initialize the pyqtgraph plot widget."""
        if not PYQTGRAPH_AVAILABLE:
            label = QLabel("pyqtgraph not installed")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(label)
            return

        self._plot_widget = pg.PlotWidget()
        self._plot_widget.setBackground("#000000")
        self._plot_widget.showGrid(x=False, y=True, alpha=0.3)

        self.layout.addWidget(self._plot_widget)

    def set_data(
        self,
        categories: Sequence[str],
        values: Sequence[float],
        *,
        colors: Sequence[str] | None = None,
    ) -> None:
        """Set bar chart data.

        Args:
            categories: Category labels for x-axis.
            values: Values for each category.
            colors: Optional colors for each bar.
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        self.clear()

        x = np.arange(len(categories))
        colors = colors or [get_chart_color(i) for i in range(len(categories))]

        # Create bar graph item
        bar_item = pg.BarGraphItem(
            x=x,
            height=values,
            width=0.6,
            brushes=[pg.mkBrush(c) for c in colors],
        )
        self._plot_widget.addItem(bar_item)
        self._bar_items.append(bar_item)

        # Set x-axis labels
        axis = self._plot_widget.getAxis("bottom")
        axis.setTicks([[(i, str(cat)) for i, cat in enumerate(categories)]])

    def set_grouped_data(
        self,
        categories: Sequence[str],
        series_data: dict[str, Sequence[float]],
        *,
        colors: dict[str, str] | None = None,
    ) -> None:
        """Set grouped bar chart data.

        Args:
            categories: Category labels for x-axis.
            series_data: Dictionary mapping series name -> values.
            colors: Optional dictionary mapping series name -> color.
        """
        if not PYQTGRAPH_AVAILABLE or self._plot_widget is None:
            return

        self.clear()

        n_series = len(series_data)
        n_categories = len(categories)
        bar_width = 0.8 / n_series

        colors = colors or {}

        for i, (series_name, values) in enumerate(series_data.items()):
            x = np.arange(n_categories) + (i - n_series / 2 + 0.5) * bar_width
            color = colors.get(series_name, get_chart_color(i))

            bar_item = pg.BarGraphItem(
                x=x,
                height=values,
                width=bar_width * 0.9,
                brush=pg.mkBrush(color),
                name=series_name,
            )
            self._plot_widget.addItem(bar_item)
            self._bar_items.append(bar_item)

        # Set x-axis labels
        axis = self._plot_widget.getAxis("bottom")
        axis.setTicks([[(i, str(cat)) for i, cat in enumerate(categories)]])

    def clear(self) -> None:
        """Clear all data from the chart."""
        if self._plot_widget is not None:
            for item in self._bar_items:
                self._plot_widget.removeItem(item)
            self._bar_items.clear()

    def _apply_theme(self) -> None:
        """Apply theme to the plot widget."""
        if self._plot_widget is None:
            return

        if self._dark_mode:
            self._plot_widget.setBackground("#1e1e1e")
        else:
            self._plot_widget.setBackground("w")


class PieChartWidget(ChartWidget):
    """Pie/Donut chart widget for distribution visualization.

    Note: pyqtgraph doesn't natively support pie charts, so this uses
    a custom QPainter implementation.
    """

    def __init__(self, parent: QWidget | None = None, *, donut: bool = False) -> None:
        super().__init__(parent)
        self._data: list[tuple[str, float]] = []
        self._colors: list[str] = []
        self._donut = donut
        self._legend_visible = True
        self.setMinimumSize(200, 200)

    def set_data(
        self,
        labels: Sequence[str],
        values: Sequence[float],
        *,
        colors: Sequence[str] | None = None,
    ) -> None:
        """Set pie chart data.

        Args:
            labels: Category labels.
            values: Values for each category.
            colors: Optional colors for each slice.
        """
        self._data = list(zip(labels, values))
        self._colors = list(colors) if colors else [
            get_chart_color(i) for i in range(len(labels))
        ]
        self.update()

    def set_legend_visible(self, visible: bool) -> None:
        """Show or hide the legend."""
        self._legend_visible = visible
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the pie chart."""
        if not self._data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Calculate dimensions
        width = self.width()
        height = self.height()
        legend_width = 150 if self._legend_visible else 0
        chart_size = min(width - legend_width, height) - 40
        chart_x = (width - legend_width - chart_size) // 2
        chart_y = (height - chart_size) // 2

        # Calculate total
        total = sum(v for _, v in self._data)
        if total == 0:
            return

        # Draw slices
        start_angle = 90 * 16  # Start from top (Qt uses 1/16 degree units)

        for i, (label, value) in enumerate(self._data):
            if value <= 0:
                continue

            span_angle = int(value / total * 360 * 16)
            color = QColor(self._colors[i])

            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))

            if self._donut:
                # Draw donut slice (outer - inner arc)
                outer_rect = (chart_x, chart_y, chart_size, chart_size)
                inner_size = chart_size * 0.5
                inner_x = chart_x + (chart_size - inner_size) // 2
                inner_y = chart_y + (chart_size - inner_size) // 2

                # This is simplified - full donut would need QPainterPath
                painter.drawPie(*outer_rect, start_angle, span_angle)
            else:
                painter.drawPie(chart_x, chart_y, chart_size, chart_size,
                                start_angle, span_angle)

            start_angle += span_angle

        # Draw donut hole
        if self._donut:
            bg_color = QColor("#000000") if self._dark_mode else QColor("white")
            painter.setBrush(QBrush(bg_color))
            inner_size = int(chart_size * 0.5)
            inner_x = chart_x + (chart_size - inner_size) // 2
            inner_y = chart_y + (chart_size - inner_size) // 2
            painter.drawEllipse(inner_x, inner_y, inner_size, inner_size)

        # Draw legend
        if self._legend_visible:
            legend_x = width - legend_width + 10
            legend_y = 30
            text_color = QColor("#E2E4F0") if self._dark_mode else QColor("#333333")
            painter.setPen(QPen(text_color))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)

            for i, (label, value) in enumerate(self._data):
                if value <= 0:
                    continue

                # Color box
                color = QColor(self._colors[i])
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                painter.drawRect(legend_x, legend_y + i * 20, 12, 12)

                # Label text
                painter.setPen(QPen(text_color))
                pct = value / total * 100
                text = f"{label[:15]} ({pct:.1f}%)"
                painter.drawText(legend_x + 18, legend_y + i * 20 + 10, text)


class SparklineWidget(QWidget):
    """Mini inline chart for showing trends in tables."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: list[float] = []
        self._color = CHART_COLORS[0]
        self._show_area = True
        self.setMinimumSize(60, 20)
        self.setMaximumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_data(self, values: Sequence[float]) -> None:
        """Set sparkline data."""
        self._data = list(values)
        self.update()

    def set_color(self, color: str) -> None:
        """Set the line color."""
        self._color = color
        self.update()

    def set_show_area(self, show: bool) -> None:
        """Show or hide the area fill."""
        self._show_area = show
        self.update()

    def paintEvent(self, event) -> None:
        """Paint the sparkline."""
        if not self._data or len(self._data) < 2:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        margin = 2

        # Calculate scaling
        min_val = min(self._data)
        max_val = max(self._data)
        val_range = max_val - min_val if max_val != min_val else 1

        # Calculate points
        points = []
        for i, val in enumerate(self._data):
            x = margin + (i / (len(self._data) - 1)) * (width - 2 * margin)
            y = height - margin - ((val - min_val) / val_range) * (height - 2 * margin)
            points.append((x, y))

        # Draw area fill
        if self._show_area:
            color = QColor(self._color)
            color.setAlpha(50)
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(Qt.PenStyle.NoPen))

            from PySide6.QtGui import QPolygonF
            from PySide6.QtCore import QPointF
            polygon = QPolygonF()
            polygon.append(QPointF(points[0][0], height - margin))
            for x, y in points:
                polygon.append(QPointF(x, y))
            polygon.append(QPointF(points[-1][0], height - margin))
            painter.drawPolygon(polygon)

        # Draw line
        color = QColor(self._color)
        painter.setPen(QPen(color, 1.5))
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
