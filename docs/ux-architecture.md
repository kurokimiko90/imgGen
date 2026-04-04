# imgGen UX Architecture & Page Design

**Version**: v1
**Date**: 2026-03-28
**Status**: Design
**Methodology**: ArchitectUX

---

## 1. Design System Foundation

### 1.1 Existing Token System (Tailwind v4)

```css
/* src/index.css — 現有 */
--color-bg: #090d1a;
--color-bg-surface: rgba(255, 255, 255, 0.04);
--color-bg-card: rgba(255, 255, 255, 0.06);
--color-bg-input: rgba(255, 255, 255, 0.08);
--color-accent: #2563eb;
--color-accent-dim: rgba(37, 99, 235, 0.18);
--color-accent-glow: rgba(37, 99, 235, 0.08);
--font-sans: 'Outfit', 'Noto Sans TC', system-ui, sans-serif;
--radius-card: 16px;
```

### 1.2 New Tokens (需擴展)

```css
@theme {
  /* 現有 tokens 保留 */

  /* Status colors — Sprint 4/5 需要 */
  --color-success: #22c55e;
  --color-warning: #f59e0b;
  --color-error: #ef4444;
  --color-info: #3b82f6;

  /* Semantic surface layers */
  --color-bg-elevated: rgba(255, 255, 255, 0.10);
  --color-bg-overlay: rgba(0, 0, 0, 0.60);

  /* Spacing scale (基於 Tailwind 4px grid) */
  /* 已由 Tailwind 內建，不需額外定義 */

  /* Animation tokens */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
}
```

### 1.3 Component Foundation

所有頁面共用的 base components（已存在）:

| Component | File | 用途 |
|-----------|------|------|
| `GlassCard` | `components/layout/GlassCard.tsx` | 毛玻璃卡片容器 |
| `PageTransition` | `components/layout/PageTransition.tsx` | 頁面進場動畫 |
| `Sidebar` / `NavItem` | `components/layout/` | 側邊導航 |

---

## 2. Information Architecture

### 2.1 Navigation Structure (擴展後)

```
Sidebar Navigation
├── Generate        /                  (現有，Sprint 1 擴展)
├── Captions        /captions          (現有)
├── History         /history           (現有)
├── Carousel        /carousel          (Sprint 3 新增)
├── Automation      /automation        (Sprint 4 新增)
├── Analytics       /analytics         (Sprint 5 新增)
├── ──────────
├── Settings        /settings          (Sprint 2 新增)
├── Tools           /tools             (現有)
└── Presets         /presets           (現有)
```

**原則**: 主創作流程在上方，配置和工具在分隔線下方。最多 9 個 nav item。

### 2.2 User Flow Map

```
                    ┌─────────────┐
                    │  Content    │
                    │  Input      │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐      ┌────▼────┐
   │  Web UI  │      │ Telegram  │      │ Webhook │
   │ Generate │      │   Bot     │      │   API   │
   └────┬────┘      └─────┬─────┘      └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Pipeline   │
                    │  extract →  │
                    │  render →   │
                    │  screenshot │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐      ┌────▼────┐
   │ Single  │      │ Carousel  │      │Animated │
   │  Card   │      │ (multi)   │      │ GIF/MP4 │
   └────┬────┘      └─────┬─────┘      └────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Publish /  │
                    │  Download   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Analytics  │
                    └─────────────┘
```

---

## 3. Page Designs

---

### 3.1 Generate Page (擴展 — Sprint 1)

**路由**: `/`
**修改**: 在 AdvancedOptions 內新增「Extraction Settings」折疊區

#### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ p-6 max-w-6xl mx-auto space-y-6                            │
│                                                             │
│ ┌─ GlassCard ────────────────────────────────────────────┐  │
│ │ InputTabs [Text] [URL] [File]                          │  │
│ │                                                        │  │
│ │ (text | url | file dropzone)                           │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard ────────────────────────────────────────────┐  │
│ │ Theme:    [dark] [light] [gradient] [warm_sun] [cozy]  │  │
│ │ Format:   [story] [square] [landscape] [twitter]       │  │
│ │ Provider: [Claude CLI ▼]                               │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ AdvancedOptions (collapsible) ────────────────────────┐  │
│ │ ▼ Advanced Options                                     │  │
│ │                                                        │  │
│ │ Scale: [1x] [2x]   WebP: [toggle]   Thread: [toggle]  │  │
│ │ Brand: [________]   Watermark: [pos▼] [opacity slider] │  │
│ │                                                        │  │
│ │ ── Extraction Settings ──────────────────────────────  │  │
│ │                                                        │  │
│ │ ┌─ 2-col grid (md:grid-cols-2 gap-4) ──────────────┐  │  │
│ │ │ Language        │ Tone                             │  │  │
│ │ │ [繁體中文  ▼]   │ [Professional  ▼]               │  │  │
│ │ ├─────────────────┼────────────────────────────────  │  │  │
│ │ │ Points range    │ Title max chars                  │  │  │
│ │ │ [3] ~ [5]       │ [15] chars                      │  │  │
│ │ ├─────────────────┴────────────────────────────────  │  │  │
│ │ │ Custom instructions                                │  │  │
│ │ │ [________________________________________________] │  │  │
│ │ └───────────────────────────────────────────────────  │  │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ [Generate Card]  [All Formats]  [Export HTML]               │
│                                                             │
│ ── Result Section (AnimatePresence, appears after gen) ──   │
│                                                             │
│ ┌─ grid-cols-1 lg:grid-cols-[1fr_380px] gap-6 ──────────┐  │
│ │ ┌─ ExtractedContentEditor ─┐ ┌─ PreviewPanel ────────┐│  │
│ │ │ Title: [editable]        │ │ Loading / Image /     ││  │
│ │ │ Key Points: [editable]   │ │ Empty state           ││  │
│ │ │ Source: [editable]       │ │                       ││  │
│ │ │ [Re-render]              │ │ [Download][Copy][HTML]││  │
│ │ └──────────────────────────┘ └───────────────────────┘│  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Extraction Settings 組件規格

