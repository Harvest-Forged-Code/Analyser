"""Centralized icon system using QtAwesome.

Provides consistent iconography across the application with support for
light/dark themes and multiple icon sizes.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import QSize

try:
    import qtawesome as qta
    QTAWESOME_AVAILABLE = True
except ImportError:
    QTAWESOME_AVAILABLE = False

if TYPE_CHECKING:
    pass


class AppIcon(Enum):
    """Application icon definitions using Material Design Icons.

    Each icon maps to a QtAwesome icon name (mdi6 prefix for Material Design Icons 6).
    """

    # Navigation icons
    NAV_DASHBOARD = "mdi6.view-dashboard"
    NAV_CALENDAR = "mdi6.calendar-month"
    NAV_EARNINGS = "mdi6.cash-plus"
    NAV_EXPENSES = "mdi6.receipt"
    NAV_PAYMENTS = "mdi6.swap-horizontal"
    NAV_GOALS = "mdi6.target"
    NAV_SAVINGS = "mdi6.piggy-bank"
    NAV_NET_WORTH = "mdi6.chart-areaspline"
    NAV_RECURRING = "mdi6.autorenew"
    NAV_UPLOAD = "mdi6.upload"
    NAV_MAPPER = "mdi6.folder-table"
    NAV_SETTINGS = "mdi6.cog"

    # Action icons
    ACTION_ADD = "mdi6.plus"
    ACTION_EDIT = "mdi6.pencil"
    ACTION_DELETE = "mdi6.delete"
    ACTION_SAVE = "mdi6.content-save"
    ACTION_CANCEL = "mdi6.close"
    ACTION_REFRESH = "mdi6.refresh"
    ACTION_SEARCH = "mdi6.magnify"
    ACTION_FILTER = "mdi6.filter"
    ACTION_EXPORT = "mdi6.export"
    ACTION_IMPORT = "mdi6.import"
    ACTION_HISTORY = "mdi6.history"
    ACTION_TOP_UP = "mdi6.plus-circle"

    # Status icons
    STATUS_SUCCESS = "mdi6.check-circle"
    STATUS_WARNING = "mdi6.alert"
    STATUS_ERROR = "mdi6.alert-circle"
    STATUS_INFO = "mdi6.information"
    STATUS_ON_TRACK = "mdi6.check"
    STATUS_AT_RISK = "mdi6.alert"
    STATUS_BEHIND = "mdi6.alert-circle"
    STATUS_COMPLETED = "mdi6.star"
    STATUS_PAUSED = "mdi6.pause"

    # Trend icons
    TREND_UP = "mdi6.trending-up"
    TREND_DOWN = "mdi6.trending-down"
    TREND_NEUTRAL = "mdi6.trending-neutral"

    # Chart icons
    CHART_LINE = "mdi6.chart-line"
    CHART_BAR = "mdi6.chart-bar"
    CHART_PIE = "mdi6.chart-pie"
    CHART_DONUT = "mdi6.chart-donut"

    # Misc icons
    MENU = "mdi6.menu"
    CLOSE = "mdi6.close"
    CHEVRON_LEFT = "mdi6.chevron-left"
    CHEVRON_RIGHT = "mdi6.chevron-right"
    CHEVRON_DOWN = "mdi6.chevron-down"
    CHEVRON_UP = "mdi6.chevron-up"
    THEME_LIGHT = "mdi6.weather-sunny"
    THEME_DARK = "mdi6.weather-night"
    CATEGORY = "mdi6.tag"
    MONEY = "mdi6.currency-usd"


# Default icon sizes
ICON_SIZE_SMALL = 16
ICON_SIZE_MEDIUM = 20
ICON_SIZE_LARGE = 24
ICON_SIZE_XLARGE = 32

# Default colors
DEFAULT_ICON_COLOR = "#D1D5DB"
DEFAULT_ICON_COLOR_LIGHT = "#5B21B6"


def get_icon(
    icon: AppIcon | str,
    *,
    color: str | None = None,
    size: int = ICON_SIZE_MEDIUM,
) -> QIcon:
    """Get a QIcon for the specified icon.

    Args:
        icon: AppIcon enum value or icon name string
        color: Icon color (hex string). Defaults to theme-appropriate color.
        size: Icon size in pixels

    Returns:
        QIcon instance, or empty QIcon if qtawesome is not available
    """
    if not QTAWESOME_AVAILABLE:
        return QIcon()

    icon_name = icon.value if isinstance(icon, AppIcon) else icon
    color = color or DEFAULT_ICON_COLOR

    try:
        return qta.icon(icon_name, color=color, scale_factor=1.0)
    except Exception:  # pylint: disable=broad-except
        # Fallback to empty icon if icon not found
        return QIcon()


def get_icon_pixmap(
    icon: AppIcon | str,
    *,
    color: str | None = None,
    size: int = ICON_SIZE_MEDIUM,
) -> QPixmap:
    """Get a QPixmap for the specified icon.

    Args:
        icon: AppIcon enum value or icon name string
        color: Icon color (hex string). Defaults to theme-appropriate color.
        size: Icon size in pixels

    Returns:
        QPixmap instance, or empty QPixmap if qtawesome is not available
    """
    qicon = get_icon(icon, color=color, size=size)
    if qicon.isNull():
        return QPixmap()
    return qicon.pixmap(QSize(size, size))


def get_themed_icon(
    icon: AppIcon | str,
    *,
    dark_mode: bool = True,
    size: int = ICON_SIZE_MEDIUM,
) -> QIcon:
    """Get a theme-aware icon.

    Args:
        icon: AppIcon enum value or icon name string
        dark_mode: Whether dark mode is active
        size: Icon size in pixels

    Returns:
        QIcon with appropriate color for the current theme
    """
    color = DEFAULT_ICON_COLOR if dark_mode else DEFAULT_ICON_COLOR_LIGHT
    return get_icon(icon, color=color, size=size)


def get_colored_icon(
    icon: AppIcon | str,
    color: str,
    *,
    size: int = ICON_SIZE_MEDIUM,
) -> QIcon:
    """Get an icon with a specific color.

    Args:
        icon: AppIcon enum value or icon name string
        color: Icon color (hex string)
        size: Icon size in pixels

    Returns:
        QIcon with the specified color
    """
    return get_icon(icon, color=color, size=size)


# Navigation icon mapping for sidebar
NAV_ICONS: dict[str, AppIcon] = {
    "Cashflow Dashboard": AppIcon.NAV_DASHBOARD,
    "Yearly Summary": AppIcon.NAV_CALENDAR,
    "Earnings": AppIcon.NAV_EARNINGS,
    "Expenses": AppIcon.NAV_EXPENSES,
    "Payments": AppIcon.NAV_PAYMENTS,
    "Budget Goals": AppIcon.NAV_GOALS,
    "Savings": AppIcon.NAV_SAVINGS,
    "Net Worth": AppIcon.NAV_NET_WORTH,
    "Recurring": AppIcon.NAV_RECURRING,
    "Upload": AppIcon.NAV_UPLOAD,
    "Mapper Hub": AppIcon.NAV_MAPPER,
    "Settings": AppIcon.NAV_SETTINGS,
}
