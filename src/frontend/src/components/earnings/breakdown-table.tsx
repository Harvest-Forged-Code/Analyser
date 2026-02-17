import Chart from "react-apexcharts";
import type { ApexOptions } from "apexcharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatPercentage, cn } from "@/lib/utils";
import type { EarningsRow, EarningsSourceTrend } from "@/api/types";
import { COLOR_INCOME } from "@/lib/constants";

interface BreakdownTableProps {
  rows: EarningsRow[];
  sourceTrend?: EarningsSourceTrend[];
  onRowClick: (subCategory: string) => void;
}

function MiniSparkline({ data }: { data: number[] }) {
  const options: ApexOptions = {
    chart: {
      type: "line",
      sparkline: { enabled: true },
      animations: { enabled: false },
    },
    stroke: { curve: "smooth", width: 2 },
    colors: [COLOR_INCOME],
    tooltip: { enabled: false },
  };

  return (
    <Chart
      options={options}
      series={[{ data }]}
      type="line"
      height={25}
      width={80}
    />
  );
}

export default function BreakdownTable({
  rows,
  sourceTrend,
  onRowClick,
}: BreakdownTableProps) {
  const trendMap = new Map(
    sourceTrend?.map((st) => [st.sub_category, st.months.map((m) => m.total)]) ?? [],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Income Breakdown</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Source</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead className="text-right">% Total</TableHead>
                <TableHead className="text-right">vs Goal</TableHead>
                <TableHead className="text-right">Trend</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length > 0 ? (
                rows.map((row) => {
                  const sparkData = trendMap.get(row.sub_category);
                  return (
                    <TableRow
                      key={row.sub_category}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => onRowClick(row.sub_category)}
                    >
                      <TableCell className="font-medium">{row.sub_category}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(row.actual)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatPercentage(row.percent_of_total)}
                      </TableCell>
                      <TableCell className="text-right">
                        {row.expected === 0 ? (
                          <span className="text-muted-foreground">--</span>
                        ) : (
                          <span
                            className={cn(
                              "font-medium",
                              row.diff > 0
                                ? "text-emerald-600"
                                : row.diff < 0
                                  ? "text-red-600"
                                  : "",
                            )}
                          >
                            {formatCurrency(row.diff, true)}
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end">
                          {sparkData && sparkData.length > 0 ? (
                            <MiniSparkline data={sparkData} />
                          ) : (
                            <span className="text-muted-foreground">--</span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    No income sources found.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
