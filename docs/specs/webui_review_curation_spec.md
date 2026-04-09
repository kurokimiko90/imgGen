# Web UI：Content Review + Curation Dashboard 規格書

> **目標**：將終端機的 `audit.py` 審核流程和 `daily_curation.py` 策展流程完整搬上 Web UI，讓使用者可以在瀏覽器（含手機）完成所有 LevelUp 操作。

---

## 現狀盤點

### 已有的 Web UI

| 頁面 | 路由 | 功能 |
|------|------|------|
| GeneratePage | `/` | imgGen 圖卡生成（已含 Smart Mode 切換、Color Mood 選擇器）✅ |
| DashboardPage | `/dashboard` | 三帳號狀態卡片 + 排程時間表 + 最近內容列表 ✅ |
| HistoryPage | `/history` | imgGen 生成歷史 ✅ |
| CaptionsPage | `/captions` | 社群文案生成 ✅ |
| ToolsPage | `/tools` | 工具集 ✅ |
| PresetsPage | `/presets` | 預設管理 ✅ |

### 已有但未連接的 UI 線索

- `QuickActions.tsx` 已有 `<Link to="/review">` 和 `<Link to="/curation">` — 但路由不存在
- `constants/accounts.ts` 已定義 `ACCOUNT_COLORS`、`STATUS_COLORS`、`STATUS_LABELS`
- `queries.ts` 已定義 `ContentItem`、`ScheduleItem`、`AccountInfo` 等型別

### 缺失

| 缺失項 | 影響 |
|--------|------|
| `/review` 路由 + ReviewPage | 無法在瀏覽器審核內容 |
| `/curation` 路由 + CurationPage | 無法在瀏覽器觸發/查看策展結果 |
| Content CRUD API | 後端只有 read endpoints，缺 approve/reject/edit |
| Curation API | 後端無觸發策展和查看結果的端點 |

---

## 架構設計

### 分層

```
Frontend (React + TanStack Query + Zustand)
    ↓ REST + SSE
Backend (FastAPI — web/api.py)
    ↓ imports
Domain (Content, ContentDAO, preflight, scheduler)
```

### 設計原則

1. **重用現有模組**：直接 import `ContentDAO`、`preflight_check`、`calculate_scheduled_time`，不重寫邏輯
2. **不可變更新**：前端用 Zustand，後端用 `dataclasses.replace()`
3. **樂觀更新**：TanStack Query `onMutate` 先更新 UI，失敗再 rollback
4. **Mobile-first**：Review 頁面卡片式佈局，觸控友善按鈕

---

## Phase A：後端 — Content Review API

### 新增端點（`web/api.py`）

| 方法 | 路由 | 說明 | Request | Response |
|------|------|------|---------|----------|
| GET | `/api/content/review` | 列出待審內容 | `?status=DRAFT,PENDING_REVIEW&account=A&limit=50` | `{items: ContentDetail[]}` |
| GET | `/api/content/{id}/detail` | 單篇完整資訊 | — | `{item: ContentDetail}` |
| POST | `/api/content/{id}/approve` | 核准 | `{publish_time?: string}` | `{item: ContentDetail, warnings: string[]}` |
| POST | `/api/content/{id}/reject` | 捨棄 | `{reason?: string}` | `{item: ContentDetail}` |
| PUT | `/api/content/{id}` | 編輯 | `{title?: string, body?: string}` | `{item: ContentDetail}` |
| POST | `/api/content/batch` | 批次操作 | `{ids: string[], action: "approve"\|"reject"}` | `{results: BatchResult[]}` |

### ContentDetail 型別

```python
class ContentDetail(BaseModel):
    id: str
    account_type: str
    status: str
    content_type: str | None
    title: str
    body: str
    reasoning: str
    image_url: str | None
    source_url: str | None
    scheduled_time: str | None
    created_at: str
    updated_at: str
    preflight_warnings: list[str]  # 自動計算
```

### 核准流程（`POST /api/content/{id}/approve`）

```python
# 1. 讀取 Content
content = dao.find_by_id(id)

# 2. 狀態轉換 DRAFT → PENDING_REVIEW → APPROVED
if content.status == ContentStatus.DRAFT:
    content.transition_to(ContentStatus.PENDING_REVIEW)
content.transition_to(ContentStatus.APPROVED)

# 3. preflight 檢查
account_cfg = config.get_account(content.account_type)
warnings = preflight_check(content, account_cfg.platforms)

# 4. 排程
if not any(w.startswith("[ERROR]") for w in warnings):
    publish_time = req.publish_time or account_cfg.publish_time
    content.scheduled_time = calculate_scheduled_time(publish_time)

# 5. 更新 DB
dao.update(content)
```

