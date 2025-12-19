"""Presentation controllers (page-level).

Single responsibility:
    Expose controllers that transform domain/presentation data into
    view-friendly structures. Views import only these controllers and
    never access domain services directly.

Design pattern:
    MVC-style separation. Controllers are pure Python (no Qt) and return
    DTOs for the views to render.
"""

from __future__ import annotations

from .yearly_summary_stats_controller import YearlySummaryStatsController
from .settings_controller import SettingsController
from .earnings_stats_controller import EarningsStatsController
from .expenses_stats_controller import ExpensesStatsController
from .payments_reconciliation_controller import PaymentsReconciliationController
from .mapper_controller import MapperController
from .upload_controller import UploadController

__all__ = [
    "YearlySummaryStatsController",
    "SettingsController",
    "EarningsStatsController",
    "ExpensesStatsController",
    "PaymentsReconciliationController",
    "MapperController",
    "UploadController",
]
