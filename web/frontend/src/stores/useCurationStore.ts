import { create } from 'zustand'
import type { CurationProgress } from '@/api/queries'

interface CurationState {
  // Filters for draft content list
  accountFilter: string | null
  sourceFilter: string | null
  daysFilter: number | null  // null=all, 1=today, 7, 30

  // Active SSE run state
  isRunning: boolean
  progress: CurationProgress[]

  // Actions
  setAccountFilter: (account: string | null) => void
  setSourceFilter: (source: string | null) => void
  setDaysFilter: (days: number | null) => void
  setRunning: (running: boolean) => void
  addProgress: (event: CurationProgress) => void
  resetProgress: () => void
}

export const useCurationStore = create<CurationState>((set) => ({
  accountFilter: null,
  sourceFilter: null,
  daysFilter: null,
  isRunning: false,
  progress: [],

  setAccountFilter: (account) => set({ accountFilter: account }),
  setSourceFilter: (source) => set({ sourceFilter: source }),
  setDaysFilter: (days) => set({ daysFilter: days }),
  setRunning: (running) => set({ isRunning: running }),

  addProgress: (event) =>
    set((s) => ({ progress: [...s.progress, event] })),

  resetProgress: () => set({ progress: [], isRunning: false }),
}))
