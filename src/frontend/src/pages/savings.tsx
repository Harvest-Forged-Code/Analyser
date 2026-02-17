import React from "react";
import { PiggyBank, DollarSign, TrendingUp, Percent } from "lucide-react";
import {
  useSavingsMetrics,
  useMonthlySavings,
} from "@/api/hooks/use-savings";
import { useEarningsMonths } from "@/api/hooks/use-earnings";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import ChartCard from "@/components/chart-card";
import EmptyState from "@/components/empty-state";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatPercentage } from "@/lib/utils";
import {
  COLOR_INCOME,
  COLOR_EXPENSE,
  COLOR_POSITIVE,
} from "@/lib/constants";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export default function SavingsPage() {
  const [selectedYear, setSelectedYear] = React.useState<number | undefined>(undefined);

  // Queries
  const { data: availableMonths } = useEarningsMonths();
  const { data: savingsMetrics, isLoading: metricsLoading } = useSavingsMetrics(selectedYear);
  const { data: monthlySavings, isLoading: chartLoading } = useMonthlySavings(selectedYear);

  // Derive available years from months
  const availableYears = React.useMemo(() => {
    if (!availableMonths) return [];
    const years = new Set<number>();
    availableMonths.forEach((month) => {
      const parts = month.split("-");
      if (parts.length > 0 && parts[0]) {
        const year = parseInt(parts[0], 10);
        if (!isNaN(year)) years.add(year);
      }
    });
    return Array.from(years).sort((a, b) => b - a);
  }, [availableMonths]);

  // Set default year
  React.useEffect(() => {
    if (availableYears.length > 0 && selectedYear === undefined) {
      setSelectedYear(availableYears[0]);
    }
  }, [availableYears, selectedYear]);

  // Format chart data
  const chartData = React.useMemo(() => {
    if (!monthlySavings) return [];
    return monthlySavings.map((item) => ({
      month: String(item.month || ""),
      earnings: Number(item.earnings || 0),
      expenses: Math.abs(Number(item.expenses || 0)),
      savings: Number(item.savings || 0),
    }));
  }, [monthlySavings]);

  const CustomTooltip = ({ active, payload }: {
    active?: boolean;
    payload?: Array<{ name: string; value: number; color: string; payload?: { month?: string } }>;
  }) => {
    if (!active || !payload || payload.length === 0) return null;

    const firstPayload = payload[0];
    const month = firstPayload?.payload?.month || "";

    return (
      <div className="bg-background border rounded-lg shadow-lg p-3 space-y-1">
        <p className="font-semibold text-sm">{month}</p>
        {payload.map((entry) => (
          <p key={entry.name} className="text-xs" style={{ color: entry.color }}>
            {entry.name}: {formatCurrency(entry.value)}
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Savings"
        description="Track your savings rate and trends"
      />

      {/* Year selector */}
      <div className="flex items-center gap-4">
        <Label htmlFor="year-select">Select Year:</Label>
        <Select
          value={selectedYear?.toString()}
          onValueChange={(value) => setSelectedYear(parseInt(value, 10))}
        >
          <SelectTrigger id="year-select" className="w-48">
            <SelectValue placeholder="Select year" />
          </SelectTrigger>
          <SelectContent>
            {availableYears.map((year) => (
              <SelectItem key={year} value={year.toString()}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {metricsLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : !savingsMetrics ? (
        <EmptyState
          icon={<PiggyBank className="h-12 w-12" />}
          title="No savings data"
          description="Import transactions to start tracking your savings"
        />
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <KpiCard
              title="Total Earnings"
              value={formatCurrency(savingsMetrics.total_earnings)}
              icon={<DollarSign className="h-5 w-5" />}
            />
            <KpiCard
              title="Total Expenses"
              value={formatCurrency(savingsMetrics.total_expenses)}
              icon={<DollarSign className="h-5 w-5" />}
            />
            <KpiCard
              title="Net Savings"
              value={formatCurrency(savingsMetrics.net_savings)}
              icon={<TrendingUp className="h-5 w-5" />}
              trend={
                savingsMetrics.net_savings >= 0
                  ? { value: Math.abs(savingsMetrics.net_savings), isPositive: true }
                  : { value: Math.abs(savingsMetrics.net_savings), isPositive: false }
              }
            />
            <KpiCard
              title="Savings Rate"
              value={formatPercentage(savingsMetrics.savings_rate)}
              icon={<Percent className="h-5 w-5" />}
            />
          </div>

          {/* Secondary info */}
          <div className="grid gap-4 md:grid-cols-2">
            <div className="border rounded-lg p-4">
              <p className="text-sm text-muted-foreground">Monthly Average Savings</p>
              <p className="text-2xl font-bold mt-1">
                {formatCurrency(savingsMetrics.monthly_average_savings)}
              </p>
            </div>
            <div className="border rounded-lg p-4">
              <p className="text-sm text-muted-foreground">Months of Data</p>
              <p className="text-2xl font-bold mt-1">
                {savingsMetrics.months_of_data}
              </p>
            </div>
          </div>

          {/* Monthly Savings Trend Chart */}
          {chartLoading ? (
            <Skeleton className="h-96 w-full" />
          ) : chartData.length === 0 ? (
            <EmptyState
              icon={<TrendingUp className="h-12 w-12" />}
              title="No monthly data"
              description="Monthly savings breakdown not available"
            />
          ) : (
            <ChartCard title="Monthly Savings Trend" description="Track earnings, expenses, and net savings over time">
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart
                  data={chartData}
                  margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="colorEarnings" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLOR_INCOME} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLOR_INCOME} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorExpenses" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLOR_EXPENSE} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLOR_EXPENSE} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLOR_POSITIVE} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={COLOR_POSITIVE} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis
                    dataKey="month"
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    tickLine={false}
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend
                    wrapperStyle={{ fontSize: 14, paddingTop: 10 }}
                    iconType="line"
                  />
                  <Area
                    type="monotone"
                    dataKey="earnings"
                    name="Earnings"
                    stroke={COLOR_INCOME}
                    strokeWidth={2}
                    fill="url(#colorEarnings)"
                  />
                  <Area
                    type="monotone"
                    dataKey="expenses"
                    name="Expenses"
                    stroke={COLOR_EXPENSE}
                    strokeWidth={2}
                    fill="url(#colorExpenses)"
                  />
                  <Area
                    type="monotone"
                    dataKey="savings"
                    name="Savings"
                    stroke={COLOR_POSITIVE}
                    strokeWidth={2}
                    fill="url(#colorSavings)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </>
      )}
    </div>
  );
}
