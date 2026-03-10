import { useState, useEffect } from "react";
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
import type {
  RecurringTransaction,
  UpdateRecurringRequest,
} from "@/api/types";

interface EditRecurringDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  transaction: RecurringTransaction | null;
  onSubmit: (id: number, data: UpdateRecurringRequest) => void;
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

export default function EditRecurringDialog({
  open,
  onOpenChange,
  transaction,
  onSubmit,
}: EditRecurringDialogProps) {
  const [form, setForm] = useState({
    description: "",
    expected_amount: "",
    frequency: "monthly",
    category: "",
    sub_category: "",
    is_expected: true,
  });

  useEffect(() => {
    if (transaction && open) {
      setForm({
        description: transaction.description,
        expected_amount: String(Math.abs(transaction.expected_amount)),
        frequency: transaction.frequency,
        category: transaction.category ?? "",
        sub_category: transaction.sub_category ?? "",
        is_expected: transaction.is_expected,
      });
    }
  }, [transaction, open]);

  const isValid =
    form.description.trim() !== "" && form.expected_amount.trim() !== "";

  function handleSubmit() {
    if (!isValid || !transaction || transaction.id === null) return;

    const updates: UpdateRecurringRequest = {};
    const trimmedDesc = form.description.trim();
    const amount = parseFloat(form.expected_amount);
    const trimmedCat = form.category.trim();
    const trimmedSub = form.sub_category.trim();

    if (trimmedDesc !== transaction.description) {
      updates.description = trimmedDesc;
    }
    if (amount !== Math.abs(transaction.expected_amount)) {
      updates.expected_amount = amount;
    }
    if (form.frequency !== transaction.frequency) {
      updates.frequency = form.frequency;
    }
    if (trimmedCat !== (transaction.category ?? "")) {
      updates.category = trimmedCat;
    }
    if (trimmedSub !== (transaction.sub_category ?? "")) {
      updates.sub_category = trimmedSub;
    }
    if (form.is_expected !== transaction.is_expected) {
      updates.is_expected = form.is_expected;
    }

    onSubmit(transaction.id, updates);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Recurring Transaction</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="edit-description">Description</Label>
            <Input
              id="edit-description"
              value={form.description}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, description: e.target.value }))
              }
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="edit-amount">Expected Amount</Label>
            <Input
              id="edit-amount"
              type="number"
              step="0.01"
              min="0"
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
            <Label htmlFor="edit-frequency">Frequency</Label>
            <Select
              value={form.frequency}
              onValueChange={(value) =>
                setForm((prev) => ({ ...prev, frequency: value }))
              }
            >
              <SelectTrigger id="edit-frequency">
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
              <Label htmlFor="edit-category">Category</Label>
              <Input
                id="edit-category"
                value={form.category}
                onChange={(e) =>
                  setForm((prev) => ({ ...prev, category: e.target.value }))
                }
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="edit-subcategory">Sub-category</Label>
              <Input
                id="edit-subcategory"
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
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!isValid}>
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
