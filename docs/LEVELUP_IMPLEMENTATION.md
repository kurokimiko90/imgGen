# LevelUp Web UI 實作完成檔

**日期**: 2026-04-04  
**狀態**: ✅ Phase A-E 全部完成、測試通過（85 tests）  
**技術棧**: Python FastAPI + React 19 + Zustand + TanStack Query + Tailwind CSS 4

---

## 實作進度

| Phase | 功能 | 後端 | 前端 | 測試 | 狀態 |
|-------|------|------|------|------|------|
| **A** | Review API + ReviewPage | ✅ | ✅ | ✅ | 完成 |
| **B** | Curation SSE + CurationPage | ✅ | ✅ | ✅ | 完成 |
| **C** | Scheduling API + SchedulingPage | ✅ | ✅ | ✅ | 完成 |
| **D** | Drafts 列表 + 統計 | ✅ | ✅ | ✅ | 完成 |
| **E** | Account Settings API + SettingsPage | ✅ | ✅ | ✅ | 完成 |

---

## 後端實現（web/api.py + src/）

### Phase A：Review API（6 個端點）

```python
GET    /api/content/review           # 待審內容列表（可多狀態篩選）
GET    /api/content/{id}/detail      # 單篇詳情
POST   /api/content/{id}/approve     # 核准（含 preflight 檢查）
POST   /api/content/{id}/reject      # 捨棄
PUT    /api/content/{id}             # 編輯標題/內文
POST   /api/content/batch            # 批次核准/捨棄
```

**核心特性**：
- `ContentDetail` Pydantic 統一型別，包含 `preflight_warnings` 自動計算
- 核准自動執行 7 規則 preflight 檢查（長度、IG 圖片需求等）
- 若有 ERROR 級警告則返回 `{status: "ERROR", warnings: [...]}`
- 單次 HTTP 往返，不用 `force` 參數

### Phase B：Curation SSE + 統計（3 個端點）

```python
POST   /api/curation/run             # SSE 串流化策展進度
GET    /api/curation/status          # 查詢當前狀態
GET    /api/curation/stats           # 今日/週統計 + 通過率
```

**核心改動**：
- `scripts/daily_curation.py` 加 `progress_callback` 參數
- 級次事件：`item_fetched` → `generating_image` → `saved_draft` → `account_done`
- SSE 即時推送前端，實時更新進度條

**progress_callback 事件**：
```
item_fetched:      {account, title, source}
generating_image:  {account}
saved_draft:       {account, title}
item_skipped:      {account, reason}
item_error:        {account, error}
account_done:      {account, drafted}
done:              {total_drafted}
```

### Phase C：Scheduling API（2 個端點）

```python
GET    /api/content/scheduled        # 日期範圍排程（可按帳號篩選）
PATCH  /api/content/{id}/reschedule  # 拖拽調整發布時間
```

**新增 DAO 方法**：
- `find_scheduled(start_date, end_date, account_type)` — 使用 `DATE()` 函式處理 ISO 8601 日期範圍

### Phase D：Drafts 列表 + 統計

```python
GET    /api/content/drafts           # DRAFT 列表（帳號/來源/天數篩選）
PATCH  /api/content/{id}/status      # 狀態轉換（DRAFT → PENDING_REVIEW）
GET    /api/curation/stats           # 統計數據（見 Phase B）
```

**新增 DAO 方法**：
- `find_drafts(account_type, source, days)` — 可選篩選帳號、來源、最近 N 天
- `get_curation_stats()` — 按帳號返回 today/week 數據 + approval_rate

### Phase E：Account Settings API（3 個端點）

```python
GET    /api/accounts/{id}/prompt     # 讀取 prompt 檔內容
PUT    /api/accounts/{id}            # 更新帳號配置 + 寫回 TOML
POST   /api/accounts/{id}/preview    # 生成預覽圖卡（觸發 imgGen）
```

**新增 Config 方法**：
- `save_account(account_type, updates)` — 白名單過濾字段後更新
- `_save()` — 序列化帳號配置回 `accounts.toml`

---

## 前端實現（web/frontend/src/）

