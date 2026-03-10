import { useState } from "react";
import PageHeader from "@/components/page-header";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { AlertCircle, Plus, Search } from "lucide-react";
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

export default function RecurringPage() {
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingTransaction, setEditingTransaction] =
    useState<RecurringTransaction | null>(null);

  // Queries
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

  // Mutations
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

  if (txError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Recurring Payments"
          description="Track and manage recurring transactions"
        />
        <div className="flex flex-col items-center justify-center py-12">
          <AlertCircle className="h-12 w-12 text-destructive mb-4" />
          <h3 className="text-lg font-semibold">
            Failed to load recurring payments
          </h3>
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

  if (txLoading || summaryLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Recurring Payments"
          description="Track and manage recurring transactions"
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
        title="Recurring Payments"
        description="Track and manage recurring transactions"
      />

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
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
