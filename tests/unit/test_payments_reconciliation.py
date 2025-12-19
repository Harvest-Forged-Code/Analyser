from __future__ import annotations

import pandas as pd

from budget_analyser.controller import PaymentsReconciliationController
from budget_analyser.controller.monthly_reports import MonthlyReports


def _mr(period_str: str, rows: list[dict]) -> MonthlyReports:
    period = pd.Period(period_str, freq="M")
    df = pd.DataFrame(rows)
    if "transaction_date" not in df.columns:
        df["transaction_date"] = pd.to_datetime([f"{period.start_time.date()}" for _ in range(len(df))])
    return MonthlyReports(
        month=period,
        earnings=pd.DataFrame(),
        expenses=pd.DataFrame(),
        expenses_category=pd.DataFrame(),
        expenses_sub_category=pd.DataFrame(),
        transactions=df,
    )


class _Logger:
    def info(self, *a, **k):
        pass
    def warning(self, *a, **k):
        pass


def test_payments_reconciliation_totals_and_diff():
    reports = [
        _mr(
            "2025-01",
            [
                {"description": "CITI AUTOPAY     PAYMENT", "sub_category": "payments_made", "amount": -120.0, "from_account": "a"},
                {"description": "ONLINE PAYMENT, THANK YOU", "sub_category": "payment_confirmations", "amount": 120.0, "from_account": "a"},
            ],
        )
    ]
    ctl = PaymentsReconciliationController(reports, _Logger())
    period = ctl.available_months()[0]
    summary = ctl.data(period)
    assert abs(summary.total_payments_made - 120.0) < 1e-9
    assert abs(summary.total_payment_confirmations - 120.0) < 1e-9
    assert abs(summary.difference) < 1e-9
    # Ensure tables have expected counts
    assert len(summary.payments_made.index) == 1
    assert len(summary.payment_confirmations.index) == 1
