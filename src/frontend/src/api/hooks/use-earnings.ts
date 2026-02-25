import { useQuery } from "@tanstack/react-query";
import apiClient from "../client";
import type {
  EarningsDashboard,
  EarningsMonthTrend,
  EarningsRow,
  EarningsSourceTrend,
} from "../types";

export function useEarningsMonths() {
  return useQuery({
    queryKey: ["earnings", "months"],
    queryFn: async () => {
      const response = await apiClient.get<string[]>("/earnings/months");
      return response.data;
    },
  });
}

export function useEarningsMonth(period: string | undefined) {
  return useQuery({
    queryKey: ["earnings", "month", period],
    queryFn: async () => {
      const response = await apiClient.get<EarningsRow[]>(`/earnings/month/${period}`);
      return response.data;
    },
    enabled: !!period,
  });
}

export function useEarningsMonthTransactions(
  period: string | undefined,
  subCategory?: string
) {
  return useQuery({
    queryKey: ["earnings", "month", period, "transactions", subCategory],
    queryFn: async () => {
      const params = subCategory ? { sub_category: subCategory } : {};
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/earnings/month/${period}/transactions`,
        { params }
      );
      return response.data;
    },
    enabled: !!period,
  });
}

export function useEarningsDashboard(period: string | undefined) {
  return useQuery({
    queryKey: ["earnings", "dashboard", period],
    queryFn: async () => {
      const response = await apiClient.get<EarningsDashboard>("/earnings/dashboard", {
        params: { period },
      });
      return response.data;
    },
    enabled: !!period,
  });
}

export function useEarningsTrend(months = 12) {
  return useQuery({
    queryKey: ["earnings", "trend", months],
    queryFn: async () => {
      const response = await apiClient.get<EarningsMonthTrend[]>("/earnings/trend", {
        params: { months },
      });
      return response.data;
    },
  });
}

export function useEarningsSourceTrend(months = 6) {
  return useQuery({
    queryKey: ["earnings", "source-trend", months],
    queryFn: async () => {
      const response = await apiClient.get<EarningsSourceTrend[]>("/earnings/source-trend", {
        params: { months },
      });
      return response.data;
    },
  });
}

export function useEarningsYear(year: number | undefined) {
  return useQuery({
    queryKey: ["earnings", "year", year],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        `/earnings/year/${year}`
      );
      return response.data;
    },
    enabled: !!year,
  });
}

export function useEarningsYearBreakdown(year: number | undefined) {
  return useQuery({
    queryKey: ["earnings", "year", year, "breakdown"],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/earnings/year/${year}/breakdown`
      );
      return response.data;
    },
    enabled: !!year,
  });
}

export function useEarningsYearTransactions(
  year: number | undefined,
  month?: string,
  subCategory?: string
) {
  return useQuery({
    queryKey: ["earnings", "year", year, "transactions", month, subCategory],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (month) params.month = month;
      if (subCategory) params.sub_category = subCategory;
      const response = await apiClient.get<Record<string, unknown>[]>(
        `/earnings/year/${year}/transactions`,
        { params }
      );
      return response.data;
    },
    enabled: !!year,
  });
}

export function useEarningsRange(
  startDate: string | undefined,
  endDate: string | undefined
) {
  return useQuery({
    queryKey: ["earnings", "range", startDate, endDate],
    queryFn: async () => {
      const response = await apiClient.get<Record<string, unknown>>(
        "/earnings/range",
        {
          params: { start_date: startDate, end_date: endDate },
        }
      );
      return response.data;
    },
    enabled: !!startDate && !!endDate,
  });
}
