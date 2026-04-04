import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useGenerateStore } from '@/stores/useGenerateStore'

const FORMATS = [
  { id: 'story', label: 'Story', ratio: '9:16' },
  { id: 'square', label: 'Square', ratio: '1:1' },
  { id: 'landscape', label: 'Landscape', ratio: '16:9' },
  { id: 'twitter', label: 'Twitter', ratio: '16:9' },
] as const

export function FormatPillGroup() {
  const format = useGenerateStore((s) => s.format)
  const setFormat = useGenerateStore((s) => s.setFormat)

  return (
    <div className="flex flex-wrap gap-2">
      {FORMATS.map((f) => (
        <button
          key={f.id}
          onClick={() => setFormat(f.id)}
          className={cn(
            'relative flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
            format === f.id
              ? 'text-text'
              : 'text-text-muted hover:text-text-secondary',
          )}
        >
          {format === f.id && (
            <motion.div
              layoutId="format-pill"
              className="absolute inset-0 rounded-full bg-accent-dim border border-accent/30"
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            />
          )}
          <span className="relative z-10 text-xs text-text-muted">{f.ratio}</span>
          <span className="relative z-10">{f.label}</span>
        </button>
      ))}
    </div>
  )
}
