import { create } from 'zustand'

interface SettingsState {
  // Which account panel is expanded
  expandedAccountId: string | null

  // Track unsaved changes per account
  dirtyAccounts: Set<string>

  // Preview image URLs keyed by accountId
  previewUrls: Record<string, string>

  // Actions
  setExpanded: (id: string | null) => void
  markDirty: (id: string) => void
  markClean: (id: string) => void
  setPreviewUrl: (id: string, url: string) => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  expandedAccountId: null,
  dirtyAccounts: new Set(),
  previewUrls: {},

  setExpanded: (id) => set({ expandedAccountId: id }),

  markDirty: (id) =>
    set((s) => {
      const next = new Set(s.dirtyAccounts)
      next.add(id)
      return { dirtyAccounts: next }
    }),

  markClean: (id) =>
    set((s) => {
      const next = new Set(s.dirtyAccounts)
      next.delete(id)
      return { dirtyAccounts: next }
    }),

  setPreviewUrl: (id, url) =>
    set((s) => ({ previewUrls: { ...s.previewUrls, [id]: url } })),
}))
