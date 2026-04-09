import { Calendar, ChevronLeft, ChevronRight, AlertCircle } from 'lucide-react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useSchedulingStore } from '@/stores/useSchedulingStore'
import { useScheduledRange, useReschedule } from '@/api/queries'
import { WeekCalendar } from '@/features/scheduling/WeekCalendar'

function addDays(isoDate: string, days: number): string {
  const d = new Date(isoDate)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

export function SchedulingPage() {
  const { view, weekStart, accountFilter, setView, prevWeek, nextWeek, setAccountFilter } =
    useSchedulingStore()

  const weekEnd = addDays(weekStart, view === 'week' ? 6 : 27)

  const scheduled = useScheduledRange(weekStart, weekEnd, accountFilter)
  const reschedule = useReschedule()

  const items = scheduled.data?.items ?? []

  const weekLabel = (() => {
    const start = new Date(weekStart)
    const end = new Date(weekEnd)
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} – ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  })()

  return (
    <PageTransition>
      <div className="p-6 space-y-5 max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar size={22} className="text-accent" />
            <div>
              <h1 className="text-xl font-semibold text-text-primary">Scheduling</h1>
              <p className="text-sm text-text-muted">{items.length} scheduled items</p>
            </div>
          </div>

          {/* View toggle */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setView('week')}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                view === 'week'
                  ? 'bg-accent/20 text-accent'
                  : 'text-text-muted hover:text-text-primary hover:bg-hover'
              }`}
            >
              Week
            </button>
            <button
              onClick={() => setView('month')}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors ${
                view === 'month'
                  ? 'bg-accent/20 text-accent'
                  : 'text-text-muted hover:text-text-primary hover:bg-hover'
              }`}
            >
              Month
            </button>
          </div>
        </div>

        {/* Navigation + filters */}
        <div className="flex items-center gap-3">
          <button
            onClick={prevWeek}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors"
          >
            <ChevronLeft size={18} />
          </button>

          <span className="text-sm text-text-primary font-medium min-w-48 text-center">{weekLabel}</span>

          <button
            onClick={nextWeek}
            className="p-1.5 text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors"
          >
            <ChevronRight size={18} />
          </button>

          <div className="ml-4">
            <select
              value={accountFilter ?? ''}
              onChange={(e) => setAccountFilter(e.target.value || null)}
              className="bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent"
            >
              <option value="">All Accounts</option>
              <option value="A">Account A</option>
              <option value="B">Account B</option>
              <option value="C">Account C</option>
            </select>
          </div>
        </div>

        {/* Drag & Drop Hint */}
        {!scheduled.isLoading && !scheduled.isError && items.length > 0 && (
          <p className="text-xs text-text-muted flex items-center gap-1">
            💡 拖拽內容卡片可重新排期
          </p>
        )}

        {/* Calendar */}
        {scheduled.isLoading ? (
          <div className="h-64 animate-pulse rounded-xl bg-white/5" />
        ) : scheduled.isError ? (
          <GlassCard>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle size={16} />
              <span className="text-sm">Failed to load scheduled content</span>
            </div>
          </GlassCard>
        ) : (
          <WeekCalendar
            weekStart={weekStart}
            items={items}
            onReschedule={async (id, newTime) => {
              await reschedule.mutateAsync({ id, scheduled_time: newTime })
            }}
            isRescheduling={reschedule.isPending}
          />
        )}
      </div>
    </PageTransition>
  )
}
