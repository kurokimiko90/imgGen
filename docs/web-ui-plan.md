# imgGen Web UI — UX Architecture & Technical Plan

**Author**: ArchitectUX
**Date**: 2026-03-28
**Version**: v4 — React + FastAPI, extracted content editing + re-render
**Status**: Implemented

---

## 1. Overview

A locally-served web application with a **sidebar + content area** layout. Each feature is a dedicated page, navigated by sidebar buttons — only one view at a time.

### Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend framework** | React 19 + TypeScript | Most mainstream, largest ecosystem, best extensibility |
| **Build tool** | Vite 6 | Fastest DX, HMR, native TS support |
| **Styling** | Tailwind CSS v4 | Utility-first, most popular CSS framework, zero runtime |
| **Component library** | shadcn/ui (Radix UI primitives) | Copy-paste ownership, fully customizable, not a dependency lock-in |
| **Animation** | Framer Motion 12 | Page transitions, layout animations, stagger effects, spring physics |
| **Icons** | Lucide React | Tree-shakable, consistent with shadcn/ui |
| **State management** | Zustand | Minimal boilerplate, one global store for generate options + results |
| **Data fetching** | TanStack Query (React Query) | Cache, retry, loading/error states, optimistic updates |
| **Backend** | FastAPI (Python) | Async, auto OpenAPI docs, Pydantic validation, modern Python |
| **API communication** | REST + SSE | REST for CRUD, SSE for watch/batch live progress |

### Why This Stack

- **Extensibility**: React component model + shadcn/ui = 新功能只需加一個 page component + 一個 API route
- **Mainstream**: React + Tailwind + Vite is the #1 combination in 2026 frontend surveys
- **Cool effects**: Framer Motion enables page transitions, parallax, spring-based hover effects, animated counters, glassmorphism with backdrop-blur — all declarative

### Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│  Browser (React SPA)                                │
│  ┌──────────┐  ┌─────────────────────────────────┐  │
│  │ Sidebar  │  │  <AnimatePresence>               │  │
│  │ (nav)    │  │    Page Component (one at a time)│  │
│  │          │  │    ← Framer Motion transitions → │  │
│  │          │  │                                   │  │
│  └──────────┘  └─────────────────────────────────┘  │
│        ↕ Zustand store (options, results, toast)    │
│        ↕ TanStack Query (API cache)                 │
└──────────────────┬──────────────────────────────────┘
                   │ fetch / SSE
