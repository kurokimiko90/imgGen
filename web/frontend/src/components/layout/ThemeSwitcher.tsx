import { Sun, Moon } from 'lucide-react'
import { useAppStore } from '@/stores/useAppStore'
import { themeIds, getTheme } from '@/themes'
import type { ThemeId } from '@/themes'

interface ThemeSwitcherProps {
  collapsed?: boolean
}

export function ThemeSwitcher({ collapsed }: ThemeSwitcherProps) {
  const theme = useAppStore((s) => s.theme)
  const setTheme = useAppStore((s) => s.setTheme)

  const cycleTheme = () => {
    const idx = themeIds.indexOf(theme)
    const next = themeIds[(idx + 1) % themeIds.length] as ThemeId
    setTheme(next)
  }

  const current = getTheme(theme)
  const isDark = theme === 'dark'

  return (
    <button
      onClick={cycleTheme}
      className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-text-muted hover:text-text-secondary hover:bg-hover transition-colors"
      title={`Theme: ${current.label}`}
    >
      {isDark ? <Moon size={18} /> : <Sun size={18} />}
      {!collapsed && <span>{current.label}</span>}
    </button>
  )
}
