import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ExtractedData } from '@/api/queries'

export interface ExtractionConfigApi {
  language: string
  tone: string
  max_points: number
  min_points: number
  title_max_chars: number
  point_max_chars: number
  custom_instructions: string
}

interface GenerateState {
  // Input
  inputMode: 'text' | 'file' | 'url'
  text: string
  url: string

  // Options
  mode: 'card' | 'article' | 'smart'
  theme: string
  colorMood: string | null
  social: boolean
  format: string
  provider: string
  scale: number
  webp: boolean
  brandName: string
  watermarkPosition: string
  watermarkOpacity: number
  thread: boolean

  // Extraction config
  extractionLanguage: string
  extractionTone: string
  extractionMaxPoints: number
  extractionMinPoints: number
  extractionTitleMaxChars: number
  extractionPointMaxChars: number
  extractionCustomInstructions: string

  // Result
  imageUrl: string | null
  title: string | null
  extractedData: ExtractedData | null
  historyId: number | null
  isGenerating: boolean

  // Actions
  setInputMode: (mode: 'text' | 'file' | 'url') => void
  setText: (text: string) => void
  setUrl: (url: string) => void
  setMode: (mode: 'card' | 'article' | 'smart') => void
  setTheme: (theme: string) => void
  setColorMood: (mood: string | null) => void
  setSocial: (social: boolean) => void
  setFormat: (format: string) => void
  setProvider: (provider: string) => void
  setScale: (scale: number) => void
  setWebp: (webp: boolean) => void
  setBrandName: (name: string) => void
  setWatermarkPosition: (pos: string) => void
  setWatermarkOpacity: (opacity: number) => void
  setThread: (thread: boolean) => void
  setExtractionLanguage: (v: string) => void
  setExtractionTone: (v: string) => void
  setExtractionMaxPoints: (v: number) => void
  setExtractionMinPoints: (v: number) => void
  setExtractionTitleMaxChars: (v: number) => void
  setExtractionPointMaxChars: (v: number) => void
  setExtractionCustomInstructions: (v: string) => void
  getExtractionConfig: () => ExtractionConfigApi | null
  setResult: (imageUrl: string, title: string, extractedData: ExtractedData, historyId: number | null) => void
  setExtractedData: (data: ExtractedData) => void
  setGenerating: (v: boolean) => void
  clearResult: () => void
  loadFromHistory: (data: ExtractedData, theme: string, format: string) => void
}

export const useGenerateStore = create<GenerateState>()(
  persist(
    (set, get) => ({
      inputMode: 'text',
      text: '',
      url: '',
      mode: 'card',
      theme: 'dark',
      colorMood: null,
      social: false,
      format: 'story',
      provider: 'cli',
      scale: 2,
      webp: false,
      brandName: '',
      watermarkPosition: 'bottom-right',
      watermarkOpacity: 0.8,
      thread: false,
      extractionLanguage: 'zh-TW',
      extractionTone: 'professional',
      extractionMaxPoints: 5,
      extractionMinPoints: 3,
      extractionTitleMaxChars: 15,
      extractionPointMaxChars: 50,
      extractionCustomInstructions: '',
      imageUrl: null,
      title: null,
      extractedData: null,
      historyId: null,
      isGenerating: false,

      setInputMode: (mode) => set({ inputMode: mode }),
      setText: (text) => set({ text }),
      setUrl: (url) => set({ url }),
      setMode: (mode) => set({ mode }),
      setTheme: (theme) => set({ theme }),
      setColorMood: (colorMood) => set({ colorMood }),
      setSocial: (social) => set({ social }),
      setFormat: (format) => set({ format }),
      setProvider: (provider) => set({ provider }),
      setScale: (scale) => set({ scale }),
      setWebp: (webp) => set({ webp }),
      setBrandName: (name) => set({ brandName: name }),
      setWatermarkPosition: (pos) => set({ watermarkPosition: pos }),
      setWatermarkOpacity: (opacity) => set({ watermarkOpacity: opacity }),
      setThread: (thread) => set({ thread }),
      setExtractionLanguage: (v) => set({ extractionLanguage: v }),
      setExtractionTone: (v) => set({ extractionTone: v }),
      setExtractionMaxPoints: (v) => set((s) => ({
        extractionMaxPoints: v,
        extractionMinPoints: Math.min(s.extractionMinPoints, v),
      })),
      setExtractionMinPoints: (v) => set((s) => ({
        extractionMinPoints: v,
        extractionMaxPoints: Math.max(s.extractionMaxPoints, v),
      })),
      setExtractionTitleMaxChars: (v) => set({ extractionTitleMaxChars: v }),
      setExtractionPointMaxChars: (v) => set({ extractionPointMaxChars: v }),
      setExtractionCustomInstructions: (v) => set({ extractionCustomInstructions: v }),
      getExtractionConfig: () => {
        const s = get()
        const isDefault =
          s.extractionLanguage === 'zh-TW' &&
          s.extractionTone === 'professional' &&
          s.extractionMaxPoints === 5 &&
          s.extractionMinPoints === 3 &&
          s.extractionTitleMaxChars === 15 &&
          s.extractionPointMaxChars === 50 &&
          s.extractionCustomInstructions === ''
        if (isDefault) return null
        return {
          language: s.extractionLanguage,
          tone: s.extractionTone,
          max_points: s.extractionMaxPoints,
          min_points: s.extractionMinPoints,
          title_max_chars: s.extractionTitleMaxChars,
          point_max_chars: s.extractionPointMaxChars,
          custom_instructions: s.extractionCustomInstructions,
        }
      },
      setResult: (imageUrl, title, extractedData, historyId) =>
        set({ imageUrl, title, extractedData, historyId, isGenerating: false }),
      setExtractedData: (data) => set({ extractedData: data }),
      setGenerating: (v) => set({ isGenerating: v }),
      clearResult: () => set({ imageUrl: null, title: null, extractedData: null, historyId: null }),
      loadFromHistory: (data, theme, format) =>
        set({
          extractedData: data,
          title: data.title,
          theme,
          format,
          imageUrl: null,
          historyId: null,
          isGenerating: false,
        }),
    }),
    {
      name: 'imggen-generate',
      partialize: (state) => ({
        mode: state.mode,
        theme: state.theme,
        colorMood: state.colorMood,
        social: state.social,
        format: state.format,
        provider: state.provider,
        scale: state.scale,
        webp: state.webp,
        brandName: state.brandName,
        watermarkPosition: state.watermarkPosition,
        watermarkOpacity: state.watermarkOpacity,
        thread: state.thread,
        extractionLanguage: state.extractionLanguage,
        extractionTone: state.extractionTone,
        extractionMaxPoints: state.extractionMaxPoints,
        extractionMinPoints: state.extractionMinPoints,
        extractionTitleMaxChars: state.extractionTitleMaxChars,
        extractionPointMaxChars: state.extractionPointMaxChars,
        extractionCustomInstructions: state.extractionCustomInstructions,
      }),
    },
  ),
)
