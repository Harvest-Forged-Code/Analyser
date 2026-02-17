import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type { PaymentsReconciliation } from "../types";

export function usePaymentMonths() {
  return useQuery({
    queryKey: ["payments", "months"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/payments/months");
      return response.data;
    },
  });
}

export function usePaymentData(period: string | undefined) {
  return useQuery({
    queryKey: ["payments", period],
    queryFn: async () => {
      const response = await apiClient.get<PaymentsReconciliation>(
        `/payments/${period}`
      );
      return response.data;
    },
    enabled: !!period,
  });
}
