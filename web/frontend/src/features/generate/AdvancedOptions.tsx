import { useGenerateStore } from '@/stores/useGenerateStore'
import { ExtractionSettings } from './ExtractionSettings'
import { ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

export function AdvancedOptions() {
  const [open, setOpen] = useState(false)
  const store = useGenerateStore()

  return (
    <div className="rounded-lg border border-border-subtle">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-text-secondary hover:text-text transition-colors"
      >
        <span>Advanced Options</span>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} />
        </motion.div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="grid grid-cols-2 gap-4 px-4 pb-4">
              {/* Scale */}
              <label className="space-y-1">
                <span className="text-xs text-text-muted">Scale</span>
                <div className="flex gap-2">
                  {[1, 2].map((s) => (
                    <button
                      key={s}
                      onClick={() => store.setScale(s)}
                      className={`rounded-md px-3 py-1.5 text-sm ${
                        store.scale === s
                          ? 'bg-accent text-white'
                          : 'bg-bg-input text-text-muted hover:text-text-secondary'
                      }`}
                    >
                      {s}x
                    </button>
                  ))}
                </div>
              </label>

              {/* WebP */}
              <label className="space-y-1">
                <span className="text-xs text-text-muted">Format</span>
                <div className="flex gap-2">
                  {[
                    { v: false, label: 'PNG' },
                    { v: true, label: 'WebP' },
                  ].map((opt) => (
                    <button
                      key={String(opt.v)}
                      onClick={() => store.setWebp(opt.v)}
                      className={`rounded-md px-3 py-1.5 text-sm ${
                        store.webp === opt.v
                          ? 'bg-accent text-white'
                          : 'bg-bg-input text-text-muted hover:text-text-secondary'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </label>

              {/* Brand name */}
              <label className="col-span-2 space-y-1">
                <span className="text-xs text-text-muted">Brand Name</span>
                <input
                  type="text"
                  value={store.brandName}
                  onChange={(e) => store.setBrandName(e.target.value)}
                  placeholder="@yourname"
                  className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50"
                />
              </label>

              {/* Watermark position */}
              <label className="space-y-1">
                <span className="text-xs text-text-muted">Watermark Position</span>
                <select
                  value={store.watermarkPosition}
                  onChange={(e) => store.setWatermarkPosition(e.target.value)}
                  className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none"
                >
                  <option value="top-left">Top Left</option>
                  <option value="top-right">Top Right</option>
                  <option value="bottom-left">Bottom Left</option>
                  <option value="bottom-right">Bottom Right</option>
                </select>
              </label>

              {/* Watermark opacity */}
              <label className="space-y-1">
                <span className="text-xs text-text-muted">
                  Watermark Opacity: {store.watermarkOpacity.toFixed(1)}
                </span>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.1}
                  value={store.watermarkOpacity}
                  onChange={(e) => store.setWatermarkOpacity(Number(e.target.value))}
                  className="w-full accent-accent"
                />
              </label>

              {/* Thread mode */}
              <label className="col-span-2 flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={store.thread}
                  onChange={(e) => store.setThread(e.target.checked)}
                  className="accent-accent"
                />
                <span className="text-sm text-text-secondary">Thread mode (split into multiple cards)</span>
              </label>

              {/* Extraction settings */}
              <div className="col-span-2">
                <ExtractionSettings />
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
