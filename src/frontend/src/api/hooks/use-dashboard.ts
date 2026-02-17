import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type { DashboardSummary } from "../types";

export function useDashboardSummary() {
  return useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<DashboardSummary>("/dashboard/summary");
      return response.data;
    },
  });
}
