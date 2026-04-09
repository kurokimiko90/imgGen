import { BarChart3, CheckCircle, Database } from 'lucide-react'
import { usePromptStats } from '@/api/queries'
import { GlassCard } from '@/components/layout/GlassCard'

interface PromptStatsBarProps {
  pipelineId: string
  stage: string
}

export function PromptStatsBar({ pipelineId, stage }: PromptStatsBarProps) {
  const { data, isLoading } = usePromptStats(pipelineId, stage)
  const stats = data?.stats

  if (isLoading) {
    return (
      <div className="grid grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <GlassCard key={i} className="h-24 animate-pulse" />
        ))}
      </div>
    )
  }

  if (!stats) {
    return <div className="text-text-muted text-sm">No data available</div>
  }

  const successRate = ((stats.successful_calls / stats.total_calls) * 100).toFixed(1)

  return (
    <div className="grid grid-cols-3 gap-4">
      <GlassCard className="p-4 space-y-2">
        <div className="flex items-center gap-2">
          <Database size={18} className="text-accent" />
          <span className="text-sm text-text-muted">Total Calls</span>
        </div>
        <div className="text-2xl font-bold">{stats.total_calls}</div>
      </GlassCard>

      <GlassCard className="p-4 space-y-2">
        <div className="flex items-center gap-2">
          <CheckCircle size={18} className="text-accent" />
          <span className="text-sm text-text-muted">Success Rate</span>
        </div>
        <div className="text-2xl font-bold">{successRate}%</div>
        <div className="text-xs text-text-secondary">
          {stats.successful_calls} / {stats.total_calls}
        </div>
      </GlassCard>

      <GlassCard className="p-4 space-y-2">
        <div className="flex items-center gap-2">
          <BarChart3 size={18} className="text-accent" />
          <span className="text-sm text-text-muted">Unique Prompts</span>
        </div>
        <div className="flex gap-3">
          <div>
            <div className="text-xs text-text-secondary">System</div>
            <div className="text-lg font-bold">{stats.unique_system_prompts}</div>
          </div>
          <div>
            <div className="text-xs text-text-secondary">User</div>
            <div className="text-lg font-bold">{stats.unique_user_prompts}</div>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
