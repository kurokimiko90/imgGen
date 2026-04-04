import { darkTheme, swissTheme } from './tokens'
import type { ThemeDefinition } from './tokens'

export type { ThemeDefinition, ThemeColors } from './tokens'

export const THEMES: Record<string, ThemeDefinition> = {
  dark: darkTheme,
  swiss: swissTheme,
}

export type ThemeId = keyof typeof THEMES

export const themeIds = Object.keys(THEMES) as ThemeId[]

export function getTheme(id: string): ThemeDefinition {
  return THEMES[id] ?? darkTheme
}
