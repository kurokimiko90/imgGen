# LevelUp Web UI 文檔索引

**最後更新**: 2026-04-04  
**狀態**: ✅ Phase A-E 完成實裝（85 tests passing）

---

## 快速導航

### 📋 總覽文檔

| 文檔 | 位置 | 內容 |
|------|------|------|
| **完整實裝檔** | `docs/LEVELUP_IMPLEMENTATION.md` | Phase A-E 完整進度、所有新增端點、測試覆蓋 |
| **項目指南** | `CLAUDE.md` | 全项目概述、命令、環境變數、架構快速參考 |
| **原始規格** | `docs/webui_levelup_unified_spec.md` | 系統設計規格文檔（融合新舊方案） |

---

### 🎨 前端文檔

| 文檔 | 位置 | 內容 |
|------|------|------|
| **前端架構** | `web/frontend/ARCHITECTURE.md` | 頁面、Store、Hook、路由、元件樹、狀態流 |
| **API 參考** | `web/frontend/API_GUIDE.md` | 6+ 端點、Request/Response 示例、Frontend 用法模式 |
| **Sidebar 導航** | `web/frontend/src/components/layout/Sidebar.tsx` | 5 個新 nav items（Review/Curation/Scheduling/Settings） |

---

### 🔧 後端模塊

**Phase A：Review API**
- 端點: GET `/api/content/review`, POST `/api/content/{id}/approve`, PUT `/api/content/{id}` 等（6 個）
- 核心: `web/api.py` 中 Phase A 實現
- 特色: Single-HTTP-roundtrip preflight（無 force 參數）

**Phase B：Curation SSE + 統計**
- 端點: POST `/api/curation/run` (SSE), GET `/api/curation/status`, GET `/api/curation/stats`
- 改動: `scripts/daily_curation.py` 加 progress_callback（10 行）
- 特色: 實時 SSE 進度串流（item_fetched → generating_image → saved_draft）

**Phase C：Scheduling**
- 端點: GET `/api/content/scheduled`, PATCH `/api/content/{id}/reschedule`
- DAO 新增: `find_scheduled(start_date, end_date, account_type)`
- 特色: 拖拽日曆排期調整

**Phase D：Drafts 列表 + 統計**
- 端點: GET `/api/content/drafts`, PATCH `/api/content/{id}/status`
- DAO 新增: `find_drafts(account, source, days)`, `get_curation_stats()`
- 特色: 多條件篩選（帳號/來源/天數）+ 統計

**Phase E：Account Settings**
- 端點: GET/PUT `/api/accounts/{id}`, POST `/api/accounts/{id}/preview`
- Config 新增: `save_account()`, `_save()`
- 特色: Prompt 編輯、配置寫回 TOML

---

### 📱 前端頁面

| 頁面 | 文件 | 功能 |
|------|------|------|
| **ReviewPage** | `src/pages/ReviewPage.tsx` | 待審內容核准（篩選、編輯、批次） |
| **CurationPage** | `src/pages/CurationPage.tsx` | SSE 進度 + DRAFT 列表管理 |
| **SchedulingPage** | `src/pages/SchedulingPage.tsx` | 週曆拖拽排期 |
| **AccountSettingsPage** | `src/pages/AccountSettingsPage.tsx` | 帳號配置、Prompt、預覽 |

---

## 開發工作流

### 查看 API 文檔

```bash
# 查看所有端點（含 Request/Response）
cat web/frontend/API_GUIDE.md

# 查看前端架構（Store、Hook、元件）
cat web/frontend/ARCHITECTURE.md
```

### 運行應用

```bash
# 後端
cd web && uvicorn api:app --reload --port 8000

# 前端
cd web/frontend && npm run dev  # localhost:5173

# 測試
pytest tests/ -v  # 85 tests
```

### 新增功能

1. 讀 `docs/LEVELUP_IMPLEMENTATION.md` 了解已有功能
2. 參考 `web/frontend/API_GUIDE.md` 調用 API
3. 參考 `web/frontend/ARCHITECTURE.md` 設計 UI

---

## 關鍵文件樹

