import { useEffect, useRef } from 'react'
import { Loader2, Check, SkipForward, AlertCircle, Image } from 'lucide-react'
import type { CurationProgress } from '@/api/queries'

interface CurationProgressFeedProps {
  events: CurationProgress[]
  isRunning: boolean
}

const EVENT_ICONS: Record<string, React.ReactNode> = {
  item_fetched: <Check size={12} className="text-blue-400" />,
  generating_image: <Image size={12} className="text-purple-400" />,
  saved_draft: <Check size={12} className="text-green-400" />,
  item_skipped: <SkipForward size={12} className="text-yellow-400" />,
  item_error: <AlertCircle size={12} className="text-red-400" />,
  account_start: <Loader2 size={12} className="text-accent animate-spin" />,
  account_done: <Check size={12} className="text-green-400" />,
}

function formatEvent(event: CurationProgress): string {
  switch (event.type) {
    case 'start':
      return `Starting curation for accounts: ${(event as unknown as { accounts?: string[] }).accounts?.join(', ') ?? ''}`
    case 'account_start':
      return `Account ${event.account}: starting...`
    case 'item_fetched':
      return `[${event.account}] Fetched: ${event.title ?? ''} (${event.source ?? ''})`
    case 'generating_image':
      return `[${event.account}] Generating image: ${event.title ?? ''}...`
    case 'saved_draft':
      return `[${event.account}] Saved draft: ${event.title ?? ''}`
    case 'item_skipped':
      return `[${event.account}] Skipped: ${event.reason ?? ''}`
    case 'item_error':
      return `[${event.account}] Error: ${event.error ?? ''}`
    case 'account_done':
      return `Account ${event.account}: done (${event.drafted ?? 0} drafted)`
    case 'done':
      return `Curation complete!`
    default:
      return JSON.stringify(event)
  }
}

export function CurationProgressFeed({ events, isRunning }: CurationProgressFeedProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [events])

  return (
    <div className="max-h-48 overflow-y-auto space-y-1 font-mono">
      {events.map((event, i) => (
        <div key={i} className="flex items-start gap-2 text-xs text-text-secondary">
          <span className="mt-0.5 shrink-0">
            {EVENT_ICONS[event.type] ?? <span className="w-3 h-3 block" />}
          </span>
          <span className={event.type === 'saved_draft' ? 'text-green-400' : event.type === 'item_error' ? 'text-red-400' : ''}>
            {formatEvent(event)}
          </span>
        </div>
      ))}
      {isRunning && (
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <Loader2 size={12} className="animate-spin" />
          <span>Running...</span>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  )
}
