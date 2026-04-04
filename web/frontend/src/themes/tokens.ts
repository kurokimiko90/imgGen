export interface ThemeColors {
  bg: string
  bgSurface: string
  bgCard: string
  bgInput: string
  accent: string
  accentDim: string
  accentGlow: string
  text: string
  textSecondary: string
  textMuted: string
  textFaint: string
  border: string
  borderSubtle: string
  hover: string
  scrollbar: string
  scrollbarHover: string
}

export interface ThemeDefinition {
  id: string
  label: string
  colors: ThemeColors
}

export const darkTheme: ThemeDefinition = {
  id: 'dark',
  label: 'Midnight',
  colors: {
    bg: '#090d1a',
    bgSurface: 'rgba(255, 255, 255, 0.04)',
    bgCard: 'rgba(255, 255, 255, 0.06)',
    bgInput: 'rgba(255, 255, 255, 0.08)',
    accent: '#2563eb',
    accentDim: 'rgba(37, 99, 235, 0.18)',
    accentGlow: 'rgba(37, 99, 235, 0.08)',
    text: '#ffffff',
    textSecondary: 'rgba(255, 255, 255, 0.60)',
    textMuted: 'rgba(255, 255, 255, 0.40)',
    textFaint: 'rgba(255, 255, 255, 0.20)',
    border: 'rgba(255, 255, 255, 0.10)',
    borderSubtle: 'rgba(255, 255, 255, 0.05)',
    hover: 'rgba(255, 255, 255, 0.05)',
    scrollbar: 'rgba(255, 255, 255, 0.10)',
    scrollbarHover: 'rgba(255, 255, 255, 0.20)',
  },
}

export const swissTheme: ThemeDefinition = {
  id: 'swiss',
  label: 'Swiss Light',
  colors: {
    bg: '#FAFAF9',
    bgSurface: 'rgba(15, 23, 42, 0.03)',
    bgCard: '#FFFFFF',
    bgInput: 'rgba(15, 23, 42, 0.05)',
    accent: '#2B7CB8',
    accentDim: 'rgba(43, 124, 184, 0.10)',
    accentGlow: 'rgba(43, 124, 184, 0.06)',
    text: '#0F172A',
    textSecondary: '#475569',
    textMuted: '#94A3B8',
    textFaint: '#CBD5E1',
    border: '#E2E8F0',
    borderSubtle: '#F1F5F9',
    hover: 'rgba(15, 23, 42, 0.04)',
    scrollbar: 'rgba(15, 23, 42, 0.12)',
    scrollbarHover: 'rgba(15, 23, 42, 0.22)',
  },
}