┌──────────────────▼──────────────────────────────────┐
│  FastAPI server (localhost:8000)                     │
│  ├── /api/generate   → pipeline.run_pipeline()      │
│  ├── /api/generate/multi → multi-format generation  │
│  ├── /api/re-render  → render_and_capture() (no AI) │
│  ├── /api/caption    → caption.generate_captions()  │
│  ├── /api/history    → history.list/search/stats()  │
│  ├── /api/history/{id} → single record + image_url  │
│  ├── /api/stats      → aggregate statistics         │
│  ├── /api/digest     → digest.generate_digest()     │
│  ├── /api/batch      → batch.run_batch() + SSE      │
│  ├── /api/watch      → watcher.watch_directory()    │
│  ├── /api/presets    → config.save/load/delete()    │
│  ├── /api/meta       → available themes/formats     │
│  └── /output/{file}  → StaticFiles                  │
│        ↕                                            │
│  src/pipeline.py, src/history.py, src/caption.py... │
└─────────────────────────────────────────────────────┘
```

---

## 2. Information Architecture

### Layout Model: Sidebar + Animated Content

```
+--------+----------------------------------------------+
| SIDE   |                                              |
| BAR    |  <AnimatePresence mode="wait">               |
|        |    <motion.div key={page}>                   |
| logo   |      [Active Page Component]                 |
|        |    </motion.div>                             |
| -----  |  </AnimatePresence>                          |
| > Gen  |                                              |
|   Cap  |  Pages slide in/out with spring physics      |
|   Hist |  Content fades + translates on switch        |
|   Tool |                                              |
|   Pre  |                                              |
| -----  |                                              |
| theme  |                                              |
| v4.0   |                                              |
+--------+----------------------------------------------+
```

### Pages (5 routes)

| Route | Sidebar Label | Icon | Description |
|-------|--------------|------|-------------|
| `/` | Generate | Sparkles | Input, theme/format pills, preview, actions |
| `/captions` | Captions | MessageSquare | Platform text captions |
| `/history` | History | Clock | List + search + stats (tab switch) |
| `/tools` | Tools | Wrench | Digest / Batch / Watch cards |
| `/presets` | Presets | Bookmark | Preset CRUD management |

### Navigation

- React Router (client-side routes, no page reload)
- Framer Motion `AnimatePresence` wraps page transitions
- Active page: accent left border + accent bg on sidebar item
- Sidebar bottom: theme toggle (dark/light/system) + version

### Responsive Sidebar

| Breakpoint | Sidebar | Behavior |
|------------|---------|----------|
| >1024px | 240px, full labels + icons | Always visible |
| 768–1024px | 64px, icons only | Hover tooltip shows label |
| <768px | Hidden | Top bar with hamburger + slide-in drawer |

---

## 3. Design System (Tailwind Config)

Extend Tailwind with imgGen tokens. Dark mode first via `class` strategy.

```ts
// tailwind.config.ts
export default {
  darkMode: 'class',   // toggle via <html class="dark">
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: '#090d1a',
          surface: 'rgba(255,255,255,0.04)',
          card: 'rgba(255,255,255,0.06)',
          input: 'rgba(255,255,255,0.08)',
        },
        accent: {
          DEFAULT: '#2563eb',
          dim: 'rgba(37,99,235,0.18)',
          glow: 'rgba(37,99,235,0.08)',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Noto Sans TC', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        title: 'clamp(26px, 4vw, 34px)',
        section: 'clamp(20px, 3vw, 24px)',
      },
      borderRadius: {
        card: '16px',
      },
      boxShadow: {
        card: '0 1px 4px rgba(37,99,235,0.10), 0 1px 2px rgba(37,99,235,0.06)',
        glow: '0 0 20px rgba(37,99,235,0.15)',
      },
      animation: {
        'fade-up': 'fadeUp 0.32s cubic-bezier(0.16,1,0.3,1)',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
}
```

### Visual Effects (Framer Motion)

```tsx
// Page transition variant
const pageVariants = {
  initial: { opacity: 0, y: 20, filter: 'blur(4px)' },
  animate: { opacity: 1, y: 0, filter: 'blur(0px)',
    transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
  exit: { opacity: 0, y: -10, filter: 'blur(4px)',
    transition: { duration: 0.2 } },
}

// Stagger children (cards, list items)
const staggerContainer = {
  animate: { transition: { staggerChildren: 0.06 } },
}

// Hover glow on cards
const cardHover = {
  whileHover: { scale: 1.02, boxShadow: '0 0 24px rgba(37,99,235,0.2)' },
  transition: { type: 'spring', stiffness: 300, damping: 20 },
}
```

### Cool Effect Catalog

| Effect | Where | How |
|--------|-------|-----|
| **Page slide + blur** | Page transitions | Framer `AnimatePresence` + blur filter |
| **Staggered fade-up** | Card lists, history rows, option pills | `staggerChildren: 0.06` |
| **Glassmorphism cards** | All card panels | `backdrop-blur-xl bg-white/5 border border-white/10` |
| **Glow hover** | Buttons, cards, sidebar items | `shadow-glow` on hover with spring |
| **Accent gradient bg** | Page background | Radial gradients fixed behind content |
| **Animated counter** | Stats page numbers | Framer `useSpring` + `useMotionValue` |
| **Progress ring** | Generation loading | SVG circle with `pathLength` animation |
| **Skeleton shimmer** | Loading states | Tailwind `animate-pulse` with gradient |
| **Toast slide-in** | Notifications | Framer `AnimatePresence` from bottom-right |
| **Pill spring** | Theme/format selection | `layoutId` shared layout animation |

---

## 4. Feature Mapping: CLI -> Web UI

| CLI Feature | Web UI Component | Page |
|-------------|-----------------|------|
| `--text` | `<Textarea>` (shadcn) | Generate |
| `--file` | Drag-and-drop `<FileUpload>` | Generate |
| `--url` | `<Input>` + fetch button | Generate |
| `--theme` | `<ToggleGroup>` with color swatches | Generate |
| `--format` | `<ToggleGroup>` with aspect ratio icons | Generate |
| `--formats` | Multi-select toggle group | Generate |
| `--provider` | `<Select>` dropdown (shadcn) | Generate |
| `--scale` | `<Switch>` 1x/2x | Generate > Advanced |
| `--webp` | `<Switch>` | Generate > Advanced |
| `--watermark` | `<FileUpload>` (image) | Generate > Advanced |
| `--watermark-position` | 4-corner visual `<RadioGroup>` | Generate > Advanced |
| `--watermark-opacity` | `<Slider>` | Generate > Advanced |
| `--brand-name` | `<Input>` | Generate > Advanced |
| `--thread` | `<Switch>` | Generate > Advanced |
| `--clipboard` | `<Button>` on preview panel | Generate |
| `--caption` | Platform `<ToggleGroup>` + generate | Captions |
| `--post twitter` | `<Button>` on preview panel | Generate |
| `--batch` | `<FileUpload>` + `<Slider>` + run | Tools |
| `--preset` | CRUD card grid | Presets |
| `history list` | `<DataTable>` with search + filter | History |
| `history stats` | Stats dashboard with animated counters | History |
| `digest` | Days/theme/provider form + generate | Tools |
| `watch` | Directory input + start/stop + live feed | Tools |

---

## 5. Component Hierarchy (React)

```
<App>
  <ThemeProvider>           /* dark/light/system via class on <html> */
  <QueryClientProvider>     /* TanStack Query */
  <Toaster />               /* shadcn toast, bottom-right */

  <div className="flex h-screen">
    <Sidebar>
      <Logo />
      <NavList>
        <NavItem icon={Sparkles}      to="/"          label="Generate" />
        <NavItem icon={MessageSquare} to="/captions"  label="Captions" />
        <NavItem icon={Clock}         to="/history"   label="History" />
        <NavItem icon={Wrench}        to="/tools"     label="Tools" />
        <NavItem icon={Bookmark}      to="/presets"   label="Presets" />
      </NavList>
      <SidebarFooter>
        <ThemeToggle />
        <VersionBadge />
      </SidebarFooter>
    </Sidebar>

    <main className="flex-1 overflow-y-auto">
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/"         element={<GeneratePage />} />
          <Route path="/captions" element={<CaptionsPage />} />
          <Route path="/history"  element={<HistoryPage />} />
          <Route path="/tools"    element={<ToolsPage />} />
          <Route path="/presets"  element={<PresetsPage />} />
        </Routes>
      </AnimatePresence>
    </main>
  </div>
</App>
```

### Generate Page — Top-to-Bottom Layout with Editable Extracted Content

After generation, AI-extracted content (title, key points, source) is displayed in an
editable panel alongside the image preview. Users can modify the content and re-render
without re-running the AI extraction (saves API cost and time).

```
<GeneratePage>
  <PageTransition>
    ┌─────────────────────────────────────────────────────┐
    │ 📝 Input Area                                       │
    │  InputTabs (Text / File / URL)                      │
    │  ThemePillGroup + FormatPillGroup + ProviderSelect  │
    │  AdvancedOptions (collapsible)                      │
    │  [Generate Card] [All Formats]                      │
    └─────────────────────────────────────────────────────┘

    ↓ After generation (AnimatePresence) ↓

    ┌──────────────────────────┬──────────────────────────┐
    │ 📋 ExtractedContentEditor │ 🖼 PreviewPanel          │
    │                           │                           │
    │ Title: [editable input]  │  [Generated Card Image]   │
    │                           │                           │
    │ Key Points:               │                           │
    │  1. [editable input] ✕   │                           │
    │  2. [editable input] ✕   │  [Download] [Copy]        │
    │  3. [editable input] ✕   │                           │
    │  + Add point              │                           │
    │                           │                           │
    │ Source: [editable input] │                           │
    │                           │                           │
    │ [🔄 Re-generate Card]    │                           │
    └──────────────────────────┴──────────────────────────┘
  </PageTransition>
</GeneratePage>
```

**Key behaviors:**
- `ExtractedContentEditor` reads/writes `useGenerateStore.extractedData`
- Re-generate calls `POST /api/re-render` (skips AI extraction)
- `PreviewPanel` shows loading spinner during generation, image + download/copy after
- Result section animates in with Framer Motion when `extractedData` or `imageUrl` exists

### History Page — Clickable Rows with Expandable Detail

Each history row is clickable and expands to show a detail panel with thumbnail,
full extracted content, and action buttons.

```
<HistoryPage>
  <PageTransition>
    [List | Stats] tab toggle + [All | 7d | 30d | 90d] filter + Search

    ┌─────────────────────────────────────────────────────┐
    │ Title          Theme   Format  Provider  Pts  Date ▼│
    ├─────────────────────────────────────────────────────┤
    │ AI Weekly      dark    story   claude    5    Mar 28│ ← click to expand
    │ ┌─────────────────────────────────────────────────┐ │
    │ │ [Thumb]  │  Title: AI Weekly Roundup            │ │
    │ │          │  Key Points:                          │ │
    │ │          │   1. AI models are getting faster     │ │
    │ │          │   2. Open source catching up          │ │
    │ │          │  Source: techcrunch.com                │ │
    │ │          │                                       │ │
    │ │          │  [Re-generate] [Open Image]           │ │
    │ └─────────────────────────────────────────────────┘ │
    │ Tech News      light   square  gemini    3    Mar 27│
    └─────────────────────────────────────────────────────┘
  </PageTransition>
</HistoryPage>
```

**Key behaviors:**
- Click row → expand `HistoryDetailPanel` with Framer Motion animation
- Detail fetches `GET /api/history/{id}` for full data + image URL
- Re-generate button loads `extractedData` into Generate store and navigates to `/`
- Stats tab shows animated counters, breakdowns by theme/provider/format

---

## 6. Backend API (FastAPI)

```python
# web/api.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="imgGen API", version="4.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"])
app.mount("/output", StaticFiles(directory="output"), name="output")
```

### Endpoints

| Method | Path | Request | Response |
|--------|------|---------|----------|
| POST | `/api/generate` | `{text?, url?, theme, format, provider, ...}` | `{ok, image_url, title, points_count, file_size, extracted_data, history_id}` |
| POST | `/api/generate/multi` | `{..., formats: ["story","twitter"]}` | `{ok, images: [{url, format, size}], title, extracted_data}` |
| POST | `/api/re-render` | `{history_id?, extracted_data, theme, format, ...}` | `{ok, image_url, title, file_size, extracted_data, history_id}` |
| POST | `/api/caption` | `{platforms: [], provider, data}` | `{ok, captions: {twitter: "...", ...}}` |
| GET | `/api/history?days=7&q=search&limit=20` | query params | `{ok, rows: [...]}` (rows include parsed `extracted_data`) |
| GET | `/api/history/{id}` | path param | `{ok, row: {..., extracted_data, image_url}}` |
| GET | `/api/stats?days=7` | query params | `{ok, total, by_theme, by_provider, by_format, avg_points, date_range, recent_titles}` |
| GET | `/api/meta` | — | `{ok, themes, formats, providers}` |
| POST | `/api/digest` | `{days, theme, provider}` | `{ok, image_url, title}` |
| POST | `/api/batch` | `FormData(file, workers)` | SSE stream: `{progress, results}` |
| POST | `/api/watch/start` | `{directory, theme, format}` | SSE stream: live events |
| POST | `/api/watch/stop` | `{}` | `{ok}` |
| GET | `/api/presets` | — | `{ok, presets: {...}}` |
| POST | `/api/presets` | `{name, values}` | `{ok}` |
| DELETE | `/api/presets/{name}` | — | `{ok}` |

All responses: `{ ok: bool, error?: string, ...data }`

### Re-render API (Skip AI)

`POST /api/re-render` allows re-generating a card image from previously extracted
(and optionally user-edited) content, skipping the expensive AI extraction step.

```python
class ReRenderRequest(BaseModel):
    history_id: int | None = None
    extracted_data: dict       # {title, key_points: [{text}], source}
    theme: str = "dark"
    format: str = "story"
    scale: int = 2
    webp: bool = False
    brand_name: str | None = None
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8
```

Flow: validates `extracted_data` → calls `render_and_capture()` directly → saves to history → returns new image URL.

### Database: `extracted_data` Column

The `generations` table includes an `extracted_data TEXT` column (JSON blob) storing
the full AI extraction result:

```json
{
  "title": "AI Weekly Roundup",
  "key_points": [{"text": "Point 1"}, {"text": "Point 2"}],
  "source": "techcrunch.com",
  "theme_suggestion": "dark"
}
```

Added via backward-compatible `ALTER TABLE ADD COLUMN` migration on startup.

---

## 7. File Structure

```
web/
  api.py                    # FastAPI app + all route handlers
  requirements.txt          # fastapi, uvicorn, python-multipart
  frontend/
    package.json
    vite.config.ts
    tsconfig.json
    tailwind.config.ts
    index.html
    src/
      main.tsx              # React entry, providers, router
      App.tsx               # Layout shell: sidebar + animated routes
      stores/
        useGenerateStore.ts # Zustand: generate options + results + extractedData + historyId
      api/
        client.ts           # fetch wrapper, base URL, error handling
        queries.ts          # TanStack Query hooks (useGenerate, useHistory, ...)
      components/
        layout/
          Sidebar.tsx
          NavItem.tsx
          MobileTopBar.tsx
          GlassCard.tsx     # Reusable glassmorphism card wrapper
          PageTransition.tsx # Framer motion page wrapper
        ui/                 # shadcn/ui components (copied in)
          button.tsx
          input.tsx
          tabs.tsx
          select.tsx
          slider.tsx
          switch.tsx
          toggle-group.tsx
          collapsible.tsx
          toast.tsx
          data-table.tsx
      pages/
        GeneratePage.tsx
        CaptionsPage.tsx
        HistoryPage.tsx
        ToolsPage.tsx
        PresetsPage.tsx
      features/
        generate/
          InputTabs.tsx               # Text/File/URL tab input
          ThemePillGroup.tsx          # 5 theme pills with spring animation
          FormatPillGroup.tsx         # 4 format pills with spring animation
          AdvancedOptions.tsx         # Collapsible: scale, webp, brand, watermark, thread
          PreviewPanel.tsx            # Image preview + download/copy buttons
          ExtractedContentEditor.tsx  # Editable title/key_points/source + re-render button
        history/
          HistoryDetailPanel.tsx      # Expandable detail: thumbnail + extracted data + actions
```

---

## 8. Development & Run

```bash
# Backend
cd web && pip install fastapi uvicorn python-multipart
uvicorn api:app --reload --port 8000

# Frontend
cd web/frontend && npm install && npm run dev
# → Vite dev server on http://localhost:5173, proxies /api to :8000
```

Production build:
```bash
cd web/frontend && npm run build
# Output to web/frontend/dist/, served by FastAPI as static files
```

Vite proxy config:
```ts
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/output': 'http://localhost:8000',
    },
  },
})
```

---

## 9. Implementation Priority

```
Phase 1: Scaffold + Generate MVP                          ✅ DONE
  1. FastAPI scaffold (api.py) + POST /api/generate + /output static
  2. Vite + React + Tailwind init
  3. Sidebar layout + React Router + Framer page transitions
  4. GeneratePage: text input + theme/format pills + generate button
  5. PreviewPanel: loading skeleton → image result + download

