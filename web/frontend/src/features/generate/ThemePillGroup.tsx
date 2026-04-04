import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import { useGenerateStore } from '@/stores/useGenerateStore'

const THEMES = [
  { id: 'dark', label: 'Dark', color: '#1a1a2e' },
  { id: 'light', label: 'Light', color: '#f0f0f5' },
  { id: 'gradient', label: 'Gradient', color: 'linear-gradient(135deg, #667eea, #764ba2)' },
  { id: 'warm_sun', label: 'Warm Sun', color: '#f59e0b' },
  { id: 'cozy', label: 'Cozy', color: '#78716c' },
] as const

export function ThemePillGroup() {
  const theme = useGenerateStore((s) => s.theme)
  const setTheme = useGenerateStore((s) => s.setTheme)

  return (
    <div className="flex flex-wrap gap-2">
      {THEMES.map((t) => (
        <button
          key={t.id}
          onClick={() => setTheme(t.id)}
          className={cn(
            'relative flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-colors',
            theme === t.id
              ? 'text-text'
              : 'text-text-muted hover:text-text-secondary',
          )}
        >
          {theme === t.id && (
            <motion.div
              layoutId="theme-pill"
              className="absolute inset-0 rounded-full bg-accent-dim border border-accent/30"
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
            />
          )}
          <span
            className="relative z-10 h-4 w-4 rounded-full border border-border shrink-0"
            style={{
              background: t.color,
            }}
          />
          <span className="relative z-10">{t.label}</span>
        </button>
      ))}
    </div>
  )
}