### Pydantic 模型

```python
class ContentApproveRequest(BaseModel):
    publish_time: str | None = None  # 覆蓋帳號預設時段

class ContentEditRequest(BaseModel):
    title: str | None = None
    body: str | None = None

class ContentBatchRequest(BaseModel):
    ids: list[str]
    action: str  # "approve" | "reject"
```

### 估算

- 新增 6 個 API endpoints
- 3 個 Pydantic request models
- 1 個 helper function `_content_to_detail()`
- 約 150 行新增 Python 程式碼

---

## Phase B：後端 — Curation API

### 新增端點

| 方法 | 路由 | 說明 | Response |
|------|------|------|----------|
| POST | `/api/curation/run` | 觸發策展（SSE 串流進度） | SSE: `{type, account, title, status}` |
| GET | `/api/curation/status` | 查詢策展狀態 | `{running: bool, last_run: string}` |

### SSE 串流格式（`/api/curation/run`）

```
Request body: {"accounts": ["A", "B", "C"], "dry_run": false}

SSE events:
  data: {"type": "start", "accounts": ["A", "B", "C"]}
  data: {"type": "scraping", "account": "A", "source": "hacker_news"}
  data: {"type": "item", "account": "A", "title": "Claude 新功能", "should_publish": true}
  data: {"type": "image", "account": "A", "title": "Claude 新功能", "image_url": "/output/..."}
  data: {"type": "account_done", "account": "A", "drafts": 3}
  ...
  data: {"type": "done", "total_drafts": 7}
```

### 實作方式

```python
@app.post("/api/curation/run")
async def api_curation_run(req: CurationRunRequest):
    async def stream():
        yield sse("start", accounts=req.accounts)
        for acct_id in req.accounts:
            # 重用 daily_curation.curate_for_account 核心邏輯
            # 但注入 progress callback 以發送 SSE 事件
            ...
        yield sse("done", total_drafts=total)
    return StreamingResponse(stream(), media_type="text/event-stream")
```

### 需要的重構

`scripts/daily_curation.py` 的 `curate_for_account()` 需要接受可選的 `progress_callback` 參數，讓 Web API 注入 SSE 事件發送。這是唯一需要改動現有模組的地方。

### 估算

- 2 個新端點
- `daily_curation.py` 新增 `progress_callback` 參數（約 10 行改動）
- 約 80 行新增 Python 程式碼

---

## Phase C：前端 — ReviewPage

### 頁面結構

```
ReviewPage
├── FilterBar（帳號篩選 A/B/C + 狀態篩選 + 排序）
├── ContentGrid / ContentList
│   └── ReviewCard × N
│       ├── 圖卡縮圖（左）
│       ├── 標題 + 內文摘要 + reasoning（右）
│       ├── StatusBadge + AccountBadge
│       └── ActionBar（Approve / Edit / Reject / Skip）
├── EditDrawer（Framer Motion 側邊滑出）
│   ├── title input
│   ├── body textarea（自動高度）
│   └── Save + Cancel
├── PreflightWarnings（核准時彈出）
│   ├── WARNING 列表（黃色）
│   ├── ERROR 列表（紅色，阻擋核准）
│   └── Confirm / Cancel
└── BatchBar（底部浮動，批次選擇時顯示）
    ├── "已選 N 篇"
    ├── Approve All / Reject All
    └── Deselect
```

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `pages/ReviewPage.tsx` | 頁面組件 |
| `features/review/FilterBar.tsx` | 帳號 + 狀態篩選器 |
| `features/review/ReviewCard.tsx` | 單篇內容卡片（圖片 + 資訊 + 操作） |
| `features/review/ActionBar.tsx` | Approve / Edit / Reject / Skip 按鈕列 |
| `features/review/EditDrawer.tsx` | 側邊編輯面板 |
| `features/review/PreflightDialog.tsx` | Preflight 警告對話框 |
| `features/review/BatchBar.tsx` | 底部批次操作浮動列 |
| `stores/useReviewStore.ts` | 審核頁狀態（選中項、篩選條件、批次模式） |

### TanStack Query Hooks（`api/queries.ts` 新增）