| Field | Type | Default | Options |
|-------|------|---------|---------|
| Language | Select | `zh-TW` | zh-TW, zh-CN, en, ja, ko |
| Tone | Select | `professional` | professional, casual, academic, marketing |
| Min Points | Number input | 3 | 1-8 |
| Max Points | Number input | 5 | 1-8 (>= min) |
| Title Max Chars | Number input | 15 | 5-100 |
| Point Max Chars | Number input | 50 | 10-200 |
| Custom Instructions | Textarea | `""` | Free text, max 500 chars |

**交互**: 所有值存入 `useGenerateStore`，透過 `partialize` 持久化到 localStorage。

#### File Upload Tab 規格 (Sprint 2.3)

```
┌─ File Dropzone ────────────────────────────────────────┐
│                                                         │
│    ┌─ border-2 border-dashed border-white/10 ────────┐  │
│    │  hover:border-accent/40 transition               │  │
│    │                                                  │  │
│    │      Upload size={32} text-white/20              │  │
│    │      Drop file here or click to browse           │  │
│    │      PDF, TXT, MD, PNG, JPG (max 10MB)           │  │
│    │                                                  │  │
│    └──────────────────────────────────────────────────┘  │
│                                                         │
│    (After selection):                                    │
│    ┌─ flex items-center gap-3 ───────────────────────┐  │
│    │ FileText icon │ article.pdf │ 2.3 MB │ [X clear]│  │
│    └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**States**: idle → dragover (border-accent, bg-accent/5) → selected (show file info)
**Validation**: Max 10MB, allowed extensions: .pdf .txt .md .png .jpg .jpeg .webp

---

### 3.2 Settings Page (新增 — Sprint 2)

**路由**: `/settings`
**Nav icon**: `Settings` (lucide)

#### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ p-6 max-w-3xl mx-auto space-y-6                            │
│                                                             │
│ ┌─ Header ───────────────────────────────────────────────┐  │
│ │ Settings icon + "Settings"                             │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: API Keys ─────────────────────────────────┐  │
│ │ ┌─ Header row ──────────────────────────────────────┐  │  │
│ │ │ Key icon + "API Keys"          [+ Create New Key] │  │  │
│ │ └───────────────────────────────────────────────────┘  │  │
│ │                                                        │  │
│ │ ┌─ Key list (space-y-2) ────────────────────────────┐  │  │
│ │ │ ┌─ Key row (flex, items-center, gap-3) ─────────┐ │  │  │
│ │ │ │ imggen_a3f8...  │ "Zapier" │ Mar 28 │ [Trash] │ │  │  │
│ │ │ └──────────────────────────────────────────────┘ │  │  │
│ │ │ ┌─ Key row ─────────────────────────────────────┐ │  │  │
│ │ │ │ imggen_x9m2...  │ "n8n"    │ Mar 25 │ [Trash] │ │  │  │
│ │ │ └──────────────────────────────────────────────┘ │  │  │
│ │ └──────────────────────────────────────────────────┘  │  │
│ │                                                        │  │
│ │ Empty state: "No API keys yet. Create one to use the   │  │
│ │ webhook API."                                          │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Create Key Modal (AnimatePresence) ────────┐  │
│ │ Key Name: [________________]                           │  │
│ │ [Cancel]  [Create]                                     │  │
│ │                                                        │  │
│ │ (After creation — show once, then hide):               │  │
│ │ ┌─ bg-success/10 border-success/20 rounded-lg p-4 ──┐ │  │
│ │ │ Your API Key (copy now, it won't be shown again):  │ │  │
│ │ │ [imggen_a3f8k2m9p7...........] [Copy]              │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Webhook Documentation ─────────────────────┐  │
│ │ Webhook icon + "Webhook API"                           │  │
│ │                                                        │  │
│ │ Endpoint:                                              │  │
│ │ ┌─ bg-bg-input rounded-lg px-4 py-3 font-mono ──────┐ │  │
│ │ │ POST /api/webhook/generate                         │ │  │
│ │ │ POST /api/webhook/generate/sync                    │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ │                                                        │  │
│ │ Example (curl):                                        │  │
│ │ ┌─ bg-bg-input rounded-lg px-4 py-3 font-mono ──────┐ │  │
│ │ │ curl -X POST http://host:8000/api/webhook/gen \    │ │  │
│ │ │   -H "X-API-Key: your_key" \                      │ │  │
│ │ │   -H "Content-Type: application/json" \            │ │  │
│ │ │   -d '{"url":"...","theme":"dark"}'                │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ │ [Copy Example]                                         │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Telegram Bot ──────────────────────────────┐  │
│ │ Bot icon + "Telegram Bot"                              │  │
│ │                                                        │  │
│ │ Bot Token:                                             │  │
│ │ [●●●●●●●●●●●●●●●●●●●] [Show/Hide] [Save]            │  │
│ │                                                        │  │
│ │ Status: ● Running (polling)  │  ○ Stopped              │  │
│ │                                                        │  │
│ │ Allowed Chat IDs: (blank = allow all)                  │  │
│ │ [___________________________________]                  │  │
│ │                                                        │  │
│ │ Default settings:                                      │  │
│ │ Theme: [dark ▼]  Format: [story ▼]  Provider: [cli ▼] │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Component Hierarchy

```
SettingsPage
├── PageTransition
├── Header (icon + title)
├── ApiKeysSection
│   ├── KeyList
│   │   └── KeyRow[] (prefix, name, date, delete button)
│   ├── CreateKeyModal (inline expandable, not dialog)
│   └── NewKeyDisplay (success state with copy)
├── WebhookDocsSection
│   ├── EndpointList (monospace code blocks)
│   └── CurlExample (copyable code block)
└── TelegramBotSection
    ├── TokenInput (password field with toggle)
    ├── StatusIndicator (dot + text)
    ├── AllowedChatsInput
    └── DefaultSettingsRow (3 selects)
