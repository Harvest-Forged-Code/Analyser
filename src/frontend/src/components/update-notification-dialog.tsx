import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { ReleaseInfo } from "@/api/types";

interface UpdateNotificationDialogProps {
  open: boolean;
  currentVersion: string;
  release: ReleaseInfo;
  onSkip: () => void;
  onDismiss: () => void;
}

export function UpdateNotificationDialog({
  open,
  currentVersion,
  release,
  onSkip,
  onDismiss,
}: UpdateNotificationDialogProps) {
  const publishedDate = release.published_at
    ? new Date(release.published_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "";

  const handleViewRelease = () => {
    window.open(release.html_url, "_blank", "noopener,noreferrer");
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onDismiss()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            Update Available
            <Badge variant="default">v{release.version}</Badge>
          </DialogTitle>
          <DialogDescription>
            A new version of Budget Analyser is available.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              Current: <span className="font-medium text-foreground">v{currentVersion}</span>
            </span>
            <span className="text-muted-foreground">
              Latest: <span className="font-medium text-foreground">v{release.version}</span>
            </span>
          </div>

          {release.name && (
            <div className="text-sm">
              <span className="font-medium">{release.name}</span>
              {publishedDate && (
                <span className="ml-2 text-muted-foreground">{publishedDate}</span>
              )}
            </div>
          )}

          {release.body && (
            <ScrollArea className="h-48 rounded-md border p-3">
              <pre className="whitespace-pre-wrap text-xs text-muted-foreground font-sans">
                {release.body}
              </pre>
            </ScrollArea>
          )}
        </div>

        <DialogFooter className="flex-row gap-2 sm:gap-0">
          <Button variant="ghost" size="sm" onClick={onSkip}>
            Skip This Version
          </Button>
          <Button variant="outline" size="sm" onClick={onDismiss}>
            Remind Me Later
          </Button>
          <Button size="sm" onClick={handleViewRelease}>
            View Release
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
