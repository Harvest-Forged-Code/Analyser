import { create } from "zustand";

interface FilterStore {
  selectedMonth: string | null;
  selectedYear: number | null;
  setSelectedMonth: (month: string | null) => void;
  setSelectedYear: (year: number | null) => void;
}

export const useFilterStore = create<FilterStore>((set) => ({
  selectedMonth: null,
  selectedYear: null,
  setSelectedMonth: (month) => set({ selectedMonth: month }),
  setSelectedYear: (year) => set({ selectedYear: year }),
}));
