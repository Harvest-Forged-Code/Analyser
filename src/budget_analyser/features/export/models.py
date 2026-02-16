"""Export feature DTOs.

Data transfer objects for export configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from collections.abc import Callable
from typing import Any


@dataclass(frozen=True)
class ExportColumn:
    """Definition of a column for export."""

    name: str  # Display name
    key: str  # Data key or attribute name
    formatter: Callable[[Any], str] | None = None

    def format_value(self, value: Any) -> str:
        """Format the value for display."""
        if value is None:
            return ""
        if self.formatter:
            return self.formatter(value)
        if isinstance(value, float):
            return f"{value:,.2f}"
        # Check datetime before date (datetime is subclass of date)
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return str(value)


@dataclass(frozen=True)
class ExportConfig:
    """Configuration for export operations."""

    title: str = "Budget Analyser Report"
    subtitle: str = ""
    include_timestamp: bool = True
    include_summary: bool = True
    page_size: str = "letter"  # 'letter' or 'a4'