```
project/imgGen/
├── web/
│   ├── api.py                    # Phase A-E API 端點（150+ 行新增）
│   └── frontend/
│       ├── ARCHITECTURE.md       # ✨ 前端架構詳解
│       ├── API_GUIDE.md          # ✨ API 端點參考
│       ├── src/
│       │   ├── pages/
│       │   │   ├── ReviewPage.tsx
│       │   │   ├── CurationPage.tsx
│       │   │   ├── SchedulingPage.tsx
│       │   │   └── AccountSettingsPage.tsx
│       │   ├── stores/
│       │   │   ├── useReviewStore.ts
│       │   │   ├── useCurationStore.ts
│       │   │   ├── useSchedulingStore.ts
│       │   │   └── useSettingsStore.ts
│       │   ├── api/
│       │   │   └── queries.ts    # TanStack Query hooks
│       │   ├── components/
│       │   │   ├── layout/
│       │   │   │   └── Sidebar.tsx  # ✨ 4 個新 nav items
│       │   │   └── features/
│       │   │       ├── review/
│       │   │       ├── curation/
│       │   │       ├── scheduling/
│       │   │       └── settings/
│       │   └── App.tsx           # ✨ 4 個新路由
│       └── vite.config.ts        # Proxy: /api → :8000
│
├── src/
│   ├── content.py                # ✨ 新增 source field
│   ├── db.py                     # ✨ 新增 find_scheduled, find_drafts, get_curation_stats
│   └── config.py                 # ✨ 新增 save_account, _save
│
├── scripts/
│   └── daily_curation.py         # ✨ 新增 progress_callback（10 行改動）
│
├── docs/
│   ├── LEVELUP_IMPLEMENTATION.md # ✨ 完整實裝檔
│   ├── LEVELUP_DOCS_INDEX.md     # ✨ 本文（文檔索引）
│   └── webui_levelup_unified_spec.md  # 原規格
│
└── CLAUDE.md                      # ✨ 更新了 Web UI 部分
```

---

## 核心設計亮點

### 1️⃣ 單次 HTTP 往返

```
舊方案：核准 → ERROR → 對話 → 再核准 (force=true) ← 2 次
新方案：核准 → preflight 自動執行 ← 1 次 HTTP
```

### 2️⃣ Progress Callback

```python
# daily_curation.py 中加 10 行
def curate_for_account(..., progress_callback=None):
    for item in scraper.fetch():
        if progress_callback:
            progress_callback("item_fetched", ...)
        # ... 處理 ...
        if progress_callback:
            progress_callback("saved_draft", ...)
```

### 3️⃣ ContentDetail 統一型別

所有 5 個 API 端點返回相同結構 → 前端無需多個適配器

### 4️⃣ Per-Page Zustand Store

每個頁面獨立 store → 狀態隔離，無跨頁污染

### 5️⃣ SSE 串流化進度

```
item_fetched → generating_image → saved_draft → account_done → done
```

實時推送給 UI，用戶看到動態進度

---

## 驗收標準（✅ 全部通過）

- [x] Phase A：Review API 完成 + ReviewPage 實現
- [x] Phase B：Curation SSE 完成 + CurationPage 實現
- [x] Phase C：Scheduling API 完成 + SchedulingPage 實現
- [x] Phase D：Drafts 列表完成 + 統計完成
- [x] Phase E：Settings API 完成 + AccountSettingsPage 實現
- [x] 路由整合：5 個頁面 + Sidebar navigation
- [x] 測試：85 tests passing
- [x] 文檔：3 個新文檔 + CLAUDE.md 更新

---

## 常見問題

**Q: API 端點在哪?**  
A: `web/api.py` (後端) 或 `web/frontend/API_GUIDE.md` (參考)

**Q: 前端怎麼調用 API?**  
A: `web/frontend/src/api/queries.ts` (TanStack Query hooks)

**Q: Store 怎麼設計?**  
A: `web/frontend/ARCHITECTURE.md` (詳細說明)

**Q: SSE 怎麼用?**  
A: `web/frontend/API_GUIDE.md` → Phase B：Curation API 部分

---

## 下一步建議

1. **前端測試** — Vitest + React Testing Library
2. **E2E 測試** — Playwright 完整流程測試
3. **性能優化** — Code-splitting、React Query 快取策略
4. **移動適配** — 響應式設計優化
5. **多語言** — i18n 國際化

---

*文檔由 LevelUp Phase A-E 實裝完成後自動生成*  
*所有相關文檔均在本索引中列出*
