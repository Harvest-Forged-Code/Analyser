from __future__ import annotations

import pandas as pd

from budget_analyser.features.reporting import ReportService

_CASHFLOW = {
    "Earnings": ["Primary_Income", "Secondary_Income", "Refunded_money"],
    "Expenses": ["Needs", "Wants", "Luxury", "Remittance"],
}


def test_report_service_normalizes_signs() -> None:
    rs = ReportService(cashflow_mapping=_CASHFLOW)
    df = pd.DataFrame(
        {
            "transaction_date": pd.to_datetime([
                "2025-01-01",
                "2025-01-02",
                "2025-01-03",
                "2025-01-04",
            ]),
            "description": ["A", "B", "C", "D"],
            # mix of signs; final earnings should be positive, expenses negative
            "amount": [100.0, -50.0, 200.0, -300.0],
            "from_account": ["acc", "acc", "acc", "acc"],
        }
    )

    earn = rs.earnings(statement=df)
    exp = rs.expenses(statement=df)

    # Earnings rows: amounts strictly positive
    assert (earn["amount"] > 0).all()
    # Expenses rows: amounts strictly negative
    assert (exp["amount"] < 0).all()

    # Ensure original df not mutated
    assert list(df["amount"]) == [100.0, -50.0, 200.0, -300.0]


def test_report_service_routes_refunds_to_earnings() -> None:
    """Refunded_money goes to earnings, not expenses, per cashflow JSON."""
    rs = ReportService(cashflow_mapping=_CASHFLOW)
    df = pd.DataFrame(
        {
            "transaction_date": pd.to_datetime([
                "2025-02-01",
                "2025-02-02",
                "2025-02-03",
                "2025-02-04",
                "2025-02-05",
                "2025-02-06",
            ]),
            "description": [
                "Payroll",
                "Transfer",
                "Groceries",
                "Refund",
                "Gift",
                "Subscription",
            ],
            "amount": [100.0, -50.0, -40.0, 30.0, 60.0, -25.0],
            "from_account": ["acc"] * 6,
            "category": [
                "Primary_Income",
                "Remittance",
                "Needs",
                "Refunded_money",
                "Secondary_Income",
                "Wants",
            ],
            "sub_category": [
                "Salary",
                "",
                "Groceries",
                "",
                "Others_income",
                "",
            ],
        }
    )

    earn = rs.earnings(statement=df)
    exp = rs.expenses(statement=df)

    # Refunded_money is an Earnings category — appears in earnings, not expenses
    assert set(earn["category"]) == {
        "Primary_Income", "Secondary_Income", "Refunded_money",
    }
    assert sorted(earn["amount"].tolist()) == sorted([100.0, 60.0, 30.0])

    # Expenses contain only expense categories — no refunds
    assert "Refunded_money" not in exp["category"].values
    assert (exp["amount"] < 0).all()