Phase 2: Generate Full + Captions                         ✅ DONE
  6. File upload + URL input tabs
  7. Advanced options (collapsible)
  8. Multi-format, clipboard actions
  9. CaptionsPage + POST /api/caption

Phase 3: History + Presets                                ✅ DONE
  11. HistoryPage: DataTable + search + days filter
  12. StatsPanel: animated counters + generate stats card
  13. PresetsPage: list + save + load + delete

Phase 4: Tools                                            ✅ DONE
  14. DigestCard + POST /api/digest
  15. BatchCard + SSE progress stream
  16. WatchCard + SSE live feed

Phase 5: Extracted Content + Re-render (v4 new)           ✅ DONE
  17. DB migration: extracted_data column + get/update helpers
  18. API: /api/generate returns extracted_data + history_id
  19. API: POST /api/re-render (skip AI, render from edited data)
  20. API: GET /api/history/{id} (single record with image_url)
  21. Frontend: ExtractedData type + useReRender + useHistoryDetail
  22. Generate store: extractedData, historyId, setExtractedData, loadFromHistory
  23. ExtractedContentEditor component (editable title/points/source)
  24. GeneratePage redesign: top input → bottom result (editor + preview)
  25. HistoryDetailPanel: expandable row detail with thumbnail + re-generate