```

#### Interaction Patterns

| Action | Behavior |
|--------|----------|
| Create Key | Inline form expands below button; on success shows key once with copy button |
| Delete Key | Confirm dialog ("Revoke key imggen_a3f8...? This cannot be undone.") |
| Copy Key/Example | `navigator.clipboard.writeText()`, button shows Check icon for 2s |
| Save Bot Token | POST to backend, show toast on success |
| Status dot | Green pulse = running, gray = stopped |

#### Store

新增 `useSettingsStore.ts`（不需要 persist — Settings 頁面直接讀寫 API）。

用 TanStack Query：
- `useApiKeys()` → GET `/api/keys`
- `useCreateKey()` → POST `/api/keys`
- `useRevokeKey()` → DELETE `/api/keys/{prefix}`
- `useTelegramStatus()` → GET `/api/telegram/status`

---

### 3.3 Carousel Page (新增 — Sprint 3)

**路由**: `/carousel`
**Nav icon**: `GalleryHorizontalEnd` (lucide)

#### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ p-6 max-w-6xl mx-auto space-y-6                            │
│                                                             │
│ ┌─ Header ───────────────────────────────────────────────┐  │
│ │ GalleryHorizontalEnd + "Carousel Generator"            │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Input (重用 InputTabs 邏輯) ───────────────┐  │
│ │ [Text] [URL] [File]                                    │  │
│ │ (input area)                                           │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Options (簡化版 — 只需 theme + provider) ──┐  │
│ │ Theme: [pills]     Provider: [select]                  │  │
│ │ Brand: [________]                                      │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ [Generate Carousel]                                         │
│                                                             │
│ ── Result (AnimatePresence) ─────────────────────────────   │
│                                                             │
│ ┌─ GlassCard: Carousel Preview ──────────────────────────┐  │
│ │ ┌─ Header ───────────────────────────────────────────┐ │  │
│ │ │ "Carousel Preview"             Slide 1 / 7        │ │  │
│ │ └───────────────────────────────────────────────────┘ │  │
│ │                                                        │  │
│ │ ┌─ Viewer (flex items-center justify-center) ────────┐ │  │
│ │ │                                                    │ │  │
│ │ │ [◀]    ┌──────────────────────┐    [▶]            │ │  │
│ │ │ prev   │                      │    next            │ │  │
│ │ │        │   Current Slide      │                    │ │  │
│ │ │        │   (aspect-[9/16])    │                    │ │  │
│ │ │        │                      │                    │ │  │
│ │ │        └──────────────────────┘                    │ │  │
│ │ │                                                    │ │  │
│ │ └────────────────────────────────────────────────────┘ │  │
│ │                                                        │  │
│ │ ┌─ Dot indicators (flex justify-center gap-2) ───────┐ │  │
│ │ │        ● ● ● ○ ○ ○ ○                              │ │  │
│ │ └────────────────────────────────────────────────────┘ │  │
│ │                                                        │  │
│ │ ┌─ Thumbnail strip (flex gap-2 overflow-x-auto) ────┐  │  │
│ │ │ [thumb1] [thumb2] [thumb3] [thumb4] ...            │  │  │
│ │ └────────────────────────────────────────────────────┘  │  │
│ │                                                        │  │
│ │ ┌─ Actions (flex gap-3) ─────────────────────────────┐ │  │
│ │ │ [Download All (.zip)]  [Download PDF]  [Copy Slide]│ │  │
│ │ └────────────────────────────────────────────────────┘ │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Slide Editor (可選，進階) ─────────────────┐  │
│ │ Cover Title: [editable]                                │  │
│ │ Slide 1 Heading: [editable]  Body: [editable]         │  │
│ │ ...                                                    │  │
│ │ CTA Text: [editable]                                   │  │
│ │ [Re-render Carousel]                                   │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Carousel Viewer 組件規格

```typescript
interface CarouselViewerProps {
  slides: Array<{ url: string; index: number }>
  pdfUrl: string
}
```

| Feature | Implementation |
|---------|---------------|
| Navigation | Left/Right arrow buttons + keyboard (ArrowLeft/Right) |
| Dots | Click to jump to slide |
| Thumbnails | Click to jump; active has `ring-2 ring-accent` |
| Swipe | Optional: `framer-motion` drag gesture on mobile |
| Animation | `AnimatePresence` with x-axis slide transition between slides |
| Download All | 新 endpoint 或前端 zip（JSZip） |
| Download PDF | `<a href={pdfUrl} download>` |

#### Store

擴展 `useGenerateStore` 或新建 `useCarouselStore`（推薦後者，保持隔離）:

```typescript
interface CarouselState {
  slides: Array<{ url: string; index: number }>
  pdfUrl: string | null
  currentSlide: number
  coverTitle: string
  carouselData: CarouselExtractedData | null
  isGenerating: boolean
}
```

---

### 3.4 Automation Page (新增 — Sprint 4)

**路由**: `/automation`
**Nav icon**: `Workflow` (lucide)

#### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ p-6 max-w-5xl mx-auto space-y-6                            │
│                                                             │
│ ┌─ Header ───────────────────────────────────────────────┐  │
│ │ Workflow + "Automation"            [+ New Rule]         │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Tab bar ──────────────────────────────────────────────┐  │
│ │ [Rules]  [Scheduled]  [Publish History]                 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ── Tab: Rules ───────────────────────────────────────────   │
│                                                             │
│ ┌─ GlassCard: Rule item ────────────────────────────────┐  │
│ │ ┌─ flex items-center justify-between ───────────────┐  │  │
│ │ │ ┌─ left ──────────────────────────────────────┐   │  │  │
│ │ │ │ 🤖 Telegram → dark / story → Twitter + LI   │   │  │  │
│ │ │ │ text-sm text-white/50: "Auto-generate and    │   │  │  │
│ │ │ │ publish when receiving Telegram messages"     │   │  │  │
│ │ │ └────────────────────────────────────────────┘   │  │  │
│ │ │ ┌─ right (flex gap-2) ──────────────────────┐   │  │  │
│ │ │ │ [toggle on/off]  [Edit]  [Delete]          │   │  │  │
│ │ │ └────────────────────────────────────────────┘   │  │  │
│ │ └───────────────────────────────────────────────────┘  │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Rule item ────────────────────────────────┐  │
│ │ 🔗 Webhook → gradient / square → Threads               │  │
│ │ "Triggered by n8n workflow for HN articles"            │  │
│ │                                [toggle] [Edit] [Delete]│  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ Empty state: "No automation rules yet. Create your first    │
│ rule to auto-generate and publish content."                 │
│                                                             │
│ ── Tab: Scheduled ───────────────────────────────────────   │
│                                                             │
│ ┌─ GlassCard: Schedule List ─────────────────────────────┐  │
│ │ Table: Title | Platform | Scheduled Time | Status | Act │  │
│ │                                                        │  │
│ │ "AI 趨勢..."  │ Twitter │ Mar 29 10:00 │ Pending │ [X] │  │
│ │ "React 19..." │ LI+TW   │ Mar 29 14:00 │ Pending │ [X] │  │
│ │ "Data Eng..." │ Threads  │ Mar 28 18:00 │ ✅ Sent │     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ── Tab: Publish History ─────────────────────────────────   │
│                                                             │
│ ┌─ GlassCard: Publication Log ───────────────────────────┐  │
│ │ Table: Title | Platform | Published | Engagement        │  │
│ │                                                        │  │
│ │ "AI 趨勢..."  │ 🐦 Twitter │ Mar 28 │ 12♥ 3🔄 2💬    │  │
│ │ "React 19..." │ 💼 LinkedIn │ Mar 27 │ 45♥ 8💬        │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### New Rule Modal / Drawer

```
┌─ Create Automation Rule ─────────────────────────────────┐
│                                                           │
│ Rule Name: [________________________________]             │
│                                                           │
│ ── Trigger ──────────────────────────────────────         │
│ Source: ● Telegram Bot  ○ Webhook  ○ Manual               │
│                                                           │
│ ── Generation Settings ──────────────────────────         │
│ Theme: [dark ▼]   Format: [story ▼]                      │
│ Provider: [cli ▼]                                        │
│ Extraction: [Default ▼] (or custom config link)          │
│                                                           │
│ ── Publish Targets ──────────────────────────────         │
│ ☑ Twitter    Caption template: [______________]          │
│ ☑ LinkedIn   Caption template: [______________]          │
│ ☐ Threads    Caption template: [______________]          │
│ ☐ Instagram  Caption template: [______________]          │
│                                                           │
│ ── Schedule ─────────────────────────────────────         │
│ ● Publish immediately                                    │
│ ○ Schedule: [time picker] [timezone ▼]                   │
│                                                           │
│                              [Cancel]  [Create Rule]      │
└───────────────────────────────────────────────────────────┘
```

#### Publish Panel (在 GeneratePage + HistoryDetailPanel 中復用)

生成完成後，在 PreviewPanel 下方或旁邊出現「Publish」按鈕：

```
┌─ Publish Panel (inline, below preview) ──────────────────┐
│ Publish to:                                               │
│                                                           │
│ ☑ 🐦 Twitter                                             │
│   Caption: [Auto-generated caption, editable.........]   │
│                                                           │
│ ☐ 💼 LinkedIn                                            │
│   Caption: [Auto-generated caption, editable.........]   │
│                                                           │
│ ☐ 🧵 Threads                                             │
│                                                           │
│ ── Schedule ─────────────────────────────────────         │
│ ● Now   ○ Schedule: [datetime-local input]               │
│                                                           │
│ [Publish]                                                 │
└───────────────────────────────────────────────────────────┘
```

---

### 3.5 Analytics Page (新增 — Sprint 5)

**路由**: `/analytics`
**Nav icon**: `TrendingUp` (lucide)

#### Layout

```
┌─────────────────────────────────────────────────────────────┐
│ p-6 max-w-6xl mx-auto space-y-6                            │
│                                                             │
│ ┌─ Header ───────────────────────────────────────────────┐  │
│ │ TrendingUp + "Analytics"                               │  │
│ │ Period: [7d] [30d] [90d] [All]                         │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ Top Stats Grid (grid-cols-2 md:grid-cols-4 gap-4) ───┐  │
│ │ ┌─ GlassCard ──┐ ┌─ GlassCard ──┐                     │  │
│ │ │ Total Posts   │ │ Total Reach  │                     │  │
│ │ │ 142           │ │ 12.4K        │                     │  │
│ │ │ ↑12% vs prev │ │ ↑23% vs prev │                     │  │
│ │ └──────────────┘ └──────────────┘                     │  │
│ │ ┌─ GlassCard ──┐ ┌─ GlassCard ──┐                     │  │
│ │ │ Avg Engage   │ │ Best Theme   │                     │  │
│ │ │ 3.2%         │ │ gradient     │                     │  │
│ │ │ ↓0.5% vs prev│ │ 8.1% engage │                     │  │
│ │ └──────────────┘ └──────────────┘                     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Engagement Over Time ──────────────────────┐  │
│ │ (Line chart — use recharts or lightweight SVG)          │  │
│ │                                                        │  │
│ │     ╱╲      ╱╲                                         │  │
│ │    ╱  ╲    ╱  ╲    ╱                                   │  │
│ │   ╱    ╲──╱    ╲──╱                                    │  │
│ │  ╱                                                     │  │
│ │  Mar 1   Mar 8   Mar 15   Mar 22   Mar 28             │  │
│ │                                                        │  │
│ │  ── Likes  ── Shares  ── Comments                      │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ grid-cols-1 md:grid-cols-2 gap-4 ────────────────────┐  │
│ │ ┌─ GlassCard: By Theme ─────────┐                     │  │
│ │ │ Horizontal bar chart           │                     │  │
│ │ │ dark      ████████ 45%         │                     │  │
│ │ │ gradient  █████ 28%            │                     │  │
│ │ │ warm_sun  ███ 15%              │                     │  │
│ │ │ light     ██ 12%               │                     │  │
│ │ └───────────────────────────────┘                     │  │
│ │ ┌─ GlassCard: By Platform ──────┐                     │  │
│ │ │ Horizontal bar chart           │                     │  │
│ │ │ Twitter   ████████ 52%         │                     │  │
│ │ │ LinkedIn  █████ 31%            │                     │  │
│ │ │ Threads   ██ 17%               │                     │  │
│ │ └───────────────────────────────┘                     │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: Top Performing Posts ──────────────────────┐  │
│ │ Table: # | Title | Theme | Platform | Engagement | Date│  │
│ │                                                        │  │
│ │ 1 │ "AI 趨勢..." │ gradient │ 🐦 │ 156 engage │ 3/25 │  │
│ │ 2 │ "React 19..." │ dark    │ 💼 │ 98 engage  │ 3/22 │  │
│ │ 3 │ "Data..."     │ dark    │ 🐦 │ 67 engage  │ 3/20 │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                             │
│ ┌─ GlassCard: AI Insights ───────────────────────────────┐  │
│ │ Sparkles + "AI Insights"              [Refresh]        │  │
│ │                                                        │  │
│ │ ┌─ insight (bg-accent/5 rounded-lg p-4) ─────────────┐ │  │
│ │ │ 💡 Your gradient theme cards get 2.3x more          │ │  │
│ │ │ engagement on Twitter. Consider using it more.      │ │  │
│ │ └────────────────────────────────────────────────────┘ │  │
│ │ ┌─ insight ──────────────────────────────────────────┐  │  │
│ │ │ 📊 Best posting time: Tue/Thu 10:00-12:00 UTC+8   │  │  │
│ │ │ based on your last 30 days of data.                │  │  │
│ │ └────────────────────────────────────────────────────┘  │  │
│ │ ┌─ insight ──────────────────────────────────────────┐  │  │
│ │ │ 🏆 Tech topic cards outperform lifestyle by 45%.   │  │  │
│ │ │ Your audience prefers technical content.            │  │  │
│ │ └────────────────────────────────────────────────────┘  │  │
│ └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### Chart Library

