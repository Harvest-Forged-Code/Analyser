import { Repeat, Calendar, CheckCircle2, AlertTriangle } from "lucide-react";
import KpiCard from "@/components/kpi-card";
import { formatCurrency } from "@/lib/utils";
import {
  COLOR_PRIMARY,
  COLOR_POSITIVE,
  COLOR_WARNING,
  COLOR_NEGATIVE,
} from "@/lib/constants";
import type { RecurringSummary } from "@/api/types";

interface RecurringKpiCardsProps {
  summary: RecurringSummary;
  anomalyCount: number;
}

export default function RecurringKpiCards({
  summary,
  anomalyCount,
}: RecurringKpiCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <KpiCard
        title="Monthly Cost"
        value={formatCurrency(summary.total_monthly_cost)}
        description="Active recurring charges"
        icon={<Repeat className="h-5 w-5" />}
        iconColor={COLOR_PRIMARY}
      />
      <KpiCard
        title="Yearly Projection"
        value={formatCurrency(summary.total_yearly_projection)}
        icon={<Calendar className="h-5 w-5" />}
        iconColor={COLOR_WARNING}
      />
      <KpiCard
        title="Active Subscriptions"
        value={summary.active_count}
        description={`${summary.confirmed_count} confirmed, ${summary.unconfirmed_count} unconfirmed`}
        icon={<CheckCircle2 className="h-5 w-5" />}
        iconColor={COLOR_POSITIVE}
      />
      <KpiCard
        title="Anomalies"
        value={anomalyCount}
        description="Unresolved anomalies"
        icon={<AlertTriangle className="h-5 w-5" />}
        iconColor={COLOR_NEGATIVE}
      />
    </div>
  );
}
