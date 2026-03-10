import { CheckCircle2, ShieldAlert } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import EmptyState from "@/components/empty-state";
import { formatCurrency } from "@/lib/utils";
import type { RecurringAnomaly } from "@/api/types";

interface AnomaliesTableProps {
  anomalies: RecurringAnomaly[];
  onResolve: (anomalyId: number) => void;
}

function formatAnomalyType(type: string): string {
  return type
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function SeverityBadge({ severity }: { severity: string }) {
  switch (severity.toLowerCase()) {
    case "critical":
      return <Badge variant="destructive">Critical</Badge>;
    case "warning":
      return (
        <Badge className="bg-amber-500 hover:bg-amber-600">Warning</Badge>
      );
    case "info":
      return <Badge variant="secondary">Info</Badge>;
    default:
      return <Badge variant="outline">{severity}</Badge>;
  }
}

export default function AnomaliesTable({
  anomalies,
  onResolve,
}: AnomaliesTableProps) {
  if (anomalies.length === 0) {
    return (
      <EmptyState
        icon={<ShieldAlert className="h-12 w-12" />}
        title="All Clear!"
        description="No anomalies detected in your recurring payments."
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Anomalies</span>
          <Badge variant="outline">{anomalies.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Expected Date</TableHead>
              <TableHead>Actual Date</TableHead>
              <TableHead>Amount Difference</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Message</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {anomalies.map((anomaly) => {
              const amountDiff =
                anomaly.expected_amount != null &&
                anomaly.actual_amount != null
                  ? anomaly.actual_amount - anomaly.expected_amount
                  : null;

              return (
                <TableRow key={anomaly.id ?? anomaly.recurring_id}>
                  <TableCell className="font-medium">
                    {formatAnomalyType(anomaly.anomaly_type)}
                  </TableCell>
                  <TableCell>
                    {anomaly.expected_date ?? "-"}
                  </TableCell>
                  <TableCell>
                    {anomaly.actual_date ?? "-"}
                  </TableCell>
                  <TableCell>
                    {amountDiff != null ? formatCurrency(amountDiff) : "-"}
                  </TableCell>
                  <TableCell>
                    <SeverityBadge severity={anomaly.severity} />
                  </TableCell>
                  <TableCell className="max-w-[300px] truncate">
                    {anomaly.message}
                  </TableCell>
                  <TableCell>
                    {!anomaly.resolved && anomaly.id != null && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onResolve(anomaly.id!)}
                      >
                        <CheckCircle2 className="mr-1 h-4 w-4" />
                        Resolve
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
