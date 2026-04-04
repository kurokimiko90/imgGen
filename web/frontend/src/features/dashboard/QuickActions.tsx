import { Link } from 'react-router-dom'
import { CheckSquare, RefreshCw } from 'lucide-react'

interface QuickActionsProps {
  pendingCount: number
}

export function QuickActions({ pendingCount }: QuickActionsProps) {
  return (
    <div className="flex gap-3 flex-wrap">
      <Link
        to="/review"
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/80 transition-colors"
      >
        <CheckSquare size={16} />
        Review Content
        {pendingCount > 0 && (
          <span className="ml-1 bg-white/20 rounded-full px-1.5 py-0.5 text-xs tabular-nums">
            {pendingCount}
          </span>
        )}
      </Link>

      <Link
        to="/curation"
        className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border-subtle text-sm text-text-secondary hover:text-text-primary hover:bg-hover transition-colors"
      >
        <RefreshCw size={16} />
        Run Curation
      </Link>
    </div>
  )
}
