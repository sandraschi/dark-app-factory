import { create } from "zustand";

interface BuildState {
  sidebarOpen: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<BuildState>((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}));
