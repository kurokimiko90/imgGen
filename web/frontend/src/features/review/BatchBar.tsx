import { Check, X } from 'lucide-react'

interface BatchBarProps {
  selectedCount: number
  onApprove: () => void
  onReject: () => void
  onCancel: () => void
  isLoading: boolean
}

export function BatchBar({ selectedCount, onApprove, onReject, onCancel, isLoading }: BatchBarProps) {
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 bg-accent/10 border border-accent/20 rounded-xl">
      <span className="text-sm text-accent font-medium">{selectedCount} selected</span>
      <div className="ml-auto flex items-center gap-2">
        <button
          onClick={onReject}
          disabled={isLoading || selectedCount === 0}
          className="px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
        >
          <X size={12} className="inline mr-1" />
          Reject All
        </button>
        <button
          onClick={onApprove}
          disabled={isLoading || selectedCount === 0}
          className="px-3 py-1.5 text-xs bg-accent/20 text-accent hover:bg-accent/30 rounded-lg transition-colors disabled:opacity-50"
        >
          <Check size={12} className="inline mr-1" />
          {isLoading ? 'Processing...' : 'Approve All'}
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-xs text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
