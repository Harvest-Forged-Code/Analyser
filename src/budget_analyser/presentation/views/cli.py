from __future__ import annotations

# pylint: disable=too-few-public-methods

from dataclasses import dataclass
from typing import Iterable

from tabulate import tabulate

from budget_analyser.presentation.controllers import MonthlyReports


@dataclass(frozen=True)
class CliView:
    def render(self, *, reports: Iterable[MonthlyReports]) -> None:
        for report in reports:
            print(f"\n=== {report.month} ===")

            print("\nEarnings")
            print(tabulate(report.earnings, headers="keys", tablefmt="grid", showindex=False))

            print("\nExpenses")
            print(tabulate(report.expenses, headers="keys", tablefmt="grid", showindex=False))

            print("\nExpenses by Category")
            print(
                tabulate(
                    report.expenses_category,
                    headers="keys",
                    tablefmt="grid",
                    showindex=True,
                )
            )

            print("\nExpenses by Sub-Category")
            print(
                tabulate(
                    report.expenses_sub_category,
                    headers="keys",
                    tablefmt="grid",
                    showindex=True,
                )
            )
