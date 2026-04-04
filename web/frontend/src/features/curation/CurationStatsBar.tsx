interface AccountStat {
  today: Record<string, number>
  week: Record<string, number>
  approval_rate: number
}

interface CurationStatsBarProps {
  stats: Record<string, AccountStat>
}

export function CurationStatsBar({ stats }: CurationStatsBarProps) {
  const accounts = ['A', 'B', 'C']

  return (
    <div className="grid grid-cols-3 gap-3">
      {accounts.map((id) => {
        const acct = stats[id]
        if (!acct) return null
        const todayTotal = Object.values(acct.today).reduce((a, b) => a + b, 0)
        const weekTotal = Object.values(acct.week).reduce((a, b) => a + b, 0)

        return (
          <div key={id} className="rounded-xl border border-border-subtle bg-white/3 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-text-muted">Account {id}</span>
              <span className="text-xs text-green-400">
                {Math.round(acct.approval_rate * 100)}% approved
              </span>
            </div>
            <div className="flex gap-3 text-xs text-text-muted">
              <span><span className="text-text-primary font-medium">{todayTotal}</span> today</span>
              <span><span className="text-text-primary font-medium">{weekTotal}</span> week</span>
            </div>
          </div>
        )
      })}
    </div>
  )
}
