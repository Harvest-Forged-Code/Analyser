import { useState, useMemo } from "react";
import { CreditCard, DollarSign, AlertTriangle } from "lucide-react";
import { usePaymentMonths, usePaymentData } from "@/api/hooks/use-payments";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { formatCurrency, formatDate, cn } from "@/lib/utils";
import { COLOR_POSITIVE, COLOR_NEGATIVE } from "@/lib/constants";

export default function PaymentsPage() {
  const { data: months, isLoading: monthsLoading } = usePaymentMonths();
  const [selectedMonth, setSelectedMonth] = useState<string | undefined>(undefined);

  // Auto-select first month
  useMemo(() => {
    if (months && months.length > 0 && !selectedMonth) {
      setSelectedMonth(months[0]);
    }
  }, [months, selectedMonth]);

  const { data: paymentData, isLoading: dataLoading } = usePaymentData(selectedMonth);

  // Column definitions for payments made
  const paymentsMadeColumns: ColumnDef<Record<string, unknown>>[] = useMemo(() => {
    if (!paymentData?.payments_made || paymentData.payments_made.length === 0) return [];
    const sample = paymentData.payments_made[0];
    if (!sample) return [];
    const keys = Object.keys(sample);

    return keys.map((key) => ({
      accessorKey: key,
      header: () => (
        <div className={key.toLowerCase().includes("amount") || key.toLowerCase().includes("date") ? "text-right" : ""}>
          {key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
        </div>
      ),
      cell: ({ row }) => {
        const value = row.getValue(key);
        if (key.toLowerCase().includes("amount") && typeof value === "number") {
          return <div className="text-right font-medium">{formatCurrency(value)}</div>;
        }
        if (key.toLowerCase().includes("date") && typeof value === "string") {
          return <div className="text-right">{formatDate(value)}</div>;
        }
        return <div>{String(value)}</div>;
      },
    }));
  }, [paymentData?.payments_made]);

  // Column definitions for payment confirmations
  const confirmationsColumns: ColumnDef<Record<string, unknown>>[] = useMemo(() => {
    if (!paymentData?.payment_confirmations || paymentData.payment_confirmations.length === 0) return [];
    const sample = paymentData.payment_confirmations[0];
    if (!sample) return [];
    const keys = Object.keys(sample);

    return keys.map((key) => ({
      accessorKey: key,
      header: () => (
        <div className={key.toLowerCase().includes("amount") || key.toLowerCase().includes("date") ? "text-right" : ""}>
          {key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
        </div>
      ),
      cell: ({ row }) => {
        const value = row.getValue(key);
        if (key.toLowerCase().includes("amount") && typeof value === "number") {
          return <div className="text-right font-medium">{formatCurrency(value)}</div>;
        }
        if (key.toLowerCase().includes("date") && typeof value === "string") {
          return <div className="text-right">{formatDate(value)}</div>;
        }
        return <div>{String(value)}</div>;
      },
    }));
  }, [paymentData?.payment_confirmations]);

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
          title="Payments Reconciliation"
          description="Match payments with confirmations"
        />
        <EmptyState
          icon={<CreditCard />}
          title="No payment data"
          description="Upload transaction data to start reconciling payments."
        />
      </div>
    );
  }

  const difference = paymentData?.difference ?? 0;
  const isReconciled = difference === 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments Reconciliation"
        description="Match payments with confirmations"
      />

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

      {dataLoading ? (
        <Skeleton className="h-96 w-full" />
      ) : paymentData ? (
        <>
          <div className="grid gap-4 md:grid-cols-3">
            <KpiCard
              title="Payments Made"
              value={formatCurrency(paymentData.total_payments_made)}
              description={`${paymentData.payments_made.length} transactions`}
              icon={<DollarSign className="h-5 w-5" />}
            />
            <KpiCard
              title="Confirmations"
              value={formatCurrency(paymentData.total_payment_confirmations)}
              description={`${paymentData.payment_confirmations.length} confirmations`}
              icon={<CreditCard className="h-5 w-5" />}
            />
            <KpiCard
              title="Difference"
              value={formatCurrency(Math.abs(difference))}
              description={isReconciled ? "Fully reconciled" : "Needs attention"}
              icon={
                <AlertTriangle
                  className="h-5 w-5"
                  style={{ color: isReconciled ? COLOR_POSITIVE : COLOR_NEGATIVE }}
                />
              }
              className={cn(
                isReconciled ? "border-green-200 bg-green-50" : "border-red-200 bg-red-50"
              )}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Payments Made</CardTitle>
              </CardHeader>
              <CardContent>
                {paymentData.payments_made.length > 0 ? (
                  <DataTable
                    columns={paymentsMadeColumns}
                    data={paymentData.payments_made}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No payments made this month
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Payment Confirmations</CardTitle>
              </CardHeader>
              <CardContent>
                {paymentData.payment_confirmations.length > 0 ? (
                  <DataTable
                    columns={confirmationsColumns}
                    data={paymentData.payment_confirmations}
                  />
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No confirmations this month
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      ) : (
        <EmptyState
          icon={<CreditCard />}
          title="No data for selected month"
          description="Try selecting a different month."
        />
      )}
    </div>
  );
}
