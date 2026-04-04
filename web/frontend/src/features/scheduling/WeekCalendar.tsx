import { useState } from 'react'
import type { ContentDetail } from '@/api/queries'

interface WeekCalendarProps {
  weekStart: string
  items: ContentDetail[]
  onReschedule: (id: string, newTime: string) => void
  isRescheduling: boolean
}

function addDays(isoDate: string, days: number): string {
  const d = new Date(isoDate)
  d.setDate(d.getDate() + days)
  return d.toISOString().slice(0, 10)
}

const ACCOUNT_COLORS: Record<string, string> = {
  A: 'bg-purple-500/20 border-purple-500/40 text-purple-300',
  B: 'bg-sky-500/20 border-sky-500/40 text-sky-300',
  C: 'bg-amber-500/20 border-amber-500/40 text-amber-300',
}

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function WeekCalendar({ weekStart, items, onReschedule }: WeekCalendarProps) {
  const [dragTarget, setDragTarget] = useState<string | null>(null)

  const days = DAYS.map((label, i) => {
    const date = addDays(weekStart, i)
    const dayItems = items.filter((item) => {
      if (!item.scheduled_time) return false
      return item.scheduled_time.startsWith(date)
    })
    return { label, date, items: dayItems }
  })

  function handleDrop(e: React.DragEvent, targetDate: string) {
    e.preventDefault()
    const id = e.dataTransfer.getData('text/plain')
    const item = items.find((it) => it.id === id)
    if (!item || !item.scheduled_time) return

    const currentTime = item.scheduled_time.slice(11, 16) // HH:MM
    const newTime = `${targetDate}T${currentTime}:00`
    onReschedule(id, newTime)
    setDragTarget(null)
  }

  return (
    <div className="grid grid-cols-7 gap-2">
      {days.map(({ label, date, items: dayItems }) => {
        const isToday = date === new Date().toISOString().slice(0, 10)

        return (
          <div
            key={date}
            className={`min-h-32 rounded-xl border p-2 transition-colors ${
              dragTarget === date
                ? 'border-accent bg-accent/10'
                : isToday
                ? 'border-accent/30 bg-accent/5'
                : 'border-border-subtle bg-white/3'
            }`}
            onDragOver={(e) => { e.preventDefault(); setDragTarget(date) }}
            onDragLeave={() => setDragTarget(null)}
            onDrop={(e) => handleDrop(e, date)}
          >
            {/* Day label */}
            <div className="text-xs font-medium mb-2">
              <span className={isToday ? 'text-accent' : 'text-text-muted'}>{label}</span>
              <span className={`ml-1 text-xs ${isToday ? 'text-accent' : 'text-text-faint'}`}>
                {new Date(date).getDate()}
              </span>
            </div>

            {/* Items */}
            <div className="space-y-1">
              {dayItems.map((item) => (
                <div
                  key={item.id}
                  draggable
                  onDragStart={(e) => e.dataTransfer.setData('text/plain', item.id)}
                  className={`p-1.5 rounded border text-xs cursor-grab active:cursor-grabbing ${ACCOUNT_COLORS[item.account_type] ?? ''}`}
                  title={item.title}
                >
                  <div className="font-medium truncate">{item.title}</div>
                  {item.scheduled_time && (
                    <div className="text-xs opacity-70 mt-0.5">
                      {item.scheduled_time.slice(11, 16)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
