import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MONTH_NAMES_SHORT } from "@/lib/constants";

export interface MonthYearSelectorProps {
  months?: string[];
  years?: number[];
  selectedMonth?: string | null;
  selectedYear?: number | null;
  onMonthChange?: (month: string) => void;
  onYearChange?: (year: number) => void;
  showMonths?: boolean;
  showYears?: boolean;
}

function formatMonthDisplay(monthStr: string): string {
  const parts = monthStr.split("-");
  if (parts.length !== 2) return monthStr;
  const [year, month] = parts;
  const monthIndex = parseInt(month ?? "1", 10) - 1;
  if (monthIndex < 0 || monthIndex >= MONTH_NAMES_SHORT.length) return monthStr;
  return `${MONTH_NAMES_SHORT[monthIndex]} ${year}`;
}

export default function MonthYearSelector({
  months = [],
  years = [],
  selectedMonth = null,
  selectedYear = null,
  onMonthChange,
  onYearChange,
  showMonths = true,
  showYears = true,
}: MonthYearSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      {showMonths && months.length > 0 && (
        <Select
          value={selectedMonth ?? undefined}
          onValueChange={(value) => {
            if (value) onMonthChange?.(value);
          }}
        >
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Select month">
              {selectedMonth ? formatMonthDisplay(selectedMonth) : "Select month"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {months.map((month) => (
              <SelectItem key={month} value={month}>
                {formatMonthDisplay(month)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {showYears && years.length > 0 && (
        <Select
          value={selectedYear?.toString() ?? undefined}
          onValueChange={(value) => {
            if (value) onYearChange?.(parseInt(value, 10));
          }}
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Select year">
              {selectedYear ?? "Select year"}
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            {years.map((year) => (
              <SelectItem key={year} value={year.toString()}>
                {year}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
