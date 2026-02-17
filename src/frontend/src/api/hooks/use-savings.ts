import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type { SavingsMetrics } from "../types";

export function useSavingsMetrics(year?: number) {
  return useQuery({
    queryKey: ["savings", "metrics", year],
    queryFn: async () => {
      const params = year ? { year } : {};
      const response = await apiClient.get<SavingsMetrics>("/savings/metrics", {
        params,
      });
      return response.data;
    },
  });
}

export function useMonthlySavings(year: number | undefined) {
  return useQuery({
    queryKey: ["savings", "monthly", year],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/savings/monthly/${year}`
      );
      return response.data;
    },
    enabled: !!year,
  });
}
