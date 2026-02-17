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
  frequency: string;
  category: string;
  sub_category: string;
  last_occurrence: string;
  is_active: boolean;
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
export interface PaymentsReconciliation {
  period: string;
  payments_made: Record<string, unknown>[];
  payment_confirmations: Record<string, unknown>[];
  total_payments_made: number;
  total_payment_confirmations: number;
  difference: number;
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
  duplicates_skipped: number;
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