```typescript
// 列出待審內容
function useReviewContent(params: {
  status?: string[]
  account?: string
  limit?: number
})

// 單篇詳情
function useContentDetail(id: string | null)

// 核准
function useApproveContent()  // useMutation

// 捨棄
function useRejectContent()   // useMutation

// 編輯
function useEditContent()     // useMutation

// 批次操作
function useBatchAction()     // useMutation
```

### Zustand Store

```typescript
interface ReviewState {
  // 篩選
  filterAccount: string | null   // null = 全部
  filterStatus: string[]         // ['DRAFT', 'PENDING_REVIEW']
  sortBy: 'created_at' | 'account_type'

  // 批次
  batchMode: boolean
  selectedIds: Set<string>

  // 編輯
  editingId: string | null

  // Actions
  setFilterAccount: (v: string | null) => void
  toggleBatchMode: () => void
  toggleSelect: (id: string) => void
  selectAll: (ids: string[]) => void
  clearSelection: () => void
  setEditingId: (id: string | null) => void
}
```

### UI 細節

- **Mobile 佈局**：`< 768px` 時 ReviewCard 改為全寬堆疊，ActionBar 變為底部固定
- **鍵盤快捷鍵**：`A` = Approve, `E` = Edit, `D` = Reject, `S` = Skip, `→` = 下一篇
- **樂觀更新**：核准/捨棄後卡片立刻淡出，查詢自動 invalidate
- **Preflight 攔截**：核准前先呼叫 approve API，若回傳 `[ERROR]` 級別 warnings，顯示對話框阻止

### 估算

- 8 個新前端檔案
- 6 個新 TanStack Query hooks
- 1 個新 Zustand store
- 約 500 行 TypeScript/TSX

---

## Phase D：前端 — CurationPage

### 頁面結構

```
CurationPage
├── Header（"Daily Curation" + 最後執行時間）
├── AccountSelector（勾選 A/B/C + Dry Run 開關）
├── RunButton（大按鈕，執行中顯示 spinner）
├── ProgressFeed（SSE 即時事件列表）
│   └── EventRow × N
│       ├── 🔍 scraping hacker_news...
│       ├── ✅ "Claude 新功能" → should_publish: true
│       ├── 🖼️ 圖卡已生成
│       └── ❌ AI 判定不發：reasoning...
├── ResultSummary（完成後顯示）
│   ├── 帳號 A：3 drafts
│   ├── 帳號 B：2 drafts
│   └── 帳號 C：1 draft
└── "Go to Review →" LinkButton
```

### 新增檔案

| 檔案 | 說明 |
|------|------|
| `pages/CurationPage.tsx` | 頁面組件 |
| `features/curation/AccountSelector.tsx` | 帳號勾選 + dry run toggle |
| `features/curation/ProgressFeed.tsx` | SSE 事件即時顯示 |
| `features/curation/ResultSummary.tsx` | 完成摘要 |
| `hooks/useSSE.ts` | 通用 SSE hook（可重用於 batch） |

### SSE Hook

```typescript
function useSSE<T>(url: string | null, body?: unknown): {
  events: T[]
  isConnected: boolean
  isDone: boolean
  error: string | null
}
```

以 `fetch()` + `ReadableStream` 實作，避免 EventSource 不支援 POST body 的問題。

### 估算

- 5 個新前端檔案
- 1 個通用 SSE hook
- 約 300 行 TypeScript/TSX

---

## Phase E：路由 + 導航整合

### App.tsx 新增路由

```tsx
<Route path="/review" element={<ReviewPage />} />
<Route path="/curation" element={<CurationPage />} />
```

### Sidebar.tsx 新增導航項

```typescript
{ to: '/review', label: 'Review', icon: CheckSquare },
{ to: '/curation', label: 'Curation', icon: RefreshCw },
```

放在 Dashboard 和 Captions 之間，形成 LevelUp 操作區塊。

### 導航結構（更新後）

```
Generate      — imgGen 圖卡生成
Dashboard     — 總覽儀表板
Review        — 內容審核 ← NEW
Curation      — 策展執行 ← NEW
Captions      — 社群文案
History       — 生成歷史
Tools         — 工具集
Presets       — 預設管理
```

---

## 實作順序

```
Phase A（後端 Review API）
  └── Phase C（前端 ReviewPage）— 依賴 Phase A

Phase B（後端 Curation API）
  └── Phase D（前端 CurationPage）— 依賴 Phase B

Phase E（路由 + 導航）— 依賴 Phase C + D
```

