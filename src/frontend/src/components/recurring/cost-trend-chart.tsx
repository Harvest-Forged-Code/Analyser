import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import ChartCard from "@/components/chart-card";
import { formatCurrency } from "@/lib/utils";
import { COLOR_PRIMARY } from "@/lib/constants";

interface CostTrendChartProps {
  trendData: Record<string, number>[];
}

export default function RecurringCostTrendChart({
  trendData,
}: CostTrendChartProps) {
  if (trendData.length === 0) {
    return null;
  }

  return (
    <ChartCard
      title="Cost Trend"
      description="Monthly recurring cost over time"
    >
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart
          data={trendData}
          margin={{ left: 10, right: 10, top: 5, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            className="stroke-muted"
          />
          <XAxis dataKey="month" />
          <YAxis tickFormatter={(v: number) => formatCurrency(v)} />
          <Tooltip
            formatter={(value?: number) => formatCurrency(value ?? 0)}
          />
          <Area
            type="monotone"
            dataKey="cost"
            stroke={COLOR_PRIMARY}
            fill={COLOR_PRIMARY}
            fillOpacity={0.2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
