import { create } from 'zustand'

type CalendarView = 'week' | 'month'

interface SchedulingState {
  view: CalendarView
  weekStart: string  // ISO date of current week's Monday
  selectedContentId: string | null
  accountFilter: string | null

  // Actions
  setView: (view: CalendarView) => void
  setWeekStart: (date: string) => void
  selectContent: (id: string | null) => void
  setAccountFilter: (account: string | null) => void
  prevWeek: () => void
  nextWeek: () => void
}

function getMonday(date: Date): string {
  const d = new Date(date)
  const day = d.getDay()
  const diff = d.getDate() - day + (day === 0 ? -6 : 1)
  d.setDate(diff)
  return d.toISOString().slice(0, 10)
}

const todayMonday = getMonday(new Date())

function addDays(isoDate: string, days: number): string {
  const d = new Date(isoDate)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export const useSchedulingStore = create<SchedulingState>((set, get) => ({
  view: 'week',
  weekStart: todayMonday,
  selectedContentId: null,
  accountFilter: null,

  setView: (view) => set({ view }),
  setWeekStart: (date) => set({ weekStart: date }),
  selectContent: (id) => set({ selectedContentId: id }),
  setAccountFilter: (account) => set({ accountFilter: account }),

  prevWeek: () => {
    const { view, weekStart } = get()
    const delta = view === 'week' ? -7 : -28
    set({ weekStart: addDays(weekStart, delta) })
  },

  nextWeek: () => {
    const { view, weekStart } = get()
    const delta = view === 'week' ? 7 : 28
    set({ weekStart: addDays(weekStart, delta) })
  },
}))
