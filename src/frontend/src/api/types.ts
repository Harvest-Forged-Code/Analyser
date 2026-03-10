// Core
export interface MonthlyReport {
  month: string;
  earnings: Record<string, unknown>[];
  expenses: Record<string, unknown>[];
  expenses_category: Record<string, unknown>[];
  expenses_sub_category: Record<string, unknown>[];
  transactions: Record<string, unknown>[];
}

// Budget Goals
export interface BudgetGoal {
  id: number | null;
  category: string;
  monthly_limit: number;
  year_month: string;
}

export interface EarningsGoal {
  id: number | null;
  sub_category: string;
  expected_amount: number;
  year_month: string;
}

export interface BudgetProgress {
  category: string;
  budget_limit: number;
  spent: number;
  remaining: number;
  percentage: number;
  status: string;
}

export interface BudgetGoalsSummary {
  total_monthly_budget: number;
  categories_tracked: number;
  month_overrides: number;
}

export interface EarningsGoalsSummary {
  total_expected_earnings: number;
  sub_categories_tracked: number;
  month_overrides: number;
}

export interface ProgressSummary {
  on_track_count: number;
  warning_count: number;
  over_budget_count: number;
  total_spent: number;
  total_budget: number;
}

export interface CategoryProgressPoint {
  year_month: string;
  budget_limit: number;
  spent: number;
  remaining: number;
  percentage: number;
  status: string;
}

// Net Worth
export interface Account {
  id: number | null;
  name: string;
  account_type: string;
  balance: number;
  last_updated: string;
  notes: string;
}

export interface NetWorthSummary {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  assets_by_type: Record<string, number>;
  liabilities_by_type: Record<string, number>;
  accounts: Account[];
}

// Recurring
export interface RecurringTransaction {
  id: number | null;
  description: string;
  expected_amount: number;
  amount_variance: number;
  frequency: string;
  category: string;
  sub_category: string;
  last_occurrence: string | null;
  next_expected: string | null;
  confidence_score: number;
  user_confirmed: boolean;
  is_expected: boolean;
  is_active: boolean;
  detection_method: string;
}

export interface RecurringDetection {
  description: string;
  expected_amount: number;
  amount_variance: number;
  frequency: string;
  category: string;
  sub_category: string;
  last_occurrence: string | null;
  occurrences: number;
  confidence_score: number;
  matching_dates: string[];
}

export interface RecurringAnomaly {
  id: number | null;
  recurring_id: number;
  anomaly_type: string;
  expected_date: string | null;
  actual_date: string | null;
  expected_amount: number | null;
  actual_amount: number | null;
  severity: string;
  message: string;
  resolved: boolean;
  detected_at: string | null;
}

export interface RecurringSummary {
  total_monthly_cost: number;
  total_yearly_projection: number;
  active_count: number;
  confirmed_count: number;
  unconfirmed_count: number;
  by_frequency: Record<string, number>;
  by_category: Record<string, number>;
  trend_data: Record<string, number>[];
}

// Savings
export interface SavingsMetrics {
  total_earnings: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  monthly_average_savings: number;
  months_of_data: number;
}

// Payments
export interface PaymentPair {
  status: string;
  amount: number;
  source_account: string;
  destination_account: string | null;
  payment_date: string;
  confirmation_date: string | null;
  payment_made: Record<string, unknown>;
  payment_confirmation: Record<string, unknown> | null;
}

export interface ReconciliationSummary {
  period: string;
  matched_pairs: PaymentPair[];
  pending_payments: PaymentPair[];
  total_matched: number;
  total_pending: number;
  match_rate: number;
}

// Forecasting
export interface ForecastPoint {
  period: string;
  value: number;
  lower_bound: number;
  upper_bound: number;
  confidence: number;
}

export interface ForecastResult {
  method: string;
  forecasts: ForecastPoint[];
  historical_data: Record<string, number>;
  metrics: Record<string, number>;
}

// Trends
export interface MonthlyTrend {
  period: string;
  value: number;
  mom_change: number;
  mom_change_pct: number;
  yoy_change: number | null;
  yoy_change_pct: number | null;
  moving_avg_3m: number | null;
  moving_avg_6m: number | null;
  moving_avg_12m: number | null;
  direction: string;
}

export interface TrendAnalysisResult {
  monthly_trends: MonthlyTrend[];
  overall_direction: string;
  average_mom_change_pct: number;
  volatility: number;
  highest_month: string | null;
  lowest_month: string | null;
}

