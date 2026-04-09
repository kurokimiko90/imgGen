export const ACCOUNT_COLORS = {
  A: { bg: 'bg-blue-500/15', border: 'border-blue-500/40', text: 'text-blue-400', dot: 'bg-blue-500' },
  B: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', dot: 'bg-emerald-500' },
  C: { bg: 'bg-slate-500/15', border: 'border-slate-500/40', text: 'text-slate-400', dot: 'bg-slate-500' },
} as const

export type AccountId = keyof typeof ACCOUNT_COLORS

export const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'text-text-muted bg-white/5',
  PENDING_REVIEW: 'text-accent bg-accent/10',
  APPROVED: 'text-accent bg-accent/10',
  PUBLISHED: 'text-accent bg-accent/10',
  REJECTED: 'text-red-600 bg-red-600/10',
  ANALYZED: 'text-accent bg-accent/10',
}

export const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Draft',
  PENDING_REVIEW: 'Pending',
  APPROVED: 'Approved',
  PUBLISHED: 'Published',
  REJECTED: 'Rejected',
  ANALYZED: 'Analyzed',
}