推薦 **recharts** (React native, tree-shakeable, 44KB gzipped):
- `LineChart` for engagement over time
- `BarChart` for theme/platform breakdown
- 配色直接用 CSS variables: `var(--color-accent)`, 等

#### AI Insights 組件

```typescript
interface Insight {
  icon: string    // emoji
  title: string
  body: string
}

// API: GET /api/analytics/insights?days=30
// 返回 AI 生成的 3-5 個洞察
```

---

## 4. Responsive Strategy

### Breakpoints

| Breakpoint | Width | Behavior |
|-----------|-------|----------|
| Mobile | < 640px | Single column, sidebar hidden (hamburger) |
| Tablet | 640-1024px | Single column, sidebar collapsed (icon only) |
| Desktop | 1024-1280px | Two column where applicable, sidebar expanded |
| Large | > 1280px | Full layout, max-w containers prevent over-stretch |

### Per-Page Responsive Rules

| Page | Mobile | Tablet | Desktop |
|------|--------|--------|---------|
| Generate | Stack all vertically | Stack all | Side-by-side result (editor + preview) |
| Settings | Full width cards | Full width cards, max-w-3xl | Same as tablet |
| Carousel | Full width viewer, swipe nav | Same + thumbnails | Side viewer + editor |
| Automation | Rules stack vertically | Same | Same |
| Analytics | Stats 2-col, charts stack | Stats 4-col, charts stack | Full grid layout |

