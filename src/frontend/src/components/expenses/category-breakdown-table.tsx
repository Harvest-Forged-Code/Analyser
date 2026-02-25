import { useState, useMemo } from "react";
import { ChevronRight, Loader2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatCurrency, formatPercentage, cn } from "@/lib/utils";
import { useExpensesMonthTransactions } from "@/api/hooks/use-expenses";

interface ExpenseRow {
  category: string;
  sub_category: string;
  amount: number;
}

interface CategoryGroup {
  category: string;
  total: number;
  subCategories: { sub_category: string; amount: number }[];
}

interface CategoryBreakdownTableProps {
  data: Record<string, unknown>[];
  search?: string;
  period?: string;
}

export default function CategoryBreakdownTable({ data, search = "", period }: CategoryBreakdownTableProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [expandedSubs, setExpandedSubs] = useState<Record<string, boolean>>({});

  const grandTotal = useMemo(
    () => data.reduce((sum, row) => sum + ((row.amount as number) || 0), 0),
    [data],
  );

  const groups: CategoryGroup[] = useMemo(() => {
    const map = new Map<string, CategoryGroup>();

    for (const row of data as unknown as ExpenseRow[]) {
      const cat = row.category || "Other";
      let group = map.get(cat);
      if (!group) {
        group = { category: cat, total: 0, subCategories: [] };
        map.set(cat, group);
      }
      group.total += row.amount || 0;
      group.subCategories.push({
        sub_category: row.sub_category,
        amount: row.amount,
      });
    }

    // Sort groups by total descending, sub-categories by amount descending
    const result = Array.from(map.values());
    result.sort((a, b) => b.total - a.total);
    for (const g of result) {
      g.subCategories.sort((a, b) => b.amount - a.amount);
    }
    return result;
  }, [data]);

  const filteredGroups = useMemo(() => {
    if (!search) return groups;
    const term = search.toLowerCase();
    return groups.filter(
      (g) =>
        g.category.toLowerCase().includes(term) ||
        g.subCategories.some((s) =>
          s.sub_category.toLowerCase().includes(term),
        ),
    );
  }, [groups, search]);

  const toggle = (category: string) =>
    setExpanded((prev) => ({ ...prev, [category]: !prev[category] }));

  const toggleSub = (key: string) =>
    setExpandedSubs((prev) => ({ ...prev, [key]: !prev[key] }));

  return (
    <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-8" />
              <TableHead>Category</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">% of Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredGroups.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="h-24 text-center">
                  No results.
                </TableCell>
              </TableRow>
            ) : (
              filteredGroups.map((group) => {
                const isOpen = expanded[group.category] ?? false;
                const pct = grandTotal > 0 ? (group.total / grandTotal) * 100 : 0;
                return (
                  <CategoryGroupRows
                    key={group.category}
                    group={group}
                    isOpen={isOpen}
                    grandTotal={grandTotal}
                    categoryPct={pct}
                    onToggle={() => toggle(group.category)}
                    expandedSubs={expandedSubs}
                    onToggleSub={toggleSub}
                    period={period}
                  />
                );
              })
            )}
          </TableBody>
        </Table>
    </div>
  );
}

