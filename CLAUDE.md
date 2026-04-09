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

## Quick Start

**環境檢查 + 完整啟動** (3 秒內):
```bash
# 1️⃣ 初次設置（一次性）
pip install -r requirements.txt
playwright install chromium
cp .env.example .env  # 複製配置（無需 API key，已完全自動化）

# 2️⃣ 啟動完整 Web UI（推薦）
# 終端 1：後端 (FastAPI @ :8001)
cd web && python -m uvicorn api:app --reload --port 8001

# 終端 2：前端 (React @ :5173，自動連接後端)
cd web/frontend && npm run dev

# ⚠️ 若港口被占用：kill -9 $(lsof -i :8001 | grep -oE '^\s*[0-9]+' | head -1)
```

**開啟瀏覽器：** http://localhost:5173

**核心頁面：**
- **Generate** — 單次圖卡生成
- **Curation** — 點擊「開始策展」觸發完整自動化管道（爬蟲 → AI 評估 → 圖卡生成 → DB 儲存）
- **Review** — 待審內容核准
- **Scheduling** — 拖拽週曆排期
- **Prompts** — 🆕 查看所有 LLM 呼叫的完整提示詞歷史記錄

---

## Commands Reference

### 🎨 CLI：單次圖卡生成（imgGen 核心）

```bash
# 基礎用法
python main.py --text "文章內容" --theme dark --format story
python main.py --url https://example.com/article --provider claude
python main.py --file article.txt --theme gradient

# 三種模式
python main.py --file notes.md --mode card --theme dark       # 卡片模式（預設）
python main.py --file notes.md --mode article --theme light   # 文章模式（結構化 3 段）
python main.py --file notes.md --mode smart --format story    # 智能模式（AI 動態佈局）
python main.py --file notes.md --mode smart --color-mood dark_tech

# 批次處理（並發控制）
python main.py --batch entries.txt --workers 3 --output-dir ./output
```

### 🔄 自動化工作流（LevelUp 系統）

**無需 API key，完全使用 Claude CLI**

```bash
# 策展（Cycle 2）— 爬蟲 → AI 評估 → 圖卡 → 儲存 DB
python scripts/daily_curation.py               # 三帳號並發 (A/B/C)
python scripts/daily_curation.py --account A   # 單帳號完整流程
python scripts/daily_curation.py --dry-run     # 乾跑：僅印出，不寫 DB

# 審核（Cycle 4）— HITL 終端審核工作流
python scripts/audit.py                        # 互動式審核 (A)pprove/(E)dit/(D)iscard/(S)kip
python scripts/audit.py --account A            # 只審帳號 A
python scripts/audit.py --batch               # 批次自動核准
python scripts/audit.py --export-md           # 匯出 Markdown（行動裝置友善審核）
python scripts/audit.py --import-md review.md # 從 Markdown 回寫 DB

# 設計循環（Cycle 3）— 自動化視覺優化
python scripts/design_review_loop.py --theme dark
python scripts/design_review_loop.py --theme dark --max-iter 3
```

### ✅ 測試

```bash
# 完整測試套件
pytest tests/ -v                               # 所有測試
pytest tests/test_config.py -v                # 單一文件
pytest tests/test_config.py::test_name -v    # 單一測試

# 虛擬環境（非必須，系統 Python 已足夠）
.venv/bin/python -m pytest tests/ -v
```

### 🌐 Web UI 開發

```bash
# 後端單獨啟動
cd web && python -m uvicorn api:app --reload --port 8001

# 前端單獨啟動
cd web/frontend && npm run dev                 # dev server @ :5173
cd web/frontend && npm run build              # 生產打包
cd web/frontend && npm run test               # 前端測試
```

### 📋 Prompt Logger（查看 LLM 呼叫記錄）

