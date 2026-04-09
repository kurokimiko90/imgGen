import { useState } from 'react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useCaption } from '@/api/queries'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { motion, AnimatePresence } from 'framer-motion'
import { MessageSquare, AtSign, Briefcase, Camera, Copy, Check, Loader2, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

const PLATFORMS = [
  { id: 'twitter', label: 'Twitter', icon: AtSign, color: '#1DA1F2' },
  { id: 'linkedin', label: 'LinkedIn', icon: Briefcase, color: '#0A66C2' },
  { id: 'instagram', label: 'Instagram', icon: Camera, color: '#E4405F' },
] as const

export function CaptionsPage() {
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['twitter', 'linkedin', 'instagram'])
  const [provider, setProvider] = useState('cli')
  const [articleText, setArticleText] = useState('')
  const [captions, setCaptions] = useState<Record<string, string>>({})
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const captionMutation = useCaption()

  const title = useGenerateStore((s) => s.title)

  const togglePlatform = (id: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    )
  }

  const handleGenerate = () => {
    if (!articleText.trim() || selectedPlatforms.length === 0) return

    captionMutation.mutate(
      {
        platforms: selectedPlatforms,
        provider,
        data: {
          title: title ?? 'Article',
          key_points: [{ text: articleText.slice(0, 200) }],
          source: '',
        },
      },
      {
        onSuccess: (data) => {
          setCaptions(data.captions)
        },
      },
    )
  }

  const handleCopy = async (platform: string, text: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedKey(platform)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  return (
    <PageTransition className="p-6 max-w-4xl space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <MessageSquare size={24} className="text-accent" />
        <h1 className="text-xl font-semibold">Captions</h1>
      </div>

      {/* Input */}
      <GlassCard className="space-y-4">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Article Text</label>
        <textarea
          value={articleText}
          onChange={(e) => setArticleText(e.target.value)}
          placeholder="Paste your article text to generate captions..."
          rows={5}
          className="w-full rounded-lg border border-border bg-bg-input px-4 py-3 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 resize-none"
        />
      </GlassCard>

      {/* Platform selector */}
      <GlassCard className="space-y-4">
        <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Platforms</label>
        <div className="flex flex-wrap gap-3">
          {PLATFORMS.map((p) => {
            const selected = selectedPlatforms.includes(p.id)
            return (
              <button
                key={p.id}
                onClick={() => togglePlatform(p.id)}
                className={cn(
                  'flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-all border',
                  selected
                    ? 'border-border bg-hover text-text'
                    : 'border-border-subtle text-text-muted hover:text-text-secondary hover:border-border',
                )}
              >
                <p.icon size={16} style={{ color: selected ? p.color : undefined }} />
                {p.label}
              </button>
            )
          })}
        </div>

        <div className="flex items-center gap-4">
          <div className="space-y-1">
            <label className="text-xs text-text-muted">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="rounded-lg border border-border bg-bg-input px-3 py-2 text-sm text-text outline-none"
            >
              <option value="cli">Claude CLI</option>
              <option value="claude">Claude API</option>
              <option value="gemini">Gemini</option>
              <option value="gpt">GPT</option>
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={!articleText.trim() || selectedPlatforms.length === 0 || captionMutation.isPending}
            className="mt-5 flex items-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-semibold text-white hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {captionMutation.isPending ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <MessageSquare size={16} />
            )}
            Generate Captions
          </button>
        </div>
      </GlassCard>

      {/* Error */}
      {captionMutation.isError && (
        <div className="flex items-center gap-2 rounded-lg border border-red-600/20 bg-red-600/10 px-4 py-3 text-sm text-red-600">
          <AlertCircle size={16} />
          {captionMutation.error.message}
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {Object.keys(captions).length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
          >
            {PLATFORMS.filter((p) => captions[p.id]).map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <GlassCard className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <p.icon size={18} style={{ color: p.color }} />
                      <span className="text-sm font-medium">{p.label}</span>
                    </div>
                    <button
                      onClick={() => handleCopy(p.id, captions[p.id])}
                      className="flex items-center gap-1 rounded-md px-2 py-1 text-xs text-text-muted hover:text-text-secondary hover:bg-hover transition-colors"
                    >
                      {copiedKey === p.id ? (
                        <>
                          <Check size={12} className="text-accent" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy size={12} />
                          Copy
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-sm text-text-secondary whitespace-pre-wrap leading-relaxed">
                    {captions[p.id]}
                  </p>
                  <div className="text-xs text-text-faint">
                    {captions[p.id].length} characters
                  </div>
                </GlassCard>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  )
}
