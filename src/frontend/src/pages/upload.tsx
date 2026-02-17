import { useState, useMemo } from "react";
import { Upload, FileCheck, AlertCircle, CheckCircle, XCircle } from "lucide-react";
import {
  useAvailableBanks,
  useMissingStatements,
  useUploadStatus,
  useValidateCsv,
  useUploadStatement,
} from "@/api/hooks/use-upload";
import type { UploadResult } from "@/api/types";
import PageHeader from "@/components/page-header";
import EmptyState from "@/components/empty-state";
import DataTable, { type ColumnDef } from "@/components/data-table";
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
import { cn } from "@/lib/utils";

export default function UploadPage() {
  const [accountType, setAccountType] = useState<string>("checking");
  const [bankName, setBankName] = useState<string>("");
  const [filePath, setFilePath] = useState<string>("");
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  const { data: banks } = useAvailableBanks(accountType);
  const { data: missingStatements, isLoading: missingLoading } = useMissingStatements();
  const { data: uploadStatus, isLoading: statusLoading } = useUploadStatus();
  const validateMutation = useValidateCsv();
  const uploadMutation = useUploadStatement();

  // Auto-select first bank when account type changes
  useMemo(() => {
    if (banks && banks.length > 0 && !bankName) {
      setBankName(banks[0] ?? "");
    }
  }, [banks, bankName]);

  const handleValidate = async () => {
    if (!filePath || !bankName) return;
    try {
      await validateMutation.mutateAsync({ file_path: filePath, bank_name: bankName });
      alert("CSV validation successful!");
    } catch (error) {
      alert(`Validation failed: ${error}`);
    }
  };

  const handleUpload = async () => {
    if (!filePath || !bankName || !accountType) return;
    try {
      const result = await uploadMutation.mutateAsync({
        file_path: filePath,
        bank_name: bankName,
        account_type: accountType,
      });
      setUploadResult(result);
    } catch (error) {
      setUploadResult({
        success: false,
        message: `Upload failed: ${error}`,
        destination_path: null,
        transactions_inserted: 0,
        duplicates_skipped: 0,
      });
    }
  };

  // Column definitions for missing statements
  const missingColumns: ColumnDef<Record<string, unknown>>[] = useMemo(() => {
    if (!missingStatements || missingStatements.length === 0) return [];
    const sample = missingStatements[0];
    if (!sample) return [];
    const keys = Object.keys(sample);

    return keys.map((key) => ({
      accessorKey: key,
      header: key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" "),
      cell: ({ row }) => String(row.getValue(key)),
    }));
  }, [missingStatements]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Upload Statements"
        description="Import bank statements to analyze"
      />

      <Card>
        <CardHeader>
          <CardTitle>Upload Form</CardTitle>
          <CardDescription>
            Select your account type, bank, and provide the path to your CSV statement file
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="account-type">Account Type</Label>
              <Select value={accountType} onValueChange={setAccountType}>
                <SelectTrigger id="account-type">
                  <SelectValue placeholder="Select account type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="checking">Checking</SelectItem>
                  <SelectItem value="credit">Credit</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bank-name">Bank Name</Label>
              <Select value={bankName} onValueChange={setBankName}>
                <SelectTrigger id="bank-name">
                  <SelectValue placeholder="Select bank" />
                </SelectTrigger>
                <SelectContent>
                  {banks && banks.length > 0 ? (
                    banks.map((bank) => (
                      <SelectItem key={bank} value={bank}>
                        {bank}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled>
                      No banks available
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="file-path">File Path</Label>
            <Input
              id="file-path"
              type="text"
              placeholder="/path/to/your/statement.csv"
              value={filePath}
              onChange={(e) => setFilePath(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <Button
              onClick={handleValidate}
              disabled={!filePath || !bankName || validateMutation.isPending}
              variant="outline"
            >
              <FileCheck className="mr-2 h-4 w-4" />
              {validateMutation.isPending ? "Validating..." : "Validate"}
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!filePath || !bankName || uploadMutation.isPending}
            >
              <Upload className="mr-2 h-4 w-4" />
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {uploadResult && (
        <Card className={cn(
          uploadResult.success
            ? "border-green-200 bg-green-50"
            : "border-red-200 bg-red-50"
        )}>
          <CardHeader>
            <div className="flex items-center gap-2">
              {uploadResult.success ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600" />
              )}
              <CardTitle>
                {uploadResult.success ? "Upload Successful" : "Upload Failed"}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm">{uploadResult.message}</p>
            {uploadResult.destination_path && (
              <p className="text-xs text-muted-foreground">
                Saved to: {uploadResult.destination_path}
              </p>
            )}
            {uploadResult.success && (
              <div className="flex gap-4 pt-2">
                <Badge variant="default">
                  {uploadResult.transactions_inserted} transactions inserted
                </Badge>
                <Badge variant="secondary">
                  {uploadResult.duplicates_skipped} duplicates skipped
                </Badge>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Missing Statements</CardTitle>
          <CardDescription>
            Months with incomplete or missing statement data
          </CardDescription>
        </CardHeader>
        <CardContent>
          {missingLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : missingStatements && missingStatements.length > 0 ? (
            <DataTable columns={missingColumns} data={missingStatements} />
          ) : (
            <EmptyState
              icon={<CheckCircle />}
              title="All statements uploaded"
              description="No missing statements detected."
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upload Status</CardTitle>
          <CardDescription>
            Current upload status and recent activity
          </CardDescription>
        </CardHeader>
        <CardContent>
          {statusLoading ? (
            <Skeleton className="h-48 w-full" />
          ) : uploadStatus ? (
            <div className="space-y-2">
              {Object.entries(uploadStatus).map(([key, value]) => (
                <div key={key} className="flex justify-between items-center py-2 border-b last:border-b-0">
                  <span className="text-sm font-medium">
                    {key.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ")}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    {typeof value === "boolean" ? (value ? "Yes" : "No") : String(value)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<AlertCircle />}
              title="No status information"
              description="Upload a statement to see status information."
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
