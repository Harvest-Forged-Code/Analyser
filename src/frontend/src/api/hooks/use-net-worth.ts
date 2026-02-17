import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type { Account, NetWorthSummary, AddAccountRequest } from "../types";

export function useAccounts() {
  return useQuery({
    queryKey: ["net-worth", "accounts"],
    queryFn: async () => {
      const response = await apiClient.get<Account[]>("/net-worth/accounts");
      return response.data;
    },
  });
}

export function useAddAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: AddAccountRequest) =>
      apiClient.post("/net-worth/accounts", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["net-worth"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useUpdateBalance() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ accountId, balance }: { accountId: number; balance: number }) =>
      apiClient
        .patch(`/net-worth/accounts/${accountId}/balance`, { balance })
        .then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["net-worth"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (accountId: number) =>
      apiClient.delete(`/net-worth/accounts/${accountId}`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["net-worth"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useNetWorthSummary() {
  return useQuery({
    queryKey: ["net-worth", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<NetWorthSummary>("/net-worth/summary");
      return response.data;
    },
  });
}
