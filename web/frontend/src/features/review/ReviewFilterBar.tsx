import { Filter, Layers } from 'lucide-react'
import { useReviewStore } from '@/stores/useReviewStore'

const ACCOUNT_OPTIONS = [
  { value: null, label: 'All Accounts' },
  { value: 'A', label: 'Account A' },
  { value: 'B', label: 'Account B' },
  { value: 'C', label: 'Account C' },
] as const

const STATUS_OPTIONS = [
  { value: 'DRAFT,PENDING_REVIEW', label: 'All Pending' },
  { value: 'DRAFT', label: 'Draft' },
  { value: 'PENDING_REVIEW', label: 'Pending Review' },
] as const

export function ReviewFilterBar() {
  const { filterAccount, filterStatus, batchMode, setFilterAccount, setFilterStatus, toggleBatchMode } =
    useReviewStore()

  const currentStatusParam = filterStatus.join(',')

  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="flex items-center gap-1.5 text-text-muted">
        <Filter size={14} />
        <span className="text-xs uppercase tracking-wider">Filter</span>
      </div>

      {/* Account filter */}
      <select
        value={filterAccount ?? ''}
        onChange={(e) => setFilterAccount(e.target.value || null)}
        className="bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent"
      >
        {ACCOUNT_OPTIONS.map((o) => (
          <option key={String(o.value)} value={o.value ?? ''}>
            {o.label}
          </option>
        ))}
      </select>

      {/* Status filter */}
      <select
        value={currentStatusParam}
        onChange={(e) => setFilterStatus(e.target.value.split(','))}
        className="bg-bg-surface border border-border-subtle rounded-lg px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:border-accent"
      >
        {STATUS_OPTIONS.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>

      <div className="ml-auto">
        <button
          onClick={toggleBatchMode}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg transition-colors ${
            batchMode
              ? 'bg-accent/20 text-accent border border-accent/30'
              : 'border border-border-subtle text-text-muted hover:text-text-primary hover:bg-hover'
          }`}
        >
          <Layers size={14} />
          <span>Batch</span>
        </button>
      </div>
    </div>
  )
}
