import { useRef } from 'react'
import { Rss, Play, AlertCircle } from 'lucide-react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useCurationStore } from '@/stores/useCurationStore'
import {
  useDrafts,
  useUpdateContentStatus,
  useCurationStats,
  type ContentDetail,
} from '@/api/queries'
import { CurationProgressFeed } from '@/features/curation/CurationProgressFeed'
import { DraftContentList } from '@/features/curation/DraftContentList'
import { CurationStatsBar } from '@/features/curation/CurationStatsBar'

export function CurationPage() {
  const {
    accountFilter,
    sourceFilter,
    daysFilter,
    isRunning,
    progress,
    setAccountFilter,
    setSourceFilter,
    setDaysFilter,
    setRunning,
    addProgress,
    resetProgress,
  } = useCurationStore()

  const sseRef = useRef<EventSource | null>(null)

  const drafts = useDrafts({
    account: accountFilter,
    source: sourceFilter,
    days: daysFilter,
  })

  const statusUpdate = useUpdateContentStatus()
  const stats = useCurationStats()

  function startCuration(accounts: string[]) {
    if (sseRef.current) {
      sseRef.current.close()
    }
    resetProgress()
    setRunning(true)

    const body = JSON.stringify({ accounts, dry_run: false })
    fetch('/api/curation/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    }).then((res) => {
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      function pump() {
        reader?.read().then(({ done, value }) => {
          if (done) {
            setRunning(false)
            drafts.refetch()
            stats.refetch()
            return
          }
          const chunk = decoder.decode(value)
          const lines = chunk.split('\n\n').filter(Boolean)
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const event = JSON.parse(line.slice(6))
                addProgress(event)
                if (event.type === 'done') {
                  setRunning(false)
                }
              } catch {
                // ignore parse errors
              }
            }
          }
          pump()
        }).catch(() => setRunning(false))
      }

      pump()
    }).catch(() => setRunning(false))
  }

  async function handleSendToReview(item: ContentDetail) {
    await statusUpdate.mutateAsync({ id: item.id, status: 'PENDING_REVIEW' })
    drafts.refetch()
  }

  async function handleRejectDraft(item: ContentDetail) {
    await statusUpdate.mutateAsync({ id: item.id, status: 'REJECTED' })
    drafts.refetch()
  }

  const items: ContentDetail[] = drafts.data?.items ?? []

  return (
    <PageTransition>
      <div className="p-6 space-y-5 max-w-5xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Rss size={22} className="text-accent" />
            <div>
              <h1 className="text-xl font-semibold text-text-primary">Curation</h1>
              <p className="text-sm text-text-muted">
                {items.length} draft{items.length !== 1 ? 's' : ''} available
              </p>
            </div>
          </div>

          {/* Run buttons */}
          <div className="flex items-center gap-2">
            {['A', 'B', 'C'].map((acct) => (
              <button
                key={acct}
                onClick={() => startCuration([acct])}
                disabled={isRunning}
                className="px-3 py-1.5 text-xs bg-bg-surface border border-border-subtle hover:border-accent text-text-muted hover:text-accent rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Run {acct}
              </button>
            ))}
            <button
              onClick={() => startCuration(['A', 'B', 'C'])}
              disabled={isRunning}
              className={`flex items-center gap-1.5 px-4 py-1.5 text-sm rounded-lg transition-colors ${
                isRunning
                  ? 'bg-accent/10 text-accent/50 cursor-not-allowed'
                  : 'bg-accent/20 text-accent hover:bg-accent/30'
              }`}
            >
              <Play size={14} />
              {isRunning ? 'Running...' : 'Run All'}
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex items-center gap-3 flex-wrap">
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

          <select
            value={sourceFilter ?? ''}
            onChange={(e) => setSourceFilter(e.target.value || null)}
            className="bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent"
          >
            <option value="">All Sources</option>
            <option value="hacker_news">Hacker News</option>
            <option value="techcrunch">TechCrunch</option>
            <option value="bbc_sport">BBC Sport</option>
            <option value="hbr">HBR</option>
            <option value="pmi">PMI</option>
          </select>

          <select
            value={daysFilter ?? ''}
            onChange={(e) => setDaysFilter(e.target.value ? Number(e.target.value) : null)}
            className="bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent"
          >
            <option value="">All Time</option>
            <option value="1">Today</option>
            <option value="7">Last 7 days</option>
            <option value="30">Last 30 days</option>
          </select>
        </div>

        {/* Stats bar */}
        {stats.data && <CurationStatsBar stats={stats.data.stats} />}

        {/* SSE Progress Feed */}
        {(isRunning || progress.length > 0) && (
          <GlassCard>
            <h2 className="text-xs uppercase tracking-wider text-text-muted mb-3">Progress</h2>
            <CurationProgressFeed events={progress} isRunning={isRunning} />
          </GlassCard>
        )}

        {/* Draft content list */}
        {drafts.isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-white/5" />
            ))}
          </div>
        ) : drafts.isError ? (
          <GlassCard>
            <div className="flex items-center gap-2 text-red-600">
              <AlertCircle size={16} />
              <span className="text-sm">Failed to load drafts</span>
            </div>
          </GlassCard>
        ) : (
          <DraftContentList
            items={items}
            onSendToReview={handleSendToReview}
            onReject={handleRejectDraft}
            isLoading={statusUpdate.isPending}
          />
        )}
      </div>
    </PageTransition>
  )
}
