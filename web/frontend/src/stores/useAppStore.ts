import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ThemeId } from '@/themes'

interface AppState {
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  theme: ThemeId
  setTheme: (theme: ThemeId) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
      theme: 'dark' as ThemeId,
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'imggen-app' },
  ),
)
