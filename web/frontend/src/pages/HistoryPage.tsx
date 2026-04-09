import { useState } from 'react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useHistory, useStats } from '@/api/queries'
import { HistoryDetailPanel } from '@/features/history/HistoryDetailPanel'
import { motion, useSpring, useTransform, AnimatePresence } from 'framer-motion'
import { Clock, Search, BarChart3, Image, Palette, Cpu, LayoutGrid, X, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useEffect, useRef } from 'react'

// ---------------------------------------------------------------------------
// Animated Counter
// ---------------------------------------------------------------------------

function AnimatedCounter({ value }: { value: number }) {
  const spring = useSpring(0, { stiffness: 80, damping: 20 })
  const display = useTransform(spring, (v) => Math.round(v))
  const ref = useRef<HTMLSpanElement>(null)

  useEffect(() => {
    spring.set(value)
  }, [value, spring])

  useEffect(() => {
    const unsubscribe = display.on('change', (v) => {
      if (ref.current) ref.current.textContent = String(v)
    })
    return unsubscribe
  }, [display])

  return <span ref={ref}>0</span>
}

// ---------------------------------------------------------------------------
// Stats Panel
// ---------------------------------------------------------------------------

function StatsPanel({ days }: { days: number | undefined }) {
  const { data } = useStats(days)

  if (!data) return null

  const statCards = [
    { label: 'Total', value: data.total, icon: Image, color: 'text-accent' },
    { label: 'Avg Points', value: data.avg_points, icon: BarChart3, color: 'text-accent' },
  ]

  return (
    <div className="space-y-4">
      {/* Top stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {statCards.map((s) => (
          <GlassCard key={s.label} className="text-center space-y-1">
            <s.icon size={20} className={cn('mx-auto', s.color)} />
            <div className="text-2xl font-bold">
              <AnimatedCounter value={s.value} />
            </div>
            <div className="text-xs text-text-muted">{s.label}</div>
          </GlassCard>
        ))}
        {data.by_theme.slice(0, 1).map((t) => (
          <GlassCard key={t.name} className="text-center space-y-1">
            <Palette size={20} className="mx-auto text-accent" />
            <div className="text-2xl font-bold">
              <AnimatedCounter value={t.count} />
            </div>
            <div className="text-xs text-text-muted">Theme: {t.name}</div>
          </GlassCard>
        ))}
        {data.by_provider.slice(0, 1).map((p) => (
          <GlassCard key={p.name} className="text-center space-y-1">
            <Cpu size={20} className="mx-auto text-accent" />
            <div className="text-2xl font-bold">
              <AnimatedCounter value={p.count} />
            </div>
            <div className="text-xs text-text-muted">Provider: {p.name}</div>
          </GlassCard>
        ))}
      </div>

      {/* Breakdown rows */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <GlassCard className="space-y-2">
          <div className="text-xs font-medium text-text-muted uppercase flex items-center gap-1">
            <Palette size={12} /> By Theme
          </div>
          {data.by_theme.map((t) => (
            <div key={t.name} className="flex items-center justify-between text-sm">
              <span className="text-text-secondary">{t.name}</span>
              <span className="text-text-muted">{t.count}</span>
            </div>
          ))}
          {data.by_theme.length === 0 && <p className="text-xs text-text-faint">No data</p>}
        </GlassCard>

        <GlassCard className="space-y-2">
          <div className="text-xs font-medium text-text-muted uppercase flex items-center gap-1">
            <Cpu size={12} /> By Provider
          </div>
          {data.by_provider.map((p) => (
            <div key={p.name} className="flex items-center justify-between text-sm">
              <span className="text-text-secondary">{p.name}</span>
              <span className="text-text-muted">{p.count}</span>
            </div>
          ))}
          {data.by_provider.length === 0 && <p className="text-xs text-text-faint">No data</p>}
        </GlassCard>

        <GlassCard className="space-y-2">
          <div className="text-xs font-medium text-text-muted uppercase flex items-center gap-1">
            <LayoutGrid size={12} /> By Format
          </div>
          {data.by_format.map((f) => (
            <div key={f.name} className="flex items-center justify-between text-sm">
              <span className="text-text-secondary">{f.name}</span>
              <span className="text-text-muted">{f.count}</span>
            </div>
          ))}
          {data.by_format.length === 0 && <p className="text-xs text-text-faint">No data</p>}
        </GlassCard>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// History Page
// ---------------------------------------------------------------------------

const DAY_OPTIONS = [
  { label: 'All', value: undefined },
  { label: '7d', value: 7 },
  { label: '30d', value: 30 },
  { label: '90d', value: 90 },
] as const

export function HistoryPage() {
  const [tab, setTab] = useState<'list' | 'stats'>('list')
  const [days, setDays] = useState<number | undefined>(undefined)
  const [search, setSearch] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedId, setExpandedId] = useState<number | null>(null)

  const { data, isLoading } = useHistory(days, searchQuery || undefined, 50)

  const handleSearch = () => {
    setSearchQuery(search)
  }

  const toggleExpand = (id: number) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  return (
    <PageTransition className="p-6 max-w-5xl space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Clock size={24} className="text-accent" />
          <h1 className="text-xl font-semibold">History</h1>
        </div>

        {/* Tab toggle */}
        <div className="flex gap-1 rounded-lg bg-bg-surface p-1">
          <button
            onClick={() => setTab('list')}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              tab === 'list' ? 'bg-accent text-white' : 'text-text-muted hover:text-text-secondary',
            )}
          >
            List
          </button>
          <button
            onClick={() => setTab('stats')}
            className={cn(
              'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              tab === 'stats' ? 'bg-accent text-white' : 'text-text-muted hover:text-text-secondary',
            )}
          >
            Stats
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Days filter */}
        <div className="flex gap-1 rounded-lg bg-bg-surface p-1">
          {DAY_OPTIONS.map((opt) => (
            <button
              key={opt.label}
              onClick={() => setDays(opt.value)}
              className={cn(
                'rounded-md px-3 py-1.5 text-xs font-medium transition-colors',
                days === opt.value ? 'bg-bg-input text-text' : 'text-text-muted hover:text-text-secondary',
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Search */}
        {tab === 'list' && (
          <div className="flex gap-2 flex-1 max-w-md">
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-faint" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search by title or URL..."
                className="w-full rounded-lg border border-border bg-bg-input pl-9 pr-3 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50"
              />
              {search && (
                <button
                  onClick={() => { setSearch(''); setSearchQuery('') }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-text-faint hover:text-text-secondary"
                >
                  <X size={14} />
                </button>
              )}
            </div>
            <button
              onClick={handleSearch}
              className="rounded-lg bg-accent-dim px-3 py-2 text-sm text-accent hover:bg-accent-dim/70 transition-colors"
            >
              Search
            </button>
          </div>
        )}
      </div>

      {/* Content */}
      {tab === 'stats' ? (
        <StatsPanel days={days} />
      ) : (
        <GlassCard className="p-0 overflow-hidden">
          {/* Table header */}
          <div className="grid grid-cols-[1fr_100px_100px_100px_80px_160px_32px] gap-2 px-4 py-3 text-xs font-medium text-text-muted uppercase border-b border-border-subtle">
            <div>Title</div>
            <div>Theme</div>
            <div>Format</div>
            <div>Provider</div>
            <div>Points</div>
            <div>Created</div>
            <div />
          </div>

          {/* Rows */}
          {isLoading ? (
            <div className="px-4 py-8 text-center text-sm text-text-faint">Loading...</div>
          ) : !data?.rows.length ? (
            <div className="px-4 py-12 text-center text-sm text-text-faint">
              No generations found
            </div>
          ) : (
            data.rows.map((row, i) => (
              <div key={row.id}>
                <motion.div
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.03 }}
                  onClick={() => toggleExpand(row.id)}
                  className={cn(
                    'grid grid-cols-[1fr_100px_100px_100px_80px_160px_32px] gap-2 px-4 py-3 text-sm border-b border-border-subtle cursor-pointer transition-colors',
                    expandedId === row.id ? 'bg-hover' : 'hover:bg-hover',
                  )}
                >
                  <div className="text-text-secondary truncate" title={row.title}>
                    {row.title}
                  </div>
                  <div>
                    <span className="rounded-full bg-hover px-2 py-0.5 text-xs text-text-muted">
                      {row.theme}
                    </span>
                  </div>
                  <div>
                    <span className="rounded-full bg-hover px-2 py-0.5 text-xs text-text-muted">
                      {row.format}
                    </span>
                  </div>
                  <div className="text-text-muted text-xs">{row.provider}</div>
                  <div className="text-text-muted text-xs">{row.key_points_count}</div>
                  <div className="text-text-faint text-xs">
                    {new Date(row.created_at).toLocaleString()}
                  </div>
                  <div className="flex items-center justify-center">
                    <motion.div
                      animate={{ rotate: expandedId === row.id ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown size={14} className="text-text-faint" />
                    </motion.div>
                  </div>
                </motion.div>

                {/* Expandable detail */}
                <AnimatePresence>
                  {expandedId === row.id && (
                    <HistoryDetailPanel row={row} />
                  )}
                </AnimatePresence>
              </div>
            ))
          )}
        </GlassCard>
      )}
    </PageTransition>
  )
}
