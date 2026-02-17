import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type { UploadResult, UploadRequest } from "../types";

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

export function useMissingStatements() {
  return useQuery({
    queryKey: ["upload", "missing"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        "/upload/missing"
      );
      return response.data;
    },
  });
}

export function useUploadStatus() {
  return useQuery({
    queryKey: ["upload", "status"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        "/upload/status"
      );
      return response.data;
    },
  });
}

export function useValidateCsv() {
  return useMutation({
    mutationFn: (data: { file_path: string; bank_name: string }) =>
      apiClient.post("/upload/validate", data).then((r) => r.data),
  });
}

export function useUploadStatement() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: UploadRequest) =>
      apiClient.post<UploadResult>("/upload/statement", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["upload"] });
      queryClient.invalidateQueries({ queryKey: ["earnings"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
    },
  });
}
