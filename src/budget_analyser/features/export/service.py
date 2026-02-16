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
    """Export data to CSV format."""

    def __init__(self, columns: list[ExportColumn]) -> None:
        self._columns = columns

    def export_to_file(
        self,
        data: Sequence[dict[str, Any]],
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
        data: Sequence[dict[str, Any]],
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


class PdfExporter:  # pylint: disable=too-few-public-methods
    """Export data to PDF format.

    Requires reportlab library. Check HAS_REPORTLAB before using.
    """

    def __init__(
        self,
        columns: list[ExportColumn],
        config: ExportConfig | None = None,
    ) -> None:
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
        """Export data to a PDF file."""
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
        """Build the PDF elements."""
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
        """Build the data table."""
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
        """Check if PDF export is available."""
        return HAS_REPORTLAB

    def export_transactions_csv(
        self,
        transactions: Sequence[dict[str, Any]],
        filepath: str | Path,
        *,
        columns: list[ExportColumn] | None = None,
    ) -> None:
        """Export transactions to CSV file."""
        cols = columns or self.TRANSACTION_COLUMNS
        exporter = CsvExporter(cols)
        exporter.export_to_file(transactions, filepath)

    def export_transactions_csv_string(
        self,
        transactions: Sequence[dict[str, Any]],
        *,
        columns: list[ExportColumn] | None = None,
    ) -> str:
        """Export transactions to CSV string."""
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
        """Export transactions to PDF file."""
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
        """Export summary report to CSV file."""
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
        """Export summary report to PDF file."""
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