### Mobile Sidebar

```
┌─ Mobile header (md:hidden) ────────────────────────────┐
│ [☰]  imgGen                                            │
└────────────────────────────────────────────────────────┘

(Hamburger opens overlay sidebar with AnimatePresence slide-in)
```

Implementation: 已有 `useAppStore.sidebarCollapsed`，需增加 mobile overlay mode。

---

## 5. Accessibility

### Keyboard Navigation

| Page | Key | Action |
|------|-----|--------|
| All | Tab/Shift+Tab | Navigate interactive elements |
| Carousel | ArrowLeft/Right | Previous/Next slide |
| Carousel | Home/End | First/Last slide |
| Settings | Enter on key row | Expand key details |
| Analytics | Tab through charts | Focus announcements |

### ARIA Requirements

| Component | ARIA |
|-----------|------|
| Tab bar (Stats/List, Rules/Schedule) | `role="tablist"`, `role="tab"`, `aria-selected` |
| Carousel viewer | `role="region"`, `aria-roledescription="carousel"`, `aria-label="Slide X of Y"` |
| Toggle switches | `role="switch"`, `aria-checked` |
| API key password field | `aria-label="API key"`, toggle button `aria-label="Show/Hide"` |
| Status dots | `aria-label="Bot status: running"` |
| Charts | `aria-label` with text summary of data |

