# CLAUDE.md

**始終使用繁體中文回覆。**

## 項目

**imgGen** — 文章 → AI 摘取 → HTML 圖卡 → Playwright 截圖。
四種 mode：`card`（Jinja2 靜態，35 主題）、`article`（3 段）、`smart`（Claude 動態 HTML，30 palette）、`carousel`（1 篇 → 3-7 張）。

批次評估走 **Gemini 2.5 Flash**（`GOOGLE_API_KEY`），生圖走 Claude API/CLI（`ANTHROPIC_API_KEY` 可選）。

## 三條使用路徑

| 路徑 | 腳本 | 適合 |
|---|---|---|
| 手動單篇 | `main.py -u URL --mode smart` | 測試/快速出圖 |
| 自動化舊版 | `scripts/daily_curation.py` | 量大，質量一般 |
| v2 精品管道 | `scripts/curate_v2.py` + `scripts/generate_images_v2.py` | 發佈用（>=8 分才存） |

詳細架構見 `docs/architecture/V2_PIPELINE.md`。

## 核心模組

| 模組 | 職責 |
|---|---|
| `main.py` | CLI 入口 |
| `src/pipeline.py` | extract→render→screenshot 協調 |
| `src/extractor.py` | 多 provider AI 摘取（預設 Haiku CLI） |
| `src/renderer.py` | Jinja2 靜態渲染（35 主題） |
| `src/smart_renderer.py` | Claude 動態 HTML 生成（預設 Haiku API） |
| `src/screenshotter.py` | Playwright 截圖 |
| `src/db.py` | ContentDAO SQLite |
| `src/scrapers/` | AI / football / pmp 爬蟲 |
| `src/curation_v2/` | v2 三階段管道模組 |
| `scripts/curate_v2.py` | v2 端到端（爬→篩→寫→審→存DB） |
| `scripts/generate_images_v2.py` | v2 APPROVED 內容 → 圖片 |
| `web/api.py` | FastAPI REST + SSE |

## 目錄規範

```
src/         核心模組（含 scrapers/, curation_v2/, migrations/）
scripts/     自動化腳本
templates/   Jinja2 主題（35 個）
prompts/     LLM prompt（含 v2/）
web/         FastAPI + React
docs/        {architecture, guides, prd, planning, reports, roadmaps, specs}
output/      生成圖片（gitignore）
.tmp/        本地臨時數據
```

## 新增 X 時放哪

| 任務 | 做法 |
|---|---|
| 新增爬蟲 | 繼承 `BaseScraper`，放 `src/scrapers/` |
| 新增主題 | `templates/new_theme.html` + 更新 `VALID_THEMES` |
| 改 DB schema | 建 `src/migrations/NNN_description.sql` |
| 新增 API 端點 | `web/api.py` + `web/frontend/src/api/queries.ts` |

## v2 管道重點

**Stage 1** Gemini Flash — 批次篩選（30 篇 = 1 次呼叫）→ depth_tier 1/3/5/7
**Stage 2** Claude Sonnet — 單篇寫作，輸出 `title/body/key_points`（存入 DB reasoning）
**Stage 3** Gemini Flash — 7 維度評審，>=8 分才 APPROVE
**Loop** Sonnet — 不過則重寫一次

生圖時從 DB 取 `key_points` 直接渲染，跳過 extract() CLI 呼叫。

**帳號配色：** A → `warm_earth`，B → `clean_light`，C → `bold_contrast`

詳細見：
- `docs/architecture/V2_PIPELINE.md` — 架構 + LLM 呼叫次數 + 成本
- `docs/guides/C_ACCOUNT_TUNING.md` — C 帳號足球爬蟲 + 調優記錄
- `docs/guides/DEPTH_TIER_GUIDE.md` — depth_tier 動態 carousel 分配
- `docs/guides/SMART_MODE_GUIDE.md` — palette 自動載入 + carousel role prompt

## 啟動

```bash
pip install -r requirements.txt && playwright install chromium
cd web && python -m uvicorn api:app --reload --port 8001
cd web/frontend && npm run dev
```

常用：
```bash
python scripts/curate_v2.py --account A          # v2 爬→審→存DB
python scripts/generate_images_v2.py             # APPROVED 內容生圖
python scripts/daily_curation.py --account A     # 舊版並發
python scripts/daily_curation.py --no-image      # 只評分
pytest tests/ -v
```

## 提交格式

`feat:` / `fix:` / `refactor:` / `docs:` / `test:` / `chore:` / `perf:`

詳細文檔在 `docs/` — 需要時用 Glob/Read 自己找。
