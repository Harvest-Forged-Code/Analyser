import { useMutation } from "@tanstack/react-query";
import apiClient from "../client";
import type { LoginRequest } from "../types";

export function useLogin() {
  return useMutation({
    mutationFn: (data: LoginRequest) =>
      apiClient.post("/auth/login", data).then((r) => r.data),
  });
}
