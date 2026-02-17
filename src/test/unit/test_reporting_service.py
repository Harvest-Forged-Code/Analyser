"""Unit tests for features.reporting.service."""

from __future__ import annotations

import pandas as pd

from budget_analyser.features.reporting.service import ReportService


class TestReportService:
    """Tests for ReportService."""

    def _make_statement(self) -> pd.DataFrame:
        return pd.DataFrame({
            "description": ["Salary", "Groceries", "Gas", "Refund"],
            "amount": [5000.0, -200.0, -50.0, 30.0],
            "category": [
                "Income", "Needs", "Needs", "Refunded_money",
            ],
            "sub_category": ["Wages", "Food", "Fuel", "Refund"],
            "year_month": ["2024-01", "2024-01", "2024-01", "2024-01"],
        })

    def test_earnings_default(self) -> None:
        svc = ReportService()
        df = svc.earnings(statement=self._make_statement())
        assert len(df) == 1
        assert df.iloc[0]["amount"] == 5000.0

    def test_expenses_default(self) -> None:
        svc = ReportService()
        df = svc.expenses(statement=self._make_statement())
        assert len(df) >= 2  # Groceries + Gas + possibly Refund

    def test_earnings_custom_mapping(self) -> None:
        svc = ReportService(
            cashflow_mapping={
                "Earnings": ["Income"],
                "Expenses": ["Needs"],
            },
        )
        df = svc.earnings(statement=self._make_statement())
        assert len(df) == 1

    def test_expenses_category_pivot(self) -> None:
        svc = ReportService()
        pivot = svc.expenses_category(
            statement=self._make_statement(),
        )
        assert not pivot.empty

    def test_expenses_sub_category_pivot(self) -> None:
        svc = ReportService()
        pivot = svc.expenses_sub_category(
            statement=self._make_statement(),
        )
        assert not pivot.empty

    def test_empty_statement(self) -> None:
        svc = ReportService()
        df = svc.earnings(statement=pd.DataFrame(
            columns=["amount", "category"],
        ))
        assert df.empty
