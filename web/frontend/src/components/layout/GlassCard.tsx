import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

interface GlassCardProps {
  children: ReactNode
  className?: string
}

export function GlassCard({ children, className }: GlassCardProps) {
  return (
    <div className={cn('glass-card p-5', className)}>
      {children}
    </div>
  )
}
