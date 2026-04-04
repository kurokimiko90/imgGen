import { useGenerateStore } from '@/stores/useGenerateStore'

const LANGUAGES = [
  { value: 'zh-TW', label: '繁體中文' },
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' },
  { value: 'ko', label: '한국어' },
]

const TONES = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'academic', label: 'Academic' },
  { value: 'marketing', label: 'Marketing' },
]

const selectClass =
  'w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none focus:border-accent/50'
const numberClass =
  'w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none focus:border-accent/50'

export function ExtractionSettings() {
  const store = useGenerateStore()

  return (
    <div className="space-y-4 border-t border-border-subtle pt-4">
      <div className="text-xs font-medium text-text-muted uppercase tracking-wider">
        Extraction Settings
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="space-y-1">
          <span className="text-xs text-text-muted">Language</span>
          <select
            aria-label="Language"
            value={store.extractionLanguage}
            onChange={(e) => store.setExtractionLanguage(e.target.value)}
            className={selectClass}
          >
            {LANGUAGES.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </label>

        <label className="space-y-1">
          <span className="text-xs text-text-muted">Tone</span>
          <select
            aria-label="Tone"
            value={store.extractionTone}
            onChange={(e) => store.setExtractionTone(e.target.value)}
            className={selectClass}
          >
            {TONES.map((t) => (
              <option key={t.value} value={t.value}>{t.label}</option>
            ))}
          </select>
        </label>

        <label className="space-y-1">
          <span className="text-xs text-text-muted">Min Points</span>
          <input
            aria-label="Min Points"
            type="number"
            min={1}
            max={8}
            value={store.extractionMinPoints}
            onChange={(e) => store.setExtractionMinPoints(Number(e.target.value))}
            className={numberClass}
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs text-text-muted">Max Points</span>
          <input
            aria-label="Max Points"
            type="number"
            min={1}
            max={8}
            value={store.extractionMaxPoints}
            onChange={(e) => store.setExtractionMaxPoints(Number(e.target.value))}
            className={numberClass}
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs text-text-muted">Title Max Chars</span>
          <input
            aria-label="Title Max Chars"
            type="number"
            min={5}
            max={100}
            value={store.extractionTitleMaxChars}
            onChange={(e) => store.setExtractionTitleMaxChars(Number(e.target.value))}
            className={numberClass}
          />
        </label>

        <label className="space-y-1">
          <span className="text-xs text-text-muted">Point Max Chars</span>
          <input
            aria-label="Point Max Chars"
            type="number"
            min={10}
            max={200}
            value={store.extractionPointMaxChars}
            onChange={(e) => store.setExtractionPointMaxChars(Number(e.target.value))}
            className={numberClass}
          />
        </label>

        <label className="col-span-2 space-y-1">
          <span className="text-xs text-text-muted">Custom Instructions</span>
          <textarea
            aria-label="Custom Instructions"
            value={store.extractionCustomInstructions}
            onChange={(e) => store.setExtractionCustomInstructions(e.target.value)}
            maxLength={500}
            rows={2}
            placeholder="E.g. Focus on technical details, include statistics..."
            className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 resize-none"
          />
        </label>
      </div>
    </div>
  )
}
