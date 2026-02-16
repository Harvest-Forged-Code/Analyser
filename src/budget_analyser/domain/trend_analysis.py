"""Time-series trend analysis (domain logic).

Backward-compatibility shim: re-exports from features.trends.
New code should import from budget_analyser.features.trends directly.
"""

from budget_analyser.features.trends import (  # pylint: disable=unused-import  # noqa: F401
    TrendDirection,
    MonthlyTrend,
    TrendAnalysisResult,
    TrendAnalysisService,
    analyze_spending_trends,
    analyze_income_trends,
)