```bash
# Web UI 中查看
# 開啟 http://localhost:5173/prompts
# 左欄記錄列表、右欄完整提示詞、頂部統計卡

# CLI API 查詢
curl http://localhost:8001/api/prompts/latest?limit=50                      # 最新 50 筆記錄（不含提示詞）
curl http://localhost:8001/api/prompts/stage/extraction/extract-key-points  # 特定 stage 的完整記錄（含提示詞）
curl http://localhost:8001/api/prompts/stats/extraction/extract-key-points  # 統計（success rate、unique prompts）
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
| `src/screenshotter.py` | Async Playwright headless Chromium screenshots; detects running event loop and uses ThreadPoolExecutor for concurrent execution |
| `src/batch.py` | Async batch with `asyncio.Semaphore(workers)` concurrency control |
| `src/config.py` | TOML config system (`~/.imggenrc`) with presets + `LevelUpConfig`/`AccountConfig` for multi-account |
| `src/history.py` | SQLite (WAL mode) generation history at `~/.imggen/history.db` |
| `src/fetcher.py` | URL content fetching (Threads.net special-cased with Googlebot UA) |
| `src/caption.py` | Platform-specific social captions (Twitter/LinkedIn/Instagram) + 完整 LLM 呼叫日誌記錄 |
| `src/publisher.py` | Twitter/X posting via tweepy |
| `src/prompt_logger.py` | 🆕 完整提示詞日誌系統 — SQLite DB (`.tmp/prompts.db`)，記錄所有 LLM 呼叫的 system/user prompt、output、success/error；支持查詢、統計、匯出 |
| `src/llm_forge_reporter.py` | 可選上報層 — 將提示詞哈希 + 元數據異步上報到中央 Hub；離線隊列機制 |
| `web/api.py` | FastAPI REST + SSE backend；**Prompt Logger API** 新增 4 端點：`/api/prompts/latest`（最新記錄）、`/api/prompts/stage/{pipeline}/{stage}`（完整提示詞）、`/api/prompts/stats/{pipeline}/{stage}`（統計）、`/api/prompts/export`（JSON 匯出） |
| `web/frontend/` | React + TypeScript + Vite + TailwindCSS；**Prompts Page** 新增：`PromptsPage`（主頁面）、`PromptStatsBar`（統計卡）、`PromptLogList`（記錄列表）、`PromptDetailPanel`（完整提示詞展示） |

**LevelUp System (multi-account social automation)**

| Module | Role |
|--------|------|
| `src/content.py` | `Content` dataclass with full schema (title, body, image_path, output_path, theme, format, provider, key_points_count, etc.) + `ContentStatus` state machine (DRAFT→PENDING_REVIEW→APPROVED→PUBLISHED→ANALYZED) |
| `src/db.py` | `ContentDAO` — SQLite CRUD for Content records; auto-discovers and applies migrations from `src/migrations/`; `find_by_status()`, `find_by_id()`, `update()`, `create()` |
| `src/preflight.py` | `preflight_check(content, platforms)` — 7-rule validation before publishing (char limits, IG image, empty fields) |
| `src/scheduler.py` | `calculate_scheduled_time()`, `assign_scheduled_times()` — publish time assignment from `AccountConfig.publish_time` |
| `src/markdown_io.py` | `export_markdown()`, `parse_markdown()`, `import_markdown()` — mobile-friendly review workflow via Markdown |
| `src/scrapers/base_scraper.py` | `RawItem` dataclass + `BaseScraper` abstract base class |
| `src/scrapers/football_scraper.py` | BBC Sport RSS (10 articles) + Google News RSS for Japanese players (6 players: Mitoma, Endo, Doan, Tomiyasu, Hatate, Furuhashi) + optional API-Football (requires `API_FOOTBALL_KEY`). Sources interleaved for content diversity. |
| `src/scrapers/tech_scraper.py` | Hacker News API + TechCrunch RSS |
| `src/scrapers/pmp_scraper.py` | HBR RSS + PMI Blog RSS |
| `scripts/daily_curation.py` | Daily curation pipeline: scrape → Claude AI curation (CLI-first, no API key) → imgGen smart image → DB DRAFT; supports A/B/C parallel execution |
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

Multi-account social media automation built on imgGen. Manages three accounts (A/B/C):

```
Cycle 2 (策展)  → daily_curation.py   爬蟲 → Claude AI 評估 → imgGen 圖卡 → DB(DRAFT)
Cycle 4 (審核)  → audit.py            Markdown 審核 → 核准/編輯/棄用 → DB(APPROVED)
Cycle 3 (設計)  → design_review_loop.py 截圖 → Claude 視覺評論 → CSS 修補 → 迭代
```

**帳號配置** (`~/.imggen/accounts.toml`):
- `[account.A]` — AI 自動化 (`prompts/account_a.txt`, `dark_tech`)
- `[account.B]` — PMP 職涯 (`prompts/account_b.txt`, `clean_light`)
- `[account.C]` — 足球英文 (`prompts/account_c.txt`, `bold_contrast`)

**狀態機**：`DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ANALYZED` (或 `→ REJECTED`)

### LevelUp Web UI (Phase A-E ✅)

完全集成於後端 (`web/api.py`) 和前端 (`web/frontend/src/`)。五個階段同步完成，共 85 項測試通過。

| 階段 | 頁面 | 核心功能 |
|------|------|---------|
| **A** | ReviewPage | 待審內容核准/編輯、preflight 檢查 |
| **B** | CurationPage | **SSE 即時進度**、策展統計 |
| **C** | SchedulingPage | 週曆視圖、拖拽排期 |
| **D** | — | DRAFT 列表、狀態轉換 |
| **E** | AccountSettingsPage | 帳號配置、Prompt 編輯 |

**架構核心**:
- **Unified Response** — `ContentDetail` Pydantic 型別跨頁面共用
- **SSE Streaming** — CurationPage 即時顯示爬蟲→AI→圖卡→保存進度
- **State Management** — 4 個獨立 Zustand store (ReviewStore, CurationStore, SchedulingStore, SettingsStore)
- **TanStack Query** — 伺服器狀態同步、自動快取和重新取得

**詳見**:
- `docs/LEVELUP_IMPLEMENTATION.md` — 完整實作文件
- `web/frontend/API_GUIDE.md` — API 端點列表（6+ 端點、Request/Response 示例）
- `web/frontend/ARCHITECTURE.md` — 前端架構詳解

### Prompt Logger System 🆕

完整 LLM 呼叫追踪系統 — 所有提取、字幕生成呼叫都自動記錄完整提示詞到本地 SQLite DB，支持查詢、統計、匯出。

**架構：**
- **後端日誌** — `src/prompt_logger.py` 記錄到 `.tmp/prompts.db`
  - 表結構：`id`, `timestamp`, `pipeline_id`, `stage`, `system_prompt`, `user_prompt`, `system_hash`, `user_hash`, `model`, `provider`, `output`, `success`, `error_message`
  - 覆蓋範圍：`src/extractor.py` (extraction)、`src/caption.py` (caption-generation)
  - 自動哈希：SHA256(prompt)[:16] 便於去重和版本控制

- **API 端點** — `web/api.py` 新增 4 個公開端點
  - `GET /api/prompts/latest?limit=50` — 最新 N 筆（不含完整提示詞，快速列表）
  - `GET /api/prompts/stage/{pipeline_id}/{stage}` — 指定 stage 的完整記錄（含 system/user/output）
  - `GET /api/prompts/stats/{pipeline_id}/{stage}` — 統計（total_calls、success_rate、unique_system_prompts）
  - `POST /api/prompts/export` — 匯出為 JSON 文件

- **Web UI** — `PromptsPage` (`/prompts`)
  - **左欄**：記錄列表（時間、model、success/fail），Stage 篩選 Tab（extraction / caption）
  - **右欄**：完整提示詞展示，三個摺疊 Section（System Prompt / User Prompt / Output），Copy 按鈕
  - **頂部**：統計卡（Total Calls、Success Rate、Unique Prompts）

**使用場景：**
- 🔍 提示詞版本控制 — 追踪 system prompt 的演變
- 🐛 除錯 — 查看失敗呼叫的完整提示詞和錯誤訊息
- 📊 成本分析 — 統計 unique prompts、成功率、output 長度趨勢
- 💾 合規記錄 — 所有 LLM 呼叫的完整追踪，支持匯出供審計

**可選：LLM Forge Hub 上報**
- `src/llm_forge_reporter.py` — 異步上報提示詞哈希 + 元數據到中央 Hub（需要 `LLM_FORGE_ENABLED=true`）
- 本地記錄完整提示詞，Hub 只收集匯總統計（成本、成功率）— 隱私保護

## Automation Status ✅

**完整自動化管道**（2026-04-05 驗證，含 Token 優化）：

```
Raw Items (RSS/API) → 爬蟲 [多源聚合，10-28 items/帳號]
  Account A (Tech): Hacker News + TechCrunch
  Account B (PMP): HBR + PMI Blog
  Account C (Football): BBC Sport (10) + Japan Players (18) + API-Football (optional)
  ↓ [1-2秒/項]
