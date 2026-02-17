"""Pydantic v2 serializers for the Budget Analyser REST API.

Each Pydantic model mirrors a frozen dataclass from the feature
layer but uses JSON-safe types (pd.DataFrame -> list[dict],
pd.Period -> str, date -> str, Enum -> str).

Also contains request/response models for API endpoints.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ===================================================================
# core/models.py
# ===================================================================

class MonthlyReportsSchema(BaseModel):
    """Serialized MonthlyReports (core DTO)."""

    month: str  # pd.Period -> str e.g. "2024-01"
    earnings: list[dict[str, Any]]
    expenses: list[dict[str, Any]]
    expenses_category: list[dict[str, Any]]
    expenses_sub_category: list[dict[str, Any]]
    transactions: list[dict[str, Any]] = Field(default_factory=list)


# ===================================================================
# features/budget_goals/models.py
# ===================================================================

class BudgetGoalSchema(BaseModel):
    """Serialized BudgetGoal."""

    id: int | None = None
    category: str
    monthly_limit: float
    year_month: str


class EarningsGoalSchema(BaseModel):
    """Serialized EarningsGoal."""

    id: int | None = None
    sub_category: str
    expected_amount: float
    year_month: str


class BudgetProgressSchema(BaseModel):
    """Serialized BudgetProgress."""

    category: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str


class BudgetGoalsSummarySchema(BaseModel):
    """Serialized BudgetGoalsSummary."""

    total_monthly_budget: float
    categories_tracked: int
    month_overrides: int


class EarningsGoalsSummarySchema(BaseModel):
    """Serialized EarningsGoalsSummary."""

    total_expected_earnings: float
    sub_categories_tracked: int
    month_overrides: int


class ProgressSummarySchema(BaseModel):
    """Serialized ProgressSummary."""

    on_track_count: int
    warning_count: int
    over_budget_count: int
    total_spent: float
    total_budget: float


class CategoryProgressPointSchema(BaseModel):
    """Serialized CategoryProgressPoint."""

    year_month: str
    budget_limit: float
    spent: float
    remaining: float
    percentage: float
    status: str


# ===================================================================
# features/net_worth/models.py
# ===================================================================

class AccountSchema(BaseModel):
    """Serialized Account."""

    id: int | None = None
    name: str
    account_type: str
    balance: float
    last_updated: str
    notes: str = ""


class NetWorthSummarySchema(BaseModel):
    """Serialized NetWorthSummary."""

    total_assets: float
    total_liabilities: float
    net_worth: float
    assets_by_type: dict[str, float]
    liabilities_by_type: dict[str, float]
    accounts: list[AccountSchema]


# ===================================================================
# features/recurring/models.py
# ===================================================================

class RecurringTransactionSchema(BaseModel):
    """Serialized RecurringTransaction."""

    id: int | None = None
    description: str
    expected_amount: float
    frequency: str
    category: str
    sub_category: str
    last_occurrence: str
    is_active: bool = True


# ===================================================================
# features/savings/models.py
# ===================================================================

class SavingsMetricsSchema(BaseModel):
    """Serialized SavingsMetrics."""

    total_earnings: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    monthly_average_savings: float
    months_of_data: int


# ===================================================================
# features/payments/models.py
# ===================================================================

class PaymentPairSchema(BaseModel):
    """Serialized PaymentPair."""

    payment_made_id: int
    payment_confirmed_id: int
    amount: float
    payment_date: str  # datetime -> ISO str
    confirmation_date: str
    days_apart: int
    confidence: float
    net_amount: float = 0.0


class PaymentMatchResultSchema(BaseModel):
    """Serialized PaymentMatchResult."""

    matched_pairs: list[PaymentPairSchema] = Field(default_factory=list)
    unmatched_payments: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    unmatched_confirmations: list[dict[str, Any]] = Field(
        default_factory=list,
    )
    match_rate: float = 100.0
    total_matched_amount: float = 0.0
    total_unmatched_payment_amount: float = 0.0
    total_unmatched_confirmation_amount: float = 0.0
    is_fully_matched: bool = True


class PaymentsReconciliationSummarySchema(BaseModel):
    """Serialized PaymentsReconciliationSummary."""

    period: str  # pd.Period -> str
    payments_made: list[dict[str, Any]]
    payment_confirmations: list[dict[str, Any]]
    total_payments_made: float
    total_payment_confirmations: float
    difference: float


# ===================================================================
# features/forecasting/models.py
# ===================================================================

class ForecastPointSchema(BaseModel):
    """Serialized ForecastPoint."""

    period: str
    value: float
    lower_bound: float
    upper_bound: float
    confidence: float


class ForecastResultSchema(BaseModel):
    """Serialized ForecastResult."""

    method: str  # ForecastMethod enum -> str value
    forecasts: list[ForecastPointSchema] = Field(default_factory=list)
    historical_data: dict[str, float] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)


# ===================================================================
# features/trends/models.py
# ===================================================================

class MonthlyTrendSchema(BaseModel):
    """Serialized MonthlyTrend."""

    period: str  # pd.Period -> str
    value: float
    mom_change: float = 0.0
    mom_change_pct: float = 0.0
    yoy_change: float | None = None
    yoy_change_pct: float | None = None
    moving_avg_3m: float | None = None
    moving_avg_6m: float | None = None
    moving_avg_12m: float | None = None
    direction: str = "unknown"  # TrendDirection enum -> str value


class TrendAnalysisResultSchema(BaseModel):
    """Serialized TrendAnalysisResult."""

    monthly_trends: list[MonthlyTrendSchema] = Field(
        default_factory=list,
    )
    overall_direction: str = "unknown"
    average_mom_change_pct: float = 0.0
    volatility: float = 0.0
    highest_month: str | None = None  # pd.Period -> str | None
    lowest_month: str | None = None


class ParetoItemSchema(BaseModel):
    """Serialized ParetoItem."""

    category: str
    amount: float
    percentage: float
    cumulative_percentage: float
    is_top_80: bool


class ParetoAnalysisSchema(BaseModel):
    """Serialized ParetoAnalysis."""

    items: list[ParetoItemSchema] = Field(default_factory=list)
    total_amount: float = 0.0
    top_80_count: int = 0
    concentration_ratio: float = 0.0


class DayPatternSchema(BaseModel):
    """Serialized DayPattern."""

    day: str  # DayOfWeek enum -> str name
    total_amount: float
    transaction_count: int
    average_transaction: float
    percentage_of_week: float


class WeeklyPatternSchema(BaseModel):
    """Serialized WeeklyPattern."""

    day_patterns: list[DayPatternSchema] = Field(default_factory=list)
    highest_day: str | None = None
    lowest_day: str | None = None
    weekend_percentage: float = 0.0


class AnomalySchema(BaseModel):
    """Serialized Anomaly."""

    transaction_date: str
    description: str
    amount: float
    category: str
    z_score: float
    anomaly_type: str
    reason: str


class AnomalyReportSchema(BaseModel):
    """Serialized AnomalyReport."""

    anomalies: list[AnomalySchema] = Field(default_factory=list)
    total_transactions: int = 0
    anomaly_rate: float = 0.0


class SavingsRateTrendSchema(BaseModel):
    """Serialized SavingsRateTrend."""

    period: str
    earnings: float
    expenses: float
    savings: float
    savings_rate: float


class BurnRateMetricsSchema(BaseModel):
    """Serialized BurnRateMetrics."""

    period_start: str  # date -> ISO str
    period_end: str
    budget_amount: float
    spent_amount: float
    days_elapsed: int
    days_remaining: int
    daily_burn_rate: float
    projected_total: float
    budget_remaining: float
    safe_daily_spend: float
    days_until_exhausted: float | None = None
    burn_rate_status: str
    projected_over_under: float
    is_over_budget: bool = False
    on_track: bool = True
    burn_rate_percentage: float = 0.0
    time_percentage: float = 0.0


class CategoryBurnRateSchema(BaseModel):
    """Serialized CategoryBurnRate."""

    category: str
    metrics: BurnRateMetricsSchema


# ===================================================================
# features/reporting/models.py
# ===================================================================

class EarningsRowSchema(BaseModel):
    """Serialized EarningsRow."""

    sub_category: str
    actual: float
    percent_of_total: float
    expected: float
    diff: float
    diff_percent: float | None = None


# ===================================================================
# features/mappers/models.py
# ===================================================================

class SuggestionSchema(BaseModel):
    """Serialized Suggestion."""

    sub_category: str
    confidence: float
    reason: str
    matched_description: str = ""


class SuggestionResultSchema(BaseModel):
    """Serialized SuggestionResult."""

    description: str
    suggestions: list[SuggestionSchema] = Field(default_factory=list)
    patterns_detected: list[str] = Field(default_factory=list)


# ===================================================================
# features/ingestion/models.py
# ===================================================================

class IngestionResultSchema(BaseModel):
    """Serialized IngestionResult."""

    success: bool
    message: str
    transactions_processed: int = 0
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


class UploadResultSchema(BaseModel):
    """Serialized UploadResult."""

    success: bool
    message: str
    destination_path: str | None = None
    transactions_inserted: int = 0
    duplicates_skipped: int = 0


# ===================================================================
# features/export/models.py
# ===================================================================

class ExportColumnSchema(BaseModel):
    """Serialized ExportColumn (without callable formatter)."""

    name: str
    key: str


class ExportConfigSchema(BaseModel):
    """Serialized ExportConfig."""

    title: str = "Budget Analyser Report"
    subtitle: str = ""
    include_timestamp: bool = True
    include_summary: bool = True
    page_size: str = "letter"


# ===================================================================
# Request models (API endpoint payloads)
# ===================================================================

class LoginRequest(BaseModel):
    """Request body for login/authentication."""

    password: str


class GenerateReportsRequest(BaseModel):
    """Request body for triggering report generation."""

    force: bool = False


class SetBudgetRequest(BaseModel):
    """Request body for setting a budget goal."""

    category: str
    monthly_limit: float
    year_month: str = "ALL"


class SetBudgetYearRequest(BaseModel):
    """Request body for setting a budget goal for a specific year."""

    category: str
    monthly_limit: float
    year: int


class SetEarningsGoalRequest(BaseModel):
    """Request body for setting an earnings goal."""

    sub_category: str
    expected_amount: float
    year_month: str = "ALL"


class AddAccountRequest(BaseModel):
    """Request body for adding a financial account."""

    name: str
    account_type: str
    balance: float = 0.0
    notes: str = ""


class UpdateBalanceRequest(BaseModel):
    """Request body for updating an account balance."""

    balance: float


class AddRecurringRequest(BaseModel):
    """Request body for adding a recurring transaction."""

    description: str
    expected_amount: float
    frequency: str = "monthly"
    category: str = ""
    sub_category: str = ""


class UploadRequest(BaseModel):
    """Request body for uploading a bank statement."""

    file_path: str
    bank_name: str
    account_type: str


class ChangePasswordRequest(BaseModel):
    """Request body for changing the login password."""

    current: str
    new_password: str
    confirm: str


# ===================================================================
# Response models (API endpoint responses)
# ===================================================================

class DashboardSummaryResponse(BaseModel):
    """Response for the dashboard summary KPI endpoint."""

    total_earnings: float = 0.0
    total_expenses: float = 0.0
    net_savings: float = 0.0
    savings_rate: float = 0.0
    months_of_data: int = 0
    net_worth: float = 0.0
    budget_categories_over: int = 0
    budget_categories_total: int = 0
    recurring_active: int = 0
    has_reports: bool = False


class AvailableMonthsResponse(BaseModel):
    """Response listing available report months."""

    months: list[str] = Field(default_factory=list)


class AvailableYearsResponse(BaseModel):
    """Response listing available report years."""

    years: list[int] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Response for the health check endpoint."""

    status: str = "healthy"


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
