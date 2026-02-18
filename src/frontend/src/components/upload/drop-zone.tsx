import { useState, useCallback, useRef, useEffect } from "react";
import { Upload, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DropZoneProps {
  onFileSelected: (path: string) => void;
  selectedFile: string | null;
}

export default function DropZone({ onFileSelected, selectedFile }: DropZoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isTauri = "__TAURI__" in window;

  useEffect(() => {
    if (!isTauri) return;

    let unlisten: (() => void) | undefined;

    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        const unlistenFn = await listen<{ paths: string[] }>(
          "tauri://drag-drop",
          (event) => {
            const paths = event.payload.paths;
            if (paths.length > 0) {
              const csvFile = paths.find((p) => p.toLowerCase().endsWith(".csv"));
              if (csvFile) {
                onFileSelected(csvFile);
              }
            }
            setIsDragOver(false);
          }
        );
        unlisten = unlistenFn;
      } catch {
        // Tauri event API not available
      }
    })();

    return () => {
      unlisten?.();
    };
  }, [isTauri, onFileSelected]);

  const handleBrowse = useCallback(async () => {
    if (isTauri) {
      try {
        const { open } = await import("@tauri-apps/plugin-dialog");
        const selected = await open({
          multiple: false,
          filters: [{ name: "CSV Files", extensions: ["csv"] }],
        });
        if (selected) {
          onFileSelected(selected as string);
        }
      } catch {
        // Fall through to file input
        fileInputRef.current?.click();
      }
    } else {
      fileInputRef.current?.click();
    }
  }, [isTauri, onFileSelected]);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        onFileSelected(file.name);
      }
    },
    [onFileSelected]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      if (!isTauri) {
        const file = e.dataTransfer.files?.[0];
        if (file && file.name.toLowerCase().endsWith(".csv")) {
          onFileSelected(file.name);
        }
      }
    },
    [isTauri, onFileSelected]
  );

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors",
        selectedFile
          ? "border-emerald-300 bg-emerald-50 dark:border-emerald-700 dark:bg-emerald-950/20"
          : isDragOver
            ? "border-blue-400 bg-blue-50 dark:border-blue-600 dark:bg-blue-950/20"
            : "border-muted-foreground/25 hover:border-muted-foreground/50"
      )}
    >
      {selectedFile ? (
        <>
          <FileText className="h-10 w-10 text-emerald-500" />
          <p className="text-sm font-medium text-emerald-700 dark:text-emerald-400">
            {selectedFile.split(/[/\\]/).pop()}
          </p>
          <p className="text-xs text-muted-foreground truncate max-w-full">
            {selectedFile}
          </p>
        </>
      ) : (
        <>
          <Upload className="h-10 w-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Drag & drop your CSV file here
          </p>
        </>
      )}
      <Button variant="outline" size="sm" onClick={handleBrowse}>
        Browse
      </Button>
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={handleFileInput}
      />
    </div>
  );
}
