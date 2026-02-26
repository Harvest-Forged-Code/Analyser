import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UpdateStore {
  skippedVersion: string | null;
  dismissedForSession: boolean;
  skipVersion: (version: string) => void;
  dismissForSession: () => void;
  resetSkippedVersion: () => void;
}

export const useUpdateStore = create<UpdateStore>()(
  persist(
    (set) => ({
      skippedVersion: null,
      dismissedForSession: false,
      skipVersion: (version: string) => set({ skippedVersion: version }),
      dismissForSession: () => set({ dismissedForSession: true }),
      resetSkippedVersion: () => set({ skippedVersion: null }),
    }),
    {
      name: "update-storage",
      partialize: (state) => ({ skippedVersion: state.skippedVersion }),
    },
  ),
);
