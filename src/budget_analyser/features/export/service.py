"""Export service (business logic).

Provides CSV and PDF export for transaction data and reports.
CSV is available by default. PDF requires the reportlab library.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence
from typing import Any

from budget_analyser.features.export.models import (
    ExportColumn,
    ExportConfig,
)

# PDF support is optional
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


class CsvExporter:
    """Export data to CSV format.

    Writes structured row data to CSV files or strings using
    the configured column definitions for header names,
    key extraction, and value formatting.

    Example:
        >>> from budget_analyser.features.export.service import (
        ...     CsvExporter,
        ... )
        >>> from budget_analyser.features.export.models import (
        ...     ExportColumn,
        ... )
        >>> exporter = CsvExporter(
        ...     columns=[ExportColumn("Name", "name")],
        ... )
        >>> exporter.export_to_string([{"name": "Alice"}])
        'Name\\r\\nAlice\\r\\n'
    """

    def __init__(self, columns: list[ExportColumn]) -> None:
        """Initialize the CSV exporter.

        Args:
            columns: Column definitions controlling which
                keys are extracted and how values are formatted.
        """
        self._columns = columns

    def export_to_file(
        self,
        data: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        include_headers: bool = True,
    ) -> None:
        """Export data to a CSV file.

        Creates parent directories if they do not exist and
        writes the data using UTF-8 encoding.

        Args:
            data: Sequence of row dictionaries to export.
            filepath: Destination file path for the CSV output.
            include_headers: Whether to write a header row.

        Example:
            >>> from pathlib import Path
            >>> exporter = CsvExporter(
            ...     columns=[ExportColumn("Name", "name")],
            ... )
            >>> exporter.export_to_file(
            ...     [{"name": "Alice"}],
            ...     Path("/tmp/out.csv"),
            ... )
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            if include_headers:
                headers = [col.name for col in self._columns]
                writer.writerow(headers)

            for row in data:
                values = [
                    col.format_value(row.get(col.key))
                    for col in self._columns
                ]
                writer.writerow(values)

    def export_to_string(
        self,
        data: Sequence[dict[str, Any]],
        *,
        include_headers: bool = True,
    ) -> str:
        """Export data to a CSV string.

        Args:
            data: Sequence of row dictionaries to export.
            include_headers: Whether to include a header row.

        Returns:
            CSV-formatted string with CRLF line endings.

        Example:
            >>> exporter = CsvExporter(
            ...     columns=[ExportColumn("Name", "name")],
            ... )
            >>> csv_str = exporter.export_to_string(
            ...     [{"name": "Bob"}],
            ... )
            >>> "Bob" in csv_str
            True
        """
        output = io.StringIO()
        writer = csv.writer(output)

        if include_headers:
            headers = [col.name for col in self._columns]
            writer.writerow(headers)

        for row in data:
            values = [
                col.format_value(row.get(col.key))
                for col in self._columns
            ]
            writer.writerow(values)

        return output.getvalue()


