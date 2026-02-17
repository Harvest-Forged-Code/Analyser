import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type { ChangePasswordRequest } from "../types";

export function useLogLevels() {
  return useQuery({
    queryKey: ["settings", "log-levels"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/settings/log-levels");
      return response.data;
    },
  });
}

export function useCurrentLogLevel() {
  return useQuery({
    queryKey: ["settings", "log-level"],
    queryFn: async () => {
      const response = await apiClient.get<{ log_level: string }>(
        "/settings/log-level"
      );
      return response.data;
    },
  });
}

export function useSetLogLevel() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (logLevel: string) =>
      apiClient.put("/settings/log-level", { log_level: logLevel }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "log-level"] });
    },
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (data: ChangePasswordRequest) =>
      apiClient.post("/settings/change-password", data).then((r) => r.data),
  });
}

export function useTheme() {
  return useQuery({
    queryKey: ["settings", "theme"],
    queryFn: async () => {
      const response = await apiClient.get<{ theme: string }>("/settings/theme");
      return response.data;
    },
  });
}

export function useSetTheme() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (theme: string) =>
      apiClient.put("/settings/theme", { theme }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings", "theme"] });
    },
  });
}
