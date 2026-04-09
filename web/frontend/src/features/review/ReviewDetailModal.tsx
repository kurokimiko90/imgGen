import { useState, useEffect } from 'react'
import { X, Check, AlertTriangle, Clock } from 'lucide-react'
import type { ContentDetail } from '@/api/queries'

interface ReviewDetailModalProps {
  item: ContentDetail
  currentIndex: number
  totalItems: number
  onClose: () => void
  onNavigate: (direction: 'prev' | 'next') => void
  onApprove: (id: string, publishTime?: string) => void
  onReject: (id: string) => void
  isApproving: boolean
  isRejecting: boolean
}

const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-accent/70 bg-accent/10',
  PENDING_REVIEW: 'text-accent bg-accent/15',
  APPROVED: 'text-accent/60 bg-accent/10',
  REJECTED: 'text-red-600/70 bg-red-600/15',
}

const ACCOUNT_COLORS: Record<string, string> = {
  A: 'bg-accent/10 text-accent',
  B: 'bg-accent/10 text-accent',
  C: 'bg-accent/10 text-accent',
}

export function ReviewDetailModal({
  item,
  currentIndex,
  totalItems,
  onClose,
  onNavigate,
  onApprove,
  onReject,
  isApproving,
  isRejecting,
}: ReviewDetailModalProps) {
  const [publishTime, setPublishTime] = useState('')
  const hasErrors = item.preflight_warnings.some((w) => w.startsWith('[ERROR]'))

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') {
        e.preventDefault()
        if (currentIndex > 0) onNavigate('prev')
      } else if (e.key === 'ArrowRight') {
        e.preventDefault()
        if (currentIndex < totalItems - 1) onNavigate('next')
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [currentIndex, totalItems, onNavigate, onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      {/* Modal */}
      <div className="w-full max-w-2xl bg-bg-surface border border-border-subtle rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border-subtle">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${ACCOUNT_COLORS[item.account_type] ?? ''}`}>
                {item.account_name || `Account ${item.account_type}`}
              </span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${STATUS_COLORS[item.status] ?? ''}`}>
                {item.status.replace('_', ' ')}
              </span>
              {item.preflight_warnings.length > 0 && (
                <span className="flex items-center gap-1 text-xs text-red-600">
                  <AlertTriangle size={12} />
                  {item.preflight_warnings.some((w) => w.startsWith('[ERROR]')) ? 'Errors' : 'Warnings'}
                </span>
              )}
            </div>
            <h2 className="text-xl font-semibold text-text-primary">{item.title}</h2>
            <p className="text-sm text-text-muted mt-1">
              Item {currentIndex + 1} of {totalItems}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-text-muted hover:text-text-primary transition-colors p-2 hover:bg-hover rounded-lg"
            title="Close (Esc)"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Image */}
          {item.image_url && (
            <div className="rounded-xl overflow-hidden border border-border-subtle">
              <img
                src={item.image_url}
                alt={item.title}
                className="w-full h-auto object-contain bg-black/20"
              />
            </div>
          )}

          {/* Body */}
          <div className="space-y-2">
            <label className="text-xs text-text-muted uppercase tracking-wider font-semibold">Content</label>
            <div className="p-3 bg-bg-base border border-border-subtle rounded-lg text-sm text-text-primary leading-relaxed">
              {item.body}
            </div>
          </div>

          {/* Preflight warnings */}
          {item.preflight_warnings.length > 0 && (
            <div className="space-y-2">
              <label className="text-xs text-text-muted uppercase tracking-wider font-semibold">
                {hasErrors ? 'Errors' : 'Warnings'}
              </label>
              <div className="space-y-2">
                {item.preflight_warnings.map((w, i) => (
                  <div
                    key={i}
                    className={`text-xs px-3 py-2 rounded-lg border ${
                      w.startsWith('[ERROR]')
                        ? 'bg-red-600/10 border-red-600/20 text-red-600'
                        : 'bg-accent/10 border-accent/20 text-accent'
                    }`}
                  >
                    {w.replace(/^\[(ERROR|WARNING)\] /, '')}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="space-y-2 text-xs text-text-muted">
            {item.source && <div>Source: {item.source}</div>}
            {item.source_url && (
              <div>
                <a
                  href={item.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent hover:underline truncate block"
                >
                  {item.source_url}
                </a>
              </div>
            )}
            <div>Created: {new Date(item.created_at).toLocaleString()}</div>
          </div>
        </div>

        {/* Footer with actions */}
        <div className="p-6 border-t border-border-subtle space-y-4">
          {/* Publish time */}
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-text-muted" />
            <label className="text-xs text-text-muted uppercase tracking-wider font-semibold">Publish Time</label>
            <input
              type="time"
              value={publishTime}
              onChange={(e) => setPublishTime(e.target.value)}
              className="ml-auto bg-bg-base border border-border-subtle rounded-lg px-2 py-1 text-sm text-text-primary focus:outline-none focus:border-accent"
            />
          </div>

          {/* Action buttons */}
          <div className="flex gap-3 justify-between">
            {/* Navigation */}
            <div className="flex gap-2">
              <button
                onClick={() => onNavigate('prev')}
                disabled={currentIndex === 0}
                className="px-3 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-hover rounded-lg disabled:opacity-30 transition-colors"
                title="Previous (← Arrow)"
              >
                ← Prev
              </button>
              <button
                onClick={() => onNavigate('next')}
                disabled={currentIndex === totalItems - 1}
                className="px-3 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-hover rounded-lg disabled:opacity-30 transition-colors"
                title="Next (→ Arrow)"
              >
                Next →
              </button>
            </div>

            {/* Review actions */}
            <div className="flex gap-2">
              <button
                onClick={() => onReject(item.id)}
                disabled={isRejecting}
                className="px-4 py-2 text-sm text-red-600 hover:bg-red-600/10 rounded-lg transition-colors disabled:opacity-50"
                title="Reject"
              >
                Reject
              </button>
              <button
                onClick={() => onApprove(item.id, publishTime || undefined)}
                disabled={isApproving || hasErrors}
                className="flex items-center gap-2 px-4 py-2 text-sm bg-accent/20 text-accent hover:bg-accent/30 rounded-lg transition-colors disabled:opacity-50"
                title={hasErrors ? 'Fix errors first' : 'Approve'}
              >
                <Check size={14} />
                Approve
              </button>
            </div>
          </div>

          {/* Keyboard hints */}
          <div className="text-xs text-text-muted/60 text-center">
            Use arrow keys (← →) to navigate • Esc to close
          </div>
        </div>
      </div>
    </div>
  )
}