AI Evaluation (Claude CLI Haiku - Batch) → 智能過濾 + URL 去重
  ↓ [should_publish=true]
Generate Image (Smart Mode: Sonnet + Playwright) → 圖卡生成
  ↓ [Card/Article: Haiku] [1-2秒/圖]
Persist to DB → Content(DRAFT) → Web UI 待審 (/api/content/review)
```

**驗證結果**：100% 成功率，Account C 已驗證 28 items → 5-23 DRAFT，~2-3 分鐘完成三帳號並發

**無需 API key** — 完全使用 Claude Code CLI，支持在任何環境（CI/CD、本地、遠端）執行

### Token Optimization Status ✅ (2026-04-05)

**已實作優化**（4/5，P0 & P1 全部完成）：

| 優化 | 說明 | 節省 | Commit |
|------|------|------|--------|
| **P0-1** Batch AI Eval | 5 個逐項呼叫 → 1 批量呼叫 + fallback | 12 calls/day (-40K tokens) | `ac21c43` |
| **P0-2** URL Dedup Cache | DB 去重檢查，跳過重複 URL | 5-10 calls/week | `570d244` |
| **P1-3** Smart Model Selection | Haiku 預設 (3x 便宜) + Sonnet 限 Smart Mode | -65% tokens | `685dd61` |
| **P1-4** Web API Cache | 24h TTL 提取快取，多格式複用 | 100% 重複 URL (0 tokens) | `685dd61` |

**模型分層策略：**
- **Haiku (預設)：** Daily curation 評估、API 圖卡生成（card/article）、批量處理 — 3x 成本優勢
- **Sonnet (保留)：** Smart Mode 動態佈局設計 — 需要複雜推理
- **Vision (可選)：** design_review_loop 圖片分析 → CLI 備用

**成本降低：** 30-52K tokens/day → 12-18K tokens/day (**↓ 65-75%**)  
**月度預估：** ~150-200K → ~40-60K tokens (**↓ 65-70%**)

## Environment Variables

| 環境變數 | 用途 | 是否必須 |
|---------|------|--------|
| `ANTHROPIC_API_KEY` | Claude API（備用，預設使用 Claude CLI） | ❌ 否 |
| `GOOGLE_API_KEY` | Gemini 抽取 | ❌ 否 |
| `OPENAI_API_KEY` | GPT 抽取 | ❌ 否 |
| `TWITTER_API_*` | Twitter 發佈（4 個金鑰） | ❌ 否 |
| `API_FOOTBALL_KEY` | 足球賽事數據（RapidAPI） | ❌ 否 |
| `TINIFY_API_KEY` | 圖像壓縮（design_review_loop） | ❌ 否 |

**預設配置**：`Claude Code CLI`（不需要任何金鑰）

---

## Development Workflow

### 🔧 修改功能

1. **分支策略** — 基於 main，命名：`feature/name` 或 `fix/description`
2. **測試優先** — 編寫測試 → 實現功能 → 驗證通過
3. **提交慣例** — `feat:` / `fix:` / `refactor:` / `docs:` / `test:`

### 📝 常見任務

| 任務 | 命令 |
|------|------|
| 添加新爬蟲 | 1. 建立 `src/scrapers/new_scraper.py` 2. 繼承 `BaseScraper` 3. 實現 `fetch()` 和多個 `_fetch_*()` 私有方法 4. 在 `fetch()` 中聚合並交錯來源（參考 `football_scraper.py`） |
| 新增 Jinja2 主題 | 1. `templates/new_theme.html` 2. 更新 `VALID_THEMES` 3. 在 `_preview` 中測試 |
| 修改資料庫結構 | 1. 建立 `src/migrations/NNN_description.sql` 2. `ContentDAO` 自動應用 3. 編寫測試驗證 |
| 後端新增端點 | 1. `web/api.py` 中新增路由 2. 定義 Pydantic Request/Response 3. 在前端 `web/frontend/src/api/queries.ts` 添加 hook |
| 前端新增頁面 | 1. `web/frontend/src/pages/NewPage.tsx` 2. 建立 `useNewStore.ts` (Zustand) 3. 路由設定 |

### 🐛 調試技巧

```bash
# 檢查後端日誌（即時）
tail -f /tmp/backend.log

