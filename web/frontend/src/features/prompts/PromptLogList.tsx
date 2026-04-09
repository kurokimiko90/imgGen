import { useState } from 'react'
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import { usePromptsLatest } from '@/api/queries'
import { GlassCard } from '@/components/layout/GlassCard'

interface PromptLogListProps {
  onSelect: (id: number, pipelineId: string, stage: string) => void
  selectedId?: number | null
}

const STAGE_TABS = [
  { label: 'extraction', value: 'extraction/extract-key-points' },
  { label: 'caption', value: 'caption-generation/caption' },
]

export function PromptLogList({ onSelect, selectedId }: PromptLogListProps) {
  const [stage, setStage] = useState('extraction/extract-key-points')
  const { data, isLoading } = usePromptsLatest(100)

  const logs = data?.logs || []
  const [pipelineId, stageName] = stage.split('/')

  // Filter logs by pipeline and stage
  const filtered = logs.filter((log) => log.pipeline_id === pipelineId && log.stage === stageName)

  if (isLoading) {
    return (
      <GlassCard className="p-4 space-y-4">
        <Loader2 size={20} className="animate-spin text-accent" />
        <p className="text-sm text-text-muted">Loading logs...</p>
      </GlassCard>
    )
  }

  return (
    <GlassCard className="p-4 space-y-4 max-h-[600px] overflow-y-auto">
      {/* Stage tabs */}
      <div className="flex gap-2">
        {STAGE_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStage(tab.value)}
            className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
              stage === tab.value
                ? 'bg-accent text-white'
                : 'bg-border-subtle text-text-muted hover:bg-border'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Log list */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <p className="text-xs text-text-muted text-center py-4">No logs for this stage</p>
        ) : (
          filtered.map((log) => (
            <button
              key={log.id}
              onClick={() => onSelect(log.id, log.pipeline_id, log.stage)}
              className={`w-full text-left p-3 rounded-lg transition-colors border border-transparent ${
                selectedId === log.id
                  ? 'bg-accent/15 border-accent/30'
                  : 'bg-border-subtle hover:bg-border'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-text-primary">
                    #{log.id}
                    {log.stage && <span className="ml-2 text-text-muted">{log.stage.replace('_', ' ')}</span>}
                  </div>
                  <div className="text-xs text-text-muted mt-0.5">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </div>
                  {log.model && (
                    <div className="text-xs text-text-secondary mt-1 truncate">
                      {log.model}
                      {log.provider && <span> ({log.provider})</span>}
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0">
                  {log.success ? (
                    <CheckCircle2 size={16} className="text-accent" />
                  ) : (
                    <AlertCircle size={16} className="text-red-600" />
                  )}
                </div>
              </div>
            </button>
          ))
        )}
      </div>

      {/* Count */}
      <div className="text-xs text-text-muted pt-2 border-t border-border-subtle">
        {filtered.length} log{filtered.length !== 1 ? 's' : ''} shown
      </div>
    </GlassCard>
  )
}
