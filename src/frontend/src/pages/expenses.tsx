import { useState, useMemo } from "react";
import { TrendingDown } from "lucide-react";
import {
  useExpensesMonths,
  useExpensesMonth,
  useExpensesYear,
  useExpensesYearBreakdown,
} from "@/api/hooks/use-expenses";
import PageHeader from "@/components/page-header";
import MonthYearSelector from "@/components/month-year-selector";
import ChartCard from "@/components/chart-card";
import EmptyState from "@/components/empty-state";
import CategoryBreakdownTable from "@/components/expenses/category-breakdown-table";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatPercentage, findDefaultMonth } from "@/lib/utils";
import { EXPENSE_CHART_COLORS } from "@/lib/constants";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function ExpensesPage() {
  const { data: months, isLoading: monthsLoading } = useExpensesMonths();

  // Derive available years from months
  const availableYears = useMemo(() => {
    if (!months || months.length === 0) return [];
    const years = months
      .filter((m): m is string => typeof m === "string" && m.includes("-"))
      .map((m) => {
        const parts = m.split("-");
        return parseInt(parts[0] ?? "");
      });
    return Array.from(new Set(years)).sort((a, b) => b - a);
  }, [months]);

  const [activeTab, setActiveTab] = useState<string>("monthly");
  const [breakdownSearch, setBreakdownSearch] = useState("");

  // Select first available month/year by default
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>(undefined);
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined);

  // Set defaults when data loads — prefer current month/year
  useMemo(() => {
    if (months && months.length > 0 && selectedMonth === undefined) {
      setSelectedMonth(findDefaultMonth(months));
    }
    if (availableYears.length > 0 && selectedYear === undefined) {
      const now = new Date().getFullYear();
      setSelectedYear(availableYears.includes(now) ? now : availableYears[0]);
    }
  }, [months, availableYears, selectedMonth, selectedYear]);

  const handleMonthChange = (month: string) => {
    setSelectedMonth(month);
    const yearStr = month.split("-")[0];
    if (yearStr) setSelectedYear(parseInt(yearStr));
  };

  const handleYearChange = (year: number) => {
    setSelectedYear(year);
    if (months) {
      const firstOfYear = months.find((m) => m.startsWith(year.toString()));
      if (firstOfYear) setSelectedMonth(firstOfYear);
    }
  };

  const { data: monthData, isLoading: monthLoading } = useExpensesMonth(selectedMonth);
  const { data: yearData, isLoading: yearLoading } = useExpensesYear(selectedYear);
  const { data: yearBreakdown, isLoading: yearBreakdownLoading } =
    useExpensesYearBreakdown(selectedYear);

  // Column definitions for yearly breakdown table
  const yearlyColumns: ColumnDef<Record<string, unknown>>[] = useMemo(() => {
    if (!yearBreakdown || yearBreakdown.length === 0) return [];
    const sample = yearBreakdown[0];
    if (!sample) return [];
    const keys = Object.keys(sample);

    return keys.map((key) => ({
      accessorKey: key,
      header: () => (
        <div className={key === "month" ? "" : "text-right"}>
          {key
            .split("_")
            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
            .join(" ")}
        </div>
      ),
      cell: ({ row }) => {
        const value = row.getValue(key);
        if (key === "month") {
          return <span className="font-medium">{value as string}</span>;
        }
        if (typeof value === "number") {
          return <div className="text-right">{formatCurrency(value)}</div>;
        }
        return <div className="text-right">{String(value)}</div>;
      },
    }));
  }, [yearBreakdown]);

  // Transform monthly data for pie chart (by category)
  const monthPieData = useMemo(() => {
    if (!monthData) return [];

    // Aggregate by category
    const categoryTotals = monthData.reduce(
      (acc, row) => {
        const category = (row.category as string) || "Other";
        const amount = ((row.amount as number | undefined) ?? 0) as number;
        const currentTotal = (acc[category] ?? 0) as number;
        acc[category] = currentTotal + amount;
        return acc;
      },
      {} as Record<string, number>
    );

    return Object.entries(categoryTotals)
      .map(([name, value]) => ({ name, value: value as number }))
      .sort((a, b) => (b.value as number) - (a.value as number));
  }, [monthData]);

  // Transform monthly data for bar chart (top sub-categories)
  const monthBarData = useMemo(() => {
    if (!monthData) return [];
    return monthData
      .map((row) => ({
        name: (row.sub_category as string) || "Other",
        amount: (row.amount as number) || 0,
      }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 10); // Top 10 sub-categories
  }, [monthData]);

  if (monthsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!months || months.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Expenses"
          description="Analyze your spending patterns"
        />
        <EmptyState
          icon={<TrendingDown className="h-12 w-12" />}
          title="No expenses data"
          description="Upload transaction data to start tracking your expenses."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Expenses"
        description="Analyze your spending patterns"
      >
        <MonthYearSelector
          months={months}
          years={availableYears}
          selectedMonth={selectedMonth ?? null}
          selectedYear={selectedYear ?? null}
          onMonthChange={handleMonthChange}
          onYearChange={handleYearChange}
          showMonths={activeTab === "monthly"}
          showYears={activeTab === "yearly"}
        />
      </PageHeader>

      <Tabs defaultValue="monthly" value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList>
          <TabsTrigger value="monthly">Monthly</TabsTrigger>
          <TabsTrigger value="yearly">Yearly</TabsTrigger>
        </TabsList>

        <TabsContent value="monthly" className="space-y-6">
          {monthLoading ? (
            <Skeleton className="h-96 w-full" />
          ) : monthData && monthData.length > 0 ? (
            <>
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between gap-4">
                    <CardTitle>Expenses Breakdown</CardTitle>
                    <Input
                      placeholder="Search categories..."
                      value={breakdownSearch}
                      onChange={(e) => setBreakdownSearch(e.target.value)}
                      className="w-[200px]"
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  <CategoryBreakdownTable data={monthData} search={breakdownSearch} period={selectedMonth} />
                </CardContent>
              </Card>

              <div className="grid gap-6 md:grid-cols-2">
                <ChartCard
                  title="Expenses by Category"
                  description="Distribution of spending across categories"
                >
                  <ResponsiveContainer width="100%" height={350}>
                    <PieChart>
                      <Pie
                        data={monthPieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={120}
                        label={(entry) => {
                          const total = monthPieData.reduce(
                            (sum, d) => sum + (d.value as number),
                            0
                          );
                          return `${entry.name}: ${formatPercentage(
                            ((entry.value as number) / total) * 100
                          )}`;
                        }}
                      >
                        {monthPieData.map((entry, index) => (
                          <Cell
                            key={`cell-${entry.name}`}
                            fill={EXPENSE_CHART_COLORS[index % EXPENSE_CHART_COLORS.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip formatter={(value) => formatCurrency(value as number)} />
                    </PieChart>
                  </ResponsiveContainer>
                </ChartCard>

                <ChartCard
                  title="Top Sub-Categories"
                  description="Highest spending sub-categories"
                >
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={monthBarData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis
                        type="number"
                        tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                      />
                      <YAxis type="category" dataKey="name" width={100} />
                      <Tooltip
                        formatter={(value) => formatCurrency(value as number)}
                      />
                      <Bar
                        dataKey="amount"
                        fill={EXPENSE_CHART_COLORS[0]}
                        radius={[0, 4, 4, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                </ChartCard>
              </div>
            </>
          ) : (
            <EmptyState
              icon={<TrendingDown className="h-12 w-12" />}
              title="No data for selected month"
              description="Try selecting a different month."
            />
          )}
        </TabsContent>

        <TabsContent value="yearly" className="space-y-6">
          {yearLoading || yearBreakdownLoading ? (
            <Skeleton className="h-96 w-full" />
          ) : yearData && yearBreakdown && yearBreakdown.length > 0 ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Year Summary</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    {Object.entries(yearData).map(([key, value]) => (
                      <div key={key} className="space-y-2">
                        <p className="text-sm text-muted-foreground">
                          {key
                            .split("_")
                            .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
                            .join(" ")}
                        </p>
                        <p className="text-2xl font-bold">
                          {typeof value === "number"
                            ? formatCurrency(value)
                            : String(value)}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Monthly Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataTable columns={yearlyColumns} data={yearBreakdown} />
                </CardContent>
              </Card>
            </>
          ) : (
            <EmptyState
              icon={<TrendingDown className="h-12 w-12" />}
              title="No data for selected year"
              description="Try selecting a different year."
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
