import { useState } from "react";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface AddRecurringDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    description: string;
    expected_amount: number;
    frequency: string;
    category: string;
    sub_category: string;
    is_expected: boolean;
  }) => void;
}

const FREQUENCY_OPTIONS = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "bi-weekly", label: "Bi-weekly" },
  { value: "monthly", label: "Monthly" },
  { value: "quarterly", label: "Quarterly" },
  { value: "semi-annual", label: "Semi-annual" },
  { value: "yearly", label: "Yearly" },
] as const;

const INITIAL_STATE = {
  description: "",
  expected_amount: "",
  frequency: "monthly",
  category: "",
  sub_category: "",
};

export default function AddRecurringDialog({
  open,
  onOpenChange,
  onSubmit,
}: AddRecurringDialogProps) {
  const [form, setForm] = useState(INITIAL_STATE);

  const isValid =
    form.description.trim() !== "" && form.expected_amount.trim() !== "";

  function handleOpenChange(next: boolean) {
    if (!next) setForm(INITIAL_STATE);
    onOpenChange(next);
  }

  function handleSubmit() {
    if (!isValid) return;
    onSubmit({
      description: form.description.trim(),
      expected_amount: parseFloat(form.expected_amount),
      frequency: form.frequency,
      category: form.category.trim(),
      sub_category: form.sub_category.trim(),
      is_expected: true,
    });
    setForm(INITIAL_STATE);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add Recurring Transaction</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="add-description">Description</Label>
            <Input
              id="add-description"
              placeholder="e.g. Netflix, Gym membership"
              value={form.description}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, description: e.target.value }))
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="add-amount">Expected Amount</Label>
            <Input
              id="add-amount"
              type="number"
              step="0.01"
              min="0"
              placeholder="0.00"
              value={form.expected_amount}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  expected_amount: e.target.value,
                }))
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="add-frequency">Frequency</Label>
            <Select
              value={form.frequency}
              onValueChange={(value) =>
                setForm((prev) => ({ ...prev, frequency: value }))
              }
            >
              <SelectTrigger id="add-frequency">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FREQUENCY_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="grid gap-2">
              <Label htmlFor="add-category">Category</Label>
              <Input
                id="add-category"
                placeholder="e.g. Entertainment"
                value={form.category}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, category: e.target.value }))
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="add-subcategory">Sub-category</Label>
              <Input
                id="add-subcategory"
                placeholder="e.g. Streaming"
                value={form.sub_category}
                onChange={(e) =>
                  setForm((prev) => ({
                    ...prev,
                    sub_category: e.target.value,
                  }))
                }
              />
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid}>
            Add
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
