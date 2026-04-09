import { useState } from 'react'
import { ScrollText } from 'lucide-react'
import { PageTransition } from '@/components/layout/PageTransition'
import { PromptStatsBar } from '@/features/prompts/PromptStatsBar'
import { PromptLogList } from '@/features/prompts/PromptLogList'
import { PromptDetailPanel } from '@/features/prompts/PromptDetailPanel'

export function PromptsPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selectedPipelineId, setSelectedPipelineId] = useState('extraction')
  const [selectedStage, setSelectedStage] = useState('extract-key-points')

  const handleSelectLog = (id: number, pipelineId: string, stage: string) => {
    setSelectedId(id)
    setSelectedPipelineId(pipelineId)
    setSelectedStage(stage)
  }

  return (
    <PageTransition className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <ScrollText size={24} className="text-accent" />
        <h1 className="text-xl font-semibold">Prompt Logs</h1>
      </div>

      {/* Stats */}
      <PromptStatsBar pipelineId={selectedPipelineId} stage={selectedStage} />

      {/* Main layout: List + Detail */}
      <div className="grid grid-cols-3 gap-6">
        {/* Left: Log list */}
        <div>
          <PromptLogList onSelect={handleSelectLog} selectedId={selectedId} />
        </div>

        {/* Right: Detail panel */}
        <div className="col-span-2">
          <PromptDetailPanel
            id={selectedId}
            pipelineId={selectedPipelineId}
            stage={selectedStage}
          />
        </div>
      </div>
    </PageTransition>
  )
}
