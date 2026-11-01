import { create } from 'zustand';

export const useUIStore = create((set) => ({
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  activeSpecSection: 'metadata',
  setActiveSpecSection: (section) => set({ activeSpecSection: section }),

  activeRightTab: 'chat', // 'chat' | 'validation' | 'dependencies'
  setActiveRightTab: (tab) => set({ activeRightTab: tab }),

  toasts: [],
  addToast: (message, type = 'info') =>
    set((state) => ({
      toasts: [...state.toasts, { id: Date.now(), message, type }],
    })),
  removeToast: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    })),
}));
