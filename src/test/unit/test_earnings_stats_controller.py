from __future__ import annotations

import logging
from typing import Dict

import pandas as pd
from pytest import approx

from budget_analyser.controller.earnings_stats_controller import EarningsStatsController, EarningsRow
from budget_analyser.controller.controllers import MonthlyReports


class _StubBudgetController:
    def __init__(self, mapping_by_month: Dict[str, Dict[str, float]]):
        self._mapping = mapping_by_month

    def get_earnings_goal_map(self, year_month: str = "ALL") -> Dict[str, float]:
        base = dict(self._mapping.get("ALL", {}))
        override = self._mapping.get(year_month, {})
        base.update(override)
        return base


def _monthly_report(period: str, amounts, subcats) -> MonthlyReports:
    earnings = pd.DataFrame(
        {
            "transaction_date": pd.to_datetime(["2025-01-01"] * len(amounts)),
            "description": ["desc"] * len(amounts),
            "amount": amounts,
            "from_account": ["acc"] * len(amounts),
            "sub_category": subcats,
        }
    )
    return MonthlyReports(
        month=pd.Period(period),
        earnings=earnings,
        expenses=pd.DataFrame(),
        expenses_category=pd.DataFrame(),
        expenses_sub_category=pd.DataFrame(),
        transactions=earnings,
    )


def _row_map(rows: list[EarningsRow]) -> Dict[str, EarningsRow]:
    return {row.sub_category: row for row in rows}


def test_table_for_month_includes_expected_and_diff() -> None:
    reports = [_monthly_report("2025-01", [100.0, 50.0], ["salary", "bonus"])]
    stub = _StubBudgetController({"ALL": {"salary": 90.0}})
    ctrl = EarningsStatsController(reports, logging.getLogger(__name__), budget_controller=stub)

    rows, actual_total, expected_total = ctrl.table_for_month(pd.Period("2025-01"))
    row_by_sub = _row_map(rows)

    assert actual_total == approx(150.0)
    assert expected_total == approx(90.0)

    salary = row_by_sub["salary"]
    assert salary.actual == approx(100.0)
    assert salary.expected == approx(90.0)
    assert salary.diff == approx(10.0)
    assert salary.percent_of_total == approx(66.666, rel=1e-3)
    assert salary.diff_percent == approx(11.111, rel=1e-3)

    bonus = row_by_sub["bonus"]
    assert bonus.expected == approx(0.0)
    assert bonus.diff == approx(50.0)


def test_table_for_year_sums_expected_per_month() -> None:
    reports = [
        _monthly_report("2025-01", [80.0], ["salary"]),
        _monthly_report("2025-02", [70.0], ["salary"]),
    ]
    stub = _StubBudgetController({
        "2025-01": {"salary": 75.0},
        "2025-02": {"salary": 85.0},
    })
    ctrl = EarningsStatsController(reports, logging.getLogger(__name__), budget_controller=stub)

    rows, actual_total, expected_total = ctrl.table_for_year(2025)
    assert actual_total == approx(150.0)
    assert expected_total == approx(160.0)

    salary = _row_map(rows)["salary"]
    assert salary.actual == approx(150.0)
    assert salary.expected == approx(160.0)
    assert salary.diff == approx(-10.0)
    assert salary.diff_percent == approx(-6.25)