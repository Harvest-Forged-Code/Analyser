from __future__ import annotations

import pandas as pd

from budget_analyser.domain.reporting import ReportService


def test_report_service_normalizes_signs() -> None:
    rs = ReportService()
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
