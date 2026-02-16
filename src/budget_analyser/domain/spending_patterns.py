"""Spending pattern analysis (domain logic).

Backward-compatibility shim: re-exports from features.trends.
New code should import from budget_analyser.features.trends directly.
"""

from budget_analyser.features.trends import (  # pylint: disable=unused-import  # noqa: F401
    DayOfWeek,
    ParetoItem,
    ParetoAnalysis,
    DayPattern,
    WeeklyPattern,
    Anomaly,
    AnomalyReport,
    SavingsRateTrend,
    SpendingPatternService,
    analyze_spending_patterns,
)
