import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";

export function useExpensesMonths() {
  return useQuery({
    queryKey: ["expenses", "months"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/expenses/months");
      return response.data;
    },
  });
}

export function useExpensesMonth(period: string | undefined) {
  return useQuery({
    queryKey: ["expenses", "month", period],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/expenses/month/${period}`
      );
      return response.data;
    },
    enabled: !!period,
  });
}

export function useExpensesMonthTransactions(
  period: string | undefined,
  category?: string,
  subCategory?: string
) {
  return useQuery({
    queryKey: ["expenses", "month", period, "transactions", category, subCategory],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (category) params.category = category;
      if (subCategory) params.sub_category = subCategory;
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/expenses/month/${period}/transactions`,
        { params }
      );
      return response.data;
    },
    enabled: !!period,
  });
}

export function useExpensesYear(year: number | undefined) {
  return useQuery({
    queryKey: ["expenses", "year", year],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/expenses/year/${year}`
      );
      return response.data[0] ?? null;
    },
    enabled: !!year,
  });
}

export function useExpensesYearBreakdown(year: number | undefined) {
  return useQuery({
    queryKey: ["expenses", "year", year, "breakdown"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/expenses/year/${year}/breakdown`
      );
      return response.data;
    },
    enabled: !!year,
  });
}

export function useExpensesYearTransactions(
  year: number | undefined,
  month?: string,
  category?: string,
  subCategory?: string
) {
  return useQuery({
    queryKey: [
      "expenses",
      "year",
      year,
      "transactions",
      month,
      category,
      subCategory,
    ],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (month) params.month = month;
      if (category) params.category = category;
      if (subCategory) params.sub_category = subCategory;
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/expenses/year/${year}/transactions`,
        { params }
      );
      return response.data;
    },
    enabled: !!year,
  });
}

export function useExpensesRange(
  startDate: string | undefined,
  endDate: string | undefined
) {
  return useQuery({
    queryKey: ["expenses", "range", startDate, endDate],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        "/expenses/range",
        {
          params: { start_date: startDate, end_date: endDate },
        }
      );
      return response.data;
    },
    enabled: !!startDate && !!endDate,
  });
}
