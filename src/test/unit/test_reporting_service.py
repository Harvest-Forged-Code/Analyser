"""Unit tests for features.reporting.service."""

from __future__ import annotations

import pandas as pd
import pytest

from budget_analyser.features.reporting.service import ReportService

_CASHFLOW = {
    "Earnings": ["Primary_Income", "Secondary_Income", "Refunded_money"],
    "Expenses": ["Needs", "Wants", "Luxury", "Remittance"],
}


class TestReportService:
    """Tests for ReportService."""

    def _make_statement(self) -> pd.DataFrame:
        return pd.DataFrame({
            "description": ["Salary", "Groceries", "Gas", "Refund"],
            "amount": [5000.0, -200.0, -50.0, 30.0],
            "category": [
                "Primary_Income", "Needs", "Needs", "Refunded_money",
            ],
            "sub_category": ["Wages", "Food", "Fuel", "Refund"],
            "year_month": ["2024-01", "2024-01", "2024-01", "2024-01"],
        })

    def test_earnings_returns_income_and_refunds(self) -> None:
        svc = ReportService(cashflow_mapping=_CASHFLOW)
        df = svc.earnings(statement=self._make_statement())
        assert set(df["category"]) == {"Primary_Income", "Refunded_money"}
        assert (df["amount"] > 0).all()

    def test_expenses_excludes_refunds(self) -> None:
        svc = ReportService(cashflow_mapping=_CASHFLOW)
        df = svc.expenses(statement=self._make_statement())
        assert "Refunded_money" not in df["category"].values
        assert len(df) == 2  # Groceries + Gas

    def test_earnings_custom_mapping(self) -> None:
        svc = ReportService(
            cashflow_mapping={
                "Earnings": ["Primary_Income"],
                "Expenses": ["Needs"],
            },
        )
        df = svc.earnings(statement=self._make_statement())
        assert len(df) == 1
        assert df.iloc[0]["category"] == "Primary_Income"

    def test_expenses_category_pivot(self) -> None:
        svc = ReportService(cashflow_mapping=_CASHFLOW)
        pivot = svc.expenses_category(
            statement=self._make_statement(),
        )
        assert not pivot.empty

    def test_expenses_sub_category_pivot(self) -> None:
        svc = ReportService(cashflow_mapping=_CASHFLOW)
        pivot = svc.expenses_sub_category(
            statement=self._make_statement(),
        )
        assert not pivot.empty

    def test_empty_statement(self) -> None:
        svc = ReportService(cashflow_mapping=_CASHFLOW)
        df = svc.earnings(statement=pd.DataFrame(
            columns=["amount", "category"],
        ))
        assert df.empty

    def test_missing_cashflow_mapping_raises(self) -> None:
        with pytest.raises(ValueError, match="cashflow_mapping"):
            ReportService(cashflow_mapping={})