# 檢查資料庫內容
sqlite3 ~/.imggen/history.db "SELECT id, account_type, source, status FROM generations WHERE account_type='C' LIMIT 10;"

# 乾跑策展（不寫 DB）
python scripts/daily_curation.py --dry-run

# 單帳號測試
python scripts/daily_curation.py --account A

# 檢查爬蟲輸出（原始）
python -c "
from src.scrapers.football_scraper import FootballScraper
s = FootballScraper()
items = s.fetch()
sources = {}
for item in items:
    sources[item.source] = sources.get(item.source, 0) + 1
print(f'總計 {len(items)} 項, 來源: {sources}')
for item in items[:3]:
    print(f'  [{item.source}] {item.title}')
"
```

---

## Troubleshooting

### ❌ 後端啟動失敗

**症狀**：`Address already in use` (port 8000/8001)

```bash
# 檢查並殺死佔用進程
ps aux | grep uvicorn
# 改用不同港口
python -m uvicorn web.api:app --port 8002
# 或修改 vite.config.ts 的 proxy 設定
```

### ❌ 前端無法連接後端

**症狀**：`ECONNREFUSED` 代理錯誤

```bash
# 1. 確認後端執行中
curl http://localhost:8001/api/meta

# 2. 檢查 vite.config.ts 港口設定
cat web/frontend/vite.config.ts | grep proxy

