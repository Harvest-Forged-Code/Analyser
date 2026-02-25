import React from "react";
import { Target, Plus, ArrowLeft } from "lucide-react";
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import {
  useSetBudget,
  useDeleteBudget,
  useSetEarningsGoal,
  useDeleteEarningsGoal,
  useBudgetGoalsSummary,
  useEarningsGoalsSummary,
  useBudgetProgress,
  useProgressSummary,
  useCategoryProgressHistory,
  useBudgetGoalsForYear,
  useEarningsGoalsForYear,
  useSetBudgetForYear,
  useSetEarningsGoalForYear,
} from "@/api/hooks/use-budget-goals";
import { useSubCategories, useCategories } from "@/api/hooks/use-mappers";
import { useEarningsMonths } from "@/api/hooks/use-earnings";
import PageHeader from "@/components/page-header";
import EmptyState from "@/components/empty-state";
import GoalsSpreadsheet from "@/components/goals-spreadsheet";
import AddGoalDialog from "@/components/add-goal-dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency, formatPercentage } from "@/lib/utils";

const CURRENT_YEAR = new Date().getFullYear();
const YEAR_OPTIONS = Array.from({ length: 5 }, (_, i) => CURRENT_YEAR - 2 + i);

export default function BudgetGoalsPage() {
  const [activeTab, setActiveTab] = React.useState("budget-goals");

  // Year selectors for spreadsheet tabs
  const [budgetYear, setBudgetYear] = React.useState(CURRENT_YEAR);
  const [earningsYear, setEarningsYear] = React.useState(CURRENT_YEAR);

  // Add dialogs
  const [budgetDialogOpen, setBudgetDialogOpen] = React.useState(false);
  const [earningsDialogOpen, setEarningsDialogOpen] = React.useState(false);

  // Progress tab state (unchanged)
  const [selectedMonth, setSelectedMonth] = React.useState<string>("");
  const [progressView, setProgressView] = React.useState<"overview" | "detail">("overview");
  const [selectedCategory, setSelectedCategory] = React.useState<string | null>(null);

  // Spreadsheet queries
  const { data: budgetYearGrid, isLoading: budgetYearLoading } = useBudgetGoalsForYear(budgetYear);
  const { data: earningsYearGrid, isLoading: earningsYearLoading } = useEarningsGoalsForYear(earningsYear);
  const { data: budgetGoalsSummary } = useBudgetGoalsSummary();
  const { data: earningsGoalsSummary } = useEarningsGoalsSummary();

  // Category dropdown data
  const { data: subCategories } = useSubCategories();
  const { data: categories } = useCategories();

  // Progress tab queries (unchanged)
  const { data: availableMonths } = useEarningsMonths();
  const { data: budgetProgress, isLoading: progressLoading } = useBudgetProgress(selectedMonth);
  const { data: progressSummary } = useProgressSummary(selectedMonth);
  const { data: categoryHistory } = useCategoryProgressHistory(selectedCategory ?? undefined);

  // Mutations for inline editing
  const setBudgetMutation = useSetBudget();
  const setEarningsGoalMutation = useSetEarningsGoal();

  // Mutations for deletion
  const deleteBudgetMutation = useDeleteBudget();
  const deleteEarningsGoalMutation = useDeleteEarningsGoal();

  // Mutations for adding new categories
  const setBudgetForYearMutation = useSetBudgetForYear();
  const setEarningsForYearMutation = useSetEarningsGoalForYear();

  // Set default selected month for progress tab
  React.useEffect(() => {
    if (availableMonths && availableMonths.length > 0 && !selectedMonth) {
      const firstMonth = availableMonths[0];
      if (firstMonth) setSelectedMonth(firstMonth);
    }
  }, [availableMonths, selectedMonth]);

  // Inline edit handlers
  const handleBudgetCellEdit = (category: string, yearMonth: string, value: number) => {
    setBudgetMutation.mutate({
      category,
      monthly_limit: value,
      year_month: yearMonth,
    });
  };

  const handleEarningsCellEdit = (subCategory: string, yearMonth: string, value: number) => {
    setEarningsGoalMutation.mutate({
      sub_category: subCategory,
      expected_amount: value,
      year_month: yearMonth,
    });
  };

  // Delete handlers
  const handleDeleteBudgetCategory = (category: string) => {
    if (!confirm(`Delete all budget goals for "${category}"?`)) return;
    deleteBudgetMutation.mutate(category);
  };

  const handleDeleteEarningsCategory = (subCategory: string) => {
    if (!confirm(`Delete all earnings goals for "${subCategory}"?`)) return;
    deleteEarningsGoalMutation.mutate(subCategory);
  };

  // Add handlers (create 12 monthly entries)
  const handleAddBudgetCategory = (category: string, amount: number) => {
    setBudgetForYearMutation.mutate(
      { category, monthly_limit: amount, year: budgetYear },
      { onSuccess: () => setBudgetDialogOpen(false) },
    );
  };

  const handleAddEarningsCategory = (subCategory: string, amount: number) => {
    setEarningsForYearMutation.mutate(
      { sub_category: subCategory, expected_amount: amount, year: earningsYear },
      { onSuccess: () => setEarningsDialogOpen(false) },
    );
  };

  // Progress tab helpers (unchanged)
  const getGaugeColor = (percentage: number): string => {
    if (percentage >= 100) return "#ef4444";
    if (percentage >= 75) return "#eab308";
    return "#22c55e";
  };

  const getStatusVariant = (
    status: string,
  ): "default" | "destructive" | "outline" | "secondary" => {
    if (status === "over") return "destructive";
    if (status === "warning") return "secondary";
    return "default";
  };

  const getStatusLabel = (status: string): string => {
    if (status === "over") return "Over Budget";
    if (status === "warning") return "Warning";
    return "On Track";
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Budget Goals" description="Set and track spending limits" />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="budget-goals">Budget Goals</TabsTrigger>
          <TabsTrigger value="earnings-goals">Earnings Goals</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
        </TabsList>

        {/* ── Budget Goals Tab ── */}
        <TabsContent value="budget-goals" className="space-y-4">
          <div className="grid grid-cols-2 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Budget</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {budgetGoalsSummary ? formatCurrency(budgetGoalsSummary.total_monthly_budget) : "—"}
                </p>
                <p className="text-xs text-muted-foreground">per month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Categories</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {budgetGoalsSummary ? budgetGoalsSummary.categories_tracked : "—"}
                </p>
                <p className="text-xs text-muted-foreground">categories tracked</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Label>Year:</Label>
              <Select value={budgetYear.toString()} onValueChange={(v) => setBudgetYear(Number(v))}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {YEAR_OPTIONS.map((y) => (
                    <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setBudgetDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />Add Category
            </Button>
          </div>

          {budgetYearGrid && Object.keys(budgetYearGrid).length === 0 && !budgetYearLoading ? (
            <EmptyState
              icon={<Target className="h-12 w-12" />}
              title="No budget goals"
              description="Add your first budget category to start tracking spending limits"
            />
          ) : (
            <GoalsSpreadsheet
              data={budgetYearGrid ?? {}}
              year={budgetYear}
              isLoading={budgetYearLoading}
              onCellEdit={handleBudgetCellEdit}
              onDeleteCategory={handleDeleteBudgetCategory}
              categoryLabel="Category"
            />
          )}

          <AddGoalDialog
            open={budgetDialogOpen}
            onOpenChange={setBudgetDialogOpen}
            categories={subCategories ?? []}
            year={budgetYear}
            onAdd={handleAddBudgetCategory}
            categoryLabel="Category"
            amountLabel="Monthly Limit"
            existingCategories={Object.keys(budgetYearGrid ?? {})}
            isPending={setBudgetForYearMutation.isPending}
          />
        </TabsContent>

        {/* ── Earnings Goals Tab ── */}
        <TabsContent value="earnings-goals" className="space-y-4">
          <div className="grid grid-cols-2 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Total Expected Earnings</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {earningsGoalsSummary ? formatCurrency(earningsGoalsSummary.total_expected_earnings) : "—"}
                </p>
                <p className="text-xs text-muted-foreground">per month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">Sub-categories</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {earningsGoalsSummary ? earningsGoalsSummary.sub_categories_tracked : "—"}
                </p>
                <p className="text-xs text-muted-foreground">sub-categories tracked</p>
              </CardContent>
            </Card>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Label>Year:</Label>
              <Select value={earningsYear.toString()} onValueChange={(v) => setEarningsYear(Number(v))}>
                <SelectTrigger className="w-28">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {YEAR_OPTIONS.map((y) => (
                    <SelectItem key={y} value={y.toString()}>{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => setEarningsDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />Add Sub-Category
            </Button>
          </div>

          {earningsYearGrid && Object.keys(earningsYearGrid).length === 0 && !earningsYearLoading ? (
            <EmptyState
              icon={<Target className="h-12 w-12" />}
              title="No earnings goals"
              description="Add your first earnings sub-category to start tracking income targets"
            />
          ) : (
            <GoalsSpreadsheet
              data={earningsYearGrid ?? {}}
              year={earningsYear}
              isLoading={earningsYearLoading}
              onCellEdit={handleEarningsCellEdit}
              onDeleteCategory={handleDeleteEarningsCategory}
              categoryLabel="Sub-Category"
            />
          )}

          <AddGoalDialog
            open={earningsDialogOpen}
            onOpenChange={setEarningsDialogOpen}
            categories={categories ?? []}
            year={earningsYear}
            onAdd={handleAddEarningsCategory}
            categoryLabel="Sub-Category"
            amountLabel="Expected Amount"
            existingCategories={Object.keys(earningsYearGrid ?? {})}
            isPending={setEarningsForYearMutation.isPending}
          />
        </TabsContent>

        {/* ── Progress Tab (UNCHANGED) ── */}
        <TabsContent value="progress" className="space-y-4">
          {progressView === "detail" && selectedCategory ? (
            /* Detail View */
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <Button variant="ghost" onClick={() => { setProgressView("overview"); setSelectedCategory(null); }}>
                  <ArrowLeft className="h-4 w-4 mr-2" />Back to Overview
                </Button>
                <h2 className="text-lg font-semibold">{selectedCategory}</h2>
                {categoryHistory && categoryHistory.length > 0 && (
                  <Badge variant={getStatusVariant(categoryHistory[categoryHistory.length - 1]?.status ?? "under")}>
                    {getStatusLabel(categoryHistory[categoryHistory.length - 1]?.status ?? "under")}
                  </Badge>
                )}
              </div>

              {!categoryHistory || categoryHistory.length === 0 ? (
                <EmptyState icon={<Target className="h-12 w-12" />} title="No history available" description="No budget data found for this category" />
              ) : (
                <>
                  <Card>
                    <CardHeader><CardTitle className="text-base">12-Month History</CardTitle></CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <ComposedChart data={categoryHistory}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="year_month" tick={{ fontSize: 12 }} />
                          <YAxis tickFormatter={(v: number) => `$${v.toFixed(0)}`} tick={{ fontSize: 12 }} />
                          <Tooltip formatter={(value: number, name: string) => [formatCurrency(value), name === "spent" ? "Spent" : "Budget"]} />
                          <Line type="monotone" dataKey="spent" stroke="#3b82f6" name="spent" strokeWidth={2} dot={{ r: 4 }} />
                          <Line type="monotone" dataKey="budget_limit" stroke="#94a3b8" name="budget_limit" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader><CardTitle className="text-base">Monthly Breakdown</CardTitle></CardHeader>
                    <CardContent>
                      <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-muted">
                            <tr>
                              <th className="text-left p-3">Month</th>
                              <th className="text-right p-3">Budget</th>
                              <th className="text-right p-3">Spent</th>
                              <th className="text-right p-3">Remaining</th>
                              <th className="text-center p-3">Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y">
                            {categoryHistory.map((point) => (
                              <tr key={point.year_month}>
                                <td className="p-3 font-medium">{point.year_month}</td>
                                <td className="p-3 text-right font-mono">{formatCurrency(point.budget_limit)}</td>
                                <td className="p-3 text-right font-mono">{formatCurrency(point.spent)}</td>
                                <td className={`p-3 text-right font-mono font-semibold ${point.remaining >= 0 ? "text-green-600" : "text-red-600"}`}>
                                  {formatCurrency(point.remaining)}
                                </td>
                                <td className="p-3 text-center">
                                  <Badge variant={getStatusVariant(point.status)}>{getStatusLabel(point.status)}</Badge>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </div>
          ) : (
            /* Overview Mode */
            <div className="space-y-6">
              <div className="flex items-center gap-4">
                <Label htmlFor="month-select">Select Month:</Label>
                <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                  <SelectTrigger id="month-select" className="w-48">
                    <SelectValue placeholder="Select month" />
                  </SelectTrigger>
                  <SelectContent>
                    {availableMonths?.map((month) => (
                      <SelectItem key={month} value={month}>{month}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {progressSummary && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card className="border-l-4 border-l-green-500">
                    <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">On Track</CardTitle></CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-green-600">{progressSummary.on_track_count}</p>
                      <p className="text-xs text-muted-foreground">categories</p>
                    </CardContent>
                  </Card>
                  <Card className="border-l-4 border-l-yellow-500">
                    <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Warning</CardTitle></CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-yellow-600">{progressSummary.warning_count}</p>
                      <p className="text-xs text-muted-foreground">categories</p>
                    </CardContent>
                  </Card>
                  <Card className="border-l-4 border-l-red-500">
                    <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Over Budget</CardTitle></CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold text-red-600">{progressSummary.over_budget_count}</p>
                      <p className="text-xs text-muted-foreground">categories</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardHeader className="pb-2"><CardTitle className="text-sm font-medium text-muted-foreground">Total Spent</CardTitle></CardHeader>
                    <CardContent>
                      <p className="text-2xl font-bold">{formatCurrency(progressSummary.total_spent)}</p>
                      <p className="text-xs text-muted-foreground">of {formatCurrency(progressSummary.total_budget)}</p>
                    </CardContent>
                  </Card>
                </div>
              )}

              {progressLoading ? (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  <Skeleton className="h-48 w-full" /><Skeleton className="h-48 w-full" /><Skeleton className="h-48 w-full" />
                </div>
              ) : !budgetProgress || budgetProgress.length === 0 ? (
                <EmptyState icon={<Target className="h-12 w-12" />} title="No budget progress" description="Set budget goals to see progress tracking" />
              ) : (
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {budgetProgress.map((progress) => {
                    const gaugeColor = getGaugeColor(progress.percentage);
                    const gaugeData = [{ value: Math.min(progress.percentage, 100), fill: gaugeColor }];
                    return (
                      <Card
                        key={progress.category}
                        className="cursor-pointer hover:shadow-md transition-shadow"
                        onClick={() => { setSelectedCategory(progress.category); setProgressView("detail"); }}
                      >
                        <CardHeader>
                          <CardTitle className="flex items-center justify-between">
                            <span className="text-sm">{progress.category}</span>
                            <Badge variant={getStatusVariant(progress.status)}>{getStatusLabel(progress.status)}</Badge>
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-3">
                          <div className="flex items-center gap-4">
                            <RadialBarChart
                              width={80}
                              height={80}
                              innerRadius="60%"
                              outerRadius="100%"
                              data={gaugeData}
                              startAngle={90}
                              endAngle={-270}
                            >
                              <RadialBar dataKey="value" background={{ fill: "#e5e7eb" }} cornerRadius={4} />
                            </RadialBarChart>
                            <div className="space-y-1">
                              <p className="text-2xl font-bold" style={{ color: gaugeColor }}>
                                {formatPercentage(progress.percentage)}
                              </p>
                              <p className="text-xs text-muted-foreground">
                                {formatCurrency(progress.spent)} of {formatCurrency(progress.budget_limit)}
                              </p>
                            </div>
                          </div>
                          <div className="pt-2 border-t">
                            <div className="flex justify-between text-sm">
                              <span className="text-muted-foreground">Remaining</span>
                              <span className={`font-mono font-semibold ${progress.remaining >= 0 ? "text-green-600" : "text-red-600"}`}>
                                {formatCurrency(progress.remaining)}
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
