import { useHistoryDetail } from '@/api/queries'
import type { HistoryRow, ExtractedData } from '@/api/queries'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  RefreshCw, ExternalLink, Loader2, List, Globe, Type,
} from 'lucide-react'

interface HistoryDetailPanelProps {
  row: HistoryRow
}

export function HistoryDetailPanel({ row }: HistoryDetailPanelProps) {
  const { data, isLoading } = useHistoryDetail(row.id)
  const store = useGenerateStore()
  const navigate = useNavigate()

  const detail = data?.row
  const extracted: ExtractedData | null = detail?.extracted_data ?? row.extracted_data ?? null

  const handleReGenerate = () => {
    if (!extracted) return
    store.loadFromHistory(extracted, row.theme, row.format)
    navigate('/')
  }

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
      className="overflow-hidden"
    >
      <div className="px-4 py-4 bg-bg-surface border-b border-border-subtle">
        <div className="flex gap-5">
          {/* Thumbnail */}
          <div className="shrink-0 w-32 h-48 rounded-lg overflow-hidden bg-bg-surface flex items-center justify-center">
            {isLoading ? (
              <Loader2 size={20} className="animate-spin text-text-faint" />
            ) : detail?.image_url ? (
              <img
                src={detail.image_url}
                alt={row.title}
                className="w-full h-full object-contain"
              />
            ) : (
              <span className="text-xs text-text-faint">No image</span>
            )}
          </div>

          {/* Content */}
          <div className="flex-1 space-y-3 min-w-0">
            {extracted ? (
              <>
                <div className="space-y-1">
                  <div className="flex items-center gap-1.5 text-xs text-text-faint">
                    <Type size={10} /> Title
                  </div>
                  <p className="text-sm text-text-secondary font-medium">{extracted.title}</p>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs text-text-faint">
                    <List size={10} /> Key Points ({extracted.key_points.length})
                  </div>
                  <ul className="space-y-1">
                    {extracted.key_points.map((p, i) => (
                      <li key={i} className="text-xs text-text-secondary flex gap-2">
                        <span className="text-text-faint shrink-0">{i + 1}.</span>
                        <span>{p.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {extracted.source && (
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-xs text-text-faint">
                      <Globe size={10} /> Source
                    </div>
                    <p className="text-xs text-text-muted">{extracted.source}</p>
                  </div>
                )}
              </>
            ) : (
              <p className="text-xs text-text-faint">No extracted data available</p>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-1">
              {extracted && (
                <button
                  onClick={handleReGenerate}
                  className="flex items-center gap-1.5 rounded-lg bg-accent-dim border border-accent/30 px-3 py-1.5 text-xs font-medium text-accent hover:bg-accent-dim/70 transition-colors"
                >
                  <RefreshCw size={12} />
                  Re-generate
                </button>
              )}
              {detail?.image_url && (
                <a
                  href={detail.image_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-text-muted hover:text-text-secondary hover:bg-hover transition-colors"
                >
                  <ExternalLink size={12} />
                  Open Image
                </a>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}
