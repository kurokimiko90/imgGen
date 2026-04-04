import { useState, useRef, useCallback } from 'react'
import { PageTransition } from '@/components/layout/PageTransition'
import { GlassCard } from '@/components/layout/GlassCard'
import { useDigest } from '@/api/queries'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Wrench, BookOpen, Layers, Eye,
  Loader2, AlertCircle, CheckCircle2, Upload,
  FolderOpen, Play, Square, Image,
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Digest Card
// ---------------------------------------------------------------------------

function DigestCard() {
  const [days, setDays] = useState(7)
  const [theme, setTheme] = useState('dark')
  const [provider, setProvider] = useState('cli')
  const digest = useDigest()

  return (
    <GlassCard className="space-y-4">
      <div className="flex items-center gap-2">
        <BookOpen size={20} className="text-purple-400" />
        <h3 className="font-medium">Weekly Digest</h3>
      </div>
      <p className="text-sm text-text-muted">
        Synthesize recent generations into a single digest card
      </p>

      <div className="grid grid-cols-3 gap-3">
        <label className="space-y-1">
          <span className="text-xs text-text-muted">Days</span>
          <input
            type="number"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            min={1}
            max={90}
            className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none"
          />
        </label>
        <label className="space-y-1">
          <span className="text-xs text-text-muted">Theme</span>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none"
          >
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="gradient">Gradient</option>
            <option value="warm_sun">Warm Sun</option>
            <option value="cozy">Cozy</option>
          </select>
        </label>
        <label className="space-y-1">
          <span className="text-xs text-text-muted">Provider</span>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none"
          >
            <option value="cli">Claude CLI</option>
            <option value="claude">Claude API</option>
            <option value="gemini">Gemini</option>
            <option value="gpt">GPT</option>
          </select>
        </label>
      </div>

      <button
        onClick={() => digest.mutate({ days, theme, provider })}
        disabled={digest.isPending}
        className="flex items-center gap-2 rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-40 transition-colors"
      >
        {digest.isPending ? <Loader2 size={16} className="animate-spin" /> : <BookOpen size={16} />}
        Generate Digest
      </button>

      {digest.isError && (
        <div className="flex items-center gap-2 text-sm text-red-400">
          <AlertCircle size={14} /> {digest.error.message}
        </div>
      )}

      {digest.data && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
          <p className="text-sm font-medium text-text-secondary">{digest.data.title}</p>
          <a
            href={digest.data.image_url}
            target="_blank"
            rel="noreferrer"
            className="block rounded-lg overflow-hidden border border-border"
          >
            <img src={digest.data.image_url} alt={digest.data.title} className="w-full" />
          </a>
        </motion.div>
      )}
    </GlassCard>
  )
}

// ---------------------------------------------------------------------------
// Batch Card
// ---------------------------------------------------------------------------

interface BatchResult {
  type: string
  index?: number
  input?: string
  status?: string
  url?: string
  error?: string
  total?: number
  ok?: number
  errors?: number
}

