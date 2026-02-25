import { useState } from "react";
import { toast } from "sonner";
import { Separator } from "@/components/ui/separator";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useLogLevels,
  useCurrentLogLevel,
  useSetLogLevel,
} from "@/api/hooks/use-settings";

export default function LoggingTab() {
  const { data: logLevels, isLoading: levelsLoading } = useLogLevels();
  const { data: currentLevel, isLoading: currentLoading } = useCurrentLogLevel();
  const setLogLevelMutation = useSetLogLevel();

  const [selectedLogLevel, setSelectedLogLevel] = useState<string>("");

  // Initialise selection from server once loaded
  if (currentLevel && !selectedLogLevel) {
    setSelectedLogLevel(currentLevel.log_level);
  }

  const handleSave = async () => {
    if (!selectedLogLevel) return;
    try {
      await setLogLevelMutation.mutateAsync(selectedLogLevel);
      toast.success("Log level updated successfully");
    } catch {
      toast.error("Failed to update log level");
    }
  };

  const isLoading = levelsLoading || currentLoading;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Logging</h2>
        <p className="text-sm text-muted-foreground">
          Configure the application logging verbosity
        </p>
      </div>

      <Separator />

      {isLoading ? (
        <div className="space-y-3 max-w-md">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-28" />
        </div>
      ) : (
        <div className="max-w-md space-y-4">
          <div className="space-y-1.5">
            <Label className="text-sm font-medium">Current Level</Label>
            <div>
              <Badge variant="default">{currentLevel?.log_level ?? "—"}</Badge>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="log-level-select">New Level</Label>
            <Select value={selectedLogLevel} onValueChange={setSelectedLogLevel}>
              <SelectTrigger id="log-level-select">
                <SelectValue placeholder="Select log level" />
              </SelectTrigger>
              <SelectContent>
                {logLevels?.map((level) => (
                  <SelectItem key={level} value={level}>
                    {level}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            onClick={handleSave}
            disabled={!selectedLogLevel || setLogLevelMutation.isPending}
          >
            {setLogLevelMutation.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      )}
    </div>
  );
}
