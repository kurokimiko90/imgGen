# Web UI 擴展規格 A/B：Content Review + Dashboard

**版本**: 1.0（Planner Agent 產出，基於前端原始碼驗證）
**日期**: 2026-03-31
**技術棧**: React 19 + Vite 8 + Zustand 5 + TanStack Query 5 + Framer Motion + Tailwind CSS 4 + lucide-react

---

## 共用基礎建設

### 新增後端 API Endpoint

| Method | Path | 說明 |
|--------|------|------|
| GET | `/api/content/pending` | 取得 PENDING_REVIEW 內容 |
| POST | `/api/content/{id}/approve` | 核准（含 preflight + 排程） |
| POST | `/api/content/{id}/reject` | 捨棄 |
| POST | `/api/content/{id}/edit` | 編輯標題/內文 |
| POST | `/api/content/batch-approve` | 批次核准 |
| GET | `/api/content/stats` | 三帳號狀態統計 |
| GET | `/api/content/recent` | 最近 N 筆內容 |
| GET | `/api/content/schedule` | 指定日期排程 |
| GET | `/api/accounts` | 帳號配置 |

### 新增路由

```typescript
// App.tsx
<Route path="/review" element={<ReviewPage />} />
<Route path="/dashboard" element={<DashboardPage />} />
```

### 新增 Sidebar 項目

```typescript
{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
{ to: '/review', label: 'Review', icon: CheckSquare },
```

### 共用 TypeScript 型別

```typescript
// types/content.ts
interface ContentItem {
  id: string
  account_type: string            // "A" | "B" | "C"
  status: string                  // ContentStatus values
  content_type: string
  title: string
  body: string
  image_path: string | null
  reasoning: string
  scheduled_time: string | null
  created_at: string
  updated_at: string
}

interface AccountInfo {
  name: string
  platforms: string[]
  publish_time: string
  color_mood: string
  tone: string
}

interface AccountStats {
  name: string
  counts: Record<string, number>
  weekly_output: number
  approval_rate: number
}
```

---

## 頁面 A：Content Review（審核台）— 評分 125

### 1. 頁面結構

```
ReviewPage
├── PageTransition
│   ├── ReviewHeader
│   │   ├── ReviewFilters (帳號 pill + 日期篩選)
│   │   └── BatchActions (全選核准 + 計數)
│   ├── ReviewCardGrid
│   │   └── ReviewCard[]
│   │       ├── CardPreview (圖卡縮圖)
│   │       ├── CardMeta (帳號 badge、content_type badge)
│   │       ├── CardContent (標題、body、reasoning 折疊)
│   │       ├── PreflightWarnings (核准時顯示)
│   │       └── CardActions (Approve / Reject / Edit / Skip)
│   └── ReviewEmptyState
└── EditModal (全頁覆蓋編輯彈窗)
```

### 2. 後端 API 詳細規格

#### `GET /api/content/pending?account={A|B|C}&date={YYYY-MM-DD}`

回傳：
```json
{
  "ok": true,
  "items": [{ "id": "42", "account_type": "A", "status": "PENDING_REVIEW", ... }]
}
```

#### `POST /api/content/{id}/approve`

Request: `{ "force": false }`

邏輯：
1. `dao.find_by_id(id)`
2. `config.get_account(account_type)` → 取得 platforms, publish_time
3. `preflight_check(content, platforms)`
4. 若有 ERROR 級警告且 `force=false` → 回傳 `needs_confirmation: true`
5. `content.transition_to(APPROVED)` → 計算 `scheduled_time` → `dao.update()`

回傳：
```json
{
  "ok": true,
  "content": { ... },
  "warnings": ["X 字數超限（320 / 280）"],
  "scheduled_time": "2026-04-01T08:00:00",
  "needs_confirmation": false
}
```

#### `POST /api/content/{id}/reject`

`content.transition_to(REJECTED)` → `dao.update()`

#### `POST /api/content/{id}/edit`

Request: `{ "title": "...", "body": "..." }`
更新欄位，不改變狀態。

#### `POST /api/content/batch-approve`

Request: `{ "ids": ["42", "43"], "force": false }`
回傳: `{ "approved": [...], "skipped": [...], "errors": [...] }`

### 3. 前端元件清單

| 元件 | Props | State | 事件 |
|------|-------|-------|------|
| `ReviewPage` | 無 | useReviewStore | 載入時 fetch |
| `ReviewFilters` | `accounts` | selectedAccount, selectedDate (store) | onAccountChange, onDateChange |
| `ReviewCardGrid` | `items, isLoading` | 無 | — |
| `ReviewCard` | `item, onApprove, onReject, onEdit, selected, onToggleSelect` | showReasoning, preflightWarnings, confirming | 按鈕點擊 |
| `PreflightWarnings` | `warnings, onConfirm, onCancel` | 無 | 確認/取消 |
| `EditModal` | `item, onSave, onClose` | editTitle, editBody | 儲存/ESC |
| `BatchActions` | `selectedIds, totalCount, onBatchApprove, onSelectAll` | 無 | 全選/核准 |

### 4. Zustand Store

```typescript
// stores/useReviewStore.ts
interface ReviewState {
  selectedAccount: string | null
  selectedDate: string | null
  selectedIds: Set<string>
  editingItem: ContentItem | null
  // Actions
  setSelectedAccount, setSelectedDate, toggleSelect, selectAll, deselectAll, setEditingItem
}
```

### 5. API 呼叫流程

