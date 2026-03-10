"""Recurring payment analytics feature.

Provides intelligent detection of recurring transactions, user confirmation
workflow, and anomaly detection for missed or unusual payments.
"""

from __future__ import annotations

from budget_analyser.features.recurring.service import (
    RecurringAnalyticsService,
)

__all__ = ["RecurringAnalyticsService"]
