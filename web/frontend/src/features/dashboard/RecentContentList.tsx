import { cn } from '@/lib/utils'
import { StatusBadge } from './StatusBadge'
import { ACCOUNT_COLORS, type AccountId } from '@/constants/accounts'

interface RecentItem {
  id: string
  account_type: string
  title: string
  status: string
  content_type: string | null
  image_url: string | null
  created_at: string
}

interface RecentContentListProps {
  items: RecentItem[]
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso
  }
}

export function RecentContentList({ items }: RecentContentListProps) {
  if (items.length === 0) {
    return (
      <div className="py-8 text-center text-sm text-text-muted">No content yet</div>
    )
  }

  return (
    <div className="divide-y divide-border-subtle">
      {items.map((item) => {
        const colors = ACCOUNT_COLORS[item.account_type as AccountId] ?? ACCOUNT_COLORS.A
        return (
          <div key={item.id} className="flex items-center gap-3 py-2.5">
            {/* Account dot */}
            <span className={cn('w-2 h-2 rounded-full shrink-0', colors.dot)} />

            {/* Thumbnail */}
            <div className="hidden sm:block w-8 h-8 rounded bg-white/5 shrink-0 overflow-hidden">
              {item.image_url && (
                <img src={item.image_url} alt="" className="w-full h-full object-cover" />
              )}
            </div>

            {/* Title */}
            <span className="flex-1 text-sm text-text-primary truncate">{item.title || '(untitled)'}</span>

            {/* Account badge */}
            <span className={cn('hidden md:inline text-xs font-medium px-1.5 py-0.5 rounded', colors.text, colors.bg)}>
              {item.account_type}
            </span>

            {/* Status */}
            <StatusBadge status={item.status} />

            {/* Date */}
            <span className="hidden lg:block text-xs text-text-muted whitespace-nowrap">{formatDate(item.created_at)}</span>
          </div>
        )
      })}
    </div>
  )
}
