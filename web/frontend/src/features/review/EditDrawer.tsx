import { useState, useEffect } from 'react'
import { X, Save } from 'lucide-react'
import { useContentDetail } from '@/api/queries'

interface EditDrawerProps {
  id: string
  onClose: () => void
  onSave: (title: string, body: string) => void
  isLoading: boolean
}

export function EditDrawer({ id, onClose, onSave, isLoading }: EditDrawerProps) {
  const detail = useContentDetail(id)
  const item = detail.data?.item

  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')

  useEffect(() => {
    if (item) {
      setTitle(item.title)
      setBody(item.body)
    }
  }, [item])

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/50" onClick={onClose} />

      {/* Drawer */}
      <div className="w-full max-w-lg bg-bg-surface border-l border-border-subtle shadow-2xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-border-subtle">
          <h2 className="text-sm font-semibold text-text-primary">Edit Content</h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {detail.isLoading ? (
            <div className="space-y-3">
              <div className="h-10 animate-pulse bg-white/5 rounded-lg" />
              <div className="h-40 animate-pulse bg-white/5 rounded-lg" />
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <label className="text-xs text-text-muted uppercase tracking-wider">Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs text-text-muted uppercase tracking-wider">Body</label>
                <textarea
                  value={body}
                  onChange={(e) => setBody(e.target.value)}
                  rows={12}
                  className="w-full bg-bg-base border border-border-subtle rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent resize-none"
                />
              </div>
            </>
          )}
        </div>

        <div className="p-4 border-t border-border-subtle flex gap-2 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-text-muted hover:text-text-primary hover:bg-hover rounded-lg"
          >
            Cancel
          </button>
          <button
            onClick={() => onSave(title, body)}
            disabled={isLoading || detail.isLoading}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-accent/20 text-accent hover:bg-accent/30 rounded-lg disabled:opacity-50"
          >
            <Save size={14} />
            {isLoading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}
