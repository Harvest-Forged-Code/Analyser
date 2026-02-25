import React from "react";
import { Trash2 } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableFooter,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

interface GoalsSpreadsheetProps {
  data: Record<string, Record<string, number>>;
  year: number;
  isLoading: boolean;
  onCellEdit: (category: string, yearMonth: string, value: number) => void;
  onDeleteCategory: (category: string) => void;
  categoryLabel?: string;
}

interface EditableCellProps {
  value: number;
  onSave: (value: number) => void;
}

function EditableCell({ value, onSave }: EditableCellProps) {
  const [editing, setEditing] = React.useState(false);
  const [editValue, setEditValue] = React.useState(value.toString());
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  React.useEffect(() => {
    setEditValue(value.toString());
  }, [value]);

  const handleSave = () => {
    const parsed = parseFloat(editValue);
    if (!isNaN(parsed) && parsed >= 0 && parsed !== value) {
      onSave(parsed);
    }
    setEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === "Tab") {
      e.preventDefault();
      handleSave();
    } else if (e.key === "Escape") {
      setEditValue(value.toString());
      setEditing(false);
    }
  };

  if (editing) {
    return (
      <Input
        ref={inputRef}
        type="number"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        onBlur={handleSave}
        onKeyDown={handleKeyDown}
        className="h-7 w-20 text-right font-mono text-xs px-1"
        step="0.01"
        min="0"
      />
    );
  }

  return (
    <button
      type="button"
      onClick={() => setEditing(true)}
      className="w-full text-right font-mono text-xs cursor-pointer hover:bg-muted rounded px-1 py-0.5 transition-colors"
    >
      {formatCurrency(value)}
    </button>
  );
}

export default function GoalsSpreadsheet({
  data,
  year,
  isLoading,
  onCellEdit,
  onDeleteCategory,
  categoryLabel = "Category",
}: GoalsSpreadsheetProps) {
  const categories = Object.keys(data);
  const yearMonths = Array.from({ length: 12 }, (_, i) => `${year}-${String(i + 1).padStart(2, "0")}`);

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }

  if (categories.length === 0) {
    return null;
  }

  // Compute totals and averages
  const monthTotals = yearMonths.map((ym) =>
    categories.reduce((sum, cat) => sum + (data[cat]?.[ym] ?? 0), 0)
  );
  const categoryAverages: Record<string, number> = {};
  for (const cat of categories) {
    const vals = yearMonths.map((ym) => data[cat]?.[ym] ?? 0);
    categoryAverages[cat] = vals.reduce((a, b) => a + b, 0) / 12;
  }
  const totalAverage = monthTotals.reduce((a, b) => a + b, 0) / 12;

  return (
    <div className="border rounded-lg">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="sticky left-0 bg-background z-10 min-w-[120px]">
              {categoryLabel}
            </TableHead>
            {MONTHS.map((month) => (
              <TableHead key={month} className="text-right min-w-[80px]">
                {month}
              </TableHead>
            ))}
            <TableHead className="text-right min-w-[80px]">Avg</TableHead>
            <TableHead className="text-center w-[60px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {categories.map((category) => (
            <TableRow key={category}>
              <TableCell className="sticky left-0 bg-background z-10 font-medium">
                {category}
              </TableCell>
              {yearMonths.map((ym) => (
                <TableCell key={ym} className="p-1">
                  <EditableCell
                    value={data[category]?.[ym] ?? 0}
                    onSave={(value) => onCellEdit(category, ym, value)}
                  />
                </TableCell>
              ))}
              <TableCell className="text-right font-mono text-xs text-muted-foreground">
                {formatCurrency(categoryAverages[category] ?? 0)}
              </TableCell>
              <TableCell className="text-center">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDeleteCategory(category)}
                  className="h-7 w-7 p-0"
                >
                  <Trash2 className="h-3.5 w-3.5 text-destructive" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell className="sticky left-0 bg-muted/50 z-10 font-bold">
              Total
            </TableCell>
            {monthTotals.map((total, i) => (
              <TableCell key={yearMonths[i]} className="text-right font-mono text-xs font-bold">
                {formatCurrency(total)}
              </TableCell>
            ))}
            <TableCell className="text-right font-mono text-xs font-bold">
              {formatCurrency(totalAverage)}
            </TableCell>
            <TableCell />
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}
