import * as React from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface KpiCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  iconColor?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export default function KpiCard({
  title,
  value,
  description,
  icon,
  iconColor,
  trend,
  className,
}: KpiCardProps) {
  return (
    <Card className={className}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {trend && (
              <div className="flex items-center gap-1">
                {trend.isPositive ? (
                  <TrendingUp className="h-4 w-4 text-emerald-500" />
                ) : (
                  <TrendingDown className="h-4 w-4 text-red-500" />
                )}
                <span
                  className={cn(
                    "text-xs font-medium",
                    trend.isPositive ? "text-emerald-500" : "text-red-500"
                  )}
                >
                  {trend.isPositive ? "+" : ""}{trend.value}%
                </span>
              </div>
            )}
            {description && (
              <p className="text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {icon && (
            <div style={iconColor ? { color: iconColor } : undefined} className={iconColor ? undefined : "text-muted-foreground"}>
              {icon}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
