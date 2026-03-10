import { Pencil, Trash2 } from "lucide-react";
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
import { formatCurrency, formatDate } from "@/lib/utils";
import type { RecurringTransaction } from "@/api/types";

interface RecurringTableProps {
  transactions: RecurringTransaction[];
  onEdit: (transaction: RecurringTransaction) => void;
  onDelete: (id: number) => void;
}

function StatusBadge({ transaction }: { transaction: RecurringTransaction }) {
  if (transaction.user_confirmed && transaction.detection_method === "manual") {
    return (
      <Badge className="bg-blue-500 hover:bg-blue-600 text-white">
        Manual
      </Badge>
    );
  }
  if (transaction.user_confirmed) {
    return (
      <Badge className="bg-emerald-500 hover:bg-emerald-600 text-white">
        Confirmed
      </Badge>
    );
  }
  return (
    <Badge variant="outline" className="text-amber-500 border-amber-500">
      Detected
    </Badge>
  );
}

export default function RecurringTable({
  transactions,
  onEdit,
  onDelete,
}: RecurringTableProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recurring Transactions</CardTitle>
      </CardHeader>
      <CardContent>
        {transactions.length === 0 ? (
          <p className="text-center text-muted-foreground py-8">
            No recurring transactions tracked yet. Use the scan feature to
            detect patterns or add one manually.
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Amount</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>Next Expected</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {transactions.map((t) => (
                <TableRow key={t.id ?? t.description}>
                  <TableCell className="font-medium max-w-[200px] truncate">
                    {t.description}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(Math.abs(t.expected_amount))}
                  </TableCell>
                  <TableCell className="capitalize">{t.frequency}</TableCell>
                  <TableCell>
                    {t.category ? (
                      <span>
                        {t.category}
                        {t.sub_category && (
                          <span className="text-muted-foreground">
                            {" / "}
                            {t.sub_category}
                          </span>
                        )}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell>
                    {t.last_occurrence ? formatDate(t.last_occurrence) : "-"}
                  </TableCell>
                  <TableCell>
                    {t.next_expected ? formatDate(t.next_expected) : "-"}
                  </TableCell>
                  <TableCell>
                    <StatusBadge transaction={t} />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => onEdit(t)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-red-500 hover:text-red-600"
                        onClick={() => {
                          if (t.id !== null) onDelete(t.id);
                        }}
                        disabled={t.id === null}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
