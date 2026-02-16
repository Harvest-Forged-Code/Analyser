"""Trends feature module.

Provides trend analysis, spending pattern detection, and burn rate tracking.
"""

from budget_analyser.features.trends.models import (
    TrendDirection,
    MonthlyTrend,
    TrendAnalysisResult,
    DayOfWeek,
    ParetoItem,
    ParetoAnalysis,
    DayPattern,
    WeeklyPattern,
    Anomaly,
    AnomalyReport,
    SavingsRateTrend,
    BurnRateMetrics,
    CategoryBurnRate,
)
from budget_analyser.features.trends.trend_analysis import (
    TrendAnalysisService,
    analyze_spending_trends,
    analyze_income_trends,
)
from budget_analyser.features.trends.spending_patterns import (
    SpendingPatternService,
    analyze_spending_patterns,
)
from budget_analyser.features.trends.burn_rate import (
    BurnRateService,
    calculate_burn_rate,
)

__all__ = [
    # Trend analysis
    "TrendDirection",
    "MonthlyTrend",
    "TrendAnalysisResult",
    "TrendAnalysisService",
    "analyze_spending_trends",
    "analyze_income_trends",
    # Spending patterns
    "DayOfWeek",
    "ParetoItem",
    "ParetoAnalysis",
    "DayPattern",
    "WeeklyPattern",
    "Anomaly",
    "AnomalyReport",
    "SavingsRateTrend",
    "SpendingPatternService",
    "analyze_spending_patterns",
    # Burn rate
    "BurnRateMetrics",
    "CategoryBurnRate",
    "BurnRateService",
    "calculate_burn_rate",
]
