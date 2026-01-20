"""Export service for generating CSV and PDF reports.

Purpose:
    Provides export functionality for transaction data and reports:
    - CSV export for raw data (compatible with spreadsheets)
    - PDF export for formatted reports (requires reportlab)

CSV is available by default. PDF export requires the reportlab library.
"""

from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Sequence, Callable

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
        PageBreak,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False


@dataclass(frozen=True)
class ExportColumn:
    """Definition of a column for export."""

    name: str  # Display name
    key: str  # Data key or attribute name
    formatter: Callable[[Any], str] | None = None  # Optional value formatter

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


class CsvExporter:
    """Export data to CSV format."""

    def __init__(self, columns: List[ExportColumn]) -> None:
        self._columns = columns

    def export_to_file(
        self,
        data: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        include_headers: bool = True,
    ) -> None:
        """Export data to a CSV file."""
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
        data: Sequence[Dict[str, Any]],
        *,
        include_headers: bool = True,
    ) -> str:
        """Export data to a CSV string."""
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


class PdfExporter:
    """Export data to PDF format.

    Requires reportlab library. Check HAS_REPORTLAB before using.
    """

    def __init__(
        self,
        columns: List[ExportColumn],
        config: ExportConfig | None = None,
    ) -> None:
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )
        self._columns = columns
        self._config = config or ExportConfig()

    def export_to_file(
        self,
        data: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        summary: Dict[str, Any] | None = None,
    ) -> None:
        """Export data to a PDF file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        page_size = letter if self._config.page_size == "letter" else A4

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
        data: Sequence[Dict[str, Any]],
        summary: Dict[str, Any] | None,
    ) -> List:
        """Build the PDF elements."""
        elements = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            spaceAfter=6,
            textColor=colors.HexColor("#1F2937"),
        )
        elements.append(Paragraph(self._config.title, title_style))

        # Subtitle
        if self._config.subtitle:
            subtitle_style = ParagraphStyle(
                "CustomSubtitle",
                parent=styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#6B7280"),
                spaceAfter=12,
            )
            elements.append(Paragraph(self._config.subtitle, subtitle_style))

        # Timestamp
        if self._config.include_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp_style = ParagraphStyle(
                "Timestamp",
                parent=styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#9CA3AF"),
                spaceAfter=12,
            )
            elements.append(Paragraph(f"Generated: {timestamp}", timestamp_style))

        elements.append(Spacer(1, 12))

        # Summary section
        if self._config.include_summary and summary:
            elements.extend(self._build_summary_section(summary, styles))
            elements.append(Spacer(1, 12))

        # Data table
        elements.extend(self._build_data_table(data))

        return elements

    def _build_summary_section(
        self,
        summary: Dict[str, Any],
        styles,
    ) -> List:
        """Build the summary section."""
        elements = []

        section_style = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.HexColor("#374151"),
        )
        elements.append(Paragraph("Summary", section_style))

        # Create summary table
        summary_data = [[k, str(v)] for k, v in summary.items()]
        if summary_data:
            table = Table(summary_data, colWidths=[2 * inch, 3 * inch])
            table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4B5563")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1F2937")),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(table)

        return elements

    def _build_data_table(self, data: Sequence[Dict[str, Any]]) -> List:
        """Build the data table."""
        elements = []

        if not data:
            return elements

        # Calculate column widths based on content
        num_cols = len(self._columns)
        col_width = 7.5 * inch / num_cols  # Total width divided by columns

        # Build table data
        table_data = []

        # Header row
        headers = [col.name for col in self._columns]
        table_data.append(headers)

        # Data rows
        for row in data:
            values = [
                col.format_value(row.get(col.key))
                for col in self._columns
            ]
            table_data.append(values)

        # Create table
        table = Table(table_data, repeatRows=1)

        # Style the table
        style_commands = [
            # Header styling
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8B5CF6")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),

            # Data styling
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#374151")),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),

            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),

            # Alternating row colors
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),

            # Alignment
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]

        table.setStyle(TableStyle(style_commands))
        elements.append(table)

        return elements


class ExportService:
    """High-level service for exporting data in various formats."""

    # Standard transaction columns
    TRANSACTION_COLUMNS = [
        ExportColumn("Date", "date"),
        ExportColumn("Description", "description"),
        ExportColumn("Amount", "amount"),
        ExportColumn("Category", "category"),
        ExportColumn("Sub-category", "sub_category"),
        ExportColumn("Account", "account"),
    ]

    # Summary report columns
    SUMMARY_COLUMNS = [
        ExportColumn("Category", "category"),
        ExportColumn("Total", "total"),
        ExportColumn("Count", "count"),
        ExportColumn("Average", "average"),
    ]

    def __init__(self) -> None:
        self._csv_exporter: CsvExporter | None = None
        self._pdf_exporter: PdfExporter | None = None

    @staticmethod
    def is_pdf_available() -> bool:
        """Check if PDF export is available."""
        return HAS_REPORTLAB

    def export_transactions_csv(
        self,
        transactions: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        columns: List[ExportColumn] | None = None,
    ) -> None:
        """Export transactions to CSV file."""
        cols = columns or self.TRANSACTION_COLUMNS
        exporter = CsvExporter(cols)
        exporter.export_to_file(transactions, filepath)

    def export_transactions_csv_string(
        self,
        transactions: Sequence[Dict[str, Any]],
        *,
        columns: List[ExportColumn] | None = None,
    ) -> str:
        """Export transactions to CSV string."""
        cols = columns or self.TRANSACTION_COLUMNS
        exporter = CsvExporter(cols)
        return exporter.export_to_string(transactions)

    def export_transactions_pdf(
        self,
        transactions: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        columns: List[ExportColumn] | None = None,
        config: ExportConfig | None = None,
        summary: Dict[str, Any] | None = None,
    ) -> None:
        """Export transactions to PDF file."""
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )

        cols = columns or self.TRANSACTION_COLUMNS
        cfg = config or ExportConfig(
            title="Transaction Report",
            subtitle="Budget Analyser Export",
        )
        exporter = PdfExporter(cols, cfg)
        exporter.export_to_file(transactions, filepath, summary=summary)

    def export_summary_csv(
        self,
        summary_data: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        columns: List[ExportColumn] | None = None,
    ) -> None:
        """Export summary report to CSV file."""
        cols = columns or self.SUMMARY_COLUMNS
        exporter = CsvExporter(cols)
        exporter.export_to_file(summary_data, filepath)

    def export_summary_pdf(
        self,
        summary_data: Sequence[Dict[str, Any]],
        filepath: str | Path,
        *,
        columns: List[ExportColumn] | None = None,
        config: ExportConfig | None = None,
        summary: Dict[str, Any] | None = None,
    ) -> None:
        """Export summary report to PDF file."""
        if not HAS_REPORTLAB:
            raise ImportError(
                "PDF export requires reportlab. Install with: pip install reportlab"
            )

        cols = columns or self.SUMMARY_COLUMNS
        cfg = config or ExportConfig(
            title="Category Summary Report",
            subtitle="Budget Analyser Export",
        )
        exporter = PdfExporter(cols, cfg)
        exporter.export_to_file(summary_data, filepath, summary=summary)


def format_currency(value: float) -> str:
    """Format a number as currency."""
    if value < 0:
        return f"-${abs(value):,.2f}"
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format a number as percentage."""
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
