import { useState, useEffect } from "react";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import EmptyState from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { usePaymentPeriods, usePaymentReconciliation } from "@/api/hooks/use-payments";
import { formatCurrency, formatPercentage, findDefaultMonth } from "@/lib/utils";
import { COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING } from "@/lib/constants";
import {
  CheckCircle2,
  Clock,
  CreditCard,
  AlertCircle,
  Percent,
  DollarSign,
} from "lucide-react";

export default function PaymentsPage() {
  const { data: periods, isLoading: periodsLoading } = usePaymentPeriods();
  const [selectedPeriod, setSelectedPeriod] = useState<string | undefined>();

  useEffect(() => {
    if (periods && periods.length > 0 && !selectedPeriod) {
      setSelectedPeriod(findDefaultMonth(periods));
    }
  }, [periods, selectedPeriod]);

  const {
    data,
    isLoading: dataLoading,
    error,
    refetch,
  } = usePaymentReconciliation(selectedPeriod);

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payment Reconciliation"
          description="Match credit card payments across accounts"
        />
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-semibold">Failed to load payments</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {error instanceof Error ? error.message : "An error occurred"}
          </p>
          <Button onClick={() => refetch()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (periodsLoading || dataLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payment Reconciliation"
          description="Match credit card payments across accounts"
        />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
        <Skeleton className="h-[300px]" />
      </div>
    );
  }

  // Empty state
  if (!periods || periods.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payment Reconciliation"
          description="Match credit card payments across accounts"
        />
        <EmptyState
          icon={<CreditCard className="h-12 w-12" />}
          title="No payment data"
          description="Upload statements with payment transactions to see reconciliation"
        />
      </div>
    );
  }

  const matchedCount = data?.matched_pairs?.length ?? 0;
  const pendingCount = data?.pending_payments?.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <PageHeader
          title="Payment Reconciliation"
          description="Match credit card payments across accounts"
        />
        <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            {periods.map((p) => (
              <SelectItem key={p} value={p}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KpiCard
          title="Total Matched"
          value={formatCurrency(data?.total_matched ?? 0)}
          description={`${matchedCount} payment${matchedCount !== 1 ? "s" : ""} reconciled`}
          icon={<DollarSign className="h-6 w-6" style={{ color: COLOR_POSITIVE }} />}
        />
        <KpiCard
          title="Total Pending"
          value={formatCurrency(data?.total_pending ?? 0)}
          description={`${pendingCount} payment${pendingCount !== 1 ? "s" : ""} unmatched`}
          icon={<Clock className="h-6 w-6" style={{ color: COLOR_WARNING }} />}
        />
        <KpiCard
          title="Match Rate"
          value={formatPercentage(data?.match_rate ?? 0)}
          description="Of payments successfully matched"
          icon={<Percent className="h-6 w-6" style={{ color: COLOR_POSITIVE }} />}
        />
      </div>

      {/* Matched Pairs Table */}
      {matchedCount > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" style={{ color: COLOR_POSITIVE }} />
              Matched Payments ({matchedCount})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Source Account</TableHead>
                  <TableHead>Destination Account</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Payment Date</TableHead>
                  <TableHead>Confirmation Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.matched_pairs.map((pair, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">
                      {pair.source_account}
                    </TableCell>
                    <TableCell>{pair.destination_account ?? "-"}</TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(pair.amount)}
                    </TableCell>
                    <TableCell>{pair.payment_date}</TableCell>
                    <TableCell>{pair.confirmation_date ?? "-"}</TableCell>
                    <TableCell>
                      <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600">
                        Matched
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Pending Payments Table */}
      {pendingCount > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" style={{ color: COLOR_NEGATIVE }} />
              Pending Payments ({pendingCount})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Account</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data?.pending_payments.map((pair, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">
                      {pair.source_account}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(pair.amount)}
                    </TableCell>
                    <TableCell>{pair.payment_date}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-amber-500 border-amber-500">
                        Pending
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}

      {/* Empty data state for selected period */}
      {matchedCount === 0 && pendingCount === 0 && data && (
        <EmptyState
          icon={<CreditCard className="h-12 w-12" />}
          title="No payments for this period"
          description="No payment transactions found for the selected month"
        />
      )}
    </div>
  );
}
