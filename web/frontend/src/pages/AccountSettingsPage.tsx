import { useState, useEffect } from 'react'
import { Settings, Save, Eye, ChevronDown, ChevronUp } from 'lucide-react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useSettingsStore } from '@/stores/useSettingsStore'
import {
  useAccounts,
  useAccountPrompt,
  useUpdateAccount,
  useAccountPreview,
  type AccountInfo,
} from '@/api/queries'

const PLATFORM_OPTIONS = ['x', 'threads', 'instagram', 'linkedin']
const COLOR_MOOD_OPTIONS = ['dark_tech', 'warm_earth', 'clean_light', 'bold_contrast', 'soft_pastel']

function AccountPanel({ id, info }: { id: string; info: AccountInfo }) {
  const { expandedAccountId, dirtyAccounts, previewUrls, setExpanded, markDirty, markClean, setPreviewUrl } =
    useSettingsStore()

  const isExpanded = expandedAccountId === id
  const isDirty = dirtyAccounts.has(id)

  const [name, setName] = useState(info.name)
  const [platforms, setPlatforms] = useState<string[]>(info.platforms)
  const [publishTime, setPublishTime] = useState(info.publish_time)
  const [colorMood, setColorMood] = useState(info.color_mood)
  const [tone, setTone] = useState(info.tone)
  const [promptContent, setPromptContent] = useState<string | null>(null)

  const promptQuery = useAccountPrompt(isExpanded ? id : null)
  const updateAccount = useUpdateAccount()
  const accountPreview = useAccountPreview()

  useEffect(() => {
    if (promptQuery.data) {
      setPromptContent(promptQuery.data.prompt)
    }
  }, [promptQuery.data])

  function handleChange() {
    markDirty(id)
  }

  async function handleSave() {
    await updateAccount.mutateAsync({
      id,
      name,
      platforms,
      publish_time: publishTime,
      color_mood: colorMood,
      tone,
      prompt_content: promptContent ?? undefined,
    })
    markClean(id)
  }

  async function handlePreview() {
    const result = await accountPreview.mutateAsync({ id, color_mood: colorMood })
    setPreviewUrl(id, result.preview_url)
  }

  const togglePlatform = (platform: string) => {
    const next = platforms.includes(platform)
      ? platforms.filter((p) => p !== platform)
      : [...platforms, platform]
    setPlatforms(next)
    handleChange()
  }

  const ACCOUNT_COLORS: Record<string, string> = {
    A: 'text-accent border-accent/20',
    B: 'text-accent border-accent/20',
    C: 'text-accent border-accent/20',
  }

  return (
    <div className={`rounded-xl border ${ACCOUNT_COLORS[id] ?? 'border-border-subtle'} overflow-hidden`}>
      {/* Header */}
      <button
        onClick={() => setExpanded(isExpanded ? null : id)}
        className="w-full flex items-center justify-between p-4 hover:bg-hover/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`text-lg font-bold ${ACCOUNT_COLORS[id]?.split(' ')[0] ?? ''}`}>
            {id}
          </span>
          <span className="text-sm font-medium text-text-primary">{name}</span>
          <span className="text-xs text-text-muted">
            {platforms.join(', ') || 'no platforms'}
          </span>
          {isDirty && (
            <span className="text-xs bg-accent/15 text-accent px-1.5 py-0.5 rounded">
              Unsaved
            </span>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp size={16} className="text-text-muted" />
        ) : (
          <ChevronDown size={16} className="text-text-muted" />
        )}
      </button>

      {/* Expanded content */}
      {isExpanded && (
        <div className="border-t border-border-subtle/50 p-4 space-y-4">
          {/* Name */}
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted uppercase tracking-wider">Display Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); handleChange() }}
              className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
            />
          </div>

          {/* Platforms */}
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted uppercase tracking-wider">Platforms</label>
            <div className="flex gap-2 flex-wrap">
              {PLATFORM_OPTIONS.map((p) => (
                <button
                  key={p}
                  onClick={() => togglePlatform(p)}
                  className={`px-3 py-1.5 text-xs rounded-lg border transition-colors ${
                    platforms.includes(p)
                      ? 'bg-accent/20 text-accent border-accent/30'
                      : 'border-border-subtle text-text-muted hover:text-text-primary hover:bg-hover'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          {/* Publish time + color mood */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <label className="text-xs text-text-muted uppercase tracking-wider">Publish Time</label>
              <input
                type="time"
                value={publishTime}
                onChange={(e) => { setPublishTime(e.target.value); handleChange() }}
                className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs text-text-muted uppercase tracking-wider">Color Mood</label>
              <div className="flex gap-1.5">
                <select
                  value={colorMood}
                  onChange={(e) => { setColorMood(e.target.value); handleChange() }}
                  className="flex-1 bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
                >
                  {COLOR_MOOD_OPTIONS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                <button
                  onClick={handlePreview}
                  disabled={accountPreview.isPending}
                  className="p-2 border border-border-subtle text-text-muted hover:text-text-primary hover:bg-hover rounded-lg transition-colors disabled:opacity-50"
                  title="Preview"
                >
                  <Eye size={16} />
                </button>
              </div>

              {/* Preview image */}
              {previewUrls[id] && (
                <img
                  src={previewUrls[id]}
                  alt="Preview"
                  className="w-full h-20 object-cover rounded-lg mt-2"
                />
              )}
            </div>
          </div>

          {/* Tone */}
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted uppercase tracking-wider">Tone</label>
            <input
              type="text"
              value={tone}
              onChange={(e) => { setTone(e.target.value); handleChange() }}
              placeholder="e.g. professional, casual, educational"
              className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
            />
          </div>

          {/* Prompt editor */}
          <div className="space-y-1.5">
            <label className="text-xs text-text-muted uppercase tracking-wider">Curation Prompt</label>
            {promptQuery.isLoading ? (
              <div className="h-24 animate-pulse bg-white/5 rounded-lg" />
            ) : (
              <textarea
                value={promptContent ?? ''}
                onChange={(e) => { setPromptContent(e.target.value); handleChange() }}
                rows={8}
                className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-accent resize-none font-mono"
              />
            )}
          </div>

          {/* Save button */}
          <div className="flex justify-end">
            <button
              onClick={handleSave}
              disabled={updateAccount.isPending || !isDirty}
              className="flex items-center gap-1.5 px-4 py-2 text-sm bg-accent/20 text-accent hover:bg-accent/30 rounded-lg disabled:opacity-50 transition-colors"
            >
              <Save size={14} />
              {updateAccount.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export function AccountSettingsPage() {
  const accounts = useAccounts()
  const accountData = accounts.data?.accounts ?? {}

  return (
    <PageTransition>
      <div className="p-6 space-y-5 max-w-3xl">
        {/* Header */}
        <div className="flex items-center gap-3">
          <Settings size={22} className="text-accent" />
          <div>
            <h1 className="text-xl font-semibold text-text-primary">Settings</h1>
            <p className="text-sm text-text-muted">Account configuration and curation prompts</p>
          </div>
        </div>

        {/* Account panels */}
        {accounts.isLoading ? (
          <div className="space-y-3">
            {['A', 'B', 'C'].map((id) => (
              <div key={id} className="h-16 animate-pulse rounded-xl bg-white/5" />
            ))}
          </div>
        ) : accounts.isError ? (
          <GlassCard>
            <p className="text-sm text-red-600">Failed to load account settings</p>
          </GlassCard>
        ) : (
          <div className="space-y-3">
            {(['A', 'B', 'C'] as const).map((id) => {
              const info = accountData[id]
              if (!info) return null
              return <AccountPanel key={id} id={id} info={info} />
            })}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
