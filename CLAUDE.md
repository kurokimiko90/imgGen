# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Communication Language

**始終使用繁體中文回覆**。所有回應、解釋、說明一律以繁體中文撰寫。

## Project Overview

**imgGen** — Article-to-image card pipeline: extracts key points from articles using AI (Claude/Gemini/GPT), renders them into styled HTML cards via Jinja2 templates or AI-driven dynamic layouts, then screenshots with Playwright. Three rendering modes:
- **Card mode** (default): Static Jinja2 templates with 28 predefined themes
- **Article mode**: Condensed prose with sections (3 paragraphs structured format)
- **Smart mode**: AI-generated dynamic HTML+CSS layouts tailored to each content (like designing a PPT slide)

No AI image generation — uses HTML+CSS for stable, text-accurate visual output.

**LevelUp Web UI** (Phase A-E ✅ Complete) — Full-stack web interface for multi-account social media automation:
- **Phase A**: Review API + ReviewPage (待審內容核准工作流)
- **Phase B**: Curation SSE + CurationPage (實時策展進度)
- **Phase C**: Scheduling API + SchedulingPage (拖拽視覺化排期)
- **Phase D**: Drafts 列表 + 統計
- **Phase E**: Account Settings API + SettingsPage (帳號配置管理)
- **Backend**: FastAPI (6+ 端點 + SSE 串流) | **Frontend**: React 19 + Zustand + TanStack Query

## Commands

```bash
# Setup
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # Add API keys

# Run CLI (imgGen core)
python main.py --text "article text" --theme dark --format story
python main.py --url https://example.com/article --provider claude
python main.py --file article.txt --theme gradient
python main.py --file notes.md --mode article --theme light   # Article mode (3 sections)
python main.py --file notes.md --mode smart --format story    # Smart mode (AI dynamic layout)
python main.py --file notes.md --mode smart --color-mood dark_tech
python main.py --batch entries.txt --workers 3 --output-dir ./output

# Design Review Loop (Cycle 3)
python scripts/design_review_loop.py --theme dark
python scripts/design_review_loop.py --theme dark --max-iter 3

# LevelUp curation (Cycle 2)
python scripts/daily_curation.py               # 三帳號並發策展
python scripts/daily_curation.py --account A   # 單帳號
python scripts/daily_curation.py --dry-run     # 不寫 DB，僅印出草稿

# LevelUp audit (Cycle 4)
python scripts/audit.py                        # 互動式審核
python scripts/audit.py --account A            # 只審帳號 A
python scripts/audit.py --batch               # 批次自動核准
python scripts/audit.py --export-md           # 匯出 review.md
python scripts/audit.py --import-md review.md # 從 Markdown 回寫 DB

# Tests
.venv/bin/python -m pytest tests/ -v          # 全部（需 venv）
pytest tests/ -v                               # system Python（略過 scrapers）
pytest tests/test_config.py -v                # 單一測試文件
pytest tests/test_config.py::test_name        # 單一測試

# Web UI (LevelUp Phase A-E)
cd web && uvicorn api:app --reload --port 8000           # Backend (FastAPI, Phase A-E API endpoints)
cd web/frontend && npm run dev                           # Frontend (React dev server, localhost:5173)
cd web/frontend && npm run build                         # Build production bundle
cd web/frontend && npm run test                          # Run tests

# API Documentation
# Review API (Phase A):     POST/GET /api/content/*
# Curation API (Phase B):   POST /api/curation/run (SSE stream)
# Scheduling API (Phase C): GET/PATCH /api/content/scheduled
# Drafts/Stats (Phase D):   GET /api/content/drafts, GET /api/curation/stats
# Settings API (Phase E):   GET/PUT /api/accounts/*
# See web/frontend/API_GUIDE.md for complete endpoint reference
```

## Architecture

### Pipeline: Extract → Render → Screenshot

```
Input (--text / --file / --url / --batch)
  → src/extractor.py    Claude/Gemini/GPT extracts JSON: {title, key_points[], source, theme_suggestion}
  → src/renderer.py     Jinja2 renders HTML card from templates/ with theme + format
  → src/screenshotter.py Playwright screenshots HTML → PNG/WebP in output/
```

`src/pipeline.py` orchestrates the three stages. Each stage is independently callable — `extract()` returns JSON, `render_and_capture()` accepts pre-extracted data. This enables re-rendering, digest synthesis, and batch processing without re-extraction.

