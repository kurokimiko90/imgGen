import { useEffect } from 'react'
import { useAppStore } from '@/stores/useAppStore'
import { getTheme } from '@/themes'
import type { ThemeColors } from '@/themes'

const CSS_VAR_MAP: Record<keyof ThemeColors, string> = {
  bg: '--color-bg',
  bgSurface: '--color-bg-surface',
  bgCard: '--color-bg-card',
  bgInput: '--color-bg-input',
  accent: '--color-accent',
  accentDim: '--color-accent-dim',
  accentGlow: '--color-accent-glow',
  text: '--color-text',
  textSecondary: '--color-text-secondary',
  textMuted: '--color-text-muted',
  textFaint: '--color-text-faint',
  border: '--color-border',
  borderSubtle: '--color-border-subtle',
  hover: '--color-hover',
  scrollbar: '--color-scrollbar',
  scrollbarHover: '--color-scrollbar-hover',
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const themeId = useAppStore((s) => s.theme)

  useEffect(() => {
    const theme = getTheme(themeId)
    const root = document.documentElement

    root.setAttribute('data-theme', theme.id)

    for (const [key, cssVar] of Object.entries(CSS_VAR_MAP)) {
      root.style.setProperty(cssVar, theme.colors[key as keyof ThemeColors])
    }

    const meta = document.querySelector('meta[name="theme-color"]')
    if (meta) {
      meta.setAttribute('content', theme.colors.bg)
    }
  }, [themeId])

  return <>{children}</>
}
