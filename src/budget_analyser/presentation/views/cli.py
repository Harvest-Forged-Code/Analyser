"""CLI view (presentation).

Purpose:
    Render report tables to stdout.

Goal:
    Keep business logic out of the view; only format/display already computed data.
"""

from __future__ import annotations

# pylint: disable=too-few-public-methods

from dataclasses import dataclass
from typing import Iterable

from tabulate import tabulate

from budget_analyser.presentation.controllers import MonthlyReports


@dataclass(frozen=True)
class CliView:
    """CLI renderer for `MonthlyReports`."""

    def render(self, *, reports: Iterable[MonthlyReports]) -> None:
        """Render month-wise reports.

        Args:
            reports: Iterable of month-wise report objects.
        """
        # Iterate month-by-month and print each table.
        for report in reports:
            # Month header.
            print(f"\n=== {report.month} ===")

            print("\nEarnings")
            # Earnings table.
            print(tabulate(report.earnings, headers="keys", tablefmt="grid", showindex=False))

            print("\nExpenses")
            # Expenses table.
            print(tabulate(report.expenses, headers="keys", tablefmt="grid", showindex=False))

            print("\nExpenses by Category")
            # Category pivot.
            print(
                tabulate(
                    report.expenses_category,
                    headers="keys",
                    tablefmt="grid",
                    showindex=True,
                )
            )

            print("\nExpenses by Sub-Category")
            # Sub-category pivot.
            print(
                tabulate(
                    report.expenses_sub_category,
                    headers="keys",
                    tablefmt="grid",
                    showindex=True,
                )
            )