```
載入/篩選 → usePendingContent(account, date) → GET /api/content/pending
Approve → useApproveContent → POST /api/content/{id}/approve
  → needs_confirmation? → 顯示 PreflightWarnings → force=true 再次呼叫
Reject → useRejectContent → POST /api/content/{id}/reject
Edit → useEditContent → POST /api/content/{id}/edit
Batch → useBatchApprove → POST /api/content/batch-approve
```

### 6. 響應式設計

| 元素 | 桌面 (≥1024) | 平板 (768-1023) | 手機 (<768) |
|------|-------------|----------------|------------|
| CardGrid | 2 欄 | 1 欄 | 1 欄 |
| ReviewCard | 左圖右文 | 左圖右文 | 圖上文下 |
| CardActions | 4 按鈕一列 | 4 按鈕一列 | 2×2 grid |
| EditModal | 居中 max-w-2xl | max-w-xl | 全螢幕 |

### 7. 測試清單

**前端**（11 個）：ReviewCard 渲染/操作、PreflightWarnings 渲染/確認、EditModal 初始值/儲存、ReviewFilters 切換、useReviewStore selectAll/toggleSelect

**後端**（9 個）：pending 查詢、approve 狀態轉換、approve preflight 警告、approve force、reject 轉換、edit 更新、batch approve 跳過 ERROR、accounts 回傳

### 8. 依賴

| 依賴 | 狀態 |
|------|------|
| Cycle 1: content.py, db.py, config.py | ✅ 已完成 |
| Cycle 4: preflight.py | 需先完成 |
| Cycle 4: scheduler.py | 需先完成 |
| Cycle 2: daily_curation.py（或測試資料） | 需先完成 |

---

## 頁面 B：Dashboard（總覽儀表板）— 評分 80

### 1. 頁面結構

```
DashboardPage
├── PageTransition
│   ├── DashboardHeader (標題 + 日期)
│   ├── AccountStatusCards (3 帳號狀態卡 grid-cols-3)
│   │   └── AccountCard[] ×3 (名稱 + 顏色標識 + DRAFT/PENDING/APPROVED/PUBLISHED 計數)
│   ├── ScheduleTimeline (今日排程時間軸 0:00-24:00)
│   ├── HealthMetrics (3 帳號健康度 grid-cols-3)
│   │   └── HealthCard[] ×3 (本週產出 + 通過率進度條)
│   ├── RecentContentList (最近 10 筆)
│   │   └── RecentContentRow[] (縮圖 + 標題 + 帳號 badge + 狀態 badge)
│   └── QuickActions (開始審核 + 觸發策展)
```

### 2. 後端 API

#### `GET /api/content/stats`

回傳：
```json
{
  "ok": true,
  "accounts": {
    "A": { "name": "AI Automation", "counts": {"DRAFT": 5, "PENDING_REVIEW": 3, ...}, "weekly_output": 7, "approval_rate": 0.86 },
    "B": { ... },
    "C": { ... }
  }
}
```

#### `GET /api/content/recent?limit=10`

最近 N 筆內容，按 created_at DESC。

#### `GET /api/content/schedule?date=2026-03-31`

指定日期的 APPROVED 排程內容。

### 3. 前端元件

| 元件 | Props |
|------|-------|
| `AccountCard` | accountId, name, counts, color |
| `ScheduleTimeline` | items: ScheduleItem[] |
| `HealthCard` | accountId, name, weeklyOutput, approvalRate, color |
| `RecentContentList` | items: RecentItem[] |
| `StatusBadge`（共用） | status: string |
| `QuickActions` | pendingCount |

帳號顏色：A = blue-400, B = amber-400, C = green-400

狀態 badge：DRAFT = gray, PENDING = yellow, APPROVED = green, PUBLISHED = blue, REJECTED = red

### 4. 狀態管理

不需 Zustand。全部用 react-query hooks（refetchInterval: 30s）。

### 5. 響應式

| 元素 | 桌面 | 手機 |
|------|------|------|
| AccountStatusCards | grid-cols-3 | grid-cols-1 |
| HealthMetrics | grid-cols-3 | grid-cols-1 |
| ScheduleTimeline | 完整顯示 | 可橫向捲動 |
| RecentContentList | 完整列 | 隱藏縮圖 |

### 6. 測試清單

**前端**（8 個）：AccountCard 渲染、計數為 0、Timeline 渲染、Timeline empty、HealthCard 渲染、RecentContentList 渲染、StatusBadge 顏色

**後端**（8 個）：stats 三帳號、counts 正確、weekly_output、approval_rate、recent limit、recent order、schedule 日期篩選、accounts

### 7. 依賴

Dashboard 依賴少，只需 Cycle 1（Content model + DB）。可獨立於 Cycle 4 開發。

---

## 交付物總覽

### 後端

| 檔案 | 動作 |
|------|------|
| `web/api.py` | 修改：+8 endpoint, +4 Pydantic model |
| `tests/test_api_review.py` | 新建：9 個測試 |
| `tests/test_api_dashboard.py` | 新建：8 個測試 |

### 前端

| 檔案 | 動作 |
|------|------|
| `App.tsx` | 修改：+2 Route |
| `Sidebar.tsx` | 修改：+2 NavItem |
| `api/queries.ts` | 修改：+8 hooks |
| `pages/ReviewPage.tsx` | 新建 |
| `pages/DashboardPage.tsx` | 新建 |
| `stores/useReviewStore.ts` | 新建 |
| `components/StatusBadge.tsx` | 新建（共用） |
| `features/review/*.tsx` | 新建：6 元件 |
| `features/review/__tests__/` | 新建：11 測試 |
| `features/dashboard/*.tsx` | 新建：5 元件 |
| `features/dashboard/__tests__/` | 新建：8 測試 |

**總計**：8 API、13 前端元件、1 store、8 hooks、17 後端測試、19 前端測試
