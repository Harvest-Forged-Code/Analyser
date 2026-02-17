import { useState } from "react";
import { Wallet, CreditCard, DollarSign, Plus, Trash2, Pencil } from "lucide-react";
import {
  useAccounts,
  useAddAccount,
  useUpdateBalance,
  useDeleteAccount,
  useNetWorthSummary,
} from "@/api/hooks/use-net-worth";
import type { Account } from "@/api/types";
import PageHeader from "@/components/page-header";
import KpiCard from "@/components/kpi-card";
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
import { COLOR_POSITIVE, COLOR_NEGATIVE } from "@/lib/constants";

const ACCOUNT_TYPES = [
  { value: "checking", label: "Checking" },
  { value: "savings", label: "Savings" },
  { value: "investment", label: "Investment" },
  { value: "credit_card", label: "Credit Card" },
  { value: "loan", label: "Loan" },
  { value: "other", label: "Other" },
];

const ACCOUNT_TYPE_COLORS: Record<string, string> = {
  checking: "bg-blue-100 text-blue-800",
  savings: "bg-green-100 text-green-800",
  investment: "bg-purple-100 text-purple-800",
  credit_card: "bg-red-100 text-red-800",
  loan: "bg-orange-100 text-orange-800",
  other: "bg-gray-100 text-gray-800",
};

