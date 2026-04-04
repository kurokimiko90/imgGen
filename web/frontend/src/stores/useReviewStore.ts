import { create } from 'zustand'

interface ReviewState {
  // Filters
  filterAccount: string | null
  filterStatus: string[]

  // Batch selection
  batchMode: boolean
  selectedIds: Set<string>

  // Edit mode
  editingId: string | null

  // Preflight warning dialog
  preflightWarnings: string[]
  pendingApproveId: string | null

  // Actions
  setFilterAccount: (account: string | null) => void
  setFilterStatus: (statuses: string[]) => void
  toggleBatchMode: () => void
  toggleSelect: (id: string) => void
  selectAll: (ids: string[]) => void
  clearSelection: () => void
  setEditingId: (id: string | null) => void
  showPreflightWarnings: (id: string, warnings: string[]) => void
  clearPreflightWarnings: () => void
}

export const useReviewStore = create<ReviewState>((set) => ({
  filterAccount: null,
  filterStatus: ['DRAFT', 'PENDING_REVIEW'],
  batchMode: false,
  selectedIds: new Set(),
  editingId: null,
  preflightWarnings: [],
  pendingApproveId: null,

  setFilterAccount: (account) => set({ filterAccount: account }),
  setFilterStatus: (statuses) => set({ filterStatus: statuses }),

  toggleBatchMode: () =>
    set((s) => ({
      batchMode: !s.batchMode,
      selectedIds: new Set(),
    })),

  toggleSelect: (id) =>
    set((s) => {
      const next = new Set(s.selectedIds)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return { selectedIds: next }
    }),

  selectAll: (ids) => set({ selectedIds: new Set(ids) }),
  clearSelection: () => set({ selectedIds: new Set() }),

  setEditingId: (id) => set({ editingId: id }),

  showPreflightWarnings: (id, warnings) =>
    set({ pendingApproveId: id, preflightWarnings: warnings }),

  clearPreflightWarnings: () =>
    set({ pendingApproveId: null, preflightWarnings: [] }),
}))