function CategoryGroupRows({
  group,
  isOpen,
  grandTotal,
  categoryPct,
  onToggle,
  expandedSubs,
  onToggleSub,
  period,
}: {
  group: CategoryGroup;
  isOpen: boolean;
  grandTotal: number;
  categoryPct: number;
  onToggle: () => void;
  expandedSubs: Record<string, boolean>;
  onToggleSub: (key: string) => void;
  period?: string;
}) {
  return (
    <>
      {/* Category header row */}
      <TableRow
        className="cursor-pointer hover:bg-muted/50"
        onClick={onToggle}
      >
        <TableCell className="w-8 px-2">
          <ChevronRight
            className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              isOpen && "rotate-90",
            )}
          />
        </TableCell>
        <TableCell>
          <span className="font-semibold">{group.category}</span>
          <span className="ml-2 text-xs text-muted-foreground">
            ({group.subCategories.length})
          </span>
        </TableCell>
        <TableCell className="text-right font-semibold">
          {formatCurrency(group.total)}
        </TableCell>
        <TableCell className="text-right font-semibold">
          {formatPercentage(categoryPct)}
        </TableCell>
      </TableRow>

      {/* Expanded sub-category rows */}
      {isOpen &&
        group.subCategories.map((sub) => {
          const subKey = `${group.category}::${sub.sub_category}`;
          const subPct = grandTotal > 0 ? (sub.amount / grandTotal) * 100 : 0;
          const isSubOpen = expandedSubs[subKey] ?? false;
          return (
            <SubCategoryRow
              key={subKey}
              category={group.category}
              subCategory={sub.sub_category}
              amount={sub.amount}
              pct={subPct}
              isOpen={isSubOpen}
              onToggle={() => onToggleSub(subKey)}
              period={period}
            />
          );
        })}
    </>
  );
}

function SubCategoryRow({
  category,
  subCategory,
  amount,
  pct,
  isOpen,
  onToggle,
  period,
}: {
  category: string;
  subCategory: string;
  amount: number;
  pct: number;
  isOpen: boolean;
  onToggle: () => void;
  period?: string;
}) {
  return (
    <>
      <TableRow
        className="bg-muted/30 cursor-pointer hover:bg-muted/50"
        onClick={onToggle}
      >
        <TableCell className="px-2">
          <ChevronRight
            className={cn(
              "ml-4 h-3.5 w-3.5 text-muted-foreground transition-transform",
              isOpen && "rotate-90",
            )}
          />
        </TableCell>
        <TableCell className="pl-10 text-muted-foreground">
          {subCategory}
        </TableCell>
        <TableCell className="text-right">
          {formatCurrency(amount)}
        </TableCell>
        <TableCell className="text-right text-muted-foreground">
          {formatPercentage(pct)}
        </TableCell>
      </TableRow>
      {isOpen && period && (
        <SubCategoryTransactions
          period={period}
          category={category}
          subCategory={subCategory}
        />
      )}
    </>
  );
}

function SubCategoryTransactions({
  period,
  category,
  subCategory,
}: {
  period: string;
  category: string;
  subCategory: string;
}) {
  const { data: transactions, isLoading } = useExpensesMonthTransactions(
    period,
    category,
    subCategory,
  );

  if (isLoading) {
    return (
      <TableRow className="bg-muted/15">
        <TableCell colSpan={4} className="py-3 text-center">
          <Loader2 className="inline h-4 w-4 animate-spin text-muted-foreground" />
          <span className="ml-2 text-sm text-muted-foreground">Loading transactions...</span>
        </TableCell>
      </TableRow>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <TableRow className="bg-muted/15">
        <TableCell colSpan={4} className="py-3 text-center text-sm text-muted-foreground">
          No transactions found.
        </TableCell>
      </TableRow>
    );
  }

  return (
    <>
      {/* Transaction header */}
      <TableRow className="bg-muted/15">
        <TableCell />
        <TableCell className="pl-14 text-xs font-medium text-muted-foreground" colSpan={3}>
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
              {transactions.length} transaction{transactions.length !== 1 ? "s" : ""}
            </Badge>
          </div>
        </TableCell>
      </TableRow>
      {transactions.map((txn, idx) => {
        const txnDate = txn.transaction_date as string;
        const txnDesc = txn.description as string;
        const txnAmount = Math.abs(txn.amount as number);
        return (
          <TableRow
            key={`txn-${txnDate}-${idx}`}
            className="bg-muted/15 text-sm"
          >
            <TableCell />
            <TableCell className="pl-14">
              <div className="flex flex-col gap-0.5">
                <span className="text-foreground">{txnDesc}</span>
                <span className="text-xs text-muted-foreground">{txnDate}</span>
              </div>
            </TableCell>
            <TableCell className="text-right">
              {formatCurrency(txnAmount)}
            </TableCell>
            <TableCell />
          </TableRow>
        );
      })}
    </>
  );
}
