import { useState } from 'react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { usePresets, useSavePreset, useDeletePreset } from '@/api/queries'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bookmark, Plus, Trash2, Download, Save,
  Loader2, AlertCircle, X, Palette, LayoutGrid, Cpu,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export function PresetsPage() {
  const { data, isLoading } = usePresets()
  const savePreset = useSavePreset()
  const deletePreset = useDeletePreset()
  const store = useGenerateStore()

  const [showForm, setShowForm] = useState(false)
  const [presetName, setPresetName] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  const presets = data?.presets ?? {}

  const handleSave = () => {
    if (!presetName.trim()) return
    savePreset.mutate(
      {
        name: presetName.trim(),
        values: {
          theme: store.theme,
          format: store.format,
          provider: store.provider,
          scale: store.scale,
          webp: store.webp,
          brand_name: store.brandName || undefined,
          watermark_position: store.watermarkPosition,
          watermark_opacity: store.watermarkOpacity,
        },
      },
      {
        onSuccess: () => {
          setPresetName('')
          setShowForm(false)
        },
      },
    )
  }

  const handleLoad = (values: Record<string, unknown>) => {
    if (typeof values.theme === 'string') store.setTheme(values.theme)
    if (typeof values.format === 'string') store.setFormat(values.format)
    if (typeof values.provider === 'string') store.setProvider(values.provider)
    if (typeof values.scale === 'number') store.setScale(values.scale)
    if (typeof values.webp === 'boolean') store.setWebp(values.webp)
    if (typeof values.brand_name === 'string') store.setBrandName(values.brand_name)
    if (typeof values.watermark_position === 'string') store.setWatermarkPosition(values.watermark_position)
    if (typeof values.watermark_opacity === 'number') store.setWatermarkOpacity(values.watermark_opacity)
  }

  const handleDelete = (name: string) => {
    deletePreset.mutate(name, {
      onSuccess: () => setDeleteConfirm(null),
    })
  }

  return (
    <PageTransition className="p-6 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Bookmark size={24} className="text-accent" />
          <h1 className="text-xl font-semibold">Presets</h1>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
        >
          {showForm ? <X size={16} /> : <Plus size={16} />}
          {showForm ? 'Cancel' : 'Save Current'}
        </button>
      </div>

      {/* Save form */}
      <AnimatePresence>
        {showForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <GlassCard className="space-y-3">
              <p className="text-sm text-text-muted">
                Save your current generate settings as a preset
              </p>
              <div className="flex gap-3">
                <input
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSave()}
                  placeholder="Preset name..."
                  className="flex-1 rounded-lg border border-border bg-bg-input px-4 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50"
                  autoFocus
                />
                <button
                  onClick={handleSave}
                  disabled={!presetName.trim() || savePreset.isPending}
                  className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-accent/90 disabled:opacity-40 transition-colors"
                >
                  {savePreset.isPending ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  Save
                </button>
              </div>
              {/* Current values preview */}
              <div className="flex flex-wrap gap-2 text-xs text-text-faint">
                <span className="rounded bg-hover px-2 py-0.5">theme: {store.theme}</span>
                <span className="rounded bg-hover px-2 py-0.5">format: {store.format}</span>
                <span className="rounded bg-hover px-2 py-0.5">provider: {store.provider}</span>
                <span className="rounded bg-hover px-2 py-0.5">scale: {store.scale}x</span>
                {store.brandName && <span className="rounded bg-hover px-2 py-0.5">brand: {store.brandName}</span>}
              </div>
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error */}
      {savePreset.isError && (
        <div className="flex items-center gap-2 text-sm text-red-600">
          <AlertCircle size={14} /> {savePreset.error.message}
        </div>
      )}

      {/* Presets grid */}
      {isLoading ? (
        <div className="text-center py-12 text-text-faint">
          <Loader2 size={24} className="mx-auto animate-spin" />
        </div>
      ) : Object.keys(presets).length === 0 ? (
        <GlassCard className="flex flex-col items-center justify-center py-16 text-center">
          <Bookmark size={40} className="text-text-faint mb-3" />
          <p className="text-sm text-text-muted">No presets saved yet</p>
          <p className="text-xs text-text-faint mt-1">
            Configure your generate options and click "Save Current" to create one
          </p>
        </GlassCard>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(presets).map(([name, values], i) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
            >
              <GlassCard className="space-y-3 group transition-shadow">
                <div className="flex items-center justify-between">
                  <h3 className="font-medium text-text">{name}</h3>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => handleLoad(values)}
                      className="rounded-md p-1.5 text-text-muted hover:text-accent hover:bg-hover transition-colors"
                      title="Load preset"
                    >
                      <Download size={14} />
                    </button>
                    {deleteConfirm === name ? (
                      <button
                        onClick={() => handleDelete(name)}
                        className="rounded-md px-2 py-1 text-xs bg-red-600 text-white hover:bg-red-700 transition-colors"
                      >
                        Confirm
                      </button>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirm(name)}
                        className="rounded-md p-1.5 text-text-muted hover:text-red-600 hover:bg-hover transition-colors"
                        title="Delete preset"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>

                {/* Values */}
                <div className="flex flex-wrap gap-2">
                  {typeof values.theme === 'string' && (
                    <span className={cn('flex items-center gap-1 rounded-full bg-hover px-2.5 py-1 text-xs text-text-muted')}>
                      <Palette size={10} /> {values.theme}
                    </span>
                  )}
                  {typeof values.format === 'string' && (
                    <span className="flex items-center gap-1 rounded-full bg-hover px-2.5 py-1 text-xs text-text-muted">
                      <LayoutGrid size={10} /> {values.format}
                    </span>
                  )}
                  {typeof values.provider === 'string' && (
                    <span className="flex items-center gap-1 rounded-full bg-hover px-2.5 py-1 text-xs text-text-muted">
                      <Cpu size={10} /> {values.provider}
                    </span>
                  )}
                  {typeof values.scale === 'number' && (
                    <span className="rounded-full bg-hover px-2.5 py-1 text-xs text-text-muted">
                      {values.scale}x
                    </span>
                  )}
                  {typeof values.brand_name === 'string' && values.brand_name && (
                    <span className="rounded-full bg-hover px-2.5 py-1 text-xs text-text-muted">
                      {values.brand_name}
                    </span>
                  )}
                </div>

                {/* Load button (always visible on mobile) */}
                <button
                  onClick={() => handleLoad(values)}
                  className="w-full rounded-lg border border-border-subtle py-2 text-sm text-text-muted hover:text-text hover:bg-hover transition-colors md:hidden"
                >
                  Load Preset
                </button>
              </GlassCard>
            </motion.div>
          ))}
        </div>
      )}
    </PageTransition>
  )
}
