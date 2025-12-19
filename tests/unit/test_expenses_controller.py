from __future__ import annotations

import pandas as pd

from budget_analyser.controller import ExpensesStatsController
from budget_analyser.controller.monthly_reports import MonthlyReports


def _mr(period_str: str, exp_rows: list[dict]) -> MonthlyReports:
    period = pd.Period(period_str, freq="M")
    expenses = pd.DataFrame(exp_rows)
    # Ensure required columns exist for controller filtering/formatting
    for col in ["transaction_date", "description", "amount", "from_account", "category", "sub_category"]:
        if col not in expenses.columns:
            if col == "transaction_date":
                expenses[col] = pd.to_datetime([f"{period.start_time.date()}" for _ in range(len(expenses))])
            elif col == "description":
                expenses[col] = ""
            elif col == "amount":
                expenses[col] = 0.0
            elif col == "from_account":
                expenses[col] = "acc"
            elif col in ("category", "sub_category"):
                expenses[col] = ""
    # Build empty earnings tables to satisfy dataclass
    empty = pd.DataFrame()
    return MonthlyReports(
        month=period,
        earnings=empty,
        expenses=expenses,
        expenses_category=empty,
        expenses_sub_category=empty,
    )


class _Logger:
    def info(self, *args, **kwargs):
        pass


def test_available_months_and_labels():
    reports = [
        _mr("2025-01", [{"description": "Groceries", "amount": -100.0, "category": "Food", "sub_category": "Groceries"}]),
        _mr("2025-02", [{"description": "Gas", "amount": -50.0, "category": "Transport", "sub_category": "Fuel"}]),
    ]
    ctl = ExpensesStatsController(reports, _Logger())
    months = ctl.available_months()
    assert [str(m) for m in months] == ["2025-01", "2025-02"]
    assert ctl.month_label(months[0]).startswith("January ")


def test_total_and_category_breakdown():
    reports = [
        _mr(
            "2025-01",
            [
                {"description": "Groceries A", "amount": -100.0, "category": "Food", "sub_category": "Groceries"},
                {"description": "Groceries B", "amount": -50.0, "category": "Food", "sub_category": "Groceries"},
                {"description": "Dining", "amount": -30.0, "category": "Food", "sub_category": "Dining"},
                {"description": "Fuel", "amount": -60.0, "category": "Transport", "sub_category": "Fuel"},
            ],
        )
    ]
    ctl = ExpensesStatsController(reports, _Logger())
    period = ctl.available_months()[0]
    # total should be positive sum of absolute values
    assert abs(ctl.total_for_month(period) - (100 + 50 + 30 + 60)) < 1e-9

    breakdown = ctl.category_breakdown(period)
    # Convert to dict for easier checks
    bd = {cat: (total, dict(subs)) for cat, total, subs in breakdown}
    assert abs(bd["Food"][0] - 180.0) < 1e-9
    assert abs(bd["Food"][1].get("Groceries", 0.0) - 150.0) < 1e-9
    assert abs(bd["Food"][1].get("Dining", 0.0) - 30.0) < 1e-9
    assert abs(bd["Transport"][0] - 60.0) < 1e-9


def test_transactions_filtering():
    reports = [
        _mr(
            "2025-01",
            [
                {"description": "Groceries A", "amount": -100.0, "category": "Food", "sub_category": "Groceries"},
                {"description": "Dining", "amount": -30.0, "category": "Food", "sub_category": "Dining"},
                {"description": "Fuel", "amount": -60.0, "category": "Transport", "sub_category": "Fuel"},
            ],
        )
    ]
    ctl = ExpensesStatsController(reports, _Logger())
    period = ctl.available_months()[0]

    all_tx = ctl.transactions(period)
    assert len(all_tx) == 3

    food_tx = ctl.transactions(period, category="Food")
    assert len(food_tx) == 2
    assert set(food_tx["sub_category"]) == {"Groceries", "Dining"}

    groceries_tx = ctl.transactions(period, category="Food", sub_category="Groceries")
    assert len(groceries_tx) == 1
    assert groceries_tx.iloc[0]["description"].startswith("Groceries")
