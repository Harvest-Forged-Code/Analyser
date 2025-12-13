"""Presentation layer facades.

This module re-exports the public controller/dataclass symbols to preserve
backward compatibility while enforcing one-class-per-file structure.
"""

from __future__ import annotations

from budget_analyser.presentation.backend_controller import BackendController
from budget_analyser.presentation.monthly_reports import MonthlyReports

__all__ = ["BackendController", "MonthlyReports"]
