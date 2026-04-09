import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { InputTabs } from '@/features/generate/InputTabs'
import { ThemePillGroup } from '@/features/generate/ThemePillGroup'
import { FormatPillGroup } from '@/features/generate/FormatPillGroup'
import { AdvancedOptions } from '@/features/generate/AdvancedOptions'
import { PreviewPanel } from '@/features/generate/PreviewPanel'
import { ExtractedContentEditor } from '@/features/generate/ExtractedContentEditor'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { useGenerate, useGenerateMulti } from '@/api/queries'
import { Sparkles, Layers, Zap, AlertCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'

type GenerateMode = 'card' | 'article' | 'smart'

const MODES: { id: GenerateMode; label: string; desc: string }[] = [
  { id: 'card', label: 'Card', desc: '靜態模板，28 種主題' },
  { id: 'article', label: 'Article', desc: '段落式排版' },
  { id: 'smart', label: 'Smart', desc: 'AI 動態版面' },
]

const COLOR_MOODS: { id: string; label: string; color: string }[] = [
  { id: 'dark_tech', label: 'Dark Tech', color: '#0f172a' },
  { id: 'warm_earth', label: 'Warm Earth', color: '#78350f' },
  { id: 'clean_light', label: 'Clean Light', color: '#e2e8f0' },
  { id: 'bold_contrast', label: 'Bold', color: '#ea580c' },
  { id: 'soft_pastel', label: 'Pastel', color: '#e879f9' },
]

export function GeneratePage() {
  const store = useGenerateStore()
  const generate = useGenerate()
  const generateMulti = useGenerateMulti()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const handleGenerate = () => {
    const params = {
      text: store.inputMode === 'text' ? store.text : undefined,
      url: store.inputMode === 'url' ? store.url : undefined,
      theme: store.theme,
      format: store.format,
      provider: store.provider,
      mode: store.mode,
      color_mood: store.mode === 'smart' ? store.colorMood : null,
      social: store.mode === 'smart' ? store.social : false,
      scale: store.scale,
      webp: store.webp,
      brand_name: store.brandName || undefined,
      watermark_position: store.watermarkPosition,
      watermark_opacity: store.watermarkOpacity,
      thread: store.thread,
      extraction_config: store.getExtractionConfig(),
    }

    store.setGenerating(true)
    store.clearResult()
    setErrorMsg(null)

    generate.mutate(params, {
      onSuccess: (data) => {
        store.setResult(data.image_url, data.title, data.extracted_data, data.history_id)
      },
      onError: (err: unknown) => {
        store.setGenerating(false)
        const msg = err instanceof Error ? err.message : '生成失敗，請檢查設定後重試'
        setErrorMsg(msg)
      },
    })
  }

  const handleGenerateAll = () => {
    const params = {
      text: store.inputMode === 'text' ? store.text : undefined,
      url: store.inputMode === 'url' ? store.url : undefined,
      theme: store.theme,
      format: store.format,
      formats: ['story', 'square', 'landscape', 'twitter'],
      provider: store.provider,
      mode: store.mode,
      color_mood: store.mode === 'smart' ? store.colorMood : null,
      social: store.mode === 'smart' ? store.social : false,
      scale: store.scale,
      webp: store.webp,
      brand_name: store.brandName || undefined,
      watermark_position: store.watermarkPosition,
      watermark_opacity: store.watermarkOpacity,
      extraction_config: store.getExtractionConfig(),
    }

    store.setGenerating(true)
    store.clearResult()
    setErrorMsg(null)

    generateMulti.mutate(params, {
      onSuccess: (data) => {
        const first = data.images[0]
        if (first) {
          store.setResult(first.url, data.title, data.extracted_data, first.history_id ?? null)
        } else {
          store.setGenerating(false)
        }
      },
      onError: (err: unknown) => {
        store.setGenerating(false)
        const msg = err instanceof Error ? err.message : '生成失敗，請檢查設定後重試'
        setErrorMsg(msg)
      },
    })
  }

  const hasInput =
    store.inputMode === 'text'
      ? store.text.trim().length > 0
      : store.url.trim().length > 0

  const hasResult = store.imageUrl !== null || store.extractedData !== null

  return (
    <PageTransition className="p-6 space-y-6">
      {/* Input Section */}
      <div className="space-y-5">
        <GlassCard>
          <InputTabs />
        </GlassCard>

        <GlassCard className="space-y-4">
          {/* Mode switcher */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Mode
            </label>
            <div className="flex gap-2">
              {MODES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => store.setMode(m.id)}
                  title={m.desc}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    store.mode === m.id
                      ? 'bg-accent text-white shadow-sm'
                      : 'bg-bg-input text-text-muted hover:text-text-secondary'
                  }`}
                >
                  {m.id === 'smart' && <Zap size={13} />}
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          {/* Theme (card/article) or Color Mood (smart) */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
              {store.mode === 'smart' ? 'Color Mood' : 'Theme'}
            </label>
            {store.mode === 'smart' ? (
              <div className="flex flex-wrap gap-2">
                {COLOR_MOODS.map((cm) => (
                  <button
                    key={cm.id}
                    onClick={() => store.setColorMood(store.colorMood === cm.id ? null : cm.id)}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-all ${
                      store.colorMood === cm.id
                        ? 'ring-2 ring-accent bg-bg-card text-text'
                        : 'bg-bg-input text-text-muted hover:text-text-secondary'
                    }`}
                  >
                    <span
                      className="inline-block h-3 w-3 rounded-full border border-white/20 shrink-0"
                      style={{ background: cm.color }}
                    />
                    {cm.label}
                  </button>
                ))}
              </div>
            ) : (
              <ThemePillGroup />
            )}
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Format
            </label>
            <FormatPillGroup />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider">
              Provider
            </label>
            <select
              value={store.provider}
              onChange={(e) => store.setProvider(e.target.value)}
              className="rounded-lg border border-border bg-bg-input px-3 py-2 text-sm text-text outline-none focus:border-accent/50"
            >
              <option value="cli">Claude CLI</option>
              <option value="claude">Claude API</option>
              <option value="gemini">Gemini</option>
              <option value="gpt">GPT</option>
            </select>
          </div>

          {/* Social Mode toggle — Smart only */}
          {store.mode === 'smart' && (
            <label className="flex cursor-pointer items-center gap-3">
              <div
                onClick={() => store.setSocial(!store.social)}
                className={`relative h-5 w-9 rounded-full transition-colors ${
                  store.social ? 'bg-accent' : 'bg-bg-input border border-border'
                }`}
              >
                <span
                  className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform ${
                    store.social ? 'translate-x-4' : 'translate-x-0.5'
                  }`}
                />
              </div>
              <span className="text-sm text-text-secondary">
                Social Mode
                <span className="ml-1.5 text-xs text-text-faint">（加入 hook 關鍵字，3 秒可掃）</span>
              </span>
            </label>
          )}
        </GlassCard>

        <AdvancedOptions />

        <div className="flex gap-3">
          <button
            onClick={handleGenerate}
            disabled={!hasInput || store.isGenerating}
            className="flex items-center gap-2 rounded-lg bg-accent px-6 py-3 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <Sparkles size={16} />
            Generate Card
          </button>
          <button
            onClick={handleGenerateAll}
            disabled={!hasInput || store.isGenerating}
            className="flex items-center gap-2 rounded-lg border border-border bg-bg-card px-5 py-3 text-sm font-medium text-text-secondary hover:text-text hover:bg-hover disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            <Layers size={16} />
            All Formats
          </button>
        </div>

        {/* Error banner */}
        <AnimatePresence>
          {errorMsg && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="flex items-start gap-3 rounded-lg border border-red-600/30 bg-red-600/10 px-4 py-3 text-sm text-red-600"
            >
              <AlertCircle size={16} className="mt-0.5 shrink-0" />
              <span>{errorMsg}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Result Section */}
      <AnimatePresence>
        {hasResult && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 24 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] }}
          >
            <div className="grid grid-cols-1 lg:grid-cols-[1fr_380px] gap-6">
              <ExtractedContentEditor />
              <PreviewPanel />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!hasResult && store.isGenerating && (
        <div className="max-w-[380px]">
          <PreviewPanel />
        </div>
      )}
    </PageTransition>
  )
}
