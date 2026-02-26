import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type { UpdateCheckResult } from "../types";

export function useUpdateCheck(enabled: boolean = true) {
  return useQuery({
    queryKey: ["updates", "check"],
    queryFn: async () => {
      const response = await apiClient.get<UpdateCheckResult>("/updates/check");
      return response.data;
    },
    enabled,
    staleTime: Infinity,
    retry: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
