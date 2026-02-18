import { useState, useEffect } from "react";
import { FileCheck, Upload, CheckCircle, XCircle, Loader2 } from "lucide-react";
import {
  useAvailableBanks,
  useValidateCsv,
  useUploadStatement,
} from "@/api/hooks/use-upload";
import type { UploadResult } from "@/api/types";
import DropZone from "./drop-zone";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export default function UploadForm() {
  const [accountType, setAccountType] = useState<string>("credit");
  const [bankName, setBankName] = useState<string>("");
  const [filePath, setFilePath] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);

  const { data: banks } = useAvailableBanks(accountType);
  const validateMutation = useValidateCsv();
  const uploadMutation = useUploadStatement();

  // Reset bank when account type changes
  useEffect(() => {
    setBankName("");
  }, [accountType]);

  // Auto-select first bank
  useEffect(() => {
    if (banks && banks.length > 0 && !bankName) {
      setBankName(banks[0] ?? "");
    }
  }, [banks, bankName]);

  const handleValidate = async () => {
    if (!filePath || !bankName) return;
    await validateMutation.mutateAsync({
      file_path: filePath,
      bank_name: bankName,
    });
  };

  const handleUpload = async () => {
    if (!filePath || !bankName || !accountType) return;
    try {
      const result = await uploadMutation.mutateAsync({
        file_path: filePath,
        bank_name: bankName,
        account_type: accountType === "checking" ? "debit" : "credit",
      });
      setUploadResult(result);
    } catch {
      setUploadResult({
        success: false,
        message: "Upload failed. Check the file and try again.",
        destination_path: null,
        transactions_inserted: 0,
        duplicates_skipped: 0,
      });
    }
  };

  const canSubmit = !!filePath && !!bankName;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Upload Statement</CardTitle>
          <CardDescription>
            Select your account type, bank, and CSV file to upload
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

          <DropZone onFileSelected={setFilePath} selectedFile={filePath} />

          <div className="flex gap-2">
            <Button
              onClick={handleValidate}
              disabled={!canSubmit || validateMutation.isPending}
              variant="outline"
            >
              {validateMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <FileCheck className="mr-2 h-4 w-4" />
              )}
              {validateMutation.isPending ? "Validating..." : "Validate"}
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!canSubmit || uploadMutation.isPending}
            >
              {uploadMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Upload className="mr-2 h-4 w-4" />
              )}
              {uploadMutation.isPending ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {uploadResult && (
        <Card
          className={cn(
            uploadResult.success
              ? "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950/20"
              : "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950/20"
          )}
        >
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
    </div>
  );
}
