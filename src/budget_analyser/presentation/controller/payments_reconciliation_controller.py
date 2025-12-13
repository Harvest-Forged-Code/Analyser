from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from budget_analyser.presentation.controllers import MonthlyReports
from .utils import month_names as _month_names


@dataclass(frozen=True)
class PaymentsReconciliationSummary:
    period: pd.Period
    payments_made: pd.DataFrame
    payment_confirmations: pd.DataFrame
    total_payments_made: float
    total_payment_confirmations: float
    difference: float  # confirmations - payments (absolute sums)


class PaymentsReconciliationController:
    """Controller to compare payments made vs payment confirmations per month.

    UI-only consumers should render the returned DataFrames and summary values.
    All computations are done here to keep views free of business logic.
    """

    SUB_PAYMENTS = "payments_made"
    SUB_CONFIRM = "payment_confirmations"

    def __init__(self, reports: List[MonthlyReports], logger: logging.Logger):
        self._reports = reports
        self._logger = logger
        # Map Period("YYYY-MM") -> MonthlyReports for quick lookup
        self._by_period: Dict[pd.Period, MonthlyReports] = {mr.month: mr for mr in self._reports}

    # ---- Public API ----
    def available_months(self) -> List[pd.Period]:
        return sorted(self._by_period.keys())

    @staticmethod
    def month_label(period: pd.Period) -> str:
        names = _month_names()
        return f"{names[int(period.month) - 1]} {int(period.year)}"

    def data(self, period: pd.Period) -> PaymentsReconciliationSummary:
        """Return the reconciliation data for a given month.

        Totals are computed as absolute sums for robust matching.
        Difference = confirmations - payments (both absolute totals).
        """
        mr = self._by_period.get(period)
        if mr is None or mr.transactions is None or mr.transactions.empty:
            empty = pd.DataFrame(columns=[
                "transaction_date",
                "description",
                "amount",
                "from_account",
                "category",
                "sub_category",
            ])
            return PaymentsReconciliationSummary(
                period=period,
                payments_made=empty,
                payment_confirmations=empty,
                total_payments_made=0.0,
                total_payment_confirmations=0.0,
                difference=0.0,
            )

        df = mr.transactions
        if "sub_category" not in df.columns:
            # Cannot filter; return empty/defaults
            self._logger.warning(
                "PaymentsReconciliation: sub_category column missing for %s", period
            )
            return PaymentsReconciliationSummary(
                period=period,
                payments_made=pd.DataFrame(columns=df.columns),
                payment_confirmations=pd.DataFrame(columns=df.columns),
                total_payments_made=0.0,
                total_payment_confirmations=0.0,
                difference=0.0,
            )

        pm = df[df["sub_category"].fillna("") == self.SUB_PAYMENTS].copy()
        pc = df[df["sub_category"].fillna("") == self.SUB_CONFIRM].copy()

        # Sort by date desc for readability if column exists
        for sub_df in (pm, pc):
            if "transaction_date" in sub_df.columns:
                try:
                    sub_df.sort_values(by="transaction_date", ascending=False, inplace=True)
                except Exception:  # pragma: no cover
                    pass

        total_pm = float(pm["amount"].abs().sum()) if not pm.empty and "amount" in pm.columns else 0.0
        total_pc = float(pc["amount"].abs().sum()) if not pc.empty and "amount" in pc.columns else 0.0
        diff = float(total_pc - total_pm)

        return PaymentsReconciliationSummary(
            period=period,
            payments_made=pm,
            payment_confirmations=pc,
            total_payments_made=total_pm,
            total_payment_confirmations=total_pc,
            difference=diff,
        )