### Color Contrast

- 所有文字 `text-white/80` 以上在 `#090d1a` 背景上滿足 WCAG AA (4.5:1)
- `text-white/40` (用於 label) 需要搭配 `text-xs font-medium uppercase` (large text exception) 或升級到 `text-white/50`
- Status colors (`success`, `error`) 不單獨傳達信息，都搭配文字或圖標

---

## 6. Interaction Patterns

### Shared Patterns

| Pattern | Implementation | Used In |
|---------|---------------|---------|
| Collapsible section | `AnimatePresence` + `motion.div height: auto` | AdvancedOptions, HistoryDetail, Rule Editor |
| Pill group selector | `flex gap-1 bg-bg-surface rounded-lg p-1` + active state | Theme, Format, Period filters |
| Inline form | Expandable area below trigger button (not modal) | Create API Key, Create Rule |
| Copy feedback | `navigator.clipboard` + 2s Check icon | API Key, Webhook example, Image URL |
| Confirm destructive | `window.confirm()` or inline "Are you sure?" | Delete key, Delete rule |
| Loading state | `Loader2 animate-spin` centered | All async operations |
| Empty state | Centered text + icon, CTA button | All list views |
| Toast/notification | Framer Motion slide-in from top-right, auto-dismiss 3s | Save success, Publish success, Errors |

