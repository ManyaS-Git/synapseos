import { create } from 'zustand';

/**
 * Global application store.
 *
 * TODO: Implement the following state:
 * - theme: 'light' | 'dark' | 'system'
 * - sidebarOpen: boolean
 * - currentView: string
 * - notifications: array
 */

interface AppState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleSidebar: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'system',
  sidebarOpen: true,
  setTheme: (theme) => set({ theme }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
}));
