"""Unit tests for EarningsStatsController dashboard methods."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from budget_analyser.core.models import MonthlyReports
from budget_analyser.features.reporting.earnings_service import (
    EarningsStatsController,
)


def _make_report(
    period: str,
    rows: list[tuple[str, float]],
) -> MonthlyReports:
    """Build a MonthlyReports with earnings data.

    Args:
        period: Period string (e.g. "2025-01").
        rows: List of (sub_category, amount) tuples.
    """
    if rows:
        df = pd.DataFrame(
            {
                "transaction_date": pd.Timestamp(f"{period}-15"),
                "description": [r[0] for r in rows],
                "amount": [r[1] for r in rows],
                "from_account": "checking",
                "sub_category": [r[0] for r in rows],
            },
        )
    else:
        df = pd.DataFrame(
            columns=[
                "transaction_date",
                "description",
                "amount",
                "from_account",
                "sub_category",
            ],
        )
    empty = pd.DataFrame()
    return MonthlyReports(
        month=pd.Period(period, freq="M"),
        earnings=df,
        expenses=empty,
        expenses_category=empty,
        expenses_sub_category=empty,
    )


def _make_controller(
    reports: list[MonthlyReports],
    *,
    budget_controller: object | None = None,
) -> EarningsStatsController:
    return EarningsStatsController(
        reports,
        logging.getLogger("test"),
        budget_controller=budget_controller,
    )


class _FakeBudgetController:
    """Stub returning fixed earnings goal map."""

    def __init__(self, goal_map: dict[str, float]) -> None:
        self._goal_map = goal_map

    def get_earnings_goal_map(
        self, year_month: str,
    ) -> list[tuple[str, float]]:
        return list(self._goal_map.items())


# -------------------------------------------------------------------
# dashboard()
# -------------------------------------------------------------------

class TestDashboard:

    def test_normal_data(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 4000.0)]),
            _make_report("2025-02", [("Salary", 5000.0)]),
        ]
        ctrl = _make_controller(reports)
        dash = ctrl.dashboard(pd.Period("2025-02", "M"))

        assert dash.current_month_total == 5000.0
        assert dash.previous_month_total == 4000.0
        assert dash.mom_change_percent == pytest.approx(25.0)
        assert dash.ytd_total == 9000.0
        assert dash.period == "2025-02"
        assert dash.year == 2025

    def test_empty_data(self) -> None:
        ctrl = _make_controller([])
        dash = ctrl.dashboard(pd.Period("2025-01", "M"))

        assert dash.current_month_total == 0.0
        assert dash.previous_month_total == 0.0
        assert dash.mom_change_percent is None
        assert dash.ytd_total == 0.0

    def test_with_goals(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 4500.0)]),
        ]
        budget = _FakeBudgetController({"Salary": 5000.0})
        ctrl = _make_controller(reports, budget_controller=budget)
        dash = ctrl.dashboard(pd.Period("2025-01", "M"))

        assert dash.goal_total == 5000.0
        assert dash.goal_progress_percent == pytest.approx(90.0)

    def test_no_goals(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 4500.0)]),
        ]
        ctrl = _make_controller(reports)
        dash = ctrl.dashboard(pd.Period("2025-01", "M"))

        assert dash.goal_total == 0.0
        assert dash.goal_progress_percent is None

    def test_first_month_no_previous(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 3000.0)]),
        ]
        ctrl = _make_controller(reports)
        dash = ctrl.dashboard(pd.Period("2025-01", "M"))

        assert dash.previous_month_total == 0.0
        assert dash.mom_change_percent is None

    def test_sparkline_length(self) -> None:
        reports = [
            _make_report(f"2025-{m:02d}", [("Salary", float(m * 1000))])
            for m in range(1, 7)
        ]
        ctrl = _make_controller(reports)
        dash = ctrl.dashboard(pd.Period("2025-06", "M"))

        assert len(dash.sparkline) == 6
        assert dash.sparkline[-1] == 6000.0

    def test_zero_previous_month(self) -> None:
        reports = [
            _make_report("2025-01", []),
            _make_report("2025-02", [("Salary", 5000.0)]),
        ]
        ctrl = _make_controller(reports)
        dash = ctrl.dashboard(pd.Period("2025-02", "M"))

        assert dash.previous_month_total == 0.0
        assert dash.mom_change_percent is None


# -------------------------------------------------------------------
# monthly_trend()
# -------------------------------------------------------------------

class TestMonthlyTrend:

    def test_returns_correct_count(self) -> None:
        reports = [
            _make_report(f"2025-{m:02d}", [("Salary", float(m * 100))])
            for m in range(1, 13)
        ]
        ctrl = _make_controller(reports)
        trend = ctrl.monthly_trend(months=6)

        assert len(trend) == 6
        assert trend[0].period == "2025-07"
        assert trend[-1].period == "2025-12"

    def test_all_months(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 1000.0)]),
            _make_report("2025-02", [("Salary", 2000.0)]),
        ]
        ctrl = _make_controller(reports)
        trend = ctrl.monthly_trend(months=12)

        assert len(trend) == 2
        assert trend[0].total == 1000.0
        assert trend[1].total == 2000.0

    def test_labels_format(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 1000.0)]),
        ]
        ctrl = _make_controller(reports)
        trend = ctrl.monthly_trend(months=1)

        assert trend[0].label == "Jan 2025"

    def test_empty_reports(self) -> None:
        ctrl = _make_controller([])
        trend = ctrl.monthly_trend(months=6)

        assert trend == []


# -------------------------------------------------------------------
# source_trend()
# -------------------------------------------------------------------

class TestSourceTrend:

    def test_single_source(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 4000.0)]),
            _make_report("2025-02", [("Salary", 5000.0)]),
        ]
        ctrl = _make_controller(reports)
        trends = ctrl.source_trend(months=6)

        assert len(trends) == 1
        assert trends[0].sub_category == "Salary"
        assert len(trends[0].months) == 2

    def test_multiple_sources(self) -> None:
        reports = [
            _make_report(
                "2025-01",
                [("Salary", 4000.0), ("Freelance", 800.0)],
            ),
            _make_report(
                "2025-02",
                [("Salary", 4500.0), ("Freelance", 600.0)],
            ),
        ]
        ctrl = _make_controller(reports)
        trends = ctrl.source_trend(months=6)

        assert len(trends) == 2
        assert trends[0].sub_category == "Salary"
        assert trends[1].sub_category == "Freelance"

    def test_source_appears_in_some_months(self) -> None:
        reports = [
            _make_report("2025-01", [("Salary", 4000.0)]),
            _make_report(
                "2025-02",
                [("Salary", 4500.0), ("Bonus", 1000.0)],
            ),
        ]
        ctrl = _make_controller(reports)
        trends = ctrl.source_trend(months=6)

        salary = next(
            t for t in trends if t.sub_category == "Salary"
        )
        bonus = next(
            t for t in trends if t.sub_category == "Bonus"
        )
        assert len(salary.months) == 2
        assert len(bonus.months) == 2
        assert bonus.months[0].total == 0.0
        assert bonus.months[1].total == 1000.0

    def test_sorted_by_total_descending(self) -> None:
        reports = [
            _make_report(
                "2025-01",
                [("Salary", 4000.0), ("Freelance", 5000.0)],
            ),
        ]
        ctrl = _make_controller(reports)
        trends = ctrl.source_trend(months=6)

        assert trends[0].sub_category == "Freelance"
        assert trends[1].sub_category == "Salary"

    def test_empty_reports(self) -> None:
        ctrl = _make_controller([])
        trends = ctrl.source_trend(months=6)

        assert trends == []