function BatchCard() {
  const [file, setFile] = useState<File | null>(null)
  const [workers, setWorkers] = useState(3)
  const [theme, setTheme] = useState('dark')
  const [format, setFormat] = useState('story')
  const [provider, setProvider] = useState('cli')
  const [results, setResults] = useState<BatchResult[]>([])
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState<{ ok: number; errors: number } | null>(null)

  const handleRun = async () => {
    if (!file) return
    setRunning(true)
    setResults([])
    setDone(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('workers', String(workers))
    formData.append('theme', theme)
    formData.append('format', format)
    formData.append('provider', provider)

    try {
      const res = await fetch('/api/batch', { method: 'POST', body: formData })
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) return

      let buffer = ''
      while (true) {
        const { done: streamDone, value } = await reader.read()
        if (streamDone) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed: BatchResult = JSON.parse(line.slice(6))
              if (parsed.type === 'done') {
                setDone({ ok: parsed.ok ?? 0, errors: parsed.errors ?? 0 })
              } else {
                setResults((prev) => [...prev, parsed])
              }
            } catch { /* skip malformed */ }
          }
        }
      }
    } finally {
      setRunning(false)
    }
  }

  return (
    <GlassCard className="space-y-4">
      <div className="flex items-center gap-2">
        <Layers size={20} className="text-amber-400" />
        <h3 className="font-medium">Batch Process</h3>
      </div>
      <p className="text-sm text-text-muted">
        Upload a text file with URLs or file paths (one per line)
      </p>

      <div className="space-y-3">
        <label className="flex items-center justify-center gap-2 rounded-lg border-2 border-dashed border-border bg-bg-input py-6 cursor-pointer hover:border-text-faint transition-colors">
          <Upload size={20} className="text-text-faint" />
          <span className="text-sm text-text-muted">
            {file ? file.name : 'Choose batch file (.txt)'}
          </span>
          <input
            type="file"
            accept=".txt"
            className="hidden"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        <div className="grid grid-cols-4 gap-3">
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Workers</span>
            <input
              type="number"
              value={workers}
              onChange={(e) => setWorkers(Number(e.target.value))}
              min={1}
              max={10}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none"
            />
          </label>
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Theme</span>
            <select value={theme} onChange={(e) => setTheme(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="gradient">Gradient</option>
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Format</span>
            <select value={format} onChange={(e) => setFormat(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none">
              <option value="story">Story</option>
              <option value="square">Square</option>
              <option value="twitter">Twitter</option>
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Provider</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none">
              <option value="cli">CLI</option>
              <option value="claude">Claude</option>
              <option value="gemini">Gemini</option>
            </select>
          </label>
        </div>

        <button
          onClick={handleRun}
          disabled={!file || running}
          className="flex items-center gap-2 rounded-lg bg-amber-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-amber-700 disabled:opacity-40 transition-colors"
        >
          {running ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          Run Batch
        </button>
      </div>

      {/* Progress */}
      <AnimatePresence>
        {results.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-2 max-h-60 overflow-y-auto">
            {results.filter((r) => r.type === 'result').map((r, i) => (
              <div key={i} className="flex items-center gap-2 text-sm">
                {r.status === 'ok' ? (
                  <CheckCircle2 size={14} className="text-green-400 shrink-0" />
                ) : (
                  <AlertCircle size={14} className="text-red-400 shrink-0" />
                )}
                <span className="text-text-muted truncate">#{r.index} {r.input}</span>
                {r.url && (
                  <a href={r.url} target="_blank" rel="noreferrer" className="text-accent text-xs hover:underline shrink-0">
                    View
                  </a>
                )}
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {done && (
        <div className="text-sm text-text-secondary">
          Done: <span className="text-green-400">{done.ok} ok</span>
          {done.errors > 0 && <>, <span className="text-red-400">{done.errors} errors</span></>}
        </div>
      )}
    </GlassCard>
  )
}

// ---------------------------------------------------------------------------
// Watch Card
// ---------------------------------------------------------------------------

interface WatchEvent {
  type: string
  file?: string
  url?: string
  title?: string
  error?: string
  directory?: string
}

function WatchCard() {
  const [directory, setDirectory] = useState('')
  const [theme, setTheme] = useState('dark')
  const [format, setFormat] = useState('story')
  const [provider, setProvider] = useState('cli')
  const [watching, setWatching] = useState(false)
  const [events, setEvents] = useState<WatchEvent[]>([])
  const abortRef = useRef<AbortController | null>(null)

  const startWatch = useCallback(async () => {
    if (!directory.trim()) return
    setWatching(true)
    setEvents([])

    const controller = new AbortController()
    abortRef.current = controller

    const formData = new FormData()
    formData.append('directory', directory)
    formData.append('theme', theme)
    formData.append('format', format)
    formData.append('provider', provider)

    try {
      const res = await fetch('/api/watch/start', {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      })
      const reader = res.body?.getReader()
      const decoder = new TextDecoder()
      if (!reader) return

      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })

        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const parsed: WatchEvent = JSON.parse(line.slice(6))
              setEvents((prev) => [...prev.slice(-50), parsed])
            } catch { /* skip */ }
          }
        }
      }
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        // user stopped
      }
    } finally {
      setWatching(false)
    }
  }, [directory, theme, format, provider])

  const stopWatch = () => {
    abortRef.current?.abort()
    fetch('/api/watch/stop', { method: 'POST' })
  }

  return (
    <GlassCard className="space-y-4">
      <div className="flex items-center gap-2">
        <Eye size={20} className="text-green-400" />
        <h3 className="font-medium">Watch Directory</h3>
      </div>
      <p className="text-sm text-text-muted">
        Monitor a folder for new .txt/.md files and auto-generate cards
      </p>

      <div className="space-y-3">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <FolderOpen size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-faint" />
            <input
              type="text"
              value={directory}
              onChange={(e) => setDirectory(e.target.value)}
              placeholder="/path/to/watch"
              disabled={watching}
              className="w-full rounded-lg border border-border bg-bg-input pl-9 pr-3 py-2 text-sm text-text placeholder-text-faint outline-none focus:border-accent/50 disabled:opacity-50"
            />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Theme</span>
            <select value={theme} onChange={(e) => setTheme(e.target.value)} disabled={watching}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none disabled:opacity-50">
              <option value="dark">Dark</option>
              <option value="light">Light</option>
              <option value="gradient">Gradient</option>
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Format</span>
            <select value={format} onChange={(e) => setFormat(e.target.value)} disabled={watching}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none disabled:opacity-50">
              <option value="story">Story</option>
              <option value="square">Square</option>
              <option value="twitter">Twitter</option>
            </select>
          </label>
          <label className="space-y-1">
            <span className="text-xs text-text-muted">Provider</span>
            <select value={provider} onChange={(e) => setProvider(e.target.value)} disabled={watching}
              className="w-full rounded-md border border-border bg-bg-input px-3 py-1.5 text-sm text-text outline-none disabled:opacity-50">
              <option value="cli">CLI</option>
              <option value="claude">Claude</option>
              <option value="gemini">Gemini</option>
            </select>
          </label>
        </div>

        {!watching ? (
          <button
            onClick={startWatch}
            disabled={!directory.trim()}
            className="flex items-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-40 transition-colors"
          >
            <Play size={16} /> Start Watching
          </button>
        ) : (
          <button
            onClick={stopWatch}
            className="flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-red-700 transition-colors"
          >
            <Square size={16} /> Stop Watching
          </button>
        )}
      </div>

      {/* Event feed */}
      {events.length > 0 && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {events.map((ev, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              {ev.type === 'started' && <Eye size={12} className="text-green-400" />}
              {ev.type === 'detected' && <FolderOpen size={12} className="text-amber-400" />}
              {ev.type === 'generated' && <Image size={12} className="text-accent" />}
              {ev.type === 'error' && <AlertCircle size={12} className="text-red-400" />}
              <span className="text-text-muted">
                {ev.type === 'started' && `Watching ${ev.directory}`}
                {ev.type === 'detected' && `Detected: ${ev.file}`}
                {ev.type === 'generated' && `Generated: ${ev.title}`}
                {ev.type === 'error' && `Error: ${ev.file} — ${ev.error}`}
              </span>
              {ev.url && (
                <a href={ev.url} target="_blank" rel="noreferrer" className="text-accent hover:underline">View</a>
              )}
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  )
}

// ---------------------------------------------------------------------------
// Tools Page
// ---------------------------------------------------------------------------

export function ToolsPage() {
  return (
    <PageTransition className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <Wrench size={24} className="text-accent" />
        <h1 className="text-xl font-semibold">Tools</h1>
      </div>

      <div className="space-y-5">
        <DigestCard />
        <BatchCard />
        <WatchCard />
      </div>
    </PageTransition>
  )
}