### Animation Tokens

```typescript
// 統一動畫配置
const transitions = {
  page: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
  expand: { duration: 0.3, ease: [0.16, 1, 0.3, 1] },
  fade: { duration: 0.15 },
  slide: { duration: 0.2, ease: 'easeOut' },
  stagger: { staggerChildren: 0.03 },
}
```

---

## 7. Component Inventory (New)

### Sprint 1

| Component | File | Parent |
|-----------|------|--------|
| `ExtractionSettings` | `features/generate/ExtractionSettings.tsx` | `AdvancedOptions` |
| `FileDropzone` | `features/generate/FileDropzone.tsx` | `InputTabs` |

### Sprint 2

| Component | File | Parent |
|-----------|------|--------|
| `SettingsPage` | `pages/SettingsPage.tsx` | `App routes` |
| `ApiKeysSection` | `features/settings/ApiKeysSection.tsx` | `SettingsPage` |
| `WebhookDocsSection` | `features/settings/WebhookDocsSection.tsx` | `SettingsPage` |
| `TelegramBotSection` | `features/settings/TelegramBotSection.tsx` | `SettingsPage` |
| `CopyButton` | `components/ui/CopyButton.tsx` | Shared |
| `CodeBlock` | `components/ui/CodeBlock.tsx` | Shared |

### Sprint 3

| Component | File | Parent |
|-----------|------|--------|
| `CarouselPage` | `pages/CarouselPage.tsx` | `App routes` |
| `CarouselViewer` | `features/carousel/CarouselViewer.tsx` | `CarouselPage` |
| `CarouselThumbnails` | `features/carousel/CarouselThumbnails.tsx` | `CarouselViewer` |
| `CarouselEditor` | `features/carousel/CarouselEditor.tsx` | `CarouselPage` |

### Sprint 4

| Component | File | Parent |
|-----------|------|--------|
| `AutomationPage` | `pages/AutomationPage.tsx` | `App routes` |
| `RuleList` | `features/automation/RuleList.tsx` | `AutomationPage` |
| `RuleForm` | `features/automation/RuleForm.tsx` | `AutomationPage` |
| `ScheduleList` | `features/automation/ScheduleList.tsx` | `AutomationPage` |
| `PublishHistory` | `features/automation/PublishHistory.tsx` | `AutomationPage` |
| `PublishPanel` | `features/publish/PublishPanel.tsx` | GeneratePage, HistoryDetail |

### Sprint 5

| Component | File | Parent |
|-----------|------|--------|
| `AnalyticsPage` | `pages/AnalyticsPage.tsx` | `App routes` |
| `StatCard` | `features/analytics/StatCard.tsx` | `AnalyticsPage` |
| `EngagementChart` | `features/analytics/EngagementChart.tsx` | `AnalyticsPage` |
| `BreakdownChart` | `features/analytics/BreakdownChart.tsx` | `AnalyticsPage` |
| `TopPostsTable` | `features/analytics/TopPostsTable.tsx` | `AnalyticsPage` |
| `AiInsights` | `features/analytics/AiInsights.tsx` | `AnalyticsPage` |

---

## 8. Updated Sidebar Navigation

```typescript
// Sidebar.tsx — 擴展後
const NAV_ITEMS = [
  // Primary creation flow
  { to: '/', label: 'Generate', icon: Sparkles },
  { to: '/carousel', label: 'Carousel', icon: GalleryHorizontalEnd },
  { to: '/captions', label: 'Captions', icon: MessageSquare },
  { to: '/history', label: 'History', icon: Clock },
  // Automation & analytics
  { to: '/automation', label: 'Automation', icon: Workflow },
  { to: '/analytics', label: 'Analytics', icon: TrendingUp },
  // Divider (render as <hr> when not collapsed)
  // Configuration
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/tools', label: 'Tools', icon: Wrench },
  { to: '/presets', label: 'Presets', icon: Bookmark },
]
```

