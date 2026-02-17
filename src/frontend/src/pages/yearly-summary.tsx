import { useState, useMemo } from "react";
import { Calendar, TrendingUp, TrendingDown, Wallet } from "lucide-react";
import {
  useEarningsMonths,
  useEarningsYearBreakdown,
} from "@/api/hooks/use-earnings";
import { useExpensesYearBreakdown } from "@/api/hooks/use-expenses";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import ChartCard from "@/components/chart-card";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency, formatPercentage, cn } from "@/lib/utils";
import { COLOR_INCOME, COLOR_EXPENSE, MONTH_NAMES_SHORT } from "@/lib/constants";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface MonthlyBreakdown {
  month: string;
  earnings: number;
  expenses: number;
  savings: number;
  savings_rate: number;
}

export default function YearlySummaryPage() {
  const { data: months, isLoading: monthsLoading } = useEarningsMonths();

  // Derive available years from months
  const availableYears = useMemo(() => {
    if (!months || months.length === 0) return [];
    const years = months.map((m) => {
      const yearPart = m.split("-")[0];
      return yearPart ? parseInt(yearPart) : 0;
    });
    return Array.from(new Set(years)).sort((a, b) => b - a);
  }, [months]);

  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined);

  // Auto-select first year
  useMemo(() => {
    if (availableYears.length > 0 && !selectedYear) {
      setSelectedYear(availableYears[0]);
    }
  }, [availableYears, selectedYear]);

  const { data: earningsBreakdown, isLoading: earningsLoading } =
    useEarningsYearBreakdown(selectedYear);
  const { data: expensesBreakdown, isLoading: expensesLoading } =
    useExpensesYearBreakdown(selectedYear);

  // Calculate yearly totals
  const yearlyTotals = useMemo(() => {
    if (!earningsBreakdown || !expensesBreakdown) {
      return { totalEarnings: 0, totalExpenses: 0, netSavings: 0, savingsRate: 0 };
    }

    const totalEarnings = earningsBreakdown.reduce(
      (sum, row) => sum + (typeof row.total === "number" ? row.total : 0),
      0
    );
    const totalExpenses = expensesBreakdown.reduce(
      (sum, row) => sum + (typeof row.total === "number" ? row.total : 0),
      0
    );
    const netSavings = totalEarnings - totalExpenses;
    const savingsRate = totalEarnings > 0 ? (netSavings / totalEarnings) * 100 : 0;

    return { totalEarnings, totalExpenses, netSavings, savingsRate };
  }, [earningsBreakdown, expensesBreakdown]);

  // Combine earnings and expenses into monthly breakdown
  const monthlyBreakdown = useMemo<MonthlyBreakdown[]>(() => {
    if (!earningsBreakdown || !expensesBreakdown) return [];

    const breakdownMap = new Map<string, MonthlyBreakdown>();

    earningsBreakdown.forEach((row) => {
      const month = String(row.month || row.period || row.name || "Unknown");
      const earnings = typeof row.total === "number" ? row.total : 0;
      breakdownMap.set(month, {
        month,
        earnings,
        expenses: 0,
        savings: 0,
        savings_rate: 0,
      });
    });

    expensesBreakdown.forEach((row) => {
      const month = String(row.month || row.period || row.name || "Unknown");
      const expenses = typeof row.total === "number" ? row.total : 0;
      const existing = breakdownMap.get(month);
      if (existing) {
        existing.expenses = expenses;
        existing.savings = existing.earnings - expenses;
        existing.savings_rate =
          existing.earnings > 0 ? (existing.savings / existing.earnings) * 100 : 0;
      } else {
        breakdownMap.set(month, {
          month,
          earnings: 0,
          expenses,
          savings: -expenses,
          savings_rate: 0,
        });
      }
    });

    return Array.from(breakdownMap.values());
  }, [earningsBreakdown, expensesBreakdown]);

  // Transform for chart
  const chartData = useMemo(() => {
    return monthlyBreakdown.map((row) => ({
      month: row.month,
      Earnings: row.earnings,
      Expenses: row.expenses,
    }));
  }, [monthlyBreakdown]);

  // Table columns
  const breakdownColumns: ColumnDef<MonthlyBreakdown>[] = [
    {
      accessorKey: "month",
      header: "Month",
      cell: ({ row }) => <span className="font-medium">{row.getValue("month")}</span>,
    },
    {
      accessorKey: "earnings",
      header: () => <div className="text-right">Earnings</div>,
      cell: ({ row }) => (
        <div className="text-right font-medium text-green-600">
          {formatCurrency(row.getValue("earnings"))}
        </div>
      ),
    },
    {
      accessorKey: "expenses",
      header: () => <div className="text-right">Expenses</div>,
      cell: ({ row }) => (
        <div className="text-right font-medium text-red-600">
          {formatCurrency(row.getValue("expenses"))}
        </div>
      ),
    },
    {
      accessorKey: "savings",
      header: () => <div className="text-right">Savings</div>,
      cell: ({ row }) => {
        const savings = row.getValue("savings") as number;
        return (
          <div
            className={cn(
              "text-right font-medium",
              savings > 0 ? "text-green-600" : savings < 0 ? "text-red-600" : ""
            )}
          >
            {formatCurrency(savings, true)}
          </div>
        );
      },
    },
    {
      accessorKey: "savings_rate",
      header: () => <div className="text-right">Savings Rate</div>,
      cell: ({ row }) => {
        const rate = row.getValue("savings_rate") as number;
        return (
          <div
            className={cn(
              "text-right",
              rate > 0 ? "text-green-600" : rate < 0 ? "text-red-600" : ""
            )}
          >
            {formatPercentage(rate, true)}
          </div>
        );
      },
    },
  ];

  if (monthsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!months || months.length === 0 || availableYears.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Yearly Summary" description="Annual financial overview" />
        <EmptyState
          icon={<Calendar />}
          title="No yearly data"
          description="Upload transaction data to start tracking your annual finances."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Yearly Summary" description="Annual financial overview" />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Select Year</CardTitle>
            <Select
              value={selectedYear?.toString()}
              onValueChange={(val) => setSelectedYear(parseInt(val))}
            >
              <SelectTrigger className="w-[180px]">
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
        </CardHeader>
      </Card>

      {earningsLoading || expensesLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : monthlyBreakdown.length > 0 ? (
        <>
          <div className="grid gap-4 md:grid-cols-4">
            <KpiCard
              title="Total Earnings"
              value={formatCurrency(yearlyTotals.totalEarnings)}
              icon={<TrendingUp className="h-5 w-5" />}
            />
            <KpiCard
              title="Total Expenses"
              value={formatCurrency(yearlyTotals.totalExpenses)}
              icon={<TrendingDown className="h-5 w-5" />}
            />
            <KpiCard
              title="Net Savings"
              value={formatCurrency(yearlyTotals.netSavings)}
              icon={<Wallet className="h-5 w-5" />}
              className={cn(
                yearlyTotals.netSavings > 0
                  ? "border-green-200 bg-green-50"
                  : "border-red-200 bg-red-50"
              )}
            />
            <KpiCard
              title="Savings Rate"
              value={formatPercentage(yearlyTotals.savingsRate)}
              description={
                yearlyTotals.savingsRate > 20
                  ? "Excellent savings!"
                  : yearlyTotals.savingsRate > 10
                    ? "Good savings"
                    : "Improve savings"
              }
            />
          </div>

          <ChartCard
            title="Monthly Earnings vs Expenses"
            description={`Financial comparison for ${selectedYear}`}
          >
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="month"
                  tickFormatter={(value) => {
                    const monthPart = String(value).split("-")[1];
                    if (!monthPart) return String(value);
                    const monthIndex = parseInt(monthPart) - 1;
                    return MONTH_NAMES_SHORT[monthIndex] || String(value);
                  }}
                />
                <YAxis tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
                <Tooltip
                  formatter={(value) => formatCurrency(value as number)}
                  labelFormatter={(label) => {
                    const monthPart = String(label).split("-")[1];
                    if (!monthPart) return String(label);
                    const monthIndex = parseInt(monthPart) - 1;
                    return MONTH_NAMES_SHORT[monthIndex] || String(label);
                  }}
                />
                <Legend />
                <Bar dataKey="Earnings" fill={COLOR_INCOME} radius={[4, 4, 0, 0]} />
                <Bar dataKey="Expenses" fill={COLOR_EXPENSE} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartCard>

          <Card>
            <CardHeader>
              <CardTitle>Monthly Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable columns={breakdownColumns} data={monthlyBreakdown} />
            </CardContent>
          </Card>
        </>
      ) : (
        <EmptyState
          icon={<Calendar />}
          title="No data for selected year"
          description="Try selecting a different year."
        />
      )}
    </div>
  );
}
