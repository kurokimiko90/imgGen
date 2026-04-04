export const ACCOUNT_COLORS = {
  A: { bg: 'bg-blue-500/15', border: 'border-blue-500/40', text: 'text-blue-400', dot: 'bg-blue-500' },
  B: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', dot: 'bg-emerald-500' },
  C: { bg: 'bg-orange-500/15', border: 'border-orange-500/40', text: 'text-orange-400', dot: 'bg-orange-500' },
} as const

export type AccountId = keyof typeof ACCOUNT_COLORS

export const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-text-muted bg-white/5',
  PENDING_REVIEW: 'text-yellow-400 bg-yellow-500/10',
  APPROVED: 'text-green-400 bg-green-500/10',
  PUBLISHED: 'text-blue-400 bg-blue-500/10',
  REJECTED: 'text-red-400 bg-red-500/10',
  ANALYZED: 'text-purple-400 bg-purple-500/10',
}

export const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Draft',
  PENDING_REVIEW: 'Pending',
  APPROVED: 'Approved',
  PUBLISHED: 'Published',
  REJECTED: 'Rejected',
  ANALYZED: 'Analyzed',
}
