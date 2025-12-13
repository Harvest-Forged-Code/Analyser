from __future__ import annotations

import pandas as pd


class ReportService:
    def earnings(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        return statement[statement["amount"] > 0]

    def expenses(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        return statement[statement["amount"] < 0]

    def expenses_category(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )

    def expenses_sub_category(self, *, statement: pd.DataFrame) -> pd.DataFrame:
        expenses = self.expenses(statement=statement)
        return expenses.pivot_table(
            index="sub_category",
            columns="year_month",
            values="amount",
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        )
