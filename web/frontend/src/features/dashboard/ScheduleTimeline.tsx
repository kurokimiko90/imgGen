import { cn } from '@/lib/utils'
import { ACCOUNT_COLORS, type AccountId } from '@/constants/accounts'
import { Clock } from 'lucide-react'

interface ScheduleItem {
  id: string
  account_type: string
  title: string
  scheduled_time: string
  content_type: string | null
  image_url: string | null
}

interface ScheduleTimelineProps {
  items: ScheduleItem[]
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch {
    return iso
  }
}

export function ScheduleTimeline({ items }: ScheduleTimelineProps) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-text-muted gap-2">
        <Clock size={24} className="opacity-40" />
        <span className="text-sm">No content scheduled for today</span>
      </div>
    )
  }

  return (
    <div className="relative overflow-x-auto">
      <div className="flex gap-3 min-w-0">
        {items.map((item) => {
          const colors = ACCOUNT_COLORS[item.account_type as AccountId] ?? ACCOUNT_COLORS.A
          return (
            <div
              key={item.id}
              className={cn(
                'flex-shrink-0 w-40 rounded-lg border p-3 space-y-1.5',
                colors.bg,
                colors.border,
              )}
            >
              <div className={cn('text-xs font-medium tabular-nums', colors.text)}>
                {formatTime(item.scheduled_time)}
              </div>
              <div className="text-xs text-text-primary line-clamp-2 leading-tight">{item.title}</div>
              <div className="flex items-center gap-1">
                <span className={cn('w-1.5 h-1.5 rounded-full', colors.dot)} />
                <span className="text-xs text-text-muted">{item.account_type}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
