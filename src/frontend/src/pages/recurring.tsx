import { useState } from "react";
import { Repeat, Plus, Trash2, Power, PowerOff } from "lucide-react";
import {
  useRecurringTransactions,
  useAddRecurring,
  useDeleteRecurring,
  useDeactivateRecurring,
} from "@/api/hooks/use-recurring";
import type { RecurringTransaction } from "@/api/types";
import PageHeader from "@/components/page-header";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { formatCurrency, formatDate, cn } from "@/lib/utils";

const FREQUENCIES = [
  { value: "monthly", label: "Monthly", color: "bg-blue-100 text-blue-800" },
  { value: "weekly", label: "Weekly", color: "bg-purple-100 text-purple-800" },
  { value: "yearly", label: "Yearly", color: "bg-green-100 text-green-800" },
];

const FREQUENCY_COLORS: Record<string, string> = {
  monthly: "bg-blue-100 text-blue-800",
  weekly: "bg-purple-100 text-purple-800",
  yearly: "bg-green-100 text-green-800",
};

export default function RecurringPage() {
  const [activeOnly, setActiveOnly] = useState(true);
  const { data: transactions, isLoading } = useRecurringTransactions(activeOnly);
  const addRecurring = useAddRecurring();
  const deleteRecurring = useDeleteRecurring();
  const deactivateRecurring = useDeactivateRecurring();

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newRecurring, setNewRecurring] = useState({
    description: "",
    expected_amount: "",
    frequency: "monthly",
    category: "",
    sub_category: "",
  });

  const handleAddRecurring = () => {
    addRecurring.mutate(
      {
        description: newRecurring.description,
        expected_amount: parseFloat(newRecurring.expected_amount),
        frequency: newRecurring.frequency || undefined,
        category: newRecurring.category || undefined,
        sub_category: newRecurring.sub_category || undefined,
      },
      {
        onSuccess: () => {
          setIsAddDialogOpen(false);
          setNewRecurring({
            description: "",
            expected_amount: "",
            frequency: "monthly",
            category: "",
            sub_category: "",
          });
        },
      }
    );
  };

  const handleDeleteRecurring = (recurringId: number | null) => {
    if (
      recurringId !== null &&
      window.confirm("Are you sure you want to delete this recurring transaction?")
    ) {
      deleteRecurring.mutate(recurringId);
    }
  };

  const handleDeactivateRecurring = (recurringId: number | null) => {
    if (
      recurringId !== null &&
      window.confirm("Are you sure you want to deactivate this recurring transaction?")
    ) {
      deactivateRecurring.mutate(recurringId);
    }
  };

  const columns: ColumnDef<RecurringTransaction>[] = [
    {
      accessorKey: "description",
      header: "Description",
      cell: ({ row }) => <span className="font-medium">{row.getValue("description")}</span>,
    },
    {
      accessorKey: "expected_amount",
      header: () => <div className="text-right">Expected Amount</div>,
      cell: ({ row }) => (
        <div className="text-right font-medium">
          {formatCurrency(row.getValue("expected_amount"))}
        </div>
      ),
    },
    {
      accessorKey: "frequency",
      header: "Frequency",
      cell: ({ row }) => {
        const frequency = row.getValue("frequency") as string;
        return (
          <Badge className={cn(FREQUENCY_COLORS[frequency] || "bg-gray-100 text-gray-800")}>
            {FREQUENCIES.find((f) => f.value === frequency)?.label || frequency}
          </Badge>
        );
      },
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => {
        const category = row.getValue("category") as string;
        return <span className="text-sm">{category || "—"}</span>;
      },
    },
    {
      accessorKey: "sub_category",
      header: "Sub Category",
      cell: ({ row }) => {
        const subCategory = row.getValue("sub_category") as string;
        return <span className="text-sm">{subCategory || "—"}</span>;
      },
    },
    {
      accessorKey: "last_occurrence",
      header: "Last Occurrence",
      cell: ({ row }) => {
        const lastOccurrence = row.getValue("last_occurrence") as string;
        return lastOccurrence ? formatDate(lastOccurrence) : "—";
      },
    },
    {
      accessorKey: "is_active",
      header: "Status",
      cell: ({ row }) => {
        const isActive = row.getValue("is_active") as boolean;
        return (
          <Badge className={isActive ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
            {isActive ? "Active" : "Inactive"}
          </Badge>
        );
      },
    },
    {
      id: "actions",
      header: () => <div className="text-right">Actions</div>,
      cell: ({ row }) => {
        const isActive = row.original.is_active;
        return (
          <div className="flex justify-end gap-2">
            {isActive && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDeactivateRecurring(row.original.id)}
                title="Deactivate"
              >
                <PowerOff className="h-4 w-4 text-orange-600" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleDeleteRecurring(row.original.id)}
              title="Delete"
            >
              <Trash2 className="h-4 w-4 text-red-600" />
            </Button>
          </div>
        );
      },
    },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Recurring Transactions"
          description="Manage regular payments and subscriptions"
          action={
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Recurring
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Recurring Transaction</DialogTitle>
                  <DialogDescription>
                    Add a new recurring transaction to track regular payments.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="description">Description</Label>
                    <Input
                      id="description"
                      value={newRecurring.description}
                      onChange={(e) =>
                        setNewRecurring({ ...newRecurring, description: e.target.value })
                      }
                      placeholder="Netflix Subscription"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="expected_amount">Expected Amount</Label>
                    <Input
                      id="expected_amount"
                      type="number"
                      step="0.01"
                      value={newRecurring.expected_amount}
                      onChange={(e) =>
                        setNewRecurring({
                          ...newRecurring,
                          expected_amount: e.target.value,
                        })
                      }
                      placeholder="15.99"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="frequency">Frequency (optional)</Label>
                    <Select
                      value={newRecurring.frequency}
                      onValueChange={(value) =>
                        setNewRecurring({ ...newRecurring, frequency: value })
                      }
                    >
                      <SelectTrigger id="frequency">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {FREQUENCIES.map((freq) => (
                          <SelectItem key={freq.value} value={freq.value}>
                            {freq.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="category">Category (optional)</Label>
                    <Input
                      id="category"
                      value={newRecurring.category}
                      onChange={(e) =>
                        setNewRecurring({ ...newRecurring, category: e.target.value })
                      }
                      placeholder="Entertainment"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="sub_category">Sub Category (optional)</Label>
                    <Input
                      id="sub_category"
                      value={newRecurring.sub_category}
                      onChange={(e) =>
                        setNewRecurring({
                          ...newRecurring,
                          sub_category: e.target.value,
                        })
                      }
                      placeholder="Streaming Services"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button
                    onClick={handleAddRecurring}
                    disabled={
                      !newRecurring.description ||
                      !newRecurring.expected_amount ||
                      addRecurring.isPending
                    }
                  >
                    {addRecurring.isPending ? "Adding..." : "Add Recurring"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          }
        />

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Filter</CardTitle>
              <div className="flex gap-2">
                <Button
                  variant={activeOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveOnly(true)}
                >
                  Active Only
                </Button>
                <Button
                  variant={!activeOnly ? "default" : "outline"}
                  size="sm"
                  onClick={() => setActiveOnly(false)}
                >
                  Show All
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        <EmptyState
          icon={<Repeat className="h-12 w-12" />}
          title="No recurring transactions yet"
          description={
            activeOnly
              ? "Add your first recurring transaction to track regular payments."
              : "No recurring transactions found. Try adding one."
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Recurring Transactions"
        description="Manage regular payments and subscriptions"
        action={
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Recurring
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Recurring Transaction</DialogTitle>
                <DialogDescription>
                  Add a new recurring transaction to track regular payments.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    value={newRecurring.description}
                    onChange={(e) =>
                      setNewRecurring({ ...newRecurring, description: e.target.value })
                    }
                    placeholder="Netflix Subscription"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="expected_amount">Expected Amount</Label>
                  <Input
                    id="expected_amount"
                    type="number"
                    step="0.01"
                    value={newRecurring.expected_amount}
                    onChange={(e) =>
                      setNewRecurring({
                        ...newRecurring,
                        expected_amount: e.target.value,
                      })
                    }
                    placeholder="15.99"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="frequency">Frequency (optional)</Label>
                  <Select
                    value={newRecurring.frequency}
                    onValueChange={(value) =>
                      setNewRecurring({ ...newRecurring, frequency: value })
                    }
                  >
                    <SelectTrigger id="frequency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {FREQUENCIES.map((freq) => (
                        <SelectItem key={freq.value} value={freq.value}>
                          {freq.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="category">Category (optional)</Label>
                  <Input
                    id="category"
                    value={newRecurring.category}
                    onChange={(e) =>
                      setNewRecurring({ ...newRecurring, category: e.target.value })
                    }
                    placeholder="Entertainment"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="sub_category">Sub Category (optional)</Label>
                  <Input
                    id="sub_category"
                    value={newRecurring.sub_category}
                    onChange={(e) =>
                      setNewRecurring({
                        ...newRecurring,
                        sub_category: e.target.value,
                      })
                    }
                    placeholder="Streaming Services"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleAddRecurring}
                  disabled={
                    !newRecurring.description ||
                    !newRecurring.expected_amount ||
                    addRecurring.isPending
                  }
                >
                  {addRecurring.isPending ? "Adding..." : "Add Recurring"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Filter</CardTitle>
            <div className="flex gap-2">
              <Button
                variant={activeOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveOnly(true)}
              >
                <Power className="mr-2 h-4 w-4" />
                Active Only
              </Button>
              <Button
                variant={!activeOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveOnly(false)}
              >
                Show All
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recurring Transactions</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} data={transactions} />
        </CardContent>
      </Card>
    </div>
  );
}
