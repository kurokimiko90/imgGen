import { cn } from '@/lib/utils'
import { ACCOUNT_COLORS, type AccountId } from '@/constants/accounts'

interface HealthCardProps {
  accountId: AccountId
  name: string
  weeklyOutput: number
  approvalRate: number
}

export function HealthCard({ accountId, name, weeklyOutput, approvalRate }: HealthCardProps) {
  const colors = ACCOUNT_COLORS[accountId]
  const pct = Math.round(approvalRate * 100)

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className={cn('w-2 h-2 rounded-full', colors.dot)} />
        <span className="text-sm font-medium text-text-primary">{name}</span>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-muted">
          <span>Weekly output</span>
          <span className="text-text-primary font-medium tabular-nums">{weeklyOutput}</span>
        </div>
      </div>

      <div className="space-y-1">
        <div className="flex justify-between text-xs text-text-muted">
          <span>Approval rate</span>
          <span className={cn('font-medium tabular-nums', colors.text)}>{pct}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all', colors.dot)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  )
}