### Key Modules

**imgGen Core**

| Module | Role |
|--------|------|
| `main.py` | Click CLI with subcommands (preset, history, watch, digest) |
| `src/pipeline.py` | Orchestrates extract → render → screenshot; supports three modes (card, article, smart); `PipelineOptions` dataclass with `mode`, `color_mood` |
| `src/extractor.py` | Multi-provider AI extraction with `ExtractionConfig` dataclass; handles card/article/smart modes |
| `src/renderer.py` | Jinja2 template rendering (28 themes, 4 formats), watermark embedding, format sizing |
| `src/smart_renderer.py` | AI-driven dynamic layout generation (Claude generates bespoke HTML+CSS per content); exports `COLOR_PALETTES`, `LAYOUT_PATTERNS` |
| `src/screenshotter.py` | Async Playwright headless Chromium screenshots |
| `src/batch.py` | Async batch with `asyncio.Semaphore(workers)` concurrency control |
| `src/config.py` | TOML config system (`~/.imggenrc`) with presets + `LevelUpConfig`/`AccountConfig` for multi-account |
| `src/history.py` | SQLite (WAL mode) generation history at `~/.imggen/history.db` |
| `src/fetcher.py` | URL content fetching (Threads.net special-cased with Googlebot UA) |
| `src/caption.py` | Platform-specific social captions (Twitter/LinkedIn/Instagram) |
| `src/publisher.py` | Twitter/X posting via tweepy |
| `web/api.py` | FastAPI REST + SSE backend; `/api/meta` includes `modes`, `color_moods`, `layout_patterns` |
| `web/frontend/` | React + TypeScript + Vite + TailwindCSS |

**LevelUp System (multi-account social automation)**

| Module | Role |
|--------|------|
| `src/content.py` | `Content` dataclass + `ContentStatus` state machine (DRAFT→PENDING_REVIEW→APPROVED→PUBLISHED→ANALYZED) |
| `src/db.py` | `ContentDAO` — SQLite CRUD for Content records; `find_by_status()`, `find_by_id()`, `update()`, `create()` |
| `src/preflight.py` | `preflight_check(content, platforms)` — 7-rule validation before publishing (char limits, IG image, empty fields) |
| `src/scheduler.py` | `calculate_scheduled_time()`, `assign_scheduled_times()` — publish time assignment from `AccountConfig.publish_time` |
| `src/markdown_io.py` | `export_markdown()`, `parse_markdown()`, `import_markdown()` — mobile-friendly review workflow via Markdown |
| `src/scrapers/base_scraper.py` | `RawItem` dataclass + `BaseScraper` abstract base class |
| `src/scrapers/football_scraper.py` | BBC Sport RSS + optional API-Football (requires `API_FOOTBALL_KEY`) |
| `src/scrapers/tech_scraper.py` | Hacker News API + TechCrunch RSS |
| `src/scrapers/pmp_scraper.py` | HBR RSS + PMI Blog RSS |
| `scripts/daily_curation.py` | Daily curation pipeline: scrape → Claude AI curation → imgGen image → DB DRAFT |
| `scripts/audit.py` | HITL terminal review system: A/E/D/S/Q interactive + `--batch` + `--export-md`/`--import-md` |
| `scripts/design_review_loop.py` | Automated design review: screenshot → Claude visual analysis → CSS patch → iterate (max 5×) |

### Template System

35 Jinja2 HTML templates in `templates/`. Four output formats with 430px base width:
- **story** (430x764) — Instagram Story / TikTok
- **square** (430x430) — Social feed
- **landscape** (430x242) — Web/email header
- **twitter** (430x215) — Twitter card

**Available themes (28):**

| Category | Themes |
|----------|--------|
| Core | dark, light, gradient, warm_sun, cozy |
| Content | hook, quote, quote_dark, editorial, thread_card |
| Data/Visual | data_impact, stats, luxury_data, paper_data |
| Comparison | versus, soft_versus, pop_split, before_after |
| Layout | studio, broadsheet, pastel, ai_theater |
| Light variants | bulletin_hook, gallery_quote, trace |
| High-impact | ranking, concept, picks |
| Opinion/Info | opinion, checklist, faq, milestone |

Additionally: `article.html` is a special template for `--mode article` that supports the 5 core themes (dark, light, gradient, warm_sun, cozy) via `data-theme` CSS attribute selector. `digest.html` and `dark_card.html` exist as standalone templates.

