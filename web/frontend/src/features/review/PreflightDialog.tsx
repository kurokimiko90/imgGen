import { AlertTriangle, X } from 'lucide-react'

interface PreflightDialogProps {
  warnings: string[]
  onClose: () => void
}

export function PreflightDialog({ warnings, onClose }: PreflightDialogProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-bg-surface border border-red-500/30 rounded-xl p-5 w-80 shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-400" />
            <h3 className="text-sm font-semibold text-red-400">Cannot Approve</h3>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X size={16} />
          </button>
        </div>

        <p className="text-xs text-text-muted">
          The following errors must be fixed before approving:
        </p>

        <ul className="space-y-1">
          {warnings.map((w, i) => (
            <li key={i} className="text-xs bg-red-500/10 text-red-400 px-2 py-1.5 rounded">
              {w.replace(/^\[ERROR\] /, '')}
            </li>
          ))}
        </ul>

        <button
          onClick={onClose}
          className="w-full px-4 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-hover rounded-lg"
        >
          Close
        </button>
      </div>
    </div>
  )
}
