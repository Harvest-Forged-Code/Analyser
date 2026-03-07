import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface EditMappingKeywordDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  originalDescription: string;
  subCategory: string;
  onConfirm: (keyword: string) => void;
  isPending?: boolean;
}

export default function EditMappingKeywordDialog({
  open,
  onOpenChange,
  originalDescription,
  subCategory,
  onConfirm,
  isPending = false,
}: EditMappingKeywordDialogProps) {
  const [keyword, setKeyword] = React.useState(originalDescription);

  React.useEffect(() => {
    if (open) {
      setKeyword(originalDescription);
    }
  }, [open, originalDescription]);

  const handleConfirm = () => {
    const trimmed = keyword.trim();
    if (!trimmed) return;
    onConfirm(trimmed);
  };

  const handleOpenChange = (value: boolean) => {
    if (!value) {
      setKeyword(originalDescription);
    }
    onOpenChange(value);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Mapping — {subCategory}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>Original Description</Label>
            <p className="text-sm text-muted-foreground break-all rounded-md border bg-muted/50 px-3 py-2">
              {originalDescription}
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="keyword">Keyword</Label>
            <Input
              id="keyword"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              autoFocus
            />
            <p className="text-xs text-muted-foreground">
              Edit to the shortest substring that uniquely identifies this merchant
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleConfirm}
            disabled={!keyword.trim() || isPending}
          >
            {isPending ? "Saving..." : "Add Mapping"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
