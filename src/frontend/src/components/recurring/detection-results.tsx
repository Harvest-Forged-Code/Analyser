import { Check, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { formatCurrency } from "@/lib/utils";
import type { RecurringDetection } from "@/api/types";

interface DetectionResultsProps {
  detections: RecurringDetection[];
  onConfirm: (detection: RecurringDetection) => void;
  onDismiss: (detection: RecurringDetection) => void;
}

export default function DetectionResults({
  detections,
  onConfirm,
  onDismiss,
}: DetectionResultsProps) {
  if (detections.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Detected Patterns ({detections.length})</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {detections.map((d, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-medium truncate">{d.description}</span>
                  <Badge variant="outline">{d.frequency}</Badge>
                  {d.category && (
                    <Badge variant="secondary">{d.category}</Badge>
                  )}
                </div>
                <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                  <span>{formatCurrency(Math.abs(d.expected_amount))}</span>
                  <span>{d.occurrences} occurrences</span>
                  <div className="flex items-center gap-2 flex-1 max-w-[150px]">
                    <Progress
                      value={d.confidence_score * 100}
                      className="h-2"
                    />
                    <span>{(d.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1 ml-4">
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-emerald-500 hover:text-emerald-600"
                  onClick={() => onConfirm(d)}
                >
                  <Check className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  className="text-red-500 hover:text-red-600"
                  onClick={() => onDismiss(d)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
