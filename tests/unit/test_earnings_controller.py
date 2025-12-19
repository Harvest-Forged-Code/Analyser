from __future__ import annotations

import pandas as pd

from budget_analyser.controller import EarningsStatsController
from budget_analyser.controller.monthly_reports import MonthlyReports


def _mr(period_str: str, earn_rows: list[dict]) -> MonthlyReports:
    period = pd.Period(period_str, freq="M")
    earnings = pd.DataFrame(earn_rows)
    # Ensure required columns exist for controller filtering/formatting
    for col in ["transaction_date", "description", "amount", "from_account", "sub_category"]:
        if col not in earnings.columns:
            if col == "transaction_date":
                earnings[col] = pd.to_datetime([f"{period.start_time.date()}" for _ in range(len(earnings))])
            elif col == "description":
                earnings[col] = ""
            elif col == "amount":
                earnings[col] = 0.0
            elif col == "from_account":
                earnings[col] = "acc"
            elif col == "sub_category":
                earnings[col] = ""
    # Build empty tables for expenses to satisfy dataclass
    empty = pd.DataFrame()
    return MonthlyReports(
        month=period,
        earnings=earnings,
        expenses=empty,
        expenses_category=empty,
        expenses_sub_category=empty,
    )


class _Logger:
    def info(self, *args, **kwargs):
        pass


def test_available_months_and_labels():
    reports = [
        _mr("2025-01", [{"description": "Salary", "amount": 1000.0, "sub_category": "Salary"}]),
        _mr("2025-02", [{"description": "Bonus", "amount": 500.0, "sub_category": "Bonus"}]),
    ]
    ctl = EarningsStatsController(reports, _Logger())
    months = ctl.available_months()
    assert [str(m) for m in months] == ["2025-01", "2025-02"]
    assert ctl.month_label(months[0]).startswith("January ")


def test_totals_and_subcategories():
    reports = [
        _mr(
            "2025-01",
            [
                {"description": "Salary A", "amount": 1000.0, "sub_category": "Salary"},
                {"description": "Salary B", "amount": 500.0, "sub_category": "Salary"},
                {"description": "Div", "amount": 200.0, "sub_category": "Dividends"},
            ],
        )
    ]
    ctl = EarningsStatsController(reports, _Logger())
    period = ctl.available_months()[0]
    assert ctl.total_for_month(period) == 1700.0
    subs = ctl.subcategory_totals(period)
    # Salary should come first with 1500
    assert subs[0][0] == "Salary" and abs(subs[0][1] - 1500.0) < 1e-9
    # Dividends present
    cats = dict(subs)
    assert abs(cats.get("Dividends", 0.0) - 200.0) < 1e-9


def test_transactions_filter_by_subcategory():
    reports = [
        _mr(
            "2025-01",
            [
                {"description": "Salary A", "amount": 1000.0, "sub_category": "Salary"},
                {"description": "Div A", "amount": 200.0, "sub_category": "Dividends"},
            ],
        )
    ]
    ctl = EarningsStatsController(reports, _Logger())
    period = ctl.available_months()[0]
    all_tx = ctl.transactions(period)
    assert len(all_tx) == 2
    sal_tx = ctl.transactions(period, sub_category="Salary")
    assert len(sal_tx) == 1
    assert sal_tx.iloc[0]["description"].startswith("Salary")
