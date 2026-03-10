import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type {
  RecurringTransaction,
  RecurringDetection,
  RecurringAnomaly,
  RecurringSummary,
  AddRecurringRequest,
  UpdateRecurringRequest,
  MarkExpectedRequest,
} from "../types";

export function useRecurringTransactions(activeOnly?: boolean) {
  return useQuery({
    queryKey: ["recurring", { activeOnly }],
    queryFn: async () => {
      const params = activeOnly ? { active_only: true } : {};
      const response = await apiClient.get<RecurringTransaction[]>("/recurring", { params });
      return response.data;
    },
  });
}

export function useRecurringDetections() {
  return useQuery({
    queryKey: ["recurring", "detect"],
    queryFn: async () => {
      const response = await apiClient.get<RecurringDetection[]>("/recurring/detect");
      return response.data;
    },
    enabled: false, // manual refetch only
  });
}

export function useRecurringSummary() {
  return useQuery({
    queryKey: ["recurring", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<RecurringSummary>("/recurring/summary");
      return response.data;
    },
  });
}

export function useRecurringAnomalies() {
  return useQuery({
    queryKey: ["recurring", "anomalies"],
    queryFn: async () => {
      const response = await apiClient.get<RecurringAnomaly[]>("/recurring/anomalies");
      return response.data;
    },
  });
}

export function useAddRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AddRecurringRequest) =>
      apiClient.post<RecurringTransaction>("/recurring", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateRecurringRequest }) =>
      apiClient.put<RecurringTransaction>(`/recurring/${id}`, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recurringId: number) =>
      apiClient.delete(`/recurring/${recurringId}`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useConfirmRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recurringId: number) =>
      apiClient.patch<RecurringTransaction>(`/recurring/${recurringId}/confirm`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDismissRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recurringId: number) =>
      apiClient.patch<RecurringTransaction>(`/recurring/${recurringId}/dismiss`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useMarkExpected() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: MarkExpectedRequest }) =>
      apiClient.patch<RecurringTransaction>(`/recurring/${id}/expected`, data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useResolveAnomaly() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (anomalyId: number) =>
      apiClient.patch(`/recurring/anomalies/${anomalyId}/resolve`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
    },
  });
}
