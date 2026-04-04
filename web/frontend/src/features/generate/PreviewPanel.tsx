import { motion, AnimatePresence } from 'framer-motion'
import { Download, Copy, Loader2, ImageIcon, Check, Code } from 'lucide-react'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { useState } from 'react'

export function PreviewPanel() {
  const imageUrl = useGenerateStore((s) => s.imageUrl)
  const title = useGenerateStore((s) => s.title)
  const historyId = useGenerateStore((s) => s.historyId)
  const isGenerating = useGenerateStore((s) => s.isGenerating)
  const [copied, setCopied] = useState(false)

  const handleDownload = () => {
    if (!imageUrl) return
    const a = document.createElement('a')
    a.href = imageUrl
    a.download = `imggen_${Date.now()}.png`
    a.click()
  }

  const handleExportHtml = () => {
    if (!historyId) return
    const a = document.createElement('a')
    a.href = `/api/export/html/${historyId}`
    a.download = `imggen_${historyId}.html`
    a.click()
  }

  const handleCopy = async () => {
    if (!imageUrl) return
    try {
      const res = await fetch(imageUrl)
      const blob = await res.blob()
      await navigator.clipboard.write([
        new ClipboardItem({ [blob.type]: blob }),
      ])
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      window.open(imageUrl, '_blank')
    }
  }

  return (
    <div className="glass-card flex flex-col items-center p-5 space-y-4">
      {/* Image area */}
      <div className="relative w-full aspect-[9/16] max-h-[500px] rounded-lg overflow-hidden bg-bg-surface flex items-center justify-center">
        <AnimatePresence mode="wait">
          {isGenerating ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center gap-3 text-text-faint"
            >
              <Loader2 size={32} className="animate-spin" />
              <span className="text-sm">Generating...</span>
            </motion.div>
          ) : imageUrl ? (
            <motion.img
              key="image"
              src={imageUrl}
              alt={title ?? 'Generated card'}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
              className="h-full w-full object-contain"
            />
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center gap-2 text-text-faint"
            >
              <ImageIcon size={40} />
              <span className="text-sm">Your card will appear here</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Action bar */}
      {imageUrl && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex gap-2 w-full"
        >
          <button
            onClick={handleDownload}
            className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-accent py-2.5 text-sm font-medium text-white hover:bg-accent/90 transition-colors"
          >
            <Download size={16} />
            Download
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center justify-center gap-2 rounded-lg bg-bg-input px-4 py-2.5 text-sm font-medium text-text-secondary hover:text-text hover:bg-hover transition-colors"
          >
            {copied ? <Check size={16} className="text-green-400" /> : <Copy size={16} />}
          </button>
          {historyId && (
            <button
              onClick={handleExportHtml}
              aria-label="Export HTML"
              className="flex items-center justify-center gap-2 rounded-lg bg-bg-input px-4 py-2.5 text-sm font-medium text-text-secondary hover:text-text hover:bg-hover transition-colors"
            >
              <Code size={16} />
            </button>
          )}
        </motion.div>
      )}
    </div>
  )
}