Templates use CSS variables for design tokens, fadeUp animations with stagger, and Jinja2 conditionals for format-aware rendering. Variables: `title`, `key_points`, `sections`, `source`, `format`, `watermark_data`, `brand_name`, `thread_index`, `thread_total`.

### Smart Mode: AI-Driven Dynamic Layouts

Smart mode (`--mode smart`) generates bespoke HTML+CSS for each piece of content using Claude API, eliminating template constraints. Key characteristics:

**Color Palettes (5 curated options):**
- `dark_tech` — dark blue, tech-forward (news, tech analysis)
- `warm_earth` — warm browns, organic feel (lifestyle, wellness)
- `clean_light` — minimal whites/blues, editorial
- `bold_contrast` — high contrast oranges/blacks, punch
- `soft_pastel` — soft pinks/purples, gentle aesthetic

**Layout Patterns (7 options):**
- `hero_list` — Hero section for main point, supporting list below
- `grid` — Equal-weight 2-column or stacked card grid
- `timeline` — Vertical timeline with sequence/progression
- `comparison` — Side-by-side or stacked contrasting sections
- `quote_centered` — Large centered quote with minimal layout
- `data_dashboard` — Data-forward with large stats and progress indicators
- `numbered_ranking` — Ranked list with emphasized first item

**Design System:**
- Shared CSS foundation: responsive typography (clamp), design tokens, fadeUp animations
- Fonts: `Outfit` (Latin), `Noto Sans TC` (Chinese)
- Exact canvas sizing, overflow hidden, no JavaScript
- All colors sourced from CSS variables (no hardcoded colors)

Smart mode auto-selects layout pattern and color mood based on content type (news, opinion, howto, data, comparison, quote, timeline, ranking). Each output is uniquely optimized like a PPT slide design.

### Extraction Output Schema

**Card mode** (default `--mode card`):
```json
{
  "title": "15-char max title",
  "key_points": [{"text": "30-50 char point"}],
  "source": "source or empty string",
  "theme_suggestion": "any valid theme name (see Template System)"
}
```

**Article mode** (`--mode article`):
```json
{
  "title": "15-char max title",
  "sections": [{"heading": "4-8 char heading", "body": ["point 1", "point 2"]}],
  "source": "source or empty string",
  "theme_suggestion": "any valid theme name (see Template System)"
}
```

**Smart mode** (`--mode smart`):
```json
{
  "title": "Concise content title",
  "key_points": [
    {"text": "First point", "importance": 1.0},
    {"text": "Second point", "importance": 0.8}
  ],
  "content_type": "news|opinion|howto|data|comparison|quote|timeline|ranking",
  "layout_hint": "hero_list|grid|timeline|comparison|quote_centered|data_dashboard|numbered_ranking",
  "color_mood": "dark_tech|warm_earth|clean_light|bold_contrast|soft_pastel",
  "source": "source or empty string"
}
```

Configurable via `ExtractionConfig`: language (zh-TW default), tone, max/min points, char limits, custom instructions, mode (card/article/smart).

### LevelUp System Architecture

LevelUp is a multi-account social media automation layer built on top of imgGen. It manages three accounts (A/B/C) through a complete pipeline:

```
Scraper (Cycle 2)
  → daily_curation.py   fetch raw items → Claude AI decides → imgGen card → Content(DRAFT) → DB

HITL Review (Cycle 4)
  → audit.py            PENDING_REVIEW → (A)pprove / (E)dit / (D)iscard / (S)kip
                        preflight_check → calculate_scheduled_time → Content(APPROVED)

Design Review (Cycle 3)
  → design_review_loop.py  screenshot → Claude visual critique → CSS patch → iterate
```

**Account config**: `~/.imggen/accounts.toml` — three `[account.X]` sections with `platforms`, `publish_time`, `color_mood`, `prompt_file`, `tone`.

**Prompt files**: `prompts/account_a.txt` (AI 自動化, dark_tech), `prompts/account_b.txt` (PMP 職涯, clean_light), `prompts/account_c.txt` (足球英文, bold_contrast).

**State machine**: `DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ANALYZED` (also `DRAFT/PENDING_REVIEW → REJECTED`).

### LevelUp Web UI: Full-Stack Implementation (Phase A-E)

**Backend** (`web/api.py`)

