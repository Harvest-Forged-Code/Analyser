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
    """Definition of a column for export.

    Attributes:
        name: Display name shown in column headers.
        key: Data key or attribute name to extract from row dicts.
        formatter: Optional callable to format cell values.
            When ``None``, built-in formatting is applied based
            on value type (float, date, datetime, etc.).

    Example:
        >>> from budget_analyser.features.export.models import (
        ...     ExportColumn,
        ... )
        >>> col = ExportColumn(
        ...     name="Amount",
        ...     key="amount",
        ...     formatter=lambda v: f"${v:,.2f}",
        ... )
        >>> col.format_value(1234.5)
        '$1,234.50'
    """

    name: str
    key: str
    formatter: Callable[[Any], str] | None = None

    def format_value(self, value: Any) -> str:
        """Format a cell value for display.

        Applies the custom *formatter* if one was provided,
        otherwise falls back to built-in formatting:
        ``None`` becomes ``""``, floats use ``{:,.2f}``,
        datetimes include time, and dates are ISO-formatted.

        Args:
            value: The raw cell value to format.

        Returns:
            A string representation suitable for display.

        Example:
            >>> col = ExportColumn(name="Date", key="date")
            >>> col.format_value(None)
            ''
            >>> col.format_value(99.9)
            '99.90'
        """
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
    """Configuration for export operations.

    Attributes:
        title: Report title displayed at the top of exports.
        subtitle: Optional subtitle shown below the title.
        include_timestamp: Whether to include a generation
            timestamp in the export.
        include_summary: Whether to include a summary section
            before the data table.
        page_size: PDF page size, either ``'letter'`` or
            ``'a4'``.

    Example:
        >>> from budget_analyser.features.export.models import (
        ...     ExportConfig,
        ... )
        >>> config = ExportConfig(
        ...     title="Monthly Report",
        ...     subtitle="January 2025",
        ...     page_size="a4",
        ... )
        >>> config.title
        'Monthly Report'
    """

    title: str = "Budget Analyser Report"
    subtitle: str = ""
    include_timestamp: bool = True
    include_summary: bool = True
    page_size: str = "letter"
