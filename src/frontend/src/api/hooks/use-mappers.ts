import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";

export function useUnmappedTransactions() {
  return useQuery({
    queryKey: ["mappers", "unmapped"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        "/mappers/unmapped"
      );
      return response.data;
    },
  });
}

export function useUnmappedDescriptions() {
  return useQuery({
    queryKey: ["mappers", "unmapped-descriptions"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>(
        "/mappers/unmapped-descriptions"
      );
      return response.data;
    },
  });
}

export function useSubCategories() {
  return useQuery({
    queryKey: ["mappers", "sub-categories"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/mappers/sub-categories");
      return response.data;
    },
  });
}

export function useCategories() {
  return useQuery({
    queryKey: ["mappers", "categories"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/mappers/categories");
      return response.data;
    },
  });
}

export function useAddDescriptions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sub_category: string; descriptions: string[] }) =>
      apiClient.post("/mappers/descriptions", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
    },
  });
}

export function useCreateSubCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sub_category: string; category: string; cashflow: string }) =>
      apiClient.post("/mappers/sub-category", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
    },
  });
}

export function useSaveMappers() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post("/mappers/save").then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries();
    },
  });
}

export function useSubCategoryMapping() {
  return useQuery({
    queryKey: ["mappers", "sub-category-mapping"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, string>>(
        "/mappers/sub-category-mapping"
      );
      return response.data;
    },
  });
}

export function useCashflowMapping() {
  return useQuery({
    queryKey: ["mappers", "cashflow"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, string>>(
        "/mappers/cashflow"
      );
      return response.data;
    },
  });
}
