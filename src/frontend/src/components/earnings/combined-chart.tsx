import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import ChartCard from "@/components/chart-card";
import type { EarningsMonthTrend, EarningsRow } from "@/api/types";
import { COLOR_INCOME, COLOR_PRIMARY } from "@/lib/constants";

interface CombinedChartProps {
  trend: EarningsMonthTrend[];
  monthRows?: EarningsRow[];
}

export default function CombinedChart({ trend, monthRows }: CombinedChartProps) {
  const categories = trend.map((t) => t.label);
  const incomeSeries = trend.map((t) => t.total);

  const goalSeries = trend.map(() => {
    if (!monthRows) return 0;
    return monthRows.reduce((sum, row) => sum + row.expected, 0);
  });

  const hasGoals = goalSeries.some((v) => v > 0);

  const series: ApexOptions["series"] = [
    {
      name: "Income",
      type: "area",
      data: incomeSeries,
    },
    ...(hasGoals
      ? [
          {
            name: "Goal",
            type: "bar" as const,
            data: goalSeries,
          },
        ]
      : []),
  ];

  const options: ApexOptions = {
    chart: {
      type: "line",
      toolbar: { show: false },
      zoom: { enabled: false },
      fontFamily: "inherit",
    },
    stroke: {
      width: [3, 0],
      curve: "smooth",
    },
    fill: {
      type: ["gradient", "solid"],
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.4,
        opacityTo: 0.05,
        stops: [0, 90, 100],
      },
      opacity: [1, 0.3],
    },
    colors: [COLOR_INCOME, COLOR_PRIMARY],
    plotOptions: {
      bar: {
        columnWidth: "50%",
        borderRadius: 4,
      },
    },
    xaxis: {
      categories,
      labels: {
        style: { fontSize: "12px" },
      },
    },
    yaxis: {
      labels: {
        formatter: (val: number) => {
          if (val >= 1000) return `$${(val / 1000).toFixed(0)}k`;
          return `$${val.toFixed(0)}`;
        },
      },
    },
    tooltip: {
      y: {
        formatter: (val: number) =>
          `$${val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
      },
    },
    legend: {
      position: "top",
      horizontalAlign: "right",
    },
    dataLabels: { enabled: false },
    grid: {
      borderColor: "hsl(var(--border))",
      strokeDashArray: 4,
    },
  };

  return (
    <ChartCard title="Income Trend" description="Monthly income with goal comparison">
      <Chart options={options} series={series} type="line" height={350} />
    </ChartCard>
  );
}
