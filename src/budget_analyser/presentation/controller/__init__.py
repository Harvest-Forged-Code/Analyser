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

__all__ = ["YearlySummaryStatsController", "SettingsController"]
