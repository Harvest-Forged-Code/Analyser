import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
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
      apiClient
        .post("/mappers/add-descriptions", data.descriptions, {
          params: { sub_category: data.sub_category },
        })
        .then((r) => r.data),
    onSuccess: (data: { message: string }) => {
      toast.success(data.message ?? "Mapping saved and transactions updated");
      queryClient.invalidateQueries({ queryKey: ["mappers"] });
      queryClient.invalidateQueries({ queryKey: ["earnings"] });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (error) => {
      toast.error(`Failed to add mapping: ${error}`);
    },
  });
}

export function useCreateSubCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { sub_category: string; category: string; cashflow: string }) =>
      apiClient
        .post("/mappers/create-sub-category", null, {
          params: { sub_category: data.sub_category, category: data.category },
        })
        .then((r) => r.data),
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
