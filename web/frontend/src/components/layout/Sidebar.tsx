import {
  Sparkles, MessageSquare, Clock, Wrench, Bookmark,
  PanelLeftClose, PanelLeft, LayoutDashboard,
  ClipboardCheck, Rss, Calendar, Settings,
} from 'lucide-react'
import { NavItem } from './NavItem'
import { ThemeSwitcher } from './ThemeSwitcher'
import { Logo } from '@/components/Logo'
import { useAppStore } from '@/stores/useAppStore'

const NAV_ITEMS = [
  { to: '/', label: 'Generate', icon: Sparkles },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/review', label: 'Review', icon: ClipboardCheck },
  { to: '/curation', label: 'Curation', icon: Rss },
  { to: '/scheduling', label: 'Scheduling', icon: Calendar },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/captions', label: 'Captions', icon: MessageSquare },
  { to: '/history', label: 'History', icon: Clock },
  { to: '/tools', label: 'Tools', icon: Wrench },
  { to: '/presets', label: 'Presets', icon: Bookmark },
] as const

export function Sidebar() {
  const collapsed = useAppStore((s) => s.sidebarCollapsed)
  const toggle = useAppStore((s) => s.toggleSidebar)

  return (
    <aside
      className={`flex flex-col border-r border-border-subtle bg-bg-surface h-screen shrink-0 transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-60'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-5">
        <Logo size={28} />
        {!collapsed && (
          <span className="text-lg font-semibold tracking-tight">imgGen</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 space-y-1 px-2">
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.to} {...item} collapsed={collapsed} />
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-border-subtle p-2 space-y-1">
        <ThemeSwitcher collapsed={collapsed} />
        <button
          onClick={toggle}
          className="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-text-muted hover:text-text-secondary hover:bg-hover transition-colors"
        >
          {collapsed ? <PanelLeft size={18} /> : <PanelLeftClose size={18} />}
          {!collapsed && <span>Collapse</span>}
        </button>
        <div className="text-xs text-text-faint text-center">v4.0</div>
      </div>
    </aside>
  )
}
