import { cn } from '@/lib/utils'
import { useGenerateStore } from '@/stores/useGenerateStore'
import { FileText, Globe, Type } from 'lucide-react'

const TABS = [
  { id: 'text' as const, label: 'Text', icon: Type },
  { id: 'file' as const, label: 'File', icon: FileText },
  { id: 'url' as const, label: 'URL', icon: Globe },
]

export function InputTabs() {
  const inputMode = useGenerateStore((s) => s.inputMode)
  const setInputMode = useGenerateStore((s) => s.setInputMode)
  const text = useGenerateStore((s) => s.text)
  const setText = useGenerateStore((s) => s.setText)
  const url = useGenerateStore((s) => s.url)
  const setUrl = useGenerateStore((s) => s.setUrl)

  return (
    <div className="space-y-3">
      {/* Tab buttons */}
      <div className="flex gap-1 rounded-lg bg-bg-surface p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setInputMode(tab.id)}
            className={cn(
              'flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
              inputMode === tab.id
                ? 'bg-accent text-white'
                : 'text-text-muted hover:text-text-secondary',
            )}
          >
            <tab.icon size={14} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {inputMode === 'text' && (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Paste your article text here..."
          rows={8}
          className="w-full rounded-lg border border-border bg-bg-input px-4 py-3 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30 resize-none"
        />
      )}

      {inputMode === 'file' && (
        <div className="flex items-center justify-center rounded-lg border-2 border-dashed border-border bg-bg-input py-12 text-center">
          <div className="space-y-2">
            <FileText size={32} className="mx-auto text-text-faint" />
            <p className="text-sm text-text-muted">
              Drop a .txt or .md file here, or click to browse
            </p>
            <input
              type="file"
              accept=".txt,.md"
              className="absolute inset-0 cursor-pointer opacity-0"
              onChange={(e) => {
                const file = e.target.files?.[0]
                if (file) {
                  file.text().then(setText)
                  setInputMode('text')
                }
              }}
            />
          </div>
        </div>
      )}

      {inputMode === 'url' && (
        <div className="flex gap-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/article"
            className="flex-1 rounded-lg border border-border bg-bg-input px-4 py-3 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/30"
          />
        </div>
      )}
    </div>
  )
}
