import { CheckCircle2, Minus } from "lucide-react";
import { useUploadStatus } from "@/api/hooks/use-upload";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { BankUploadStatus } from "@/api/types";

function groupByAccountType(
  statuses: BankUploadStatus[]
): Record<string, BankUploadStatus[]> {
  const groups: Record<string, BankUploadStatus[]> = {};
  for (const s of statuses) {
    const key = s.account_type;
    if (!groups[key]) groups[key] = [];
    groups[key].push(s);
  }
  return groups;
}

export default function UploadStatusGrid() {
  const { data: statuses, isLoading } = useUploadStatus();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Bank Upload Status</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-32 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!statuses || statuses.length === 0) {
    return null;
  }

  const grouped = groupByAccountType(statuses);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Bank Upload Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {Object.entries(grouped).map(([accountType, banks]) => (
          <div key={accountType} className="space-y-3">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              {accountType === "credit" ? "Credit Cards" : "Checking Accounts"}
            </h3>
            <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {banks.map((bank) => (
                <div
                  key={`${bank.bank_name}-${bank.account_type}`}
                  className="flex items-center justify-between rounded-lg border p-3"
                >
                  <div className="space-y-1">
                    <p className="text-sm font-medium capitalize">
                      {bank.bank_name}
                    </p>
                    <Badge
                      variant="secondary"
                      className={
                        bank.account_type === "credit"
                          ? "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400"
                          : "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400"
                      }
                    >
                      {bank.account_type}
                    </Badge>
                  </div>
                  {bank.is_uploaded ? (
                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                  ) : (
                    <Minus className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
