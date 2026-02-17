import { create } from "zustand";

interface NavigationStore {
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useNavigationStore = create<NavigationStore>((set) => ({
  isSidebarCollapsed: false,
  toggleSidebar: () =>
    set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