export interface ParetoItem {
  category: string;
  amount: number;
  percentage: number;
  cumulative_percentage: number;
  is_top_80: boolean;
}

export interface ParetoAnalysis {
  items: ParetoItem[];
  total_amount: number;
  top_80_count: number;
  concentration_ratio: number;
}

export interface BurnRateMetrics {
  period_start: string;
  period_end: string;
  budget_amount: number;
  spent_amount: number;
  days_elapsed: number;
  days_remaining: number;
  daily_burn_rate: number;
  projected_total: number;
  budget_remaining: number;
  safe_daily_spend: number;
  days_until_exhausted: number | null;
  burn_rate_status: string;
  projected_over_under: number;
  is_over_budget: boolean;
  on_track: boolean;
  burn_rate_percentage: number;
  time_percentage: number;
}

export interface WeeklyPattern {
  day_patterns: {
    day: string;
    total_amount: number;
    transaction_count: number;
    average_transaction: number;
    percentage_of_week: number;
  }[];
  highest_day: string | null;
  lowest_day: string | null;
  weekend_percentage: number;
}

export interface AnomalyReport {
  anomalies: {
    transaction_date: string;
    description: string;
    amount: number;
    category: string;
    z_score: number;
    anomaly_type: string;
    reason: string;
  }[];
  total_transactions: number;
  anomaly_rate: number;
}

// Reporting
export interface EarningsRow {
  sub_category: string;
  actual: number;
  percent_of_total: number;
  expected: number;
  diff: number;
  diff_percent: number | null;
}

// Earnings Dashboard
export interface EarningsMonthTrend {
  period: string;
  label: string;
  total: number;
}

export interface EarningsSourceTrend {
  sub_category: string;
  months: EarningsMonthTrend[];
}

export interface EarningsDashboard {
  current_month_total: number;
  previous_month_total: number;
  mom_change_percent: number | null;
  ytd_total: number;
  goal_total: number;
  goal_progress_percent: number | null;
  period: string;
  year: number;
  sparkline: number[];
}

// Mappers
export interface Suggestion {
  sub_category: string;
  confidence: number;
  reason: string;
  matched_description: string;
}

export interface SuggestionResult {
  description: string;
  suggestions: Suggestion[];
  patterns_detected: string[];
}

// Ingestion
export interface UploadResult {
  success: boolean;
  message: string;
  destination_path: string | null;
  transactions_inserted: number;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
  row_count: number;
  date_range: string;
}

export interface UploadHistoryEntry {
  file_name: string;
  bank_name: string;
  account_type: string;
  uploaded_at: string;
  transactions_inserted: number;
}

// Dashboard
export interface DashboardSummary {
  total_earnings: number;
  total_expenses: number;
  net_savings: number;
  savings_rate: number;
  months_of_data: number;
  net_worth: number;
  budget_categories_over: number;
  budget_categories_total: number;
  recurring_active: number;
  has_reports: boolean;
}

// Request types
export interface LoginRequest {
  password: string;
}

export interface SetBudgetRequest {
  category: string;
  monthly_limit: number;
  year_month?: string;
}

export interface SetEarningsGoalRequest {
  sub_category: string;
  expected_amount: number;
  year_month?: string;
}

export type YearGrid = Record<string, Record<string, number>>;

export interface SetBudgetYearRequest {
  category: string;
  monthly_limit: number;
  year: number;
}

export interface SetEarningsYearRequest {
  sub_category: string;
  expected_amount: number;
  year: number;
}

export interface AddAccountRequest {
  name: string;
  account_type: string;
  balance?: number;
  notes?: string;
}

export interface AddRecurringRequest {
  description: string;
  expected_amount: number;
  frequency?: string;
  category?: string;
  sub_category?: string;
  is_expected?: boolean;
}

export interface UpdateRecurringRequest {
  description?: string;
  expected_amount?: number;
  frequency?: string;
  category?: string;
  sub_category?: string;
  is_expected?: boolean;
}

export interface MarkExpectedRequest {
  is_expected: boolean;
}

export interface UploadRequest {
  file_path: string;
  bank_name: string;
  account_type: string;
}

export interface ChangePasswordRequest {
  current: string;
  new_password: string;
  confirm: string;
}

// Auto-update
export interface ReleaseInfo {
  tag_name: string;
  version: string;
  name: string;
  body: string;
  html_url: string;
  published_at: string;
}

export interface UpdateCheckResult {
  update_available: boolean;
  current_version: string;
  latest_version: string;
  release: ReleaseInfo | null;
}
