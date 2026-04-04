import { cn } from '@/lib/utils'
import { STATUS_COLORS, STATUS_LABELS } from '@/constants/accounts'

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const colorClass = STATUS_COLORS[status] ?? 'text-text-muted bg-white/5'
  const label = STATUS_LABELS[status] ?? status

  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', colorClass, className)}>
      {label}
    </span>
  )
}
