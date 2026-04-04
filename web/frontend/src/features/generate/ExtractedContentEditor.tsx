import { useState } from 'react'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { useReRender } from '@/api/queries'
import type { ExtractedData } from '@/api/queries'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RefreshCw, Plus, X, Type, List, Globe, Loader2, ChevronDown, ChevronUp,
} from 'lucide-react'

function PointRow({
  text,
  index,
  onChange,
  onRemove,
}: {
  text: string
  index: number
  onChange: (index: number, value: string) => void
  onRemove: (index: number) => void
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 12, height: 0 }}
      className="flex items-center gap-2 group"
    >
      <span className="text-xs text-text-faint w-5 text-right shrink-0">{index + 1}.</span>
      <input
        type="text"
        value={text}
        onChange={(e) => onChange(index, e.target.value)}
        className="flex-1 rounded-lg border border-border bg-bg-input px-3 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 transition-colors"
      />
      <button
        onClick={() => onRemove(index)}
        className="shrink-0 rounded-md p-1.5 text-text-faint hover:text-red-400 hover:bg-hover opacity-0 group-hover:opacity-100 transition-all"
        title="Remove point"
      >
        <X size={14} />
      </button>
    </motion.div>
  )
}

export function ExtractedContentEditor() {
  const store = useGenerateStore()
  const reRender = useReRender()
  const [collapsed, setCollapsed] = useState(false)

  const data = store.extractedData
  if (!data) return null

  const updateField = <K extends keyof ExtractedData>(key: K, value: ExtractedData[K]) => {
    store.setExtractedData({ ...data, [key]: value })
  }

  const updatePoint = (index: number, text: string) => {
    const updated = data.key_points.map((p, i) =>
      i === index ? { text } : p,
    )
    updateField('key_points', updated)
  }

  const removePoint = (index: number) => {
    updateField('key_points', data.key_points.filter((_, i) => i !== index))
  }

  const addPoint = () => {
    updateField('key_points', [...data.key_points, { text: '' }])
  }

  const handleReRender = () => {
    store.setGenerating(true)
    reRender.mutate(
      {
        history_id: store.historyId,
        extracted_data: data,
        theme: store.theme,
        format: store.format,
        scale: store.scale,
        webp: store.webp,
        brand_name: store.brandName || undefined,
        watermark_position: store.watermarkPosition,
        watermark_opacity: store.watermarkOpacity,
      },
      {
        onSuccess: (result) => {
          store.setResult(result.image_url, result.title, result.extracted_data, result.history_id)
        },
        onError: () => {
          store.setGenerating(false)
        },
      },
    )
  }

  const isDirty = true // always allow re-render with current data

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card space-y-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-text-secondary flex items-center gap-2">
          <List size={14} />
          Extracted Content
        </h3>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="rounded-md p-1 text-text-faint hover:text-text-secondary transition-colors"
        >
          {collapsed ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </button>
      </div>

      <AnimatePresence initial={false}>
        {!collapsed && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden space-y-4"
          >
            {/* Title */}
            <div className="space-y-1.5">
              <label className="flex items-center gap-1.5 text-xs text-text-muted">
                <Type size={11} /> Title
              </label>
              <input
                type="text"
                value={data.title}
                onChange={(e) => updateField('title', e.target.value)}
                className="w-full rounded-lg border border-border bg-bg-input px-3 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 transition-colors"
              />
            </div>

            {/* Key Points */}
            <div className="space-y-2">
              <label className="flex items-center gap-1.5 text-xs text-text-muted">
                <List size={11} /> Key Points ({data.key_points.length})
              </label>
              <div className="space-y-2">
                <AnimatePresence initial={false}>
                  {data.key_points.map((point, i) => (
                    <PointRow
                      key={i}
                      text={point.text}
                      index={i}
                      onChange={updatePoint}
                      onRemove={removePoint}
                    />
                  ))}
                </AnimatePresence>
              </div>
              <button
                onClick={addPoint}
                className="flex items-center gap-1.5 rounded-lg border border-dashed border-border px-3 py-2 text-xs text-text-faint hover:text-text-secondary hover:border-text-faint transition-colors w-full justify-center"
              >
                <Plus size={12} /> Add point
              </button>
            </div>

            {/* Source */}
            <div className="space-y-1.5">
              <label className="flex items-center gap-1.5 text-xs text-text-muted">
                <Globe size={11} /> Source
              </label>
              <input
                type="text"
                value={data.source}
                onChange={(e) => updateField('source', e.target.value)}
                placeholder="e.g. techcrunch.com"
                className="w-full rounded-lg border border-border bg-bg-input px-3 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 transition-colors"
              />
            </div>

            {/* Re-generate button */}
            <button
              onClick={handleReRender}
              disabled={!isDirty || store.isGenerating}
              className="flex items-center justify-center gap-2 w-full rounded-lg bg-accent-dim border border-accent/30 px-4 py-2.5 text-sm font-medium text-accent hover:bg-accent-dim/70 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {store.isGenerating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              Re-generate Card
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