| Phase | Endpoints | Features |
|-------|-----------|----------|
| **A** | `GET /api/content/review` | 篩選待審內容（DRAFT/PENDING_REVIEW） |
| | `POST /api/content/{id}/approve` | 單次往返 preflight 檢查 |
| | `POST /api/content/{id}/reject` | 捨棄內容 |
| | `PUT /api/content/{id}` | 編輯標題/內文 |
| | `POST /api/content/batch` | 批次核准/捨棄 |
| **B** | `POST /api/curation/run` | SSE 串流化進度（爬蟲→AI→圖卡→保存） |
| | `GET /api/curation/status` | 查詢策展狀態 |
| | `GET /api/curation/stats` | 今日/週統計 + 通過率 |
| **C** | `GET /api/content/scheduled` | 日期範圍排程查詢 |
| | `PATCH /api/content/{id}/reschedule` | 拖拽調整發布時間 |
| **D** | `GET /api/content/drafts` | DRAFT 列表（帳號/來源/天數篩選） |
| | `PATCH /api/content/{id}/status` | 狀態轉換（DRAFT → PENDING_REVIEW） |
| **E** | `GET/PUT /api/accounts/{id}` | 讀寫帳號配置 |
| | `POST /api/accounts/{id}/preview` | 預覽圖卡生成 |

**Core Concepts**:
- `ContentDetail` Pydantic 統一型別（所有頁面共用）
- Single-HTTP-roundtrip preflight（無 `force` 參數，核准直接判定）
- Progress callback pattern（daily_curation.py 中 10 行改動）
- SSE streaming（實時 UI 更新）

**Frontend** (`web/frontend/src/`)

| 頁面 | Store | 功能 |
|------|-------|------|
| **ReviewPage** | `useReviewStore` | 待審內容篩選、核准/編輯/批次操作 |
| **CurationPage** | `useCurationStore` | SSE 進度動態、DRAFT 列表管理 |
| **SchedulingPage** | `useSchedulingStore` | 週曆視圖、拖拽排期、時間調整 |
| **AccountSettingsPage** | `useSettingsStore` | 帳號配置編輯、Prompt 編輯、預覽 |
| **DashboardPage** | — | 統計儀表板（已存在） |

**State Management**:
- Zustand stores (4 pages, isolated per page)
- TanStack Query (server state, caching, refetch)
- React 19 + Framer Motion (page transitions)

**API Query Hooks** (`api/queries.ts`):
- Phase A: `useReviewContent`, `useApproveContent`, `useRejectContent`, `useEditContent`, `useBatchAction`
- Phase B: `useCurationStatus`, `useCurationStats`
- Phase C: `useScheduledRange`, `useReschedule`
- Phase D: `useDrafts`, `useUpdateContentStatus`
- Phase E: `useAccountPrompt`, `useUpdateAccount`, `useAccountPreview`

**Key Architecture Decisions**:
1. **Unified ContentDetail** — Same response type across Review/Scheduling/Curation pages (no adapter logic in frontend)
2. **Single-roundtrip approval** — Backend executes preflight automatically, returns `{status: "OK"|"WARNING"|"ERROR", warnings[]}`
3. **Progress callback** — Minimal backend change (10 lines) for real-time SSE streaming via `progress_callback` parameter
4. **Per-page Zustand stores** — Each page manages its own UI state (filters, selections, modals) independently
5. **Drag-and-drop scheduling** — ISO datetime extraction from ContentDetail, drop triggers PATCH reschedule

**Documentation**:
- `docs/LEVELUP_IMPLEMENTATION.md` — 完整實作檔 (Phase A-E, 85 tests passing)
- `web/frontend/ARCHITECTURE.md` — 前端架構詳解 (Store 設計、元件樹、路由)
- `web/frontend/API_GUIDE.md` — API 參考 (6+ 端點、Request/Response 示例、Frontend 用法)

## Environment Variables

**imgGen core** — Required: `ANTHROPIC_API_KEY` (Claude provider). Optional: `GOOGLE_API_KEY` (Gemini), `OPENAI_API_KEY` (GPT), `TWITTER_API_KEY`/`TWITTER_API_SECRET`/`TWITTER_ACCESS_TOKEN`/`TWITTER_ACCESS_SECRET` (publishing).

**LevelUp** — Optional: `API_FOOTBALL_KEY` (RapidAPI, for football fixture data), `TINIFY_API_KEY` (image compression in design_review_loop).
