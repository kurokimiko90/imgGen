import { useState } from 'react'
import { Check, X, Pencil, AlertTriangle, Clock, ChevronDown, ChevronUp } from 'lucide-react'
import type { ContentDetail } from '@/api/queries'
import { useReviewStore } from '@/stores/useReviewStore'

interface ReviewCardProps {
  item: ContentDetail
  selectable: boolean
  selected: boolean
  onApprove: (id: string, publishTime?: string) => void
  onReject: (id: string) => void
  onEdit: (id: string) => void
  isApproving: boolean
  isRejecting: boolean
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-yellow-400 bg-yellow-400/10',
  PENDING_REVIEW: 'text-blue-400 bg-blue-400/10',
  APPROVED: 'text-green-400 bg-green-400/10',
  REJECTED: 'text-red-400 bg-red-400/10',
}

const ACCOUNT_COLORS: Record<string, string> = {
  A: 'bg-purple-500/20 text-purple-300',
  B: 'bg-sky-500/20 text-sky-300',
  C: 'bg-amber-500/20 text-amber-300',
}

export function ReviewCard({
  item,
  selectable,
  selected,
  onApprove,
  onReject,
  onEdit,
  isApproving,
  isRejecting,
}: ReviewCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [publishTime, setPublishTime] = useState('')
  const { toggleSelect } = useReviewStore()

  const hasErrors = item.preflight_warnings.some((w) => w.startsWith('[ERROR]'))
  const hasWarnings = item.preflight_warnings.length > 0

  return (
    <div
      className={`rounded-xl border transition-all ${
        selected
          ? 'border-accent bg-accent/5'
          : 'border-border-subtle bg-white/3 hover:border-border-strong'
      }`}
    >
      <div className="p-4">
        {/* Top row: account badge + status + title */}
        <div className="flex items-start gap-3">
          {selectable && (
            <input
              type="checkbox"
              checked={selected}
              onChange={() => toggleSelect(item.id)}
              className="mt-0.5 accent-accent shrink-0"
            />
          )}

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${ACCOUNT_COLORS[item.account_type] ?? ''}`}>
                {item.account_name || `Account ${item.account_type}`}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[item.status] ?? ''}`}>
                {item.status.replace('_', ' ')}
              </span>
              {hasErrors && (
                <span className="flex items-center gap-1 text-xs text-red-400">
                  <AlertTriangle size={12} />
                  Errors
                </span>
              )}
              {!hasErrors && hasWarnings && (
                <span className="flex items-center gap-1 text-xs text-yellow-400">
                  <AlertTriangle size={12} />
                  Warnings
                </span>
              )}
            </div>

            <h3 className="text-sm font-semibold text-text-primary truncate">{item.title}</h3>
            <p className={`text-xs text-text-muted mt-0.5 ${expanded ? '' : 'line-clamp-2'}`}>
              {item.body}
            </p>
          </div>

          {/* Image preview */}
          {item.image_url && (
            <img
              src={item.image_url}
              alt={item.title}
              className="w-16 h-16 rounded-lg object-cover shrink-0"
            />
          )}
        </div>

        {/* Preflight warnings */}
        {hasWarnings && expanded && (
          <div className="mt-3 space-y-1">
            {item.preflight_warnings.map((w, i) => (
              <div
                key={i}
                className={`text-xs px-2 py-1 rounded ${
                  w.startsWith('[ERROR]')
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-yellow-500/10 text-yellow-400'
                }`}
              >
                {w.replace(/^\[(ERROR|WARNING)\] /, '')}
              </div>
            ))}
          </div>
        )}

        {/* Source and time */}
        {expanded && (
          <div className="mt-3 space-y-1.5 text-xs text-text-muted">
            {item.source && <span>Source: {item.source}</span>}
            {item.source_url && (
              <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="block hover:text-accent truncate">
                {item.source_url}
              </a>
            )}
            <span>Created: {new Date(item.created_at).toLocaleString()}</span>
          </div>
        )}

        {/* Actions row */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border-subtle/50">
          {!selectable && (
            <>
              {/* Publish time */}
              <div className="flex items-center gap-1.5">
                <Clock size={12} className="text-text-muted" />
                <input
                  type="time"
                  value={publishTime}
                  onChange={(e) => setPublishTime(e.target.value)}
                  className="bg-transparent text-xs text-text-muted border-none focus:outline-none w-20"
                  placeholder="HH:MM"
                />
              </div>

              <div className="ml-auto flex items-center gap-1.5">
                <button
                  onClick={() => onEdit(item.id)}
                  className="p-1.5 text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors"
                  title="Edit"
                >
                  <Pencil size={14} />
                </button>
                <button
                  onClick={() => onReject(item.id)}
                  disabled={isRejecting}
                  className="px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                >
                  <X size={13} className="inline mr-1" />
                  Reject
                </button>
                <button
                  onClick={() => onApprove(item.id, publishTime || undefined)}
                  disabled={isApproving || hasErrors}
                  className="px-3 py-1.5 text-xs bg-accent/20 text-accent hover:bg-accent/30 rounded-lg transition-colors disabled:opacity-50"
                  title={hasErrors ? 'Fix errors first' : 'Approve'}
                >
                  <Check size={13} className="inline mr-1" />
                  Approve
                </button>
              </div>
            </>
          )}

          {/* Expand toggle */}
          <button
            onClick={() => setExpanded(!expanded)}
            className={`${selectable ? 'ml-auto' : ''} p-1.5 text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors`}
          >
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>
    </div>
  )
}