class PdfExporter:  # pylint: disable=too-few-public-methods
    """Export data to PDF format.

    Requires the ``reportlab`` library. Check ``HAS_REPORTLAB``
    before instantiating to avoid ``ImportError``.

    Example:
        >>> from budget_analyser.features.export.service import (
        ...     PdfExporter, HAS_REPORTLAB,
        ... )
        >>> if HAS_REPORTLAB:
        ...     exporter = PdfExporter(columns=[])
    """

    def __init__(
        self,
        columns: list[ExportColumn],
        config: ExportConfig | None = None,
    ) -> None:
        """Initialize the PDF exporter.

        Args:
            columns: Column definitions for the data table.
            config: Export configuration. Defaults to
                ``ExportConfig()`` when ``None``.

        Raises:
            ImportError: If ``reportlab`` is not installed.
        """
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. "
                "Install with: pip install reportlab"
            )
        self._columns = columns
        self._config = config or ExportConfig()

    def export_to_file(
        self,
        data: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Export data to a PDF file.

        Creates parent directories if they do not exist and
        writes a styled PDF document with optional title,
        timestamp, summary section, and data table.

        Args:
            data: Sequence of row dictionaries to export.
            filepath: Destination file path for the PDF output.
            summary: Optional key-value pairs rendered as a
                summary section before the data table.

        Example:
            >>> from pathlib import Path
            >>> exporter = PdfExporter(columns=EARNINGS_COLUMNS)
            >>> exporter.export_to_file(
            ...     data=[{"date": "2025-01-01", "amount": 100}],
            ...     filepath=Path("/tmp/report.pdf"),
            ... )
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        page_size = (
            letter if self._config.page_size == "letter" else A4
        )

        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=page_size,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        elements = self._build_elements(data, summary)
        doc.build(elements)

    def _build_elements(
        self,
        data: Sequence[dict[str, Any]],
        summary: dict[str, Any] | None,
    ) -> list:
        """Build the full list of PDF flowable elements.

        Assembles the title, optional subtitle, optional
        timestamp, optional summary section, and data table.

        Args:
            data: Row dictionaries for the data table.
            summary: Optional key-value pairs for the summary.

        Returns:
            List of reportlab flowable elements ready for
            document building.
        """
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#1F2937"),
        )
        elements.append(
            Paragraph(self._config.title, title_style),
        )

        if self._config.subtitle:
            subtitle_style = ParagraphStyle(
                "CustomSubtitle",
                parent=styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#6B7280"),
                spaceAfter=12,
            )
            elements.append(
                Paragraph(self._config.subtitle, subtitle_style),
            )

        if self._config.include_timestamp:
            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S",
            )
            timestamp_style = ParagraphStyle(
                "Timestamp",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#9CA3AF"),
                spaceAfter=12,
            )
            elements.append(
                Paragraph(
                    f"Generated: {timestamp}", timestamp_style,
                ),
            )

        elements.append(Spacer(1, 12))

        if self._config.include_summary and summary:
            elements.extend(
                self._build_summary_section(summary, styles),
            )
            elements.append(Spacer(1, 12))

        elements.extend(self._build_data_table(data))

        return elements

    def _build_summary_section(
        self,
        summary: dict[str, Any],
        styles: object,
    ) -> list:
        """Build the summary section of the PDF.

        Renders key-value pairs as a two-column table with a
        "Summary" heading.

        Args:
            summary: Dictionary of label-to-value pairs.
            styles: reportlab stylesheet for paragraph styling.

        Returns:
            List of flowable elements for the summary section.
        """
        elements = []

        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor("#374151"),
        )
        elements.append(Paragraph("Summary", section_style))

        summary_data = [[k, str(v)] for k, v in summary.items()]
        if summary_data:
            table = Table(
                summary_data, colWidths=[2 * inch, 3 * inch],
            )
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1),
                 colors.HexColor("#4B5563")),
                ("TEXTCOLOR", (1, 0), (1, -1),
                 colors.HexColor("#1F2937")),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        return elements

    def _build_data_table(
        self, data: Sequence[dict[str, Any]],
    ) -> list:
        """Build the styled data table for the PDF.

        Creates a table with a purple header row, alternating
        row backgrounds, and grid lines.

        Args:
            data: Row dictionaries for the table body.

        Returns:
            List containing the styled ``Table`` element,
            or an empty list if *data* is empty.
        """
        elements = []

        if not data:
            return elements

        table_data = []

        headers = [col.name for col in self._columns]
        table_data.append(headers)

        for row in data:
            values = [
                col.format_value(row.get(col.key))
                for col in self._columns
            ]
            table_data.append(values)

        table = Table(table_data, repeatRows=1)

        style_commands = [
            ("BACKGROUND", (0, 0), (-1, 0),
             colors.HexColor("#8B5CF6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1),
             colors.HexColor("#374151")),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5,
             colors.HexColor("#E5E7EB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F9FAFB")]),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements


