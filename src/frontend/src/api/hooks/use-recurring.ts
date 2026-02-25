import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type { RecurringTransaction, AddRecurringRequest } from "../types";

export function useRecurringTransactions(activeOnly?: boolean) {
  return useQuery({
    queryKey: ["recurring", { activeOnly }],
    queryFn: async () => {
      const params = activeOnly ? { active_only: true } : {};
      const response = await apiClient.get<RecurringTransaction[]>("/recurring", {
        params,
      });
      return response.data;
    },
  });
}

export function useAddRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AddRecurringRequest) =>
      apiClient.post("/recurring", data).then((r) => r.data),
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

export function useDeactivateRecurring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (recurringId: number) =>
      apiClient.patch(`/recurring/${recurringId}/deactivate`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["recurring"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useRecurringSummary() {
  return useQuery({
    queryKey: ["recurring", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        "/recurring/summary"
      );
      return response.data;
    },
  });
}
