import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "../client";
import type {
  UploadResult,
  UploadRequest,
  UploadStats,
  ValidationResult,
  BankUploadStatus,
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

export function useUploadStatus() {
  return useQuery({
    queryKey: ["upload", "status"],
    queryFn: async () => {
      const response = await apiClient.get<BankUploadStatus[]>(
        "/upload/status"
      );
      return response.data;
    },
  });
}

export function useUploadStats() {
  return useQuery({
    queryKey: ["upload", "stats"],
    queryFn: async () => {
      const response = await apiClient.get<UploadStats>("/upload/stats");
      return response.data;
    },
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
