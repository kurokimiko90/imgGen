import { ArrowRight, X } from 'lucide-react'
import type { ContentDetail } from '@/api/queries'
import { GlassCard } from '@/components/layout/GlassCard'

interface DraftContentListProps {
  items: ContentDetail[]
  onSendToReview: (item: ContentDetail) => void
  onReject: (item: ContentDetail) => void
  isLoading: boolean
}

const SOURCE_LABELS: Record<string, string> = {
  hacker_news: 'HN',
  techcrunch: 'TC',
  bbc_sport: 'BBC',
  hbr: 'HBR',
  pmi: 'PMI',
}

const ACCOUNT_COLORS: Record<string, string> = {
  A: 'bg-purple-500/20 text-purple-300',
  B: 'bg-sky-500/20 text-sky-300',
  C: 'bg-amber-500/20 text-amber-300',
}

export function DraftContentList({ items, onSendToReview, onReject, isLoading }: DraftContentListProps) {
  if (items.length === 0) {
    return (
      <GlassCard>
        <p className="text-sm text-text-muted text-center py-6">No drafts found</p>
      </GlassCard>
    )
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center gap-3 p-3 rounded-xl border border-border-subtle bg-white/3 hover:border-border-strong transition-colors"
        >
          {/* Account badge */}
          <span className={`shrink-0 px-2 py-0.5 rounded text-xs font-medium ${ACCOUNT_COLORS[item.account_type] ?? ''}`}>
            {item.account_type}
          </span>

          {/* Source badge */}
          {item.source && (
            <span className="shrink-0 px-2 py-0.5 rounded text-xs bg-white/10 text-text-muted">
              {SOURCE_LABELS[item.source] ?? item.source}
            </span>
          )}

          {/* Title + body */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-text-primary truncate">{item.title}</p>
            <p className="text-xs text-text-muted truncate">{item.body}</p>
          </div>

          {/* Image thumbnail */}
          {item.image_url && (
            <img src={item.image_url} alt="" className="w-10 h-10 rounded object-cover shrink-0" />
          )}

          {/* Time */}
          <span className="text-xs text-text-muted shrink-0">
            {new Date(item.created_at).toLocaleDateString()}
          </span>

          {/* Actions */}
          <div className="flex items-center gap-1 shrink-0">
            <button
              onClick={() => onReject(item)}
              disabled={isLoading}
              className="p-1.5 text-text-muted hover:text-red-400 hover:bg-red-500/10 rounded transition-colors disabled:opacity-50"
              title="Reject"
            >
              <X size={14} />
            </button>
            <button
              onClick={() => onSendToReview(item)}
              disabled={isLoading}
              className="flex items-center gap-1 px-2.5 py-1 text-xs bg-accent/20 text-accent hover:bg-accent/30 rounded-lg transition-colors disabled:opacity-50"
              title="Send to Review"
            >
              Review
              <ArrowRight size={12} />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
