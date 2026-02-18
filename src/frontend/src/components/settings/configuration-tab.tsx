import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Save, RotateCcw } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useConfig, useSaveConfig } from "@/api/hooks/use-settings";
import IniEditor from "./ini-editor";

interface ConfigurationTabProps {
  isDark: boolean;
}

export default function ConfigurationTab({ isDark }: ConfigurationTabProps) {
  const { data, isLoading } = useConfig();
  const saveConfigMutation = useSaveConfig();

  const [editedContent, setEditedContent] = useState<string>("");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Populate editor from server once (and only on reset)
  useEffect(() => {
    if (data?.content !== undefined && !hasUnsavedChanges) {
      setEditedContent(data.content);
    }
  }, [data?.content, hasUnsavedChanges]);

  const handleChange = (value: string) => {
    setEditedContent(value);
    setHasUnsavedChanges(true);
  };

  const handleSave = async () => {
    try {
      await saveConfigMutation.mutateAsync(editedContent);
      setHasUnsavedChanges(false);
      toast.success("Configuration saved successfully");
    } catch (error: unknown) {
      const message =
        error instanceof Error ? error.message : "Failed to save configuration";
      toast.error(message);
    }
  };

  const handleReset = () => {
    if (data?.content !== undefined) {
      setEditedContent(data.content);
      setHasUnsavedChanges(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Configuration</h2>
          <p className="text-sm text-muted-foreground">
            Edit the raw INI configuration file directly
          </p>
        </div>

        <div className="flex shrink-0 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={!hasUnsavedChanges || isLoading}
          >
            <RotateCcw className="mr-1.5 h-4 w-4" />
            Reset
          </Button>
          <Button
            size="sm"
            onClick={handleSave}
            disabled={!hasUnsavedChanges || saveConfigMutation.isPending}
          >
            <Save className="mr-1.5 h-4 w-4" />
            {saveConfigMutation.isPending ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>

      <Separator />

      {isLoading ? (
        <Skeleton className="h-[420px] w-full" />
      ) : (
        <IniEditor
          value={editedContent}
          onChange={handleChange}
          isDark={isDark}
        />
      )}
    </div>
  );
}