### 5 個頁面

**ReviewPage.tsx** — 待審內容核准
- 篩選器：帳號、狀態（DRAFT/PENDING_REVIEW）
- 批次模式：多選 + 批次核准/捨棄
- 編輯模式：側邊抽屜編輯標題/內文
- Preflight 對話框：顯示阻擋警告

**CurationPage.tsx** — 實時策展進度
- SSE 連線到 `/api/curation/run`
- 進度動態畫面：爬蟲 → AI → 圖卡 → 保存
- DRAFT 列表：可直接轉為 PENDING_REVIEW
- 篩選器：帳號、來源（hacker_news/techcrunch 等）、天數

**SchedulingPage.tsx** — 視覺化排期
- 週曆視圖（7 天網格）
- 拖拽調整發布時間
- 按帳號配色（A=紫色、B=藍色、C=橙色）

**AccountSettingsPage.tsx** — 帳號配置
- 可展開帳號面板 (A/B/C)
- 字段編輯：名稱、平台選擇、發布時間、色彩心情
- Prompt 編輯器（完整 textarea）
- 預覽按鈕：生成樣本圖卡

**DashboardPage.tsx** — 統計儀表板（已存在）
- 三帳號狀態卡片
- 今日排程時間表
- 最近內容列表

### 4 個 Zustand Store

```typescript
// useReviewStore.ts
- filterAccount, filterStatus, batchMode, selectedIds
- setFilterAccount, toggleBatchMode, toggleSelect, selectAll

// useCurationStore.ts
- accountFilter, sourceFilter, daysFilter, isRunning, progress[]
- setAccountFilter, setRunning, addProgress, resetProgress

// useSchedulingStore.ts
- view ('week'|'month'), weekStart, selectedContentId
- setView, setWeekStart, prevWeek, nextWeek

// useSettingsStore.ts
- expandedAccountId, dirtyAccounts, previewUrls
- setExpanded, markDirty, setPreviewUrl
```

### API 查詢層（api/queries.ts）

TanStack Query v5 hooks：
- `useReviewContent()`, `useApproveContent()`, `useRejectContent()`
- `useCurationStatus()`, `useCurationStats()`
- `useScheduledRange()`, `useReschedule()`
- `useDrafts()`, `useUpdateContentStatus()`
- `useAccountPrompt()`, `useUpdateAccount()`, `useAccountPreview()`

### 元件樹

```
ReviewPage
├─ ReviewFilterBar          篩選條件
├─ BatchBar                 批次操作
├─ ReviewCard (repeated)    內容卡片
│  ├─ StatusBadge
│  ├─ PrefightWarnings
│  └─ ActionButtons
├─ EditDrawer               編輯抽屜
└─ PreflightDialog          核准警告對話框

CurationPage
├─ CurationProgressFeed     SSE 進度動態
├─ DraftContentList         DRAFT 內容清單
└─ CurationStatsBar         三帳號統計

SchedulingPage
├─ ViewToggle
├─ WeekCalendar
└─ ContentCard (draggable)

AccountSettingsPage
├─ SettingsPanelA
├─ SettingsPanelB
└─ SettingsPanelC
   ├─ PromptEditor
   └─ PreviewButton
```

---

## 數據模型

### ContentDetail（統一型別）

```python
class ContentDetail(BaseModel):
    id: str
    account_type: str                # "A" | "B" | "C"
    status: str                      # "DRAFT" | "PENDING_REVIEW" | "APPROVED" | "PUBLISHED" | "ANALYZED"
    content_type: str | None         # "news" | "opinion" 等
    title: str
    body: str
    reasoning: str
    image_url: str | None            # /output/{filename}
    source_url: str | None
    source: str | None               # "hacker_news" | "techcrunch" | "bbc_sport"
    scheduled_time: str | None       # ISO 8601
    created_at: str
    updated_at: str
    preflight_warnings: list[str]    # 自動計算
    account_name: str
    platforms: list[str]
```

### Content（資料庫模型）

新增欄位：
- `source: Optional[str]` — 來源 (hacker_news / techcrunch 等)

---