Sidebar supports `divider` items:

```typescript
type NavItemType =
  | { type: 'link'; to: string; label: string; icon: LucideIcon }
  | { type: 'divider' }

const NAV_ITEMS: NavItemType[] = [
  { type: 'link', to: '/', label: 'Generate', icon: Sparkles },
  { type: 'link', to: '/carousel', label: 'Carousel', icon: GalleryHorizontalEnd },
  { type: 'link', to: '/captions', label: 'Captions', icon: MessageSquare },
  { type: 'link', to: '/history', label: 'History', icon: Clock },
  { type: 'divider' },
  { type: 'link', to: '/automation', label: 'Automation', icon: Workflow },
  { type: 'link', to: '/analytics', label: 'Analytics', icon: TrendingUp },
  { type: 'divider' },
  { type: 'link', to: '/settings', label: 'Settings', icon: Settings },
  { type: 'link', to: '/tools', label: 'Tools', icon: Wrench },
  { type: 'link', to: '/presets', label: 'Presets', icon: Bookmark },
]
```

---

## 9. Implementation Priority

| Sprint | New Pages | New Shared Components | Modified Pages |
|--------|-----------|----------------------|----------------|
| **Sprint 1** | — | `ExtractionSettings`, `FileDropzone` | GeneratePage (AdvancedOptions), PreviewPanel (HTML export) |
| **Sprint 2** | `SettingsPage` | `CopyButton`, `CodeBlock` | Sidebar (add Settings), InputTabs (file upload) |
| **Sprint 3** | `CarouselPage` | `CarouselViewer`, `CarouselThumbnails` | Sidebar (add Carousel) |
| **Sprint 4** | `AutomationPage` | `PublishPanel` | Sidebar (add Automation), GeneratePage (publish), HistoryDetailPanel (publish) |
| **Sprint 5** | `AnalyticsPage` | `StatCard`, chart components, `AiInsights` | Sidebar (add Analytics) |

---

## 10. File Structure (Final)

```
src/
├── components/
│   ├── layout/
│   │   ├── GlassCard.tsx
│   │   ├── NavItem.tsx
│   │   ├── PageTransition.tsx
│   │   └── Sidebar.tsx
│   └── ui/                          # Sprint 2 新增
│       ├── CopyButton.tsx
│       ├── CodeBlock.tsx
│       └── Toast.tsx
├── features/
│   ├── generate/
│   │   ├── AdvancedOptions.tsx
│   │   ├── ExtractionSettings.tsx   # Sprint 1
│   │   ├── ExtractedContentEditor.tsx
│   │   ├── FileDropzone.tsx         # Sprint 2.3
│   │   ├── FormatPillGroup.tsx
│   │   ├── InputTabs.tsx
│   │   ├── PreviewPanel.tsx
│   │   └── ThemePillGroup.tsx
│   ├── history/
│   │   └── HistoryDetailPanel.tsx
│   ├── settings/                    # Sprint 2
│   │   ├── ApiKeysSection.tsx
│   │   ├── WebhookDocsSection.tsx
│   │   └── TelegramBotSection.tsx
│   ├── carousel/                    # Sprint 3
│   │   ├── CarouselViewer.tsx
│   │   ├── CarouselThumbnails.tsx
│   │   └── CarouselEditor.tsx
│   ├── automation/                  # Sprint 4
│   │   ├── RuleList.tsx
│   │   ├── RuleForm.tsx
│   │   ├── ScheduleList.tsx
│   │   └── PublishHistory.tsx
│   ├── publish/                     # Sprint 4
│   │   └── PublishPanel.tsx
│   └── analytics/                   # Sprint 5
│       ├── StatCard.tsx
│       ├── EngagementChart.tsx
│       ├── BreakdownChart.tsx
│       ├── TopPostsTable.tsx
│       └── AiInsights.tsx
├── pages/
│   ├── GeneratePage.tsx
│   ├── CaptionsPage.tsx
│   ├── HistoryPage.tsx
│   ├── ToolsPage.tsx
│   ├── PresetsPage.tsx
│   ├── SettingsPage.tsx             # Sprint 2
│   ├── CarouselPage.tsx             # Sprint 3
│   ├── AutomationPage.tsx           # Sprint 4
│   └── AnalyticsPage.tsx            # Sprint 5
├── stores/
│   ├── useAppStore.ts
│   ├── useGenerateStore.ts
│   └── useCarouselStore.ts          # Sprint 3
├── api/
│   ├── client.ts
│   └── queries.ts
├── lib/
│   └── utils.ts
├── App.tsx
├── main.tsx
└── index.css
```

---

**ArchitectUX Foundation Date**: 2026-03-28
**Developer Handoff**: Ready for Sprint 1 implementation
**Next Step**: Implement Sprint 1 — ExtractionSettings component + HTML export button
