import React from "react";
import { Target, Plus, Trash2, Pencil } from "lucide-react";
import {
  useBudgetGoals,
  useSetBudget,
  useDeleteBudget,
  useBudgetProgress,
  useEarningsGoals,
  useSetEarningsGoal,
  useDeleteEarningsGoal,
  useBudgetGoalsSummary,
  useEarningsGoalsSummary,
} from "@/api/hooks/use-budget-goals";
import { useEarningsMonths } from "@/api/hooks/use-earnings";
import PageHeader from "@/components/page-header";
import EmptyState from "@/components/empty-state";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

export default function BudgetGoalsPage() {
  const [activeTab, setActiveTab] = React.useState("budget-goals");
  const [budgetDialogOpen, setBudgetDialogOpen] = React.useState(false);
  const [earningsDialogOpen, setEarningsDialogOpen] = React.useState(false);
  const [selectedMonth, setSelectedMonth] = React.useState<string>("");

  // Budget Goals form
  const [budgetCategory, setBudgetCategory] = React.useState("");
  const [budgetLimit, setBudgetLimit] = React.useState("");
  const [budgetYearMonth, setBudgetYearMonth] = React.useState("ALL");

  // Earnings Goals form
  const [earningsSubCategory, setEarningsSubCategory] = React.useState("");
  const [earningsAmount, setEarningsAmount] = React.useState("");
  const [earningsYearMonth, setEarningsYearMonth] = React.useState("ALL");

  // Queries
  const { data: budgetGoalsSummary } = useBudgetGoalsSummary();
  const { data: earningsGoalsSummary } = useEarningsGoalsSummary();
  const { data: budgetGoals, isLoading: budgetGoalsLoading } = useBudgetGoals();
  const { data: earningsGoals, isLoading: earningsGoalsLoading } = useEarningsGoals();
  const { data: availableMonths } = useEarningsMonths();
  const { data: budgetProgress, isLoading: progressLoading } = useBudgetProgress(selectedMonth);

  // Mutations
  const setBudgetMutation = useSetBudget();
  const deleteBudgetMutation = useDeleteBudget();
  const setEarningsGoalMutation = useSetEarningsGoal();
  const deleteEarningsGoalMutation = useDeleteEarningsGoal();

  // Set default selected month when available months load
  React.useEffect(() => {
    if (availableMonths && availableMonths.length > 0 && !selectedMonth) {
      const firstMonth = availableMonths[0];
      if (firstMonth) setSelectedMonth(firstMonth);
    }
  }, [availableMonths, selectedMonth]);

  const handleAddBudgetGoal = () => {
    if (!budgetCategory || !budgetLimit) {
      alert("Please fill in all required fields");
      return;
    }

    setBudgetMutation.mutate(
      {
        category: budgetCategory,
        monthly_limit: parseFloat(budgetLimit),
        year_month: budgetYearMonth,
      },
      {
        onSuccess: () => {
          setBudgetDialogOpen(false);
          setBudgetCategory("");
          setBudgetLimit("");
          setBudgetYearMonth("ALL");
        },
        onError: (error) => {
          alert(`Failed to add budget goal: ${error.message}`);
        },
      }
    );
  };

  const handleDeleteBudgetGoal = (category: string) => {
    if (!confirm(`Delete budget goal for ${category}?`)) return;

    deleteBudgetMutation.mutate(category, {
      onError: (error) => {
        alert(`Failed to delete budget goal: ${error.message}`);
      },
    });
  };

  const handleAddEarningsGoal = () => {
    if (!earningsSubCategory || !earningsAmount) {
      alert("Please fill in all required fields");
      return;
    }

    setEarningsGoalMutation.mutate(
      {
        sub_category: earningsSubCategory,
        expected_amount: parseFloat(earningsAmount),
        year_month: earningsYearMonth,
      },
      {
        onSuccess: () => {
          setEarningsDialogOpen(false);
          setEarningsSubCategory("");
          setEarningsAmount("");
          setEarningsYearMonth("ALL");
        },
        onError: (error) => {
          alert(`Failed to add earnings goal: ${error.message}`);
        },
      }
    );
  };

  const handleDeleteEarningsGoal = (subCategory: string) => {
    if (!confirm(`Delete earnings goal for ${subCategory}?`)) return;

    deleteEarningsGoalMutation.mutate(subCategory, {
      onError: (error) => {
        alert(`Failed to delete earnings goal: ${error.message}`);
      },
    });
  };

  const getProgressColorClass = (percentage: number): string => {
    if (percentage < 75) return "bg-green-500";
    if (percentage <= 100) return "bg-yellow-500";
    return "bg-red-500";
  };

  const getStatusVariant = (status: string): "default" | "destructive" | "outline" | "secondary" => {
    if (status === "OVER_BUDGET") return "destructive";
    if (status === "ON_TRACK") return "default";
    return "secondary";
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Budget Goals"
        description="Set and track spending limits"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="budget-goals">Budget Goals</TabsTrigger>
          <TabsTrigger value="earnings-goals">Earnings Goals</TabsTrigger>
          <TabsTrigger value="progress">Progress</TabsTrigger>
        </TabsList>

        {/* Budget Goals Tab */}
        <TabsContent value="budget-goals" className="space-y-4">
          {/* Summary Strip */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Budget
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {budgetGoalsSummary
                    ? formatCurrency(budgetGoalsSummary.total_monthly_budget)
                    : "\u2014"}
                </p>
                <p className="text-xs text-muted-foreground">per month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {budgetGoalsSummary
                    ? budgetGoalsSummary.categories_tracked
                    : "\u2014"}
                </p>
                <p className="text-xs text-muted-foreground">
                  categories tracked
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Month Overrides
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {budgetGoalsSummary
                    ? budgetGoalsSummary.month_overrides
                    : "\u2014"}
                </p>
                <p className="text-xs text-muted-foreground">overrides</p>
              </CardContent>
            </Card>
          </div>

          {/* Header Row */}
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Budget Goals</h2>
            <Dialog open={budgetDialogOpen} onOpenChange={setBudgetDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Budget Goal
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Budget Goal</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="budget-category">Category</Label>
                    <Input
                      id="budget-category"
                      placeholder="e.g., Groceries"
                      value={budgetCategory}
                      onChange={(e) => setBudgetCategory(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="budget-limit">Monthly Limit</Label>
                    <Input
                      id="budget-limit"
                      type="number"
                      placeholder="0.00"
                      value={budgetLimit}
                      onChange={(e) => setBudgetLimit(e.target.value)}
                      step="0.01"
                      min="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="budget-year-month">Year Month</Label>
                    <Input
                      id="budget-year-month"
                      placeholder="ALL or YYYY-MM"
                      value={budgetYearMonth}
                      onChange={(e) => setBudgetYearMonth(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setBudgetDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleAddBudgetGoal}
                    disabled={setBudgetMutation.isPending}
                  >
                    {setBudgetMutation.isPending ? "Adding..." : "Add Goal"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Card Grid */}
          {budgetGoalsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : !budgetGoals || budgetGoals.length === 0 ? (
            <EmptyState
              icon={<Target className="h-12 w-12" />}
              title="No budget goals"
              description="Add your first budget goal to start tracking spending limits"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {budgetGoals.map((goal) => {
                const overrideCount = budgetGoals.filter(
                  (g) =>
                    g.category === goal.category && g.year_month !== "ALL"
                ).length;
                return (
                  <Card key={goal.id}>
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center justify-between">
                        <span>{goal.category}</span>
                        <Badge variant="outline">
                          {goal.year_month === "ALL"
                            ? "All Months"
                            : goal.year_month}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-2xl font-bold">
                        {formatCurrency(goal.monthly_limit)}
                        <span className="text-sm font-normal text-muted-foreground">
                          /mo
                        </span>
                      </p>
                      {goal.year_month === "ALL" && overrideCount > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {overrideCount} override{overrideCount > 1 ? "s" : ""}
                        </p>
                      )}
                      <div className="flex items-center gap-2 pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setBudgetCategory(goal.category);
                            setBudgetLimit(goal.monthly_limit.toString());
                            setBudgetYearMonth(goal.year_month);
                            setBudgetDialogOpen(true);
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() =>
                            handleDeleteBudgetGoal(goal.category)
                          }
                          disabled={deleteBudgetMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Earnings Goals Tab */}
        <TabsContent value="earnings-goals" className="space-y-4">
          {/* Summary Strip */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total Expected Earnings
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {earningsGoalsSummary
                    ? formatCurrency(earningsGoalsSummary.total_expected_earnings)
                    : "—"}
                </p>
                <p className="text-xs text-muted-foreground">per month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Sub-categories
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {earningsGoalsSummary
                    ? earningsGoalsSummary.sub_categories_tracked
                    : "—"}
                </p>
                <p className="text-xs text-muted-foreground">sub-categories tracked</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Month Overrides
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">
                  {earningsGoalsSummary ? earningsGoalsSummary.month_overrides : "—"}
                </p>
                <p className="text-xs text-muted-foreground">overrides</p>
              </CardContent>
            </Card>
          </div>

          {/* Header Row */}
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Earnings Goals</h2>
            <Dialog open={earningsDialogOpen} onOpenChange={setEarningsDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Earnings Goal
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Earnings Goal</DialogTitle>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="space-y-2">
                    <Label htmlFor="earnings-subcategory">Sub Category</Label>
                    <Input
                      id="earnings-subcategory"
                      placeholder="e.g., Salary"
                      value={earningsSubCategory}
                      onChange={(e) => setEarningsSubCategory(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="earnings-amount">Expected Amount</Label>
                    <Input
                      id="earnings-amount"
                      type="number"
                      placeholder="0.00"
                      value={earningsAmount}
                      onChange={(e) => setEarningsAmount(e.target.value)}
                      step="0.01"
                      min="0"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="earnings-year-month">Year Month</Label>
                    <Input
                      id="earnings-year-month"
                      placeholder="ALL or YYYY-MM"
                      value={earningsYearMonth}
                      onChange={(e) => setEarningsYearMonth(e.target.value)}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setEarningsDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleAddEarningsGoal}
                    disabled={setEarningsGoalMutation.isPending}
                  >
                    {setEarningsGoalMutation.isPending ? "Adding..." : "Add Goal"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Card Grid */}
          {earningsGoalsLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : !earningsGoals || earningsGoals.length === 0 ? (
            <EmptyState
              icon={<Target className="h-12 w-12" />}
              title="No earnings goals"
              description="Add your first earnings goal to start tracking income targets"
            />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {earningsGoals.map((goal) => {
                const overrideCount = earningsGoals.filter(
                  (g) => g.sub_category === goal.sub_category && g.year_month !== "ALL"
                ).length;
                return (
                  <Card key={goal.id}>
                    <CardHeader className="pb-2">
                      <CardTitle className="flex items-center justify-between">
                        <span>{goal.sub_category}</span>
                        <Badge variant="outline">
                          {goal.year_month === "ALL" ? "All Months" : goal.year_month}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <p className="text-2xl font-bold">
                        {formatCurrency(goal.expected_amount)}
                        <span className="text-sm font-normal text-muted-foreground">/mo</span>
                      </p>
                      {goal.year_month === "ALL" && overrideCount > 0 && (
                        <p className="text-xs text-muted-foreground">
                          {overrideCount} override{overrideCount > 1 ? "s" : ""}
                        </p>
                      )}
                      <div className="flex items-center gap-2 pt-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setEarningsSubCategory(goal.sub_category);
                            setEarningsAmount(goal.expected_amount.toString());
                            setEarningsYearMonth(goal.year_month);
                            setEarningsDialogOpen(true);
                          }}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteEarningsGoal(goal.sub_category)}
                          disabled={deleteEarningsGoalMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Progress Tab */}
        <TabsContent value="progress" className="space-y-4">
          <div className="flex items-center gap-4">
            <Label htmlFor="month-select">Select Month:</Label>
            <Select value={selectedMonth} onValueChange={setSelectedMonth}>
              <SelectTrigger id="month-select" className="w-48">
                <SelectValue placeholder="Select month" />
              </SelectTrigger>
              <SelectContent>
                {availableMonths?.map((month) => (
                  <SelectItem key={month} value={month}>
                    {month}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {progressLoading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
              <Skeleton className="h-48 w-full" />
            </div>
          ) : !budgetProgress || budgetProgress.length === 0 ? (
            <EmptyState
              icon={<Target className="h-12 w-12" />}
              title="No budget progress"
              description="Set budget goals to see progress tracking"
            />
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {budgetProgress.map((progress) => (
                <Card key={progress.category}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{progress.category}</span>
                      <Badge variant={getStatusVariant(progress.status)}>
                        {progress.status.replace(/_/g, " ")}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Spent</span>
                        <span className="font-mono font-medium">
                          {formatCurrency(progress.spent)}
                        </span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Budget</span>
                        <span className="font-mono font-medium">
                          {formatCurrency(progress.budget_limit)}
                        </span>
                      </div>
                      <div className="relative h-2 w-full overflow-hidden rounded-full bg-primary/20">
                        <div
                          className={`h-full transition-all ${getProgressColorClass(progress.percentage)}`}
                          style={{ width: `${Math.min(progress.percentage, 100)}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Progress</span>
                        <span className="font-semibold">
                          {formatPercentage(progress.percentage)}
                        </span>
                      </div>
                    </div>
                    <div className="pt-2 border-t">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Remaining</span>
                        <span
                          className={`font-mono font-semibold ${
                            progress.remaining >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          {formatCurrency(progress.remaining)}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
