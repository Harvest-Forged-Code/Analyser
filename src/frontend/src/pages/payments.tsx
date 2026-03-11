import { useState, useEffect } from "react";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
import EmptyState from "@/components/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
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
import {
  useRecurringTransactions,
  useRecurringDetections,
  useRecurringSummary,
  useRecurringAnomalies,
  useAddRecurring,
  useUpdateRecurring,
  useDeleteRecurring,
  useResolveAnomaly,
} from "@/api/hooks/use-recurring";
import type {
  RecurringTransaction,
  RecurringDetection,
  UpdateRecurringRequest,
} from "@/api/types";
import RecurringKpiCards from "@/components/recurring/recurring-kpi-cards";
import RecurringCategoryChart from "@/components/recurring/category-chart";
import RecurringCostTrendChart from "@/components/recurring/cost-trend-chart";
import DetectionResults from "@/components/recurring/detection-results";
import RecurringTable from "@/components/recurring/recurring-table";
import AddRecurringDialog from "@/components/recurring/add-recurring-dialog";
import EditRecurringDialog from "@/components/recurring/edit-recurring-dialog";
import AnomaliesTable from "@/components/recurring/anomalies-table";
import { formatCurrency, formatPercentage, findDefaultMonth } from "@/lib/utils";
import { COLOR_POSITIVE, COLOR_NEGATIVE, COLOR_WARNING } from "@/lib/constants";
import {
  CheckCircle2,
  Clock,
  CreditCard,
  AlertCircle,
  Percent,
  DollarSign,
  Plus,
  Search,
} from "lucide-react";

function ReconciliationTab() {
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
  } = usePaymentReconciliation(selectedPeriod);

  if (periodsLoading || dataLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
        <Skeleton className="h-[300px]" />
      </div>
    );
  }

  if (!periods || periods.length === 0) {
    return (
      <EmptyState
        icon={<CreditCard className="h-12 w-12" />}
        title="No payment data"
        description="Upload statements with payment transactions to see reconciliation"
      />
    );
  }

  const matchedCount = data?.matched_pairs?.length ?? 0;
  const pendingCount = data?.pending_payments?.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
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

export default function PaymentsPage() {
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] =
    useState<RecurringTransaction | null>(null);

  // Recurring queries
  const {
    data: transactions,
    isLoading: txLoading,
    error: txError,
    refetch: refetchTx,
  } = useRecurringTransactions(true);
  const { data: summary, isLoading: summaryLoading } = useRecurringSummary();
  const { data: anomalies } = useRecurringAnomalies();
  const {
    data: detections,
    isFetching: detectLoading,
    refetch: runDetection,
  } = useRecurringDetections();

  // Recurring mutations
  const addMutation = useAddRecurring();
  const updateMutation = useUpdateRecurring();
  const deleteMutation = useDeleteRecurring();
  const resolveMutation = useResolveAnomaly();

  const handleConfirmDetection = (detection: RecurringDetection) => {
    addMutation.mutate({
      description: detection.description,
      expected_amount: detection.expected_amount,
      frequency: detection.frequency,
      category: detection.category,
      sub_category: detection.sub_category,
    });
  };

  const handleEdit = (transaction: RecurringTransaction) => {
    setEditingTransaction(transaction);
    setEditDialogOpen(true);
  };

  const handleEditSubmit = (id: number, data: UpdateRecurringRequest) => {
    updateMutation.mutate({ id, data });
    setEditDialogOpen(false);
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const handleAddSubmit = (data: {
    description: string;
    expected_amount: number;
    frequency: string;
    category: string;
    sub_category: string;
    is_expected: boolean;
  }) => {
    addMutation.mutate(data);
    setAddDialogOpen(false);
  };

  const handleResolve = (anomalyId: number) => {
    resolveMutation.mutate(anomalyId);
  };

  // Error state
  if (txError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payments"
          description="Manage recurring subscriptions and payment reconciliation"
        />
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-semibold">Failed to load payments</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            {txError instanceof Error ? txError.message : "An error occurred"}
          </p>
          <Button onClick={() => refetchTx()} className="mt-4">
            Retry
          </Button>
        </div>
      </div>
    );
  }

  // Loading state
  if (txLoading || summaryLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Payments"
          description="Manage recurring subscriptions and payment reconciliation"
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[120px]" />
          ))}
        </div>
        <Skeleton className="h-[400px]" />
      </div>
    );
  }

  const anomalyCount = anomalies?.filter((a) => !a.resolved).length ?? 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Payments"
        description="Manage recurring subscriptions and payment reconciliation"
      />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
          <TabsTrigger value="reconciliation">Reconciliation</TabsTrigger>
          <TabsTrigger value="anomalies">
            Anomalies
            {anomalyCount > 0 && (
              <span className="ml-1.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-[10px] font-medium text-destructive-foreground">
                {anomalyCount}
              </span>
            )}
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {summary && (
            <>
              <RecurringKpiCards
                summary={summary}
                anomalyCount={anomalyCount}
              />
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RecurringCategoryChart byCategory={summary.by_category} />
                <RecurringCostTrendChart trendData={summary.trend_data} />
              </div>
            </>
          )}
        </TabsContent>

        {/* Subscriptions Tab */}
        <TabsContent value="subscriptions" className="space-y-6">
          <div className="flex items-center gap-2">
            <Button
              onClick={() => runDetection()}
              disabled={detectLoading}
              variant="outline"
            >
              <Search className="h-4 w-4 mr-2" />
              {detectLoading ? "Scanning..." : "Scan Transactions"}
            </Button>
            <Button onClick={() => setAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Recurring
            </Button>
          </div>

          {detections && detections.length > 0 && (
            <DetectionResults
              detections={detections}
              onConfirm={handleConfirmDetection}
              onDismiss={() => {}}
            />
          )}

          <RecurringTable
            transactions={transactions ?? []}
            onEdit={handleEdit}
            onDelete={handleDelete}
          />
        </TabsContent>

        {/* Reconciliation Tab */}
        <TabsContent value="reconciliation" className="space-y-6">
          <ReconciliationTab />
        </TabsContent>

        {/* Anomalies Tab */}
        <TabsContent value="anomalies" className="space-y-6">
          <AnomaliesTable
            anomalies={anomalies?.filter((a) => !a.resolved) ?? []}
            onResolve={handleResolve}
          />
        </TabsContent>
      </Tabs>

      <AddRecurringDialog
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
        onSubmit={handleAddSubmit}
      />
      <EditRecurringDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        transaction={editingTransaction}
        onSubmit={handleEditSubmit}
      />
    </div>
  );
}
