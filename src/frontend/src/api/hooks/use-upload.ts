import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "../client";
import type {
  UploadResult,
  UploadRequest,
  ValidationResult,
} from "../types";

export function useAvailableBanks(accountType: string | undefined) {
  return useQuery({
    queryKey: ["upload", "banks", accountType],
    queryFn: async () => {
      const response = await apiClient.get<string[]>(
        `/upload/banks/${accountType}`
      );
      return response.data;
    },
    enabled: !!accountType,
  });
}

export function useValidateCsv() {
  return useMutation({
    mutationFn: async (data: { file_path: string; bank_name: string }) => {
      const response = await apiClient.post<ValidationResult>(
        "/upload/validate",
        data
      );
      return response.data;
    },
    onSuccess: (data) => {
      if (data.valid) {
        toast.success("CSV validation passed");
      } else {
        toast.error(data.message);
      }
    },
    onError: (error) => {
      toast.error(`Validation failed: ${error}`);
    },
  });
}

export function useUploadStatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: UploadRequest) => {
      const response = await apiClient.post<UploadResult>("/upload", data);
      return response.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(
          `Uploaded successfully: ${data.transactions_inserted} transactions added`
        );
      } else {
        toast.error(data.message);
      }
      queryClient.invalidateQueries({ queryKey: ["upload"] });
      queryClient.invalidateQueries({ queryKey: ["earnings"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
    },
    onError: (error) => {
      toast.error(`Upload failed: ${error}`);
    },
  });
}

export function useValidateCsvFile() {
  return useMutation({
    mutationFn: async (data: { file: File; bank_name: string }) => {
      const formData = new FormData();
      formData.append("file", data.file);
      formData.append("bank_name", data.bank_name);
      const response = await apiClient.post<ValidationResult>(
        "/upload/validate-file",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return response.data;
    },
    onSuccess: (data) => {
      if (data.valid) {
        toast.success("CSV validation passed");
      } else {
        toast.error(data.message);
      }
    },
    onError: (error) => {
      toast.error(`Validation failed: ${error}`);
    },
  });
}

export function useUploadStatementFile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: {
      file: File;
      bank_name: string;
      account_type: string;
    }) => {
      const formData = new FormData();
      formData.append("file", data.file);
      formData.append("bank_name", data.bank_name);
      formData.append("account_type", data.account_type);
      const response = await apiClient.post<UploadResult>(
        "/upload/file",
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return response.data;
    },
    onSuccess: (data) => {
      if (data.success) {
        toast.success(
          `Uploaded successfully: ${data.transactions_inserted} transactions added`
        );
      } else {
        toast.error(data.message);
      }
      queryClient.invalidateQueries({ queryKey: ["upload"] });
      queryClient.invalidateQueries({ queryKey: ["earnings"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
    },
    onError: (error) => {
      toast.error(`Upload failed: ${error}`);
    },
  });
}
