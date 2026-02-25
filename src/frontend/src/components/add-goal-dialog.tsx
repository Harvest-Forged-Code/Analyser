import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface AddGoalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  categories: string[];
  year: number;
  onAdd: (category: string, amount: number) => void;
  categoryLabel?: string;
  amountLabel?: string;
  existingCategories?: string[];
  isPending?: boolean;
}

export default function AddGoalDialog({
  open,
  onOpenChange,
  categories,
  year,
  onAdd,
  categoryLabel = "Category",
  amountLabel = "Monthly Limit",
  existingCategories = [],
  isPending = false,
}: AddGoalDialogProps) {
  const [selectedCategory, setSelectedCategory] = React.useState("");
  const [amount, setAmount] = React.useState("");

  const availableCategories = categories.filter(
    (cat) => !existingCategories.includes(cat)
  );

  const handleAdd = () => {
    if (!selectedCategory || !amount) return;
    const parsed = parseFloat(amount);
    if (isNaN(parsed) || parsed <= 0) return;
    onAdd(selectedCategory, parsed);
    setSelectedCategory("");
    setAmount("");
  };

  const handleOpenChange = (value: boolean) => {
    if (!value) {
      setSelectedCategory("");
      setAmount("");
    }
    onOpenChange(value);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add {categoryLabel} for {year}</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label>{categoryLabel}</Label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger>
                <SelectValue placeholder={`Select ${categoryLabel.toLowerCase()}`} />
              </SelectTrigger>
              <SelectContent>
                {availableCategories.length === 0 ? (
                  <SelectItem value="__none" disabled>
                    No categories available
                  </SelectItem>
                ) : (
                  availableCategories.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>{amountLabel}</Label>
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              step="0.01"
              min="0"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleAdd}
            disabled={!selectedCategory || !amount || isPending}
          >
            {isPending ? "Adding..." : "Add"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