export default function NetWorthPage() {
  const { data: accounts, isLoading: accountsLoading } = useAccounts();
  const { data: summary, isLoading: summaryLoading } = useNetWorthSummary();
  const addAccount = useAddAccount();
  const updateBalance = useUpdateBalance();
  const deleteAccount = useDeleteAccount();

  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isUpdateBalanceDialogOpen, setIsUpdateBalanceDialogOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<Account | null>(null);

  const [newAccount, setNewAccount] = useState({
    name: "",
    account_type: "checking",
    balance: "",
    notes: "",
  });

  const [newBalance, setNewBalance] = useState("");

  const handleAddAccount = () => {
    addAccount.mutate(
      {
        name: newAccount.name,
        account_type: newAccount.account_type,
        balance: newAccount.balance ? parseFloat(newAccount.balance) : undefined,
        notes: newAccount.notes || undefined,
      },
      {
        onSuccess: () => {
          setIsAddDialogOpen(false);
          setNewAccount({ name: "", account_type: "checking", balance: "", notes: "" });
        },
      }
    );
  };

  const handleUpdateBalance = () => {
    if (selectedAccount && selectedAccount.id !== null) {
      updateBalance.mutate(
        {
          accountId: selectedAccount.id,
          balance: parseFloat(newBalance),
        },
        {
          onSuccess: () => {
            setIsUpdateBalanceDialogOpen(false);
            setSelectedAccount(null);
            setNewBalance("");
          },
        }
      );
    }
  };

  const handleDeleteAccount = (accountId: number | null) => {
    if (accountId !== null && window.confirm("Are you sure you want to delete this account?")) {
      deleteAccount.mutate(accountId);
    }
  };

  const openUpdateBalanceDialog = (account: Account) => {
    setSelectedAccount(account);
    setNewBalance(account.balance.toString());
    setIsUpdateBalanceDialogOpen(true);
  };

  const columns: ColumnDef<Account>[] = [
    {
      accessorKey: "name",
      header: "Name",
      cell: ({ row }) => <span className="font-medium">{row.getValue("name")}</span>,
    },
    {
      accessorKey: "account_type",
      header: "Type",
      cell: ({ row }) => {
        const type = row.getValue("account_type") as string;
        return (
          <Badge className={cn(ACCOUNT_TYPE_COLORS[type] || ACCOUNT_TYPE_COLORS.other)}>
            {ACCOUNT_TYPES.find((t) => t.value === type)?.label || type}
          </Badge>
        );
      },
    },
    {
      accessorKey: "balance",
      header: () => <div className="text-right">Balance</div>,
      cell: ({ row }) => {
        const balance = row.getValue("balance") as number;
        return (
          <div
            className={cn(
              "text-right font-medium",
              balance >= 0 ? "text-green-600" : "text-red-600"
            )}
          >
            {formatCurrency(balance)}
          </div>
        );
      },
    },
    {
      accessorKey: "last_updated",
      header: "Last Updated",
      cell: ({ row }) => formatDate(row.getValue("last_updated")),
    },
    {
      accessorKey: "notes",
      header: "Notes",
      cell: ({ row }) => {
        const notes = row.getValue("notes") as string;
        return <span className="text-sm text-muted-foreground">{notes || "—"}</span>;
      },
    },
    {
      id: "actions",
      header: () => <div className="text-right">Actions</div>,
      cell: ({ row }) => (
        <div className="flex justify-end gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => openUpdateBalanceDialog(row.original)}
          >
            <Pencil className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleDeleteAccount(row.original.id)}
          >
            <Trash2 className="h-4 w-4 text-red-600" />
          </Button>
        </div>
      ),
    },
  ];

  if (accountsLoading || summaryLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (!accounts || accounts.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Net Worth"
          description="Track your assets and liabilities"
          action={
            <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Account
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Account</DialogTitle>
                  <DialogDescription>
                    Add a new account to track your net worth.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      value={newAccount.name}
                      onChange={(e) =>
                        setNewAccount({ ...newAccount, name: e.target.value })
                      }
                      placeholder="Checking Account"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="account_type">Account Type</Label>
                    <Select
                      value={newAccount.account_type}
                      onValueChange={(value) =>
                        setNewAccount({ ...newAccount, account_type: value })
                      }
                    >
                      <SelectTrigger id="account_type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ACCOUNT_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="balance">Balance (optional)</Label>
                    <Input
                      id="balance"
                      type="number"
                      step="0.01"
                      value={newAccount.balance}
                      onChange={(e) =>
                        setNewAccount({ ...newAccount, balance: e.target.value })
                      }
                      placeholder="0.00"
                    />
                  </div>
                  <div className="grid gap-2">
                    <Label htmlFor="notes">Notes (optional)</Label>
                    <Input
                      id="notes"
                      value={newAccount.notes}
                      onChange={(e) =>
                        setNewAccount({ ...newAccount, notes: e.target.value })
                      }
                      placeholder="Additional information"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setIsAddDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleAddAccount}
                    disabled={!newAccount.name || addAccount.isPending}
                  >
                    {addAccount.isPending ? "Adding..." : "Add Account"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          }
        />
        <EmptyState
          icon={<Wallet className="h-12 w-12" />}
          title="No accounts yet"
          description="Add your first account to start tracking your net worth."
        />
      </div>
    );
  }

  const netWorthValue = summary?.net_worth || 0;
  const netWorthColor = netWorthValue >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Net Worth"
        description="Track your assets and liabilities"
        action={
          <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Account
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Account</DialogTitle>
                <DialogDescription>
                  Add a new account to track your net worth.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label htmlFor="name">Name</Label>
                  <Input
                    id="name"
                    value={newAccount.name}
                    onChange={(e) =>
                      setNewAccount({ ...newAccount, name: e.target.value })
                    }
                    placeholder="Checking Account"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="account_type">Account Type</Label>
                  <Select
                    value={newAccount.account_type}
                    onValueChange={(value) =>
                      setNewAccount({ ...newAccount, account_type: value })
                    }
                  >
                    <SelectTrigger id="account_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ACCOUNT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="balance">Balance (optional)</Label>
                  <Input
                    id="balance"
                    type="number"
                    step="0.01"
                    value={newAccount.balance}
                    onChange={(e) =>
                      setNewAccount({ ...newAccount, balance: e.target.value })
                    }
                    placeholder="0.00"
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="notes">Notes (optional)</Label>
                  <Input
                    id="notes"
                    value={newAccount.notes}
                    onChange={(e) =>
                      setNewAccount({ ...newAccount, notes: e.target.value })
                    }
                    placeholder="Additional information"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setIsAddDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAddAccount}
                  disabled={!newAccount.name || addAccount.isPending}
                >
                  {addAccount.isPending ? "Adding..." : "Add Account"}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard
          title="Total Assets"
          value={formatCurrency(summary?.total_assets || 0)}
          icon={<Wallet className="h-5 w-5" />}
          iconColor={COLOR_POSITIVE}
        />
        <KpiCard
          title="Total Liabilities"
          value={formatCurrency(summary?.total_liabilities || 0)}
          icon={<CreditCard className="h-5 w-5" />}
          iconColor={COLOR_NEGATIVE}
        />
        <KpiCard
          title="Net Worth"
          value={formatCurrency(netWorthValue)}
          icon={<DollarSign className="h-5 w-5" />}
          iconColor={netWorthColor}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Assets by Type</CardTitle>
          </CardHeader>
          <CardContent>
            {summary?.assets_by_type &&
            Object.keys(summary.assets_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(summary.assets_by_type).map(([type, amount]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {ACCOUNT_TYPES.find((t) => t.value === type)?.label || type}
                    </span>
                    <span className="text-sm font-bold text-green-600">
                      {formatCurrency(amount)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No assets</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Liabilities by Type</CardTitle>
          </CardHeader>
          <CardContent>
            {summary?.liabilities_by_type &&
            Object.keys(summary.liabilities_by_type).length > 0 ? (
              <div className="space-y-3">
                {Object.entries(summary.liabilities_by_type).map(([type, amount]) => (
                  <div key={type} className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {ACCOUNT_TYPES.find((t) => t.value === type)?.label || type}
                    </span>
                    <span className="text-sm font-bold text-red-600">
                      {formatCurrency(amount)}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No liabilities</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Accounts</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable columns={columns} data={accounts} />
        </CardContent>
      </Card>

      <Dialog open={isUpdateBalanceDialogOpen} onOpenChange={setIsUpdateBalanceDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Update Balance</DialogTitle>
            <DialogDescription>
              Update the balance for {selectedAccount?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label>Current Balance</Label>
              <Input
                value={formatCurrency(selectedAccount?.balance || 0)}
                disabled
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="new_balance">New Balance</Label>
              <Input
                id="new_balance"
                type="number"
                step="0.01"
                value={newBalance}
                onChange={(e) => setNewBalance(e.target.value)}
                placeholder="0.00"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsUpdateBalanceDialogOpen(false)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpdateBalance}
              disabled={!newBalance || updateBalance.isPending}
            >
              {updateBalance.isPending ? "Updating..." : "Update Balance"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
