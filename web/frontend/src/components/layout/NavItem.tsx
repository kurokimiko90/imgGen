import { cn } from '@/lib/utils'
import { NavLink } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'

interface NavItemProps {
  to: string
  label: string
  icon: LucideIcon
  collapsed?: boolean
}

export function NavItem({ to, label, icon: Icon, collapsed }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all',
          'hover:bg-hover',
          isActive
            ? 'bg-accent-dim text-text border-l-2 border-accent'
            : 'text-text-secondary border-l-2 border-transparent',
          collapsed && 'justify-center px-2',
        )
      }
      title={collapsed ? label : undefined}
    >
      <Icon size={20} />
      {!collapsed && <span>{label}</span>}
    </NavLink>
  )
}
