import { Database, CreditCard, Calendar, Copy } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn, formatDate } from "@/lib/utils";
import type { UploadStats } from "@/api/types";

interface UploadKpiCardsProps {
  stats: UploadStats;
}

export default function UploadKpiCards({ stats }: UploadKpiCardsProps) {
  const highDuplicateRate = stats.duplicate_rate > 20;

  return (
    <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
      {/* Total Transactions */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Total Transactions
              </p>
              <p className="text-2xl font-bold">
                {stats.total_transactions.toLocaleString()}
              </p>
            </div>
            <Database className="h-5 w-5 text-sky-500" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {stats.total_uploads} uploads total
          </p>
        </CardContent>
      </Card>

      {/* Active Accounts */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Active Accounts
              </p>
              <p className="text-2xl font-bold">{stats.total_accounts}</p>
            </div>
            <CreditCard className="h-5 w-5 text-violet-500" />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Unique bank accounts
          </p>
        </CardContent>
      </Card>

      {/* Last Upload */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Last Upload
              </p>
              <p className="text-2xl font-bold">
                {stats.last_upload_date
                  ? formatDate(stats.last_upload_date)
                  : "Never"}
              </p>
            </div>
            <Calendar className="h-5 w-5 text-amber-500" />
          </div>
        </CardContent>
      </Card>

      {/* Duplicate Rate */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Duplicate Rate
              </p>
              <p
                className={cn(
                  "text-2xl font-bold",
                  highDuplicateRate ? "text-red-600" : "text-emerald-600"
                )}
              >
                {stats.duplicate_rate.toFixed(1)}%
              </p>
            </div>
            <Copy
              className={cn(
                "h-5 w-5",
                highDuplicateRate ? "text-red-500" : "text-emerald-500"
              )}
            />
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            {stats.total_duplicates_skipped.toLocaleString()} duplicates skipped
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
