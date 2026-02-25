import { useState, useMemo } from "react";
import { TrendingUp } from "lucide-react";
import {
  useEarningsMonths,
  useEarningsMonth,
  useEarningsDashboard,
  useEarningsTrend,
  useEarningsSourceTrend,
} from "@/api/hooks/use-earnings";
import PageHeader from "@/components/page-header";
import MonthYearSelector from "@/components/month-year-selector";
import EmptyState from "@/components/empty-state";
import KpiCards from "@/components/earnings/kpi-cards";
import CombinedChart from "@/components/earnings/combined-chart";
import BreakdownTable from "@/components/earnings/breakdown-table";
import TransactionModal from "@/components/earnings/transaction-modal";
import { Skeleton } from "@/components/ui/skeleton";
import { findDefaultMonth } from "@/lib/utils";

export default function EarningsPage() {
  const { data: months, isLoading: monthsLoading } = useEarningsMonths();

  // Derive available years from months
  const availableYears = useMemo(() => {
    if (!months || months.length === 0) return [];
    const years = months
      .filter((m): m is string => typeof m === "string" && m.includes("-"))
      .map((m) => parseInt(m.split("-")[0] ?? ""));
    return Array.from(new Set(years)).sort((a, b) => b - a);
  }, [months]);

  // Period selection state
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

  // Transaction modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [modalSubCategory, setModalSubCategory] = useState<string | undefined>(undefined);

  // Data hooks
  const { data: dashboard, isLoading: dashboardLoading } =
    useEarningsDashboard(selectedMonth);
  const { data: trend, isLoading: trendLoading } = useEarningsTrend(12);
  const { data: sourceTrend } = useEarningsSourceTrend(6);
  const { data: monthData, isLoading: monthLoading } = useEarningsMonth(selectedMonth);

  // Extract rows from month data response
  const monthRows = useMemo(() => {
    if (!monthData) return [];
    // API returns { rows, actual_total, expected_total }
    if ("rows" in monthData && Array.isArray(monthData.rows)) {
      return monthData.rows;
    }
    if (Array.isArray(monthData)) return monthData;
    return [];
  }, [monthData]);

  const handleRowClick = (subCategory: string) => {
    setModalSubCategory(subCategory);
    setModalOpen(true);
  };

  const handleMonthChange = (month: string) => {
    setSelectedMonth(month);
    // Update year to match selected month
    const yearStr = month.split("-")[0];
    if (yearStr) setSelectedYear(parseInt(yearStr));
  };

  const handleYearChange = (year: number) => {
    setSelectedYear(year);
    // Select first month of that year if available
    if (months) {
      const monthsOfYear = months.filter((m) => m.startsWith(year.toString()));
      if (monthsOfYear.length > 0) {
        setSelectedMonth(monthsOfYear[0]);
      }
    }
  };

  if (monthsLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
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
      >
        <MonthYearSelector
          months={months}
          years={availableYears}
          selectedMonth={selectedMonth ?? null}
          selectedYear={selectedYear ?? null}
          onMonthChange={handleMonthChange}
          onYearChange={handleYearChange}
        />
      </PageHeader>

      {/* KPI Cards */}
      {dashboardLoading ? (
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
          <Skeleton className="h-36" />
        </div>
      ) : dashboard ? (
        <KpiCards dashboard={dashboard} />
      ) : null}

      {/* Combined Chart */}
      {trendLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : trend && trend.length > 0 ? (
        <CombinedChart trend={trend} monthRows={monthRows} />
      ) : null}

      {/* Breakdown Table */}
      {monthLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : monthRows.length > 0 ? (
        <BreakdownTable
          rows={monthRows}
          sourceTrend={sourceTrend}
          onRowClick={handleRowClick}
        />
      ) : (
        <EmptyState
          icon={<TrendingUp className="h-12 w-12" />}
          title="No data for selected month"
          description="Try selecting a different month."
        />
      )}

      {/* Transaction Modal */}
      <TransactionModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        period={selectedMonth}
        subCategory={modalSubCategory}
      />
    </div>
  );
}
