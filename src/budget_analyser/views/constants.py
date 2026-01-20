"""Design tokens and constants for the views layer.

Provides consistent styling values across all UI components.
"""
from __future__ import annotations

from typing import Final


# Typography - Font Sizes
FONT_SIZE_PAGE_TITLE: Final = 22
FONT_SIZE_SECTION_TITLE: Final = 11
FONT_SIZE_CARD_VALUE: Final = 28
FONT_SIZE_TABLE_HEADER: Final = 12
FONT_SIZE_BODY: Final = 13
FONT_SIZE_CAPTION: Final = 12
FONT_SIZE_SMALL: Final = 11

# Spacing
SPACING_PAGE_PADDING: Final = 32
SPACING_SECTION_GAP: Final = 24
SPACING_CARD_PADDING: Final = 20
SPACING_CARD_GAP: Final = 16
SPACING_ELEMENT_GAP: Final = 12
SPACING_TIGHT_GAP: Final = 8

# Colors - Semantic (Colorblind-safe)
COLOR_INCOME: Final = "#0EA5E9"       # Sky Blue - for income/positive
COLOR_EXPENSE: Final = "#F97316"      # Orange - for expenses/negative
COLOR_POSITIVE: Final = "#10B981"     # Emerald - success/under budget
COLOR_NEGATIVE: Final = "#EF4444"     # Red - alert/over budget
COLOR_WARNING: Final = "#F59E0B"      # Amber - warning/near limit
COLOR_PRIMARY: Final = "#8B5CF6"      # Purple - primary accent
COLOR_NEUTRAL: Final = "#6B7280"      # Gray - neutral/muted
COLOR_MUTED: Final = "#9CA3AF"        # Light Gray - secondary text

# Colors - Text
COLOR_TEXT_PRIMARY: Final = "#F5F3FF"
COLOR_TEXT_SECONDARY: Final = "#E2E4F0"
COLOR_TEXT_MUTED: Final = "#9CA3AF"
COLOR_TEXT_ACCENT: Final = "#DDD6FE"

# Colors - Backgrounds (with alpha)
COLOR_CARD_BG: Final = "rgba(18, 18, 20, 0.95)"
COLOR_CARD_BORDER: Final = "rgba(60, 60, 70, 0.3)"
COLOR_POSITIVE_BG: Final = "rgba(16, 185, 129, 0.15)"
COLOR_NEGATIVE_BG: Final = "rgba(239, 68, 68, 0.15)"
COLOR_WARNING_BG: Final = "rgba(245, 158, 11, 0.15)"
COLOR_PRIMARY_BG: Final = "rgba(139, 92, 246, 0.15)"
COLOR_INCOME_BG: Final = "rgba(14, 165, 233, 0.15)"
COLOR_EXPENSE_BG: Final = "rgba(249, 115, 22, 0.15)"

# Chart color palettes
INCOME_CHART_COLORS: Final = [
    "#0EA5E9",  # Sky Blue
    "#8B5CF6",  # Purple
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
    "#6366F1",  # Indigo
    "#EC4899",  # Pink
    "#14B8A6",  # Teal
    "#84CC16",  # Lime
]

EXPENSE_CHART_COLORS: Final = [
    "#F97316",  # Orange
    "#8B5CF6",  # Purple
    "#0EA5E9",  # Sky Blue
    "#10B981",  # Emerald
    "#EF4444",  # Red
    "#F59E0B",  # Amber
    "#EC4899",  # Pink
    "#6366F1",  # Indigo
]

# Component sizes
KPI_CARD_MIN_HEIGHT: Final = 120
KPI_CARD_MIN_WIDTH: Final = 200
PROGRESS_BAR_HEIGHT: Final = 8
PROGRESS_BAR_HEIGHT_LARGE: Final = 12
DONUT_CHART_SIZE: Final = 250
GOAL_CARD_MIN_WIDTH: Final = 280
GOAL_CARD_MIN_HEIGHT: Final = 200
ACTION_BUTTON_MIN_HEIGHT: Final = 44
ACTION_BUTTON_MIN_WIDTH: Final = 100

# Border radius
BORDER_RADIUS_CARD: Final = 18
BORDER_RADIUS_BUTTON: Final = 14
BORDER_RADIUS_INPUT: Final = 12
BORDER_RADIUS_PROGRESS: Final = 4


def get_status_color(percentage: float) -> str:
    """Get appropriate status color based on percentage.

    Args:
        percentage: Current percentage (0-100+)

    Returns:
        Hex color string
    """
    if percentage <= 70:
        return COLOR_POSITIVE
    elif percentage <= 90:
        return COLOR_INCOME
    elif percentage <= 100:
        return COLOR_WARNING
    return COLOR_EXPENSE


def get_trend_color(direction: str) -> str:
    """Get color for trend indicator.

    Args:
        direction: "up", "down", or "neutral"

    Returns:
        Hex color string
    """
    if direction == "up":
        return COLOR_INCOME
    elif direction == "down":
        return COLOR_EXPENSE
    return COLOR_MUTED


def format_currency(amount: float, show_sign: bool = False) -> str:
    """Format amount as currency string.

    Args:
        amount: Dollar amount
        show_sign: Whether to show + for positive amounts

    Returns:
        Formatted currency string
    """
    if show_sign and amount > 0:
        return f"+${amount:,.2f}"
    elif amount < 0:
        return f"-${abs(amount):,.2f}"
    return f"${amount:,.2f}"


def format_percentage(value: float, show_sign: bool = False) -> str:
    """Format value as percentage string.

    Args:
        value: Percentage value
        show_sign: Whether to show + for positive values

    Returns:
        Formatted percentage string
    """
    if show_sign and value > 0:
        return f"+{value:.1f}%"
    return f"{value:.1f}%"


# Short month names for display
MONTH_NAMES_SHORT: Final = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]

MONTH_NAMES_FULL: Final = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def format_year_month(year_month: str, short: bool = True) -> str:
    """Format year-month string to human-readable format.

    Args:
        year_month: String in "YYYY-MM" format (e.g., "2026-01") or "ALL"
        short: If True, use short month names (e.g., "Jan 2026")
               If False, use full month names (e.g., "January 2026")

    Returns:
        Formatted string like "Jan 2026" or "January 2026"
        Returns "ALL" unchanged if input is "ALL"
    """
    if not year_month or year_month == "ALL":
        return year_month or "ALL"

    try:
        parts = year_month.split("-")
        if len(parts) != 2:
            return year_month

        year = int(parts[0])
        month = int(parts[1])

        if month < 1 or month > 12:
            return year_month

        month_names = MONTH_NAMES_SHORT if short else MONTH_NAMES_FULL
        return f"{month_names[month - 1]} {year}"
    except (ValueError, IndexError):
        return year_month


def parse_month_name_to_number(month_name: str) -> int | None:
    """Parse month name (short or full) to month number (1-12).

    Args:
        month_name: Month name like "Jan", "January", etc.

    Returns:
        Month number (1-12) or None if not found
    """
    month_lower = month_name.lower().strip()

    for i, name in enumerate(MONTH_NAMES_SHORT):
        if name.lower() == month_lower:
            return i + 1

    for i, name in enumerate(MONTH_NAMES_FULL):
        if name.lower() == month_lower:
            return i + 1

    return None