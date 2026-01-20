"""Unit tests for the export service."""

from __future__ import annotations

import csv
import io
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from budget_analyser.domain.export_service import (
    ExportColumn,
    ExportConfig,
    CsvExporter,
    ExportService,
    format_currency,
    format_percentage,
    EARNINGS_COLUMNS,
    EXPENSES_COLUMNS,
    MONTHLY_SUMMARY_COLUMNS,
    CATEGORY_BREAKDOWN_COLUMNS,
)


class TestExportColumn:
    """Tests for ExportColumn dataclass."""

    def test_format_value_string(self):
        """String values should pass through unchanged."""
        column = ExportColumn("Name", "name")
        assert column.format_value("Test") == "Test"

    def test_format_value_none(self):
        """None values should return empty string."""
        column = ExportColumn("Name", "name")
        assert column.format_value(None) == ""

    def test_format_value_float_default(self):
        """Float values should format with 2 decimal places by default."""
        column = ExportColumn("Amount", "amount")
        assert column.format_value(1234.567) == "1,234.57"

    def test_format_value_date(self):
        """Date values should format as YYYY-MM-DD."""
        column = ExportColumn("Date", "date")
        assert column.format_value(date(2024, 6, 15)) == "2024-06-15"

    def test_format_value_datetime(self):
        """Datetime values should format with time."""
        column = ExportColumn("Timestamp", "timestamp")
        result = column.format_value(datetime(2024, 6, 15, 14, 30, 45))
        assert result == "2024-06-15 14:30:45"

    def test_format_value_with_custom_formatter(self):
        """Custom formatter should be used when provided."""
        column = ExportColumn("Amount", "amount", lambda x: f"${x:.0f}")
        assert column.format_value(1234.56) == "$1235"

    def test_format_value_integer(self):
        """Integer values should convert to string."""
        column = ExportColumn("Count", "count")
        assert column.format_value(42) == "42"


class TestFormatHelpers:
    """Tests for format helper functions."""

    def test_format_currency_positive(self):
        """Positive currency should format with $ prefix."""
        assert format_currency(1234.56) == "$1,234.56"

    def test_format_currency_negative(self):
        """Negative currency should format with -$ prefix."""
        assert format_currency(-1234.56) == "-$1,234.56"

    def test_format_currency_zero(self):
        """Zero currency should format correctly."""
        assert format_currency(0) == "$0.00"

    def test_format_percentage(self):
        """Percentage should format with % suffix."""
        assert format_percentage(45.678) == "45.7%"

    def test_format_percentage_zero(self):
        """Zero percentage should format correctly."""
        assert format_percentage(0) == "0.0%"


class TestCsvExporter:
    """Tests for CsvExporter class."""

    @pytest.fixture
    def sample_columns(self):
        """Sample columns for testing."""
        return [
            ExportColumn("Date", "date"),
            ExportColumn("Description", "description"),
            ExportColumn("Amount", "amount"),
        ]

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return [
            {"date": date(2024, 6, 1), "description": "Coffee", "amount": 5.50},
            {"date": date(2024, 6, 2), "description": "Groceries", "amount": 45.99},
            {"date": date(2024, 6, 3), "description": "Gas", "amount": 35.00},
        ]

    def test_export_to_string_with_headers(self, sample_columns, sample_data):
        """Export should include headers by default."""
        exporter = CsvExporter(sample_columns)
        result = exporter.export_to_string(sample_data)

        lines = result.strip().split("\n")
        assert len(lines) == 4  # Header + 3 data rows
        assert "Date,Description,Amount" in lines[0]

    def test_export_to_string_without_headers(self, sample_columns, sample_data):
        """Export should omit headers when specified."""
        exporter = CsvExporter(sample_columns)
        result = exporter.export_to_string(sample_data, include_headers=False)

        lines = result.strip().split("\n")
        assert len(lines) == 3  # 3 data rows only

    def test_export_to_string_data_formatting(self, sample_columns, sample_data):
        """Data should be formatted correctly."""
        exporter = CsvExporter(sample_columns)
        result = exporter.export_to_string(sample_data)

        # Parse the CSV
        reader = csv.reader(io.StringIO(result))
        rows = list(reader)

        # Check first data row
        assert rows[1][0] == "2024-06-01"
        assert rows[1][1] == "Coffee"
        assert rows[1][2] == "5.50"

    def test_export_to_file(self, sample_columns, sample_data):
        """Export should write to file correctly."""
        exporter = CsvExporter(sample_columns)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = Path(f.name)

        try:
            exporter.export_to_file(sample_data, filepath)

            # Read and verify
            with open(filepath, "r") as f:
                content = f.read()

            assert "Date,Description,Amount" in content
            assert "Coffee" in content
            assert "Groceries" in content
        finally:
            filepath.unlink()

    def test_export_to_file_creates_directory(self, sample_columns, sample_data):
        """Export should create parent directories if needed."""
        exporter = CsvExporter(sample_columns)

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "export.csv"
            exporter.export_to_file(sample_data, filepath)

            assert filepath.exists()

    def test_export_empty_data(self, sample_columns):
        """Export should handle empty data."""
        exporter = CsvExporter(sample_columns)
        result = exporter.export_to_string([])

        lines = result.strip().split("\n")
        assert len(lines) == 1  # Header only

    def test_export_missing_keys(self, sample_columns):
        """Export should handle missing keys gracefully."""
        exporter = CsvExporter(sample_columns)
        data = [{"date": date(2024, 6, 1), "description": "Test"}]  # Missing 'amount'

        result = exporter.export_to_string(data)

        reader = csv.reader(io.StringIO(result))
        rows = list(reader)
        assert rows[1][2] == ""  # Missing amount should be empty


class TestExportService:
    """Tests for ExportService class."""

    @pytest.fixture
    def service(self):
        """Create export service instance."""
        return ExportService()

    @pytest.fixture
    def sample_transactions(self):
        """Sample transaction data."""
        return [
            {
                "date": date(2024, 6, 1),
                "description": "Paycheck",
                "amount": 3000.00,
                "category": "Income",
                "sub_category": "Salary",
                "account": "Checking",
            },
            {
                "date": date(2024, 6, 2),
                "description": "Groceries",
                "amount": -85.50,
                "category": "Food",
                "sub_category": "Groceries",
                "account": "Credit Card",
            },
        ]

    def test_export_transactions_csv(self, service, sample_transactions):
        """Test CSV export of transactions."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = Path(f.name)

        try:
            service.export_transactions_csv(sample_transactions, filepath)

            with open(filepath, "r") as f:
                content = f.read()

            assert "Date,Description,Amount,Category,Sub-category,Account" in content
            assert "Paycheck" in content
            assert "Groceries" in content
        finally:
            filepath.unlink()

    def test_export_transactions_csv_string(self, service, sample_transactions):
        """Test CSV string export of transactions."""
        result = service.export_transactions_csv_string(sample_transactions)

        assert "Date,Description,Amount,Category,Sub-category,Account" in result
        assert "Paycheck" in result

    def test_export_transactions_csv_custom_columns(self, service, sample_transactions):
        """Test CSV export with custom columns."""
        custom_columns = [
            ExportColumn("Date", "date"),
            ExportColumn("Amount", "amount", format_currency),
        ]

        result = service.export_transactions_csv_string(
            sample_transactions, columns=custom_columns
        )

        # Should have our custom headers
        assert "Date,Amount" in result
        # Should have formatted amounts
        assert "$3,000.00" in result

    def test_export_summary_csv(self, service):
        """Test CSV export of summary data."""
        summary_data = [
            {"category": "Food", "total": 500.00, "count": 15, "average": 33.33},
            {"category": "Transport", "total": 200.00, "count": 8, "average": 25.00},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            filepath = Path(f.name)

        try:
            service.export_summary_csv(summary_data, filepath)

            with open(filepath, "r") as f:
                content = f.read()

            assert "Category,Total,Count,Average" in content
            assert "Food" in content
        finally:
            filepath.unlink()

    def test_is_pdf_available(self, service):
        """Test PDF availability check."""
        # This will be True or False depending on whether reportlab is installed
        result = service.is_pdf_available()
        assert isinstance(result, bool)


class TestExportConfig:
    """Tests for ExportConfig dataclass."""

    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = ExportConfig()
        assert config.title == "Budget Analyser Report"
        assert config.subtitle == ""
        assert config.include_timestamp is True
        assert config.include_summary is True
        assert config.page_size == "letter"

    def test_custom_config(self):
        """Custom config values should be preserved."""
        config = ExportConfig(
            title="My Report",
            subtitle="January 2024",
            include_timestamp=False,
            include_summary=False,
            page_size="a4",
        )
        assert config.title == "My Report"
        assert config.subtitle == "January 2024"
        assert config.include_timestamp is False
        assert config.include_summary is False
        assert config.page_size == "a4"


class TestPredefinedColumns:
    """Tests for predefined column sets."""

    def test_earnings_columns_defined(self):
        """Earnings columns should be properly defined."""
        assert len(EARNINGS_COLUMNS) == 5
        column_names = [col.name for col in EARNINGS_COLUMNS]
        assert "Date" in column_names
        assert "Amount" in column_names

    def test_expenses_columns_defined(self):
        """Expenses columns should be properly defined."""
        assert len(EXPENSES_COLUMNS) == 5
        column_names = [col.name for col in EXPENSES_COLUMNS]
        assert "Date" in column_names
        assert "Amount" in column_names

    def test_monthly_summary_columns_defined(self):
        """Monthly summary columns should be properly defined."""
        assert len(MONTHLY_SUMMARY_COLUMNS) == 5
        column_names = [col.name for col in MONTHLY_SUMMARY_COLUMNS]
        assert "Month" in column_names
        assert "Savings Rate" in column_names

    def test_category_breakdown_columns_defined(self):
        """Category breakdown columns should be properly defined."""
        assert len(CATEGORY_BREAKDOWN_COLUMNS) == 4
        column_names = [col.name for col in CATEGORY_BREAKDOWN_COLUMNS]
        assert "Category" in column_names
        assert "Percentage" in column_names

    def test_earnings_amount_formatter(self):
        """Earnings amount column should use currency formatter."""
        amount_col = next(c for c in EARNINGS_COLUMNS if c.key == "amount")
        assert amount_col.format_value(1234.56) == "$1,234.56"

    def test_monthly_summary_savings_rate_formatter(self):
        """Savings rate column should use percentage formatter."""
        rate_col = next(c for c in MONTHLY_SUMMARY_COLUMNS if c.key == "savings_rate")
        assert rate_col.format_value(25.5) == "25.5%"
