import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { AccountCard } from '@/features/dashboard/AccountCard'
import { HealthCard } from '@/features/dashboard/HealthCard'
import { ScheduleTimeline } from '@/features/dashboard/ScheduleTimeline'
import { RecentContentList } from '@/features/dashboard/RecentContentList'
import { QuickActions } from '@/features/dashboard/QuickActions'
import { useContentStats, useRecentContent, useScheduledContent } from '@/api/queries'
import { LayoutDashboard } from 'lucide-react'
const ACCOUNT_IDS = ['A', 'B', 'C'] as const

export function DashboardPage() {
  const stats = useContentStats()
  const recent = useRecentContent(10)
  const schedule = useScheduledContent()

  const accounts = stats.data?.accounts ?? {}
  const pendingCount = ACCOUNT_IDS.reduce(
    (sum, id) => sum + (accounts[id]?.counts?.PENDING_REVIEW ?? 0),
    0,
  )

  return (
    <PageTransition>
      <div className="p-6 space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LayoutDashboard size={22} className="text-accent" />
            <div>
              <h1 className="text-xl font-semibold text-text-primary">Dashboard</h1>
              <p className="text-sm text-text-muted">
                {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
          </div>
          <QuickActions pendingCount={pendingCount} />
        </div>

        {/* Account Status Cards */}
        <section>
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">Account Status</h2>
          {stats.isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {ACCOUNT_IDS.map((id) => (
                <div key={id} className="rounded-xl border border-border-subtle bg-white/3 h-28 animate-pulse" />
              ))}
            </div>
          ) : stats.isError ? (
            <div className="text-sm text-red-400 glass-card p-4">Failed to load stats</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {ACCOUNT_IDS.map((id) => {
                const acct = accounts[id]
                if (!acct) return null
                return (
                  <AccountCard
                    key={id}
                    accountId={id}
                    name={acct.name}
                    counts={{
                      DRAFT: acct.counts.DRAFT ?? 0,
                      PENDING_REVIEW: acct.counts.PENDING_REVIEW ?? 0,
                      APPROVED: acct.counts.APPROVED ?? 0,
                      PUBLISHED: acct.counts.PUBLISHED ?? 0,
                      REJECTED: acct.counts.REJECTED ?? 0,
                    }}
                  />
                )
              })}
            </div>
          )}
        </section>

        {/* Today's Schedule */}
        <GlassCard>
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">Today's Schedule</h2>
          {schedule.isLoading ? (
            <div className="h-16 animate-pulse bg-white/5 rounded-lg" />
          ) : (
            <ScheduleTimeline items={schedule.data?.items ?? []} />
          )}
        </GlassCard>

        {/* Health Metrics */}
        <section>
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">Health Metrics</h2>
          {stats.isLoading ? (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {ACCOUNT_IDS.map((id) => (
                <div key={id} className="glass-card h-24 animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {ACCOUNT_IDS.map((id) => {
                const acct = accounts[id]
                if (!acct) return null
                return (
                  <HealthCard
                    key={id}
                    accountId={id}
                    name={acct.name}
                    weeklyOutput={acct.weekly_output}
                    approvalRate={acct.approval_rate}
                  />
                )
              })}
            </div>
          )}
        </section>

        {/* Recent Content */}
        <GlassCard>
          <h2 className="text-sm font-medium text-text-muted uppercase tracking-wider mb-3">Recent Content</h2>
          {recent.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-8 animate-pulse bg-white/5 rounded" />
              ))}
            </div>
          ) : recent.isError ? (
            <div className="text-sm text-red-400">Failed to load recent content</div>
          ) : (
            <RecentContentList items={recent.data?.items ?? []} />
          )}
        </GlassCard>
      </div>
    </PageTransition>
  )
}