class ExportService:
    """High-level service for exporting data in various formats."""

    TRANSACTION_COLUMNS = [
        ExportColumn("Date", "date"),
        ExportColumn("Description", "description"),
        ExportColumn("Amount", "amount"),
        ExportColumn("Category", "category"),
        ExportColumn("Sub-category", "sub_category"),
        ExportColumn("Account", "account"),
    ]

    SUMMARY_COLUMNS = [
        ExportColumn("Category", "category"),
        ExportColumn("Total", "total"),
        ExportColumn("Count", "count"),
        ExportColumn("Average", "average"),
    ]

    @staticmethod
    def is_pdf_available() -> bool:
        """Check if PDF export is available.

        Returns:
            ``True`` if the ``reportlab`` library is installed.

        Example:
            >>> from budget_analyser.features.export.service import (
            ...     ExportService,
            ... )
            >>> isinstance(ExportService.is_pdf_available(), bool)
            True
        """
        return HAS_REPORTLAB

    def export_transactions_csv(
        self,
        transactions: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        columns: list[ExportColumn] | None = None,
    ) -> None:
        """Export transactions to a CSV file.

        Args:
            transactions: Sequence of transaction dicts.
            filepath: Destination file path for the CSV.
            columns: Custom column definitions. Defaults to
                ``TRANSACTION_COLUMNS``.

        Example:
            >>> from pathlib import Path
            >>> svc = ExportService()
            >>> svc.export_transactions_csv(
            ...     transactions=[{"date": "2025-01-01"}],
            ...     filepath=Path("/tmp/txns.csv"),
            ... )
        """
        cols = columns or self.TRANSACTION_COLUMNS
        exporter = CsvExporter(cols)
        exporter.export_to_file(transactions, filepath)

    def export_transactions_csv_string(
        self,
        transactions: Sequence[dict[str, Any]],
        *,
        columns: list[ExportColumn] | None = None,
    ) -> str:
        """Export transactions to a CSV string.

        Args:
            transactions: Sequence of transaction dicts.
            columns: Custom column definitions. Defaults to
                ``TRANSACTION_COLUMNS``.

        Returns:
            CSV-formatted string with headers and data rows.

        Example:
            >>> svc = ExportService()
            >>> csv = svc.export_transactions_csv_string(
            ...     transactions=[{"date": "2025-01-01"}],
            ... )
            >>> "Date" in csv
            True
        """
        cols = columns or self.TRANSACTION_COLUMNS
        exporter = CsvExporter(cols)
        return exporter.export_to_string(transactions)

    def export_transactions_pdf(
        self,
        transactions: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        columns: list[ExportColumn] | None = None,
        config: ExportConfig | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Export transactions to a PDF file.

        Args:
            transactions: Sequence of transaction dicts.
            filepath: Destination file path for the PDF.
            columns: Custom column definitions. Defaults to
                ``TRANSACTION_COLUMNS``.
            config: PDF export configuration. Defaults to a
                config titled "Transaction Report".
            summary: Optional key-value pairs rendered as a
                summary section before the data table.

        Raises:
            ImportError: If ``reportlab`` is not installed.

        Example:
            >>> svc = ExportService()
            >>> if svc.is_pdf_available():
            ...     svc.export_transactions_pdf(
            ...         transactions=[{"date": "2025-01-01"}],
            ...         filepath=Path("/tmp/report.pdf"),
            ...     )
        """
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. "
                "Install with: pip install reportlab"
            )

        cols = columns or self.TRANSACTION_COLUMNS
        cfg = config or ExportConfig(
            title="Transaction Report",
            subtitle="Budget Analyser Export",
        )
        exporter = PdfExporter(cols, cfg)
        exporter.export_to_file(
            transactions, filepath, summary=summary,
        )

    def export_summary_csv(
        self,
        summary_data: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        columns: list[ExportColumn] | None = None,
    ) -> None:
        """Export summary report to a CSV file.

        Args:
            summary_data: Sequence of summary row dicts.
            filepath: Destination file path for the CSV.
            columns: Custom column definitions. Defaults to
                ``SUMMARY_COLUMNS``.

        Example:
            >>> svc = ExportService()
            >>> svc.export_summary_csv(
            ...     summary_data=[{"category": "Food"}],
            ...     filepath=Path("/tmp/summary.csv"),
            ... )
        """
        cols = columns or self.SUMMARY_COLUMNS
        exporter = CsvExporter(cols)
        exporter.export_to_file(summary_data, filepath)

    def export_summary_pdf(
        self,
        summary_data: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        columns: list[ExportColumn] | None = None,
        config: ExportConfig | None = None,
        summary: dict[str, Any] | None = None,
    ) -> None:
        """Export summary report to a PDF file.

        Args:
            summary_data: Sequence of summary row dicts.
            filepath: Destination file path for the PDF.
            columns: Custom column definitions. Defaults to
                ``SUMMARY_COLUMNS``.
            config: PDF export configuration. Defaults to a
                config titled "Category Summary Report".
            summary: Optional key-value pairs rendered as a
                summary section before the data table.

        Raises:
            ImportError: If ``reportlab`` is not installed.

        Example:
            >>> svc = ExportService()
            >>> if svc.is_pdf_available():
            ...     svc.export_summary_pdf(
            ...         summary_data=[{"category": "Food"}],
            ...         filepath=Path("/tmp/summary.pdf"),
            ...     )
        """
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. "
                "Install with: pip install reportlab"
            )

        cols = columns or self.SUMMARY_COLUMNS
        cfg = config or ExportConfig(
            title="Category Summary Report",
            subtitle="Budget Analyser Export",
        )
        exporter = PdfExporter(cols, cfg)
        exporter.export_to_file(
            summary_data, filepath, summary=summary,
        )


def format_currency(value: float) -> str:
    """Format a number as USD currency string.

    Negative values are displayed with a leading minus sign.

    Args:
        value: The numeric value to format.

    Returns:
        Currency string with dollar sign and two decimal places
        (e.g. ``"$1,234.56"`` or ``"-$50.00"``).

    Example:
        >>> format_currency(1234.5)
        '$1,234.50'
        >>> format_currency(-50)
        '-$50.00'
    """
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a number as a percentage string.

    Args:
        value: The numeric value to format (e.g. ``75.123``).

    Returns:
        Percentage string with one decimal place
        (e.g. ``"75.1%"``).

    Example:
        >>> format_percentage(75.123)
        '75.1%'
    """
    return f"{value:.1f}%"


# Pre-configured column sets for common exports
EARNINGS_COLUMNS = [
    ExportColumn("Date", "date"),
    ExportColumn("Description", "description"),
    ExportColumn("Amount", "amount", format_currency),
    ExportColumn("Category", "category"),
    ExportColumn("Sub-category", "sub_category"),
]

EXPENSES_COLUMNS = [
    ExportColumn("Date", "date"),
    ExportColumn("Description", "description"),
    ExportColumn("Amount", "amount", format_currency),
    ExportColumn("Category", "category"),
    ExportColumn("Sub-category", "sub_category"),
]

MONTHLY_SUMMARY_COLUMNS = [
    ExportColumn("Month", "month"),
    ExportColumn("Total Earnings", "earnings", format_currency),
    ExportColumn("Total Expenses", "expenses", format_currency),
    ExportColumn("Net Savings", "net", format_currency),
    ExportColumn("Savings Rate", "savings_rate", format_percentage),
]

CATEGORY_BREAKDOWN_COLUMNS = [
    ExportColumn("Category", "category"),
    ExportColumn("Amount", "amount", format_currency),
    ExportColumn("Percentage", "percentage", format_percentage),
    ExportColumn("Transaction Count", "count"),
]
