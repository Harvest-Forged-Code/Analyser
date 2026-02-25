import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import EmptyState from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useDashboardSummary } from "@/api/hooks/use-dashboard";
import { formatCurrency, formatPercentage } from "@/lib/utils";
import {
  COLOR_INCOME,
  COLOR_EXPENSE,
  COLOR_POSITIVE,
  COLOR_NEGATIVE,
} from "@/lib/constants";
import {
  DollarSign,
  ShoppingCart,
  PiggyBank,
  Percent,
  Wallet,
  Target,
  Repeat,
  Calendar,
  BarChart3,
  AlertCircle,
} from "lucide-react";

export default function DashboardPage() {
  const { data, isLoading, error, refetch } = useDashboardSummary();

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          description="Your financial overview at a glance"
        />
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-semibold">Failed to load dashboard</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "An error occurred"}
          </p>
          <Button onClick={() => refetch()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          description="Your financial overview at a glance"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
      </div>
    );
  }

  // Empty state (no data)
  if (!data?.has_reports) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Dashboard"
          description="Your financial overview at a glance"
        />
        <EmptyState
          icon={<BarChart3 className="h-12 w-12" />}
          title="No data available"
          description="Upload a statement to get started with your financial tracking"
          action={
            <Button onClick={() => window.location.hash = "#/upload"}>
              Upload Statement
            </Button>
          }
        />
      </div>
    );
  }

  // Determine net savings color based on value
  const netSavingsColor = data.net_savings >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Your financial overview at a glance"
      />

      {/* Primary KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Total Earnings"
          value={formatCurrency(data.total_earnings)}
          description="All income sources"
          icon={<DollarSign className="h-6 w-6" style={{ color: COLOR_INCOME }} />}
        />
        <KpiCard
          title="Total Expenses"
          value={formatCurrency(data.total_expenses)}
          description="All spending"
          icon={<ShoppingCart className="h-6 w-6" style={{ color: COLOR_EXPENSE }} />}
        />
        <KpiCard
          title="Net Savings"
          value={formatCurrency(data.net_savings)}
          description={data.net_savings >= 0 ? "Positive cash flow" : "Negative cash flow"}
          icon={<PiggyBank className="h-6 w-6" style={{ color: netSavingsColor }} />}
        />
        <KpiCard
          title="Savings Rate"
          value={formatPercentage(data.savings_rate)}
          description="Of total earnings"
          icon={<Percent className="h-6 w-6" />}
        />
      </div>

      {/* Secondary KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard
          title="Net Worth"
          value={formatCurrency(data.net_worth)}
          description="Assets minus liabilities"
          icon={<Wallet className="h-6 w-6" />}
        />
        <KpiCard
          title="Budget Status"
          value={`${data.budget_categories_over} of ${data.budget_categories_total}`}
          description={
            data.budget_categories_over === 0
              ? "All categories on track"
              : data.budget_categories_over === 1
              ? "Category over budget"
              : "Categories over budget"
          }
          icon={<Target className="h-6 w-6" />}
        />
        <KpiCard
          title="Recurring Active"
          value={data.recurring_active}
          description="Active recurring transactions"
          icon={<Repeat className="h-6 w-6" />}
        />
        <KpiCard
          title="Months of Data"
          value={data.months_of_data}
          description="Total tracking period"
          icon={<Calendar className="h-6 w-6" />}
        />
      </div>
    </div>
  );
}
