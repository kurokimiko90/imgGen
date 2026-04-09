import { useState } from 'react'
import { ChevronDown, Copy, Check } from 'lucide-react'
import { usePromptsByStage } from '@/api/queries'
import { GlassCard } from '@/components/layout/GlassCard'

interface PromptDetailPanelProps {
  id: number | null
  pipelineId: string
  stage: string
}

type CopiedField = 'system' | 'user' | 'output' | null

export function PromptDetailPanel({ id, pipelineId, stage }: PromptDetailPanelProps) {
  const [copied, setCopied] = useState<CopiedField>(null)
  const [expandedSection, setExpandedSection] = useState<'system' | 'user' | 'output'>('system')

  const { data } = usePromptsByStage(pipelineId, stage)
  const logs = data?.logs || []

  const log = id != null ? logs.find((l) => l.id === id) : null

  const copyToClipboard = (text: string, field: CopiedField) => {
    navigator.clipboard.writeText(text)
    setCopied(field)
    setTimeout(() => setCopied(null), 2000)
  }

  if (!log) {
    return (
      <GlassCard className="p-6 text-center text-text-muted">
        <p>Select a log entry to view details</p>
      </GlassCard>
    )
  }

  // Try to parse JSON output
  let parsedOutput = log.output
  if (log.output) {
    try {
      parsedOutput = JSON.stringify(JSON.parse(log.output), null, 2)
    } catch {
      // Keep as is if not JSON
    }
  }

  return (
    <div className="space-y-4">
      {/* Header info */}
      <GlassCard className="p-4 space-y-2">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="text-text-muted text-xs">Model</div>
            <div className="font-medium">{log.model || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-text-muted text-xs">Provider</div>
            <div className="font-medium">{log.provider || 'Unknown'}</div>
          </div>
          <div>
            <div className="text-text-muted text-xs">Time</div>
            <div className="font-medium text-sm">{new Date(log.timestamp).toLocaleString()}</div>
          </div>
          <div>
            <div className="text-text-muted text-xs">Status</div>
            <div className={`font-medium text-sm ${log.success ? 'text-accent' : 'text-red-600'}`}>
              {log.success ? '✓ Success' : '✗ Failed'}
            </div>
          </div>
        </div>
        {!log.success && log.error_message && (
          <div className="mt-2 p-2 bg-red-600/10 rounded text-xs text-red-600 border border-red-600/20">
            {log.error_message}
          </div>
        )}
      </GlassCard>

      {/* System Prompt */}
      <PromptSection
        title="📋 System Prompt"
        field="system"
        content={log.system_prompt || '(empty)'}
        hash={log.system_hash}
        isExpanded={expandedSection === 'system'}
        onToggle={() => setExpandedSection(expandedSection === 'system' ? 'user' : 'system')}
        onCopy={() => copyToClipboard(log.system_prompt || '', 'system')}
        isCopied={copied === 'system'}
      />

      {/* User Prompt */}
      <PromptSection
        title="📝 User Prompt"
        field="user"
        content={log.user_prompt || '(empty)'}
        hash={log.user_hash}
        isExpanded={expandedSection === 'user'}
        onToggle={() => setExpandedSection(expandedSection === 'user' ? 'output' : 'user')}
        onCopy={() => copyToClipboard(log.user_prompt || '', 'user')}
        isCopied={copied === 'user'}
      />

      {/* Output */}
      <PromptSection
        title="💬 Output"
        field="output"
        content={parsedOutput || '(empty)'}
        hash={log.output_length ? `${log.output_length} chars` : 'N/A'}
        isExpanded={expandedSection === 'output'}
        onToggle={() => setExpandedSection(expandedSection === 'output' ? 'system' : 'output')}
        onCopy={() => copyToClipboard(log.output || '', 'output')}
        isCopied={copied === 'output'}
      />
    </div>
  )
}

interface PromptSectionProps {
  title: string
  field: 'system' | 'user' | 'output'
  content: string
  hash: string
  isExpanded: boolean
  onToggle: () => void
  onCopy: () => void
  isCopied: boolean
}

function PromptSection({
  title,
  content,
  hash,
  isExpanded,
  onToggle,
  onCopy,
  isCopied,
}: PromptSectionProps) {
  const truncated = content.length > 500 && !isExpanded
  const displayContent = truncated ? content.slice(0, 500) + '...' : content

  return (
    <GlassCard className="p-4 space-y-3">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between hover:opacity-80 transition-opacity"
      >
        <h3 className="font-medium text-sm">{title}</h3>
        <ChevronDown size={16} className={`transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
      </button>

      {/* Hash */}
      <div className="text-xs text-text-muted">Hash: {hash}</div>

      {/* Content */}
      {isExpanded && (
        <div className="space-y-2">
          <pre className="bg-black/30 rounded p-3 text-xs overflow-x-auto max-h-64 overflow-y-auto font-mono">
            {displayContent}
          </pre>

          {/* Copy button */}
          <button
            onClick={onCopy}
            className="flex items-center gap-2 text-xs px-2 py-1 rounded bg-accent/10 hover:bg-accent/20 text-accent transition-colors"
          >
            {isCopied ? (
              <>
                <Check size={14} /> Copied
              </>
            ) : (
              <>
                <Copy size={14} /> Copy
              </>
            )}
          </button>
        </div>
      )}
    </GlassCard>
  )
}