# 3. 前端需要後端執行才能開發
# 終端 1：後端
cd web && python -m uvicorn api:app --reload --port 8001
# 終端 2：前端（在後端啟動後）
cd web/frontend && npm run dev
```

### ❌ 資料庫遷移失敗

**症狀**：`column not found` 或 `table does not exist`

```bash
# 1. 檢查遷移檔案
ls -la src/migrations/

# 2. 驗證 DB 架構
sqlite3 ~/.imggen/history.db ".schema generations"

# 3. 重置資料庫（若開發環境）
rm ~/.imggen/history.db*
python scripts/daily_curation.py --dry-run  # 重新初始化
```

### ❌ 圖卡生成失敗

**症狀**：`Playwright timeout` 或 `blank screenshot`

```bash
# 1. 檢查 Chromium 安裝
playwright install chromium

# 2. 測試單張圖卡（除錯模式）
python -c "
from src.renderer import render_and_capture
data = {'title': 'Test', 'key_points': [{'text': 'Point 1'}]}
render_and_capture(data, 'dark', 'story')
"

# 3. 檢查 screenshotter.py 日誌
# 新增 --verbose 旗標（若支援）
```

### ❌ 策展無新內容

**症狀**：`imported 0 items` 或爬蟲空結果

```bash
# 1. 測試爬蟲原始輸出
python -c "from src.scrapers.football_scraper import FootballScraper; print(FootballScraper().fetch())"

# 2. 檢查帳號配置
cat ~/.imggen/accounts.toml | grep -A 5 "account.A"

# 3. 查看 AI 評估過濾結果（乾跑）
python scripts/daily_curation.py --account A --dry-run | grep should_publish
```

### ❌ Prompt Logger 查看為空

**症狀**：http://localhost:5173/prompts 頁面無記錄

```bash
# 1. 檢查後端是否有日誌資料
curl http://localhost:8001/api/prompts/latest

# 2. 若為空，先運行一次提取生成日誌
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "test article", "theme": "dark", "provider": "cli"}'

# 3. 驗證資料庫
ls -la .tmp/prompts.db

# 4. 檢查前端連接
# 確認後端運行於 :8001，前端 vite proxy 設定正確
cat web/frontend/vite.config.ts | grep proxy
```

---

## Resources

- **架構圖**：見 `docs/` 資料夾
- **API 完整參考**：`web/frontend/API_GUIDE.md`
- **前端元件**：`web/frontend/src/pages/` 和 `web/frontend/src/components/`
- **爬蟲列表**：`src/scrapers/` (football, tech, pmp)
- **樣板系統**：`templates/` (28 主題 + article.html)
- **Prompt Logger**：
  - Web UI：`web/frontend/src/pages/PromptsPage.tsx` + 3 個 feature 組件
  - API：`web/api.py` 的 `/api/prompts/*` 4 個端點
  - DB 層：`src/prompt_logger.py` 和 `.tmp/prompts.db`
