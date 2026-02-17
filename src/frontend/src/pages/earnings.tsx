import { useState, useMemo } from "react";
import { TrendingUp } from "lucide-react";
import {
  useEarningsMonths,
  useEarningsMonth,
  useEarningsYear,
  useEarningsYearBreakdown,
} from "@/api/hooks/use-earnings";
import type { EarningsRow } from "@/api/types";
import PageHeader from "@/components/page-header";
import ChartCard from "@/components/chart-card";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
import { INCOME_CHART_COLORS } from "@/lib/constants";
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

export default function EarningsPage() {
  const { data: months, isLoading: monthsLoading } = useEarningsMonths();

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

  // Select first available month/year by default
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>(undefined);
  const [selectedYear, setSelectedYear] = useState<number | undefined>(undefined);

  // Set defaults when data loads
  useMemo(() => {
    if (months && months.length > 0 && selectedMonth === undefined) {
      setSelectedMonth(months[0]);
    }
    if (availableYears.length > 0 && selectedYear === undefined) {
      setSelectedYear(availableYears[0]);
    }
  }, [months, availableYears, selectedMonth, selectedYear]);

  const { data: monthData, isLoading: monthLoading } = useEarningsMonth(selectedMonth);
  const { data: yearData, isLoading: yearLoading } = useEarningsYear(selectedYear);
  const { data: yearBreakdown, isLoading: yearBreakdownLoading } =
    useEarningsYearBreakdown(selectedYear);

  // Column definitions for monthly table
  const monthlyColumns: ColumnDef<EarningsRow>[] = [
    {
      accessorKey: "sub_category",
      header: "Sub Category",
      cell: ({ row }) => (
        <span className="font-medium">{row.getValue("sub_category")}</span>
      ),
    },
    {
      accessorKey: "actual",
      header: () => <div className="text-right">Actual</div>,
      cell: ({ row }) => (
        <div className="text-right font-medium">
          {formatCurrency(row.getValue("actual"))}
        </div>
      ),
    },
    {
      accessorKey: "percent_of_total",
      header: () => <div className="text-right">% of Total</div>,
      cell: ({ row }) => (
        <div className="text-right">
          {formatPercentage(row.getValue("percent_of_total"))}
        </div>
      ),
    },
    {
      accessorKey: "expected",
      header: () => <div className="text-right">Expected</div>,
      cell: ({ row }) => (
        <div className="text-right">{formatCurrency(row.getValue("expected"))}</div>
      ),
    },
    {
      accessorKey: "diff",
      header: () => <div className="text-right">Diff</div>,
      cell: ({ row }) => {
        const diff = row.getValue("diff") as number;
        return (
          <div
            className={cn(
              "text-right font-medium",
              diff > 0 ? "text-green-600" : diff < 0 ? "text-red-600" : ""
            )}
          >
            {formatCurrency(diff, true)}
          </div>
        );
      },
    },
    {
      accessorKey: "diff_percent",
      header: () => <div className="text-right">Diff %</div>,
      cell: ({ row }) => {
        const diffPercent = row.getValue("diff_percent") as number | null;
        if (diffPercent === null) return <div className="text-right">—</div>;
        return (
          <div
            className={cn(
              "text-right",
              diffPercent > 0
                ? "text-green-600"
                : diffPercent < 0
                  ? "text-red-600"
                  : ""
            )}
          >
            {formatPercentage(diffPercent, true)}
          </div>
        );
      },
    },
  ];

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

  // Transform monthly data for chart
  const monthChartData = useMemo(() => {
    if (!monthData) return [];
    return monthData.map((row) => ({
      name: row.sub_category,
      Actual: row.actual,
      Expected: row.expected,
    }));
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
          title="Earnings"
          description="Track your income sources and trends"
        />
        <EmptyState
          icon={<TrendingUp className="h-12 w-12" />}
          title="No earnings data"
          description="Upload transaction data to start tracking your earnings."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Earnings"
        description="Track your income sources and trends"
      />

      <Tabs defaultValue="monthly" className="space-y-6">
        <TabsList>
          <TabsTrigger value="monthly">Monthly</TabsTrigger>
          <TabsTrigger value="yearly">Yearly</TabsTrigger>
        </TabsList>

        <TabsContent value="monthly" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Select Month</CardTitle>
                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select month" />
                  </SelectTrigger>
                  <SelectContent>
                    {months.map((month) => (
                      <SelectItem key={month} value={month}>
                        {month}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
          </Card>

          {monthLoading ? (
            <Skeleton className="h-96 w-full" />
          ) : monthData && monthData.length > 0 ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Earnings Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                  <DataTable columns={monthlyColumns} data={monthData} />
                </CardContent>
              </Card>

              <ChartCard title="Actual vs Expected" description="Compare actual earnings against expected amounts">
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={monthChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis
                      tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                    />
                    <Tooltip
                      formatter={(value) => formatCurrency(value as number)}
                    />
                    <Legend />
                    <Bar
                      dataKey="Actual"
                      fill={INCOME_CHART_COLORS[0]}
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="Expected"
                      fill={INCOME_CHART_COLORS[1]}
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
            </>
          ) : (
            <EmptyState
              icon={<TrendingUp className="h-12 w-12" />}
              title="No data for selected month"
              description="Try selecting a different month."
            />
          )}
        </TabsContent>

        <TabsContent value="yearly" className="space-y-6">
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
              icon={<TrendingUp className="h-12 w-12" />}
              title="No data for selected year"
              description="Try selecting a different year."
            />
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