Phase 6: Polish (TODO)
  26. Mobile responsive: drawer sidebar, stacked layouts
  27. Error boundaries + toast notifications
  28. Reduced motion / accessibility improvements

--- Value Expansion Roadmap (v5) — 自動化內容管道 ---

Phase 7: Quick Wins
  29. Smart URL extraction (trafilatura) — cleaner article parsing
  30. Extraction prompt customization — language, tone, audience, point count
  31. Export HTML — download rendered HTML for embedding

Phase 8: Modern Content Ingestion (replaces RSS)
  32. Telegram Bot — forward article/URL → receive card image
  33. Webhook API — POST /api/webhook/generate + API Key auth → Zapier/n8n/IFTTT/Shortcuts
  34. PDF and image input — PyMuPDF + Vision API OCR

Phase 9: Output Diversification
  35. Carousel / multi-slide output — Instagram/LinkedIn carousels + PDF
  36. Animated card output — GIF/MP4 via Playwright video capture
  37. New card types: Quote / Compare / Stats cards + templates

Phase 10: Distribution Automation
  38. Multi-platform publishing — LinkedIn → Threads → Instagram APIs
  39. Scheduled publishing — APScheduler + calendar UI
  40. End-to-end automation — Telegram → generate → auto-publish pipeline

Phase 11: Feedback Intelligence
  41. Engagement tracking — poll platform APIs for likes/impressions
  42. A/B theme testing — same content, multiple themes, track winner
  43. AI content insights — optimal posting times, best theme/content combos
```

---

## 10. Accessibility

- shadcn/ui built on Radix UI = keyboard + screen reader support by default
- All form inputs have `<Label>` from shadcn
- Focus ring: `ring-2 ring-accent` on all interactive elements
- Color contrast: WCAG AA (dark theme already passes)
- `aria-live` region for toast notifications
- Reduced motion: `prefers-reduced-motion` disables Framer animations

---

## 11. Notes

- Frontend and backend are **separate processes** in dev (Vite + FastAPI), **single process** in prod (FastAPI serves built static files)
- All existing `src/*.py` modules are imported directly by `api.py` — no duplication
- Image output goes to the same `output/` directory as CLI
- SSE (Server-Sent Events) for watch and batch progress — no WebSocket complexity
- Zustand store persists generate options to `localStorage` so they survive page refresh
