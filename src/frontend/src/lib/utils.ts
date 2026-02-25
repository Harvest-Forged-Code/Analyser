import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number, showSign = false): string {
  if (showSign && amount > 0)
    return `+$${amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  if (amount < 0)
    return `-$${Math.abs(amount).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  return `$${amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatPercentage(value: number, showSign = false): string {
  if (showSign && value > 0) return `+${value.toFixed(1)}%`;
  return `${value.toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/**
 * Find the current month in available months, or fall back to the latest.
 *
 * Months are expected in "YYYY-MM" format.
 */
export function findDefaultMonth(months: string[]): string | undefined {
  if (months.length === 0) return undefined;
  const now = new Date();
  const current = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  if (months.includes(current)) return current;
  // Fall back to latest available month (last after sort)
    return [...months].sort().slice(-1)[0];
}