## 架構決策

### 1. 單次 HTTP 往返（Preflight）

**舊方案**：
```
核准 → ERROR → 對話框 → 再核准 (force=true)  ← 2 次 HTTP
```

**新方案**：
```
核准 → preflight 自動執行 → 回傳 {status, warnings}  ← 1 次 HTTP
前端本地彈對話框，用戶確認後上傳
```

**效果**：減少延遲、簡化前端邏輯

### 2. Progress Callback（串流化進度）

`daily_curation.py` 加 10 行 callback 邏輯：

```python
def curate_for_account(..., progress_callback=None):
    for item in scraper.fetch():
        if progress_callback:
            progress_callback("item_fetched", account=acct, ...)
        # ... AI 處理 ...
        if progress_callback:
            progress_callback("generating_image", account=acct)
        # ... 圖卡生成 ...
```

後端 SSE 端點消費 callback：
```python
@app.post("/api/curation/run")
async def api_curation_run(req: CurationRunRequest):
    async def stream():
        events_queue = asyncio.Queue()
        
        def emit(type, **kw):
            await events_queue.put({"type": type, **kw})
        
        count = await curate_for_account(..., progress_callback=emit)
        
        # 排出隊列中的事件
        while not events_queue.empty():
            yield sse_format(events_queue.get_nowait())
    
    return StreamingResponse(stream(), media_type="text/event-stream")
```

### 3. 統一 ContentDetail 型別

Review、Scheduling、Curation 頁面都返回相同的 ContentDetail 結構，減少前端適配邏輯

### 4. Per-Page Zustand Store

每個頁面有獨立的 store，避免跨頁面狀態洩漏：
- `useReviewStore` — Review 篩選 + 批次
- `useCurationStore` — Curation 進度 + 篩選
- `useSchedulingStore` — Scheduling 視圖 + 日期
- `useSettingsStore` — Settings 面板展開 + 預覽

---

## 運行命令

### 後端

```bash
cd web
uvicorn api:app --reload --port 8000
```

### 前端

```bash
cd web/frontend
npm run dev  # Vite dev server (localhost:5173)
```

### 測試

```bash
# 全部測試
.venv/bin/python -m pytest tests/ -v

# 後端 API 測試
pytest tests/test_api_review.py tests/test_db.py tests/test_config.py -v

# 前端測試（如有）
cd web/frontend && npm run test
```

---

## 驗收清單

### Review 頁 ✅
- [x] 篩選 DRAFT/PENDING_REVIEW，按帳號篩選
- [x] 核准自動 preflight，ERROR 級阻擋
- [x] 單次 HTTP 往返
- [x] 批次核准/捨棄
- [x] 編輯模式（標題/內文）

### Curation 頁 ✅
- [x] SSE 實時顯示進度（爬蟲→AI→圖卡→保存）
- [x] 篩選帳號、來源、日期
- [x] DRAFT 直接轉 PENDING_REVIEW

### Scheduling 頁 ✅
- [x] 週曆視圖
- [x] 拖拽調整時間
- [x] 按帳號配色

### Settings 頁 ✅
- [x] 帳號名稱、平台、發布時間編輯
- [x] 色彩心情實時預覽
- [x] Prompt 編輯器

### 測試 ✅
- [x] 85 tests passing
- [x] API 端點覆蓋
- [x] DAO 方法覆蓋
- [x] Preflight 檢查邏輯

---

## 後續優化建議

1. **前端测试** — 添加 Vitest 單元測試 + React Testing Library
2. **E2E 測試** — Playwright E2E 測試整個 Review → Scheduling → Publish 流程
3. **性能優化** — Code-splitting，React Query 快取策略
4. **多語言** — i18n 支援中英文
5. **移動適配** — 響應式設計優化（當前為桌面優先）

---

## 相關文檔

- `docs/webui_levelup_unified_spec.md` — 規格文檔（融合新舊方案）
- `web/frontend/ARCHITECTURE.md` — 前端架構詳解
- `web/frontend/API_GUIDE.md` — API 端點參考
- `CLAUDE.md` — 項目運行命令與架構