**建議平行度**：Phase A + B 可同時開發（獨立 API 端點），Phase C + D 各自依賴上游後端。

### 開發任務拆解

| # | 任務 | 檔案 | 依賴 | 估算（新增行） |
|---|------|------|------|--------------|
| A1 | `_content_to_detail()` helper | `web/api.py` | — | 30 |
| A2 | `GET /api/content/review` + `GET /api/content/{id}/detail` | `web/api.py` | A1 | 40 |
| A3 | `POST /api/content/{id}/approve` | `web/api.py` | A1 | 35 |
| A4 | `POST /api/content/{id}/reject` + `PUT /api/content/{id}` | `web/api.py` | A1 | 30 |
| A5 | `POST /api/content/batch` | `web/api.py` | A3, A4 | 25 |
| B1 | `daily_curation.py` 加 progress_callback | `scripts/daily_curation.py` | — | 10 |
| B2 | `POST /api/curation/run` SSE | `web/api.py` | B1 | 50 |
| B3 | `GET /api/curation/status` | `web/api.py` | — | 20 |
| C1 | `useReviewStore` | `stores/useReviewStore.ts` | — | 50 |
| C2 | Review query hooks | `api/queries.ts` | A2-A5 | 60 |
| C3 | `FilterBar` + `ReviewCard` | `features/review/` | C1, C2 | 120 |
| C4 | `ActionBar` + `PreflightDialog` | `features/review/` | C2 | 80 |
| C5 | `EditDrawer` | `features/review/` | C2 | 60 |
| C6 | `BatchBar` + `ReviewPage` 組裝 | `pages/ReviewPage.tsx` | C3-C5 | 80 |
| D1 | `useSSE` hook | `hooks/useSSE.ts` | — | 40 |
| D2 | `AccountSelector` + `ProgressFeed` | `features/curation/` | D1 | 80 |
| D3 | `ResultSummary` + `CurationPage` 組裝 | `pages/CurationPage.tsx` | D2, B2 | 60 |
| E1 | 路由 + Sidebar 更新 | `App.tsx`, `Sidebar.tsx` | C6, D3 | 15 |

### 測試策略

| 層級 | 工具 | 覆蓋範圍 |
|------|------|---------|
| 後端 API | `pytest` + `httpx.AsyncClient` | A1-A5, B1-B3（mock ContentDAO） |
| 前端 Store | `vitest` | useReviewStore 狀態邏輯 |
| 前端 Component | `@testing-library/react` + `vitest` | ReviewCard、FilterBar 渲染 |
| E2E | Playwright（手動，可選） | 完整審核流程 |

### 新增測試檔案

```
tests/test_content_api.py          # Phase A 後端測試
tests/test_curation_api.py         # Phase B 後端測試
web/frontend/src/stores/__tests__/useReviewStore.test.ts
web/frontend/src/features/review/__tests__/ReviewCard.test.tsx
```

---

## 更新後的 Sidebar 標記

完成後，Sidebar 導航每一項都將有完整功能：

```
Generate      — ✅ imgGen core + Smart Mode
Dashboard     — ✅ 三帳號統計 + 排程 + 最近內容
Review        — 🆕 內容審核（取代 audit.py）
Curation      — 🆕 策展執行（取代 daily_curation.py CLI）
Captions      — ✅ 社群文案
History       — ✅ 生成歷史
Tools         — ✅ 工具集
Presets       — ✅ 預設管理
```

---

## 驗收標準

### Review Page
- [ ] 可按帳號 / 狀態篩選待審內容
- [ ] 單篇可查看完整 body + reasoning + 圖卡預覽
- [ ] Approve 時自動執行 preflight，ERROR 級別阻擋核准
- [ ] 核准後 scheduled_time 自動填入
- [ ] Edit 可修改 title + body 後核准
- [ ] 批次模式可一次核准/捨棄多篇
- [ ] 手機上可流暢操作（觸控按鈕 ≥ 44px）

### Curation Page
- [ ] 可選擇帳號 + dry run 模式
- [ ] 執行時即時顯示 SSE 進度事件
- [ ] 完成後顯示各帳號 DRAFT 數量摘要
- [ ] 可一鍵跳轉到 Review Page
- [ ] 執行中不可重複觸發

### 整合
- [ ] Dashboard QuickActions 連結正常跳轉
- [ ] Sidebar 新項目正確高亮
- [ ] 所有新 API 有對應測試（≥ 80% 覆蓋率）
