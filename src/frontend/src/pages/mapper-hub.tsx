import { useState, useMemo } from "react";
import { Map, Plus, AlertCircle, CheckCircle } from "lucide-react";
import EditMappingKeywordDialog from "@/components/edit-mapping-keyword-dialog";
import {
  useUnmappedDescriptions,
  useSubCategories,
  useCategories,
  useAddDescriptions,
  useCreateSubCategory,
  useSubCategoryMapping,
  useCashflowMapping,
  type UnmappedDescription,
} from "@/api/hooks/use-mappers";
import PageHeader from "@/components/page-header";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function MapperHubPage() {
  const { data: unmappedDescriptions, isLoading: unmappedLoading } = useUnmappedDescriptions();
  const { data: subCategories, isLoading: subCategoriesLoading } = useSubCategories();
  const { data: categories, isLoading: categoriesLoading } = useCategories();
  const { data: subCategoryMapping, isLoading: subCategoryMappingLoading } = useSubCategoryMapping();
  const { data: cashflowMapping, isLoading: cashflowMappingLoading } = useCashflowMapping();

  const addDescriptionsMutation = useAddDescriptions();
  const createSubCategoryMutation = useCreateSubCategory();

  // State for unmapped descriptions
  const [selectedMappings, setSelectedMappings] = useState<Record<string, string>>({});
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [pendingItem, setPendingItem] = useState<UnmappedDescription | null>(null);

  // State for new sub-category form
  const [newSubCategory, setNewSubCategory] = useState<string>("");
  const [newCategory, setNewCategory] = useState<string>("");
  const [newCashflow, setNewCashflow] = useState<string>("expense");

  const handleOpenEditDialog = (item: UnmappedDescription) => {
    setPendingItem(item);
    setEditDialogOpen(true);
  };

  const handleConfirmKeyword = async (keyword: string) => {
    if (!pendingItem) return;
    const subCategory = selectedMappings[pendingItem.description];
    try {
      await addDescriptionsMutation.mutateAsync({
        sub_category: subCategory,
        descriptions: [keyword],
      });
      setSelectedMappings((prev) => {
        const updated = { ...prev };
        delete updated[pendingItem.description];
        return updated;
      });
      setEditDialogOpen(false);
      setPendingItem(null);
    } catch {
      // Error handled via onError toast in useAddDescriptions
    }
  };

  const handleCreateSubCategory = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!newSubCategory || !newCategory || !newCashflow) {
      alert("All fields are required");
      return;
    }

    try {
      await createSubCategoryMutation.mutateAsync({
        sub_category: newSubCategory,
        category: newCategory,
        cashflow: newCashflow,
      });
      // Clear form
      setNewSubCategory("");
      setNewCategory("");
      setNewCashflow("expense");
    } catch (error) {
      alert(`Failed to create sub-category: ${error}`);
    }
  };

  // Sub-category mapping table columns
  const subCategoryColumns: ColumnDef<{ subCategory: string; category: string }>[] = [
    {
      accessorKey: "subCategory",
      header: "Sub Category",
      cell: ({ row }) => <span className="font-medium">{row.getValue("subCategory")}</span>,
    },
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => <Badge variant="outline">{row.getValue("category")}</Badge>,
    },
  ];

  const subCategoryData = useMemo(() => {
    if (!subCategoryMapping) return [];
    return Object.entries(subCategoryMapping).map(([subCategory, category]) => ({
      subCategory,
      category,
    }));
  }, [subCategoryMapping]);

  // Cashflow mapping table columns
  const cashflowColumns: ColumnDef<{ category: string; cashflow: string }>[] = [
    {
      accessorKey: "category",
      header: "Category",
      cell: ({ row }) => <span className="font-medium">{row.getValue("category")}</span>,
    },
    {
      accessorKey: "cashflow",
      header: "Cashflow Type",
      cell: ({ row }) => {
        const cashflow = row.getValue("cashflow") as string;
        const variant =
          cashflow === "income"
            ? "default"
            : cashflow === "expense"
              ? "destructive"
              : "secondary";
        return <Badge variant={variant}>{cashflow}</Badge>;
      },
    },
  ];

  const cashflowData = useMemo(() => {
    if (!cashflowMapping) return [];
    return Object.entries(cashflowMapping).map(([category, cashflow]) => ({
      category,
      cashflow,
    }));
  }, [cashflowMapping]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Mapper Hub"
        description="Manage transaction categorization"
      />

      <Tabs defaultValue="unmapped" className="space-y-6">
        <TabsList>
          <TabsTrigger value="unmapped">
            Unmapped
            {unmappedDescriptions && unmappedDescriptions.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {unmappedDescriptions.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="sub-categories">Sub-Categories</TabsTrigger>
          <TabsTrigger value="cashflow">Cashflow</TabsTrigger>
        </TabsList>

        <TabsContent value="unmapped" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Unmapped Descriptions</CardTitle>
              <CardDescription>
                Map transaction descriptions to sub-categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              {unmappedLoading || subCategoriesLoading ? (
                <Skeleton className="h-96 w-full" />
              ) : unmappedDescriptions && unmappedDescriptions.length > 0 ? (
                <div className="space-y-4">
                  {unmappedDescriptions.map((item) => (
                    <div
                      key={item.description}
                      className="flex items-center gap-4 p-4 border rounded-lg"
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{item.description}</p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <span className="text-sm text-muted-foreground">
                            ${Math.abs(item.total_amount).toFixed(2)}
                          </span>
                          {item.accounts.map((account) => (
                            <Badge key={account} variant="secondary" className="text-xs">
                              {account}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="w-64 shrink-0">
                        <Select
                          value={selectedMappings[item.description] || ""}
                          onValueChange={(value) =>
                            setSelectedMappings((prev) => ({ ...prev, [item.description]: value }))
                          }
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select sub-category" />
                          </SelectTrigger>
                          <SelectContent>
                            {subCategories && subCategories.length > 0 ? (
                              subCategories.map((subCat) => (
                                <SelectItem key={subCat} value={subCat}>
                                  {subCat}
                                </SelectItem>
                              ))
                            ) : (
                              <SelectItem value="none" disabled>
                                No sub-categories
                              </SelectItem>
                            )}
                          </SelectContent>
                        </Select>
                      </div>
                      <Button
                        onClick={() => handleOpenEditDialog(item)}
                        disabled={
                          !selectedMappings[item.description] || addDescriptionsMutation.isPending
                        }
                        size="sm"
                      >
                        <Plus className="mr-1 h-3 w-3" />
                        Add
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<CheckCircle />}
                  title="All descriptions mapped"
                  description="No unmapped transaction descriptions found."
                />
              )}
            </CardContent>
          </Card>
          {pendingItem && (
            <EditMappingKeywordDialog
              open={editDialogOpen}
              onOpenChange={(open) => {
                setEditDialogOpen(open);
                if (!open) setPendingItem(null);
              }}
              originalDescription={pendingItem.description}
              subCategory={selectedMappings[pendingItem.description] ?? ""}
              onConfirm={handleConfirmKeyword}
              isPending={addDescriptionsMutation.isPending}
            />
          )}
        </TabsContent>

        <TabsContent value="sub-categories" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Add New Sub-Category</CardTitle>
              <CardDescription>
                Create a new sub-category and assign it to a category
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateSubCategory} className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="sub-category">Sub Category</Label>
                    <Input
                      id="sub-category"
                      type="text"
                      placeholder="e.g., Groceries"
                      value={newSubCategory}
                      onChange={(e) => setNewSubCategory(e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="category">Category</Label>
                    {categoriesLoading ? (
                      <Skeleton className="h-10 w-full" />
                    ) : (
                      <Select value={newCategory} onValueChange={setNewCategory}>
                        <SelectTrigger id="category">
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories && categories.length > 0 ? (
                            categories.map((cat) => (
                              <SelectItem key={cat} value={cat}>
                                {cat}
                              </SelectItem>
                            ))
                          ) : (
                            <SelectItem value="none" disabled>
                              No categories
                            </SelectItem>
                          )}
                        </SelectContent>
                      </Select>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cashflow">Cashflow Type</Label>
                    <Select value={newCashflow} onValueChange={setNewCashflow}>
                      <SelectTrigger id="cashflow">
                        <SelectValue placeholder="Select cashflow" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="income">Income</SelectItem>
                        <SelectItem value="expense">Expense</SelectItem>
                        <SelectItem value="transfer">Transfer</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <Button
                  type="submit"
                  disabled={createSubCategoryMutation.isPending}
                  className="w-full"
                >
                  <Plus className="mr-2 h-4 w-4" />
                  {createSubCategoryMutation.isPending
                    ? "Creating..."
                    : "Create Sub-Category"}
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sub-Category Mapping</CardTitle>
              <CardDescription>
                Current mapping of sub-categories to categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              {subCategoryMappingLoading ? (
                <Skeleton className="h-96 w-full" />
              ) : subCategoryData.length > 0 ? (
                <DataTable
                  columns={subCategoryColumns}
                  data={subCategoryData}
                  searchKey="subCategory"
                  searchPlaceholder="Search sub-categories..."
                />
              ) : (
                <EmptyState
                  icon={<AlertCircle />}
                  title="No sub-category mappings"
                  description="Create sub-categories to see mappings."
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cashflow" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Cashflow Mapping</CardTitle>
              <CardDescription>
                View how categories are mapped to cashflow types (read-only)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {cashflowMappingLoading ? (
                <Skeleton className="h-96 w-full" />
              ) : cashflowData.length > 0 ? (
                <DataTable
                  columns={cashflowColumns}
                  data={cashflowData}
                  searchKey="category"
                  searchPlaceholder="Search categories..."
                />
              ) : (
                <EmptyState
                  icon={<Map />}
                  title="No cashflow mappings"
                  description="Create categories to see cashflow mappings."
                />
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
