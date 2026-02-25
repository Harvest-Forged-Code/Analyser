import { DollarSign, Target, TrendingUp, TrendingDown, Calendar } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn, formatCurrency, formatPercentage } from "@/lib/utils";
import type { EarningsDashboard } from "@/api/types";
import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";

interface KpiCardsProps {
  dashboard: EarningsDashboard;
}

function SparklineChart({ data }: { data: number[] }) {
  const options: ApexOptions = {
    chart: {
      type: "area",
      sparkline: { enabled: true },
      animations: { enabled: false },
    },
    stroke: { curve: "smooth", width: 2 },
    fill: {
      type: "gradient",
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.1,
      },
    },
    colors: ["#0EA5E9"],
    tooltip: { enabled: false },
  };

  return (
    <Chart
      options={options}
      series={[{ data }]}
      type="area"
      height={40}
      width={100}
    />
  );
}

export default function KpiCards({ dashboard }: KpiCardsProps) {
  const momPositive = (dashboard.mom_change_percent ?? 0) >= 0;
  const goalPercent = Math.min(dashboard.goal_progress_percent ?? 0, 100);

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
      {/* Total Income */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">Total Income</p>
              <p className="text-2xl font-bold">{formatCurrency(dashboard.current_month_total)}</p>
            </div>
            <DollarSign className="h-5 w-5 text-sky-500" />
          </div>
          <div className="mt-2">
            <SparklineChart data={dashboard.sparkline} />
          </div>
        </CardContent>
      </Card>

      {/* vs Goal */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">vs Goal</p>
              <p className="text-2xl font-bold">
                {dashboard.goal_progress_percent !== null
                  ? formatPercentage(dashboard.goal_progress_percent)
                  : "N/A"}
              </p>
            </div>
            <Target className="h-5 w-5 text-violet-500" />
          </div>
          {dashboard.goal_total > 0 && (
            <div className="mt-3 space-y-1">
              <Progress value={goalPercent} className="h-2" />
              <p className="text-xs text-muted-foreground">
                {formatCurrency(dashboard.current_month_total)} of{" "}
                {formatCurrency(dashboard.goal_total)}
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* MoM Change */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">MoM Change</p>
              <p
                className={cn(
                  "text-2xl font-bold",
                  dashboard.mom_change_percent === null
                    ? ""
                    : momPositive
                      ? "text-emerald-600"
                      : "text-red-600"
                )}
              >
                {dashboard.mom_change_percent !== null
                  ? formatPercentage(dashboard.mom_change_percent, true)
                  : "N/A"}
              </p>
            </div>
            {momPositive ? (
              <TrendingUp className="h-5 w-5 text-emerald-500" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-500" />
            )}
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            vs {formatCurrency(dashboard.previous_month_total)} last month
          </p>
        </CardContent>
      </Card>

      {/* YTD Total */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">YTD Total</p>
              <p className="text-2xl font-bold">{formatCurrency(dashboard.ytd_total)}</p>
            </div>
            <Calendar className="h-5 w-5 text-amber-500" />
          </div>
          <div className="mt-2">
            <SparklineChart data={dashboard.sparkline} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
