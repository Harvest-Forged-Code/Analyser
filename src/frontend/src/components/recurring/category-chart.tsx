import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts";
import ChartCard from "@/components/chart-card";
import { formatCurrency } from "@/lib/utils";
import { EXPENSE_CHART_COLORS } from "@/lib/constants";

interface CategoryChartProps {
  byCategory: Record<string, number>;
}

export default function RecurringCategoryChart({
  byCategory,
}: CategoryChartProps) {
  const data = Object.entries(byCategory)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);

  if (data.length === 0) {
    return null;
  }

  return (
    <ChartCard
      title="Cost by Category"
      description="Monthly recurring cost breakdown"
    >
      <ResponsiveContainer
        width="100%"
        height={Math.max(200, data.length * 40)}
      >
        <BarChart
          data={data}
          layout="vertical"
          margin={{ left: 80, right: 20, top: 5, bottom: 5 }}
        >
          <XAxis
            type="number"
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <YAxis type="category" dataKey="name" width={80} />
          <Tooltip
            formatter={(value?: number) => formatCurrency(value ?? 0)}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((_, index) => (
              <Cell
                key={index}
                fill={
                  EXPENSE_CHART_COLORS[
                    index % EXPENSE_CHART_COLORS.length
                  ]
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
