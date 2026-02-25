import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import apiClient from "../client";
import type {
  BudgetGoal,
  EarningsGoal,
  BudgetProgress,
  BudgetGoalsSummary,
  EarningsGoalsSummary,
  ProgressSummary,
  CategoryProgressPoint,
  SetBudgetRequest,
  SetEarningsGoalRequest,
  YearGrid,
  SetBudgetYearRequest,
  SetEarningsYearRequest,
} from "../types";

export function useBudgetGoals() {
  return useQuery({
    queryKey: ["budget-goals"],
    queryFn: async () => {
      const response = await apiClient.get<BudgetGoal[]>("/budget-goals");
      return response.data;
    },
  });
}

export function useSetBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SetBudgetRequest) =>
      apiClient.post("/budget-goals", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget-goals"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteBudget() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (category: string) =>
      apiClient.delete("/budget-goals", { params: { category } }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget-goals"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useBudgetProgress(yearMonth: string | undefined) {
  return useQuery({
    queryKey: ["budget-goals", "progress", yearMonth],
    queryFn: async () => {
      const response = await apiClient.get<BudgetProgress[]>(
        `/budget-goals/progress/${yearMonth}`
      );
      return response.data;
    },
    enabled: !!yearMonth,
  });
}

export function useEarningsGoals() {
  return useQuery({
    queryKey: ["earnings-goals"],
    queryFn: async () => {
      const response = await apiClient.get<EarningsGoal[]>("/earnings-goals");
      return response.data;
    },
  });
}

export function useSetEarningsGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SetEarningsGoalRequest) =>
      apiClient.post("/earnings-goals", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["earnings-goals"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useDeleteEarningsGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (subCategory: string) =>
      apiClient.delete("/budget-goals/earnings", { params: { sub_category: subCategory } }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["earnings-goals"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useBudgetGoalsSummary() {
  return useQuery({
    queryKey: ["budget-goals", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<BudgetGoalsSummary>(
        "/budget-goals/summary"
      );
      return response.data;
    },
  });
}

export function useEarningsGoalsSummary() {
  return useQuery({
    queryKey: ["earnings-goals", "summary"],
    queryFn: async () => {
      const response = await apiClient.get<EarningsGoalsSummary>(
        "/budget-goals/earnings/summary"
      );
      return response.data;
    },
  });
}

export function useProgressSummary(yearMonth: string | undefined) {
  return useQuery({
    queryKey: ["budget-goals", "progress", "summary", yearMonth],
    queryFn: async () => {
      const response = await apiClient.get<ProgressSummary>(
        `/budget-goals/progress/${yearMonth}/summary`
      );
      return response.data;
    },
    enabled: !!yearMonth,
  });
}

export function useCategoryProgressHistory(category: string | undefined) {
  return useQuery({
    queryKey: ["budget-goals", "progress", "history", category],
    queryFn: async () => {
      const response = await apiClient.get<CategoryProgressPoint[]>(
        `/budget-goals/progress/history/${category}`
      );
      return response.data;
    },
    enabled: !!category,
  });
}

export function useBudgetGoalsForYear(year: number) {
  return useQuery({
    queryKey: ["budget-goals", "year", year],
    queryFn: async () => {
      const response = await apiClient.get<YearGrid>(
        `/budget-goals/year/${year}`
      );
      return response.data;
    },
  });
}

export function useEarningsGoalsForYear(year: number) {
  return useQuery({
    queryKey: ["earnings-goals", "year", year],
    queryFn: async () => {
      const response = await apiClient.get<YearGrid>(
        `/budget-goals/earnings/year/${year}`
      );
      return response.data;
    },
  });
}

export function useSetBudgetForYear() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SetBudgetYearRequest) =>
      apiClient.post("/budget-goals/year", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["budget-goals"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["budget-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

export function useSetEarningsGoalForYear() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SetEarningsYearRequest) =>
      apiClient.post("/budget-goals/earnings/year", data).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["earnings-goals"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "summary"] });
      queryClient.invalidateQueries({ queryKey: ["earnings-goals", "year"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
