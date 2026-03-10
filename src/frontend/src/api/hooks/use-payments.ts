import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type { ReconciliationSummary } from "../types";

export function usePaymentPeriods() {
  return useQuery({
    queryKey: ["payments", "periods"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/payments/periods");
      return response.data;
    },
  });
}

export function usePaymentReconciliation(period?: string) {
  return useQuery({
    queryKey: ["payments", "reconciliation", period],
    queryFn: async () => {
      const url = period
        ? `/payments/reconciliation/${period}`
        : "/payments/reconciliation";
      const response = await apiClient.get<ReconciliationSummary>(url);
      return response.data;
    },
    enabled: !!period,
  });
}
