import { cn } from '@/lib/utils'
import { ACCOUNT_COLORS, STATUS_LABELS, type AccountId } from '@/constants/accounts'

interface AccountCounts {
  DRAFT: number
  PENDING_REVIEW: number
  APPROVED: number
  PUBLISHED: number
  REJECTED: number
}

interface AccountCardProps {
  accountId: AccountId
  name: string
  counts: AccountCounts
}

const STATUS_ORDER: Array<keyof AccountCounts> = [
  'DRAFT', 'PENDING_REVIEW', 'APPROVED', 'PUBLISHED', 'REJECTED',
]

export function AccountCard({ accountId, name, counts }: AccountCardProps) {
  const colors = ACCOUNT_COLORS[accountId]
  const total = Object.values(counts).reduce((s, n) => s + n, 0)

  return (
    <div className={cn('rounded-xl border p-4 space-y-3', colors.bg, colors.border)}>
      <div className="flex items-center gap-2">
        <span className={cn('w-2.5 h-2.5 rounded-full shrink-0', colors.dot)} />
        <span className={cn('text-sm font-semibold', colors.text)}>{name}</span>
        <span className="ml-auto text-xs text-text-muted">{total} total</span>
      </div>

      <div className="grid grid-cols-2 gap-1.5">
        {STATUS_ORDER.map((s) => (
          <div key={s} className="flex items-center justify-between text-xs">
            <span className="text-text-muted">{STATUS_LABELS[s]}</span>
            <span className={cn('font-medium tabular-nums', counts[s] > 0 ? 'text-text-primary' : 'text-text-faint')}>
              {counts[s]}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
