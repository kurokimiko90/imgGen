# CLAUDE.md

**始終使用繁體中文回覆。**

## 項目

**imgGen** — 文章 → AI 摘取 → HTML 圖卡 → Playwright 截圖。四種模式：`card`（Jinja2 靜態，28 主題）、`article`（3 段結構）、`smart`（Claude 動態 HTML+CSS）、`carousel`（1 篇 → 3-7 張輪播）。附 **LevelUp Web UI**（多帳號社交自動化，FastAPI + React 19）。

預設走 Claude Code CLI，**無需任何 API key**。`.env` 內所有 key 皆可選。

## 核心模組

| 模組 | 職責 |
|---|---|
| `main.py` | CLI 入口 |
| `src/pipeline.py` | 協調 extract→render→screenshot；`run_carousel_pipeline` 並行渲染 |
| `src/extractor.py` | 多 provider AI 摘取（Claude/Gemini/GPT，預設 Haiku） |
| `src/renderer.py` | Jinja2 靜態渲染（28 主題 × 4 格式） |
| `src/smart_renderer.py` | Claude 動態佈局生成（預設 Sonnet） |
| `src/screenshotter.py` | Playwright 非同步截圖 |
| `src/config.py` | TOML 配置 + 多帳號（`~/.imggen/accounts.toml`） |
| `src/db.py` | ContentDAO SQLite，自動遷移 |
| `src/content.py` | Content dataclass + 狀態機 |
| `src/scrapers/` | AI / football / pmp / tech 爬蟲 |
| `scripts/daily_curation.py` | 三帳號並發：爬 → 批次評估 → 生圖 → DRAFT |
| `scripts/elite_review.py` | 2-agent 並行審查 + 學習回路 |
| `web/api.py` | FastAPI REST + SSE |
| `web/frontend/` | React 19 + Zustand + TanStack Query |

## 目錄規範

```
src/         核心模組（含 scrapers/, migrations/）
scripts/     自動化腳本
tests/       所有測試
templates/   Jinja2 主題
prompts/     LLM prompt 文字檔（含 agents/）
web/         FastAPI + React
docs/        {architecture, guides, prd, planning, reports, roadmaps, specs}
output/      生成圖片（gitignore，只保 .gitkeep）
.tmp/        本地臨時數據（含 prompts.db）
```

- 新文件依類型放對應 `docs/` 子目錄
- secrets 只放 `.env`，永不提交
- 測試一律放 `tests/`

## 新增 X 時放哪

| 任務 | 做法 |
|---|---|
| 新增爬蟲 | 繼承 `BaseScraper`，放 `src/scrapers/` |
| 新增主題 | `templates/new_theme.html` + 更新 `VALID_THEMES` |
| 改 DB schema | 建 `src/migrations/NNN_description.sql` |
| 新增 API 端點 | `web/api.py` + `web/frontend/src/api/queries.ts` |
| 新增前端頁面 | `pages/NewPage.tsx` + `useNewStore.ts` + 路由 |

## 重要特性

### depth_tier 動態 Carousel 分配（P8，2026-04-10）
批次評估時，Claude 判斷內容深度（tier=1/3/5/7），自動決定輪播圖 slides 數：
- **tier=1** → 1 slide（事件快訊）
- **tier=3** → 3 slides（觀點論述）
- **tier=5** → 5 slides（系統教學）

見 `prompts/account_X.txt` 的 `depth_reason` 與 `depth_tier` 欄位。輸出時自動列印 tier 分佈，便於監控 AI 判斷穩定度。

**CLI override：** `--carousel --slides N` 強制所有文章走同一 slides 數。

## 啟動

```bash
pip install -r requirements.txt && playwright install chromium
cd web && python -m uvicorn api:app --reload --port 8001   # 後端 :8001
cd web/frontend && npm run dev                              # 前端 :5173
```

常用：
```bash
python scripts/daily_curation.py [--account A|B|C]          # 三帳號並發（tier-driven）
python scripts/daily_curation.py --account A --dry-run      # 純評估，無 AI 呼叫（fixture）
python scripts/daily_curation.py --account A --no-image     # 跳過圖片，省 60% token
python scripts/daily_curation.py --account A --carousel --slides 5  # 強制 5-slide carousel
pytest tests/ -v                                             # 測試
```

## 提交格式

`feat:` / `fix:` / `refactor:` / `docs:` / `test:` / `chore:` / `perf:`

詳細文檔在 `docs/` — 需要時用 Glob/Read 自己找。
