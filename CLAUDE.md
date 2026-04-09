# CLAUDE.md

## 語言要求
**始終使用繁體中文回覆。**

## 項目概述

**imgGen** — 文章 → AI 摘取 → HTML 圖卡 → Playwright 截圖管道。三種渲染模式：
- **card**（預設）：Jinja2 靜態模板，28 主題
- **article**：結構化 3 段文章格式
- **smart**：Claude 動態生成 HTML+CSS，每張卡片獨立設計

**LevelUp Web UI**（Phase A-E ✅）— 多帳號社交媒體自動化全棧介面。

---

## 快速啟動

```bash
pip install -r requirements.txt && playwright install chromium
cp .env.example .env

# 後端 (FastAPI @ :8001)
cd web && python -m uvicorn api:app --reload --port 8001

# 前端 (React @ :5173)
cd web/frontend && npm run dev
```

---

## 常用命令

```bash
# 單次圖卡生成
python main.py --text "內容" --theme dark --format story
python main.py --file article.txt --mode smart --color-mood dark_tech

# 自動化工作流
python scripts/daily_curation.py              # 三帳號並發
python scripts/daily_curation.py --account A --dry-run
python scripts/audit.py                       # 互動審核
python scripts/design_review_loop.py --theme dark

# 測試
pytest tests/ -v
pytest tests/test_config.py::test_name -v
```

---

## 架構

```
Input → src/extractor.py → src/renderer.py → src/screenshotter.py → output/
```

### 核心模組

| 模組 | 職責 |
|------|------|
| `main.py` | CLI 入口（preset, history, watch, digest） |
| `src/pipeline.py` | 協調 extract→render→screenshot，支持三種 mode |
| `src/extractor.py` | 多 provider AI 摘取（Claude/Gemini/GPT） |
| `src/renderer.py` | Jinja2 渲染（28 主題 × 4 格式） |
| `src/smart_renderer.py` | AI 動態佈局生成 |
| `src/screenshotter.py` | Playwright 非同步截圖 |
| `src/batch.py` | 並發批次（asyncio.Semaphore） |
| `src/config.py` | TOML 配置（`~/.imggenrc`）+ 多帳號 |
| `src/db.py` | ContentDAO SQLite CRUD，自動遷移 |
| `src/content.py` | Content dataclass + 狀態機 |
| `src/prompt_logger.py` | LLM 呼叫完整日誌（`.tmp/prompts.db`） |
| `src/scrapers/` | football / tech / pmp 爬蟲 |
| `web/api.py` | FastAPI REST + SSE |
| `web/frontend/` | React 19 + Zustand + TanStack Query |

### LevelUp 自動化流程

```
Cycle 2: RSS爬蟲 → Claude批量評估 → imgGen圖卡 → DB(DRAFT)
Cycle 3: 截圖 → Claude視覺分析 → CSS修補 → 迭代
Cycle 4: Markdown審核 → 核准/編輯/棄用 → DB(APPROVED)
```

---

## 文件夾規範

```
imgGen/
├── src/              核心 Python 模組（含 scrapers/, migrations/）
├── scripts/          自動化腳本（daily_curation, audit, design_review_loop）
├── tests/            所有測試文件
├── templates/        Jinja2 HTML 模板（28 主題）
├── prompts/          LLM prompt 文字檔
├── web/              FastAPI 後端 + React 前端
│   └── frontend/src/ components/, features/, pages/, stores/
├── output/           生成圖片（.gitignore，只保留 .gitkeep）
├── docs/             所有文件（見下方）
│   ├── architecture/ 系統設計、UX、擴展規劃
│   ├── guides/       用戶指南（Smart Mode、Prompt Logger 等）
│   ├── prd/          產品需求文件
│   ├── planning/     計畫、Backlog
│   ├── reports/      實作報告、狀態報告
│   ├── roadmaps/     各 Cycle 路線圖
│   └── specs/        Cycle 規格、Web UI 規格
└── .tmp/             本地臨時數據（.gitignore，含 prompts.db）
```

**規範：**
- 新文件 → 依類型放對應 `docs/` 子目錄
- 測試腳本 → 一律放 `tests/`
- `output/` → 不提交圖片，只保留 `.gitkeep`
- secrets → 只放 `.env`，不提交

---

## 環境變數

| 變數 | 用途 | 必須 |
|------|------|------|
| `ANTHROPIC_API_KEY` | Claude API（備用） | ❌ |
| `GOOGLE_API_KEY` | Gemini 摘取 | ❌ |
| `OPENAI_API_KEY` | GPT 摘取 | ❌ |
| `TWITTER_API_*` | Twitter 發佈 | ❌ |
| `API_FOOTBALL_KEY` | 足球賽事數據 | ❌ |

預設使用 Claude Code CLI，**無需任何 API key**。

---

## 開發規範

| 任務 | 做法 |
|------|------|
| 新增爬蟲 | 繼承 `BaseScraper`，放 `src/scrapers/` |
| 新增主題 | `templates/new_theme.html` + 更新 `VALID_THEMES` |
| 修改 DB 結構 | 建立 `src/migrations/NNN_description.sql` |
| 新增後端端點 | `web/api.py` + `web/frontend/src/api/queries.ts` |
| 新增前端頁面 | `pages/NewPage.tsx` + `useNewStore.ts` + 路由 |

**提交格式：** `feat:` / `fix:` / `refactor:` / `docs:` / `test:`

---

## 常見問題

```bash
# 端口被占用
kill -9 $(lsof -ti :8001)

# 前端無法連接後端
curl http://localhost:8001/api/meta

# 資料庫重置（開發環境）
rm ~/.imggen/history.db* && python scripts/daily_curation.py --dry-run

# Playwright 截圖失敗
playwright install chromium

# 查看 Prompt 日誌
curl http://localhost:8001/api/prompts/latest
```

---

## 參考文件

- `docs/guides/SMART_MODE_GUIDE.md` — Smart Mode 完整說明
- `docs/guides/PROMPT_LOGGER_GUIDE.md` — Prompt Logger 使用指南
- `docs/reports/LEVELUP_IMPLEMENTATION.md` — LevelUp 實作細節
- `web/frontend/API_GUIDE.md` — API 端點完整參考
- `web/frontend/ARCHITECTURE.md` — 前端架構詳解
