import { useState, useMemo } from "react";
import { ChevronRight } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCurrency, formatPercentage, cn } from "@/lib/utils";

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
}

export default function CategoryBreakdownTable({ data, search = "" }: CategoryBreakdownTableProps) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

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
}: {
  group: CategoryGroup;
  isOpen: boolean;
  grandTotal: number;
  categoryPct: number;
  onToggle: () => void;
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
          const subPct = grandTotal > 0 ? (sub.amount / grandTotal) * 100 : 0;
          return (
            <TableRow key={`${group.category}-${sub.sub_category}`} className="bg-muted/30">
              <TableCell />
              <TableCell className="pl-10 text-muted-foreground">
                {sub.sub_category}
              </TableCell>
              <TableCell className="text-right">
                {formatCurrency(sub.amount)}
              </TableCell>
              <TableCell className="text-right text-muted-foreground">
                {formatPercentage(subPct)}
              </TableCell>
            </TableRow>
          );
        })}
    </>
  );
}
