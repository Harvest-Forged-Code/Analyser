import { useState, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useEarningsMonthTransactions } from "@/api/hooks/use-earnings";
import { formatCurrency, formatDate } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface TransactionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  period: string | undefined;
  subCategory: string | undefined;
}

export default function TransactionModal({
  open,
  onOpenChange,
  period,
  subCategory,
}: TransactionModalProps) {
  const [search, setSearch] = useState("");

  const { data: transactions, isLoading } = useEarningsMonthTransactions(
    open ? period : undefined,
    subCategory,
  );

  const filtered = useMemo(() => {
    if (!transactions) return [];
    if (!search.trim()) return transactions;
    const term = search.toLowerCase();
    return transactions.filter((tx) => {
      const desc = String(tx.description ?? "").toLowerCase();
      return desc.includes(term);
    });
  }, [transactions, search]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{subCategory ?? "Transactions"}</DialogTitle>
          <DialogDescription>
            {period ? `Transactions for ${period}` : "Select a period"}
          </DialogDescription>
        </DialogHeader>

        <Input
          placeholder="Search by description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="mb-4"
        />

        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
          </div>
        ) : (
          <ScrollArea className="max-h-[400px]">
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.length > 0 ? (
                    filtered.map((tx, index) => (
                      <TableRow key={index}>
                        <TableCell className="whitespace-nowrap">
                          {tx.transaction_date
                            ? formatDate(String(tx.transaction_date))
                            : "--"}
                        </TableCell>
                        <TableCell>{String(tx.description ?? "")}</TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(Number(tx.amount ?? 0))}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={3} className="h-16 text-center">
                        No transactions found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  );
}
