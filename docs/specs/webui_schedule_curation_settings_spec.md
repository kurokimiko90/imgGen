# Web UI 擴展規格 C/D/E：Scheduling + Curation + Account Settings

**版本**: 1.0（Planner Agent 產出，基於前端原始碼驗證）
**日期**: 2026-03-31
**技術棧**: React 19 + Vite 8 + Zustand 5 + TanStack Query 5 + Framer Motion + Tailwind CSS 4 + lucide-react

---

## 共用新增

### 帳號顏色常數

```typescript
// constants/accounts.ts
export const ACCOUNT_COLORS = {
  A: { bg: 'bg-blue-500/15', border: 'border-blue-500/40', text: 'text-blue-400', dot: 'bg-blue-500' },
  B: { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-400', dot: 'bg-emerald-500' },
  C: { bg: 'bg-orange-500/15', border: 'border-orange-500/40', text: 'text-orange-400', dot: 'bg-orange-500' },
} as const
```

### 新增 Sidebar 項目

```typescript
{ to: '/scheduling', label: 'Scheduling', icon: Calendar },
{ to: '/curation', label: 'Curation', icon: Database },
{ to: '/settings', label: 'Settings', icon: Settings },
```

### 新增路由

```typescript
<Route path="/scheduling" element={<SchedulingPage />} />
<Route path="/curation" element={<CurationPage />} />
<Route path="/settings" element={<AccountSettingsPage />} />
```

---

## 頁面 C：Scheduling（排程日曆）— 評分 80

### 1. 頁面結構

```
SchedulingPage
├── PageTransition
│   ├── SchedulingHeader
│   │   ├── ViewToggle (week / month)
│   │   └── WeekNavigator (< This Week >)
│   ├── AccountLegend (A:藍 B:綠 C:橙)
│   ├── WeekCalendarGrid（預設）
│   │   └── DayColumn ×7
│   │       ├── DayHeader (日期 + 星期)
│   │       └── ScheduleCard[] (縮圖 + 標題 + 帳號色條)
│   ├── MonthCalendarGrid（切換）
│   │   └── MonthDayCell ×28-31
│   │       └── ScheduleCardMini[]
│   ├── ConflictWarning (同帳號同時段)
│   └── ContentDetailDrawer (右側/底部面板)
│       ├── ContentMeta + Body + Reasoning
│       ├── ImagePreview
│       └── RescheduleAction
```

### 2. 後端 API

#### `GET /api/contents/scheduled?start=2026-03-30&end=2026-04-06&account=A`

回傳 APPROVED + PUBLISHED 狀態，scheduled_time 在日期範圍內的內容。

**需 ContentDAO 新增方法**: `find_scheduled(start, end, account)`

#### `PATCH /api/contents/{id}/reschedule`

Request: `{ "scheduled_time": "2026-04-01T09:00:00" }`

只允許 APPROVED / PUBLISHED 狀態的內容。

#### `GET /api/contents/{id}`

單一內容詳情（供 Drawer 使用）。

### 3. 前端元件

| 元件 | 說明 |
|------|------|
| `SchedulingPage` | 頁面入口 |
| `ViewToggle` | week / month 切換 |
| `WeekNavigator` | ← This Week → 導覽 |
| `AccountLegend` | 帳號顏色圖例 |
| `WeekCalendarGrid` | 7 欄日曆 + Drag & Drop |
| `DayColumn` | 單日欄位 |
| `ScheduleCard` | 可拖拽的排程卡片 |
| `MonthCalendarGrid` | 月視圖 |
| `ContentDetailDrawer` | 點擊卡片展開的詳情面板 |
| `ConflictWarning` | 衝突提醒 |

### 4. Zustand Store

```typescript
// stores/useSchedulingStore.ts
interface SchedulingState {
  view: 'week' | 'month'
  weekStart: Date
  selectedContentId: string | null
  accountFilter: string | null
  // Actions: setView, setWeekStart, navigateWeek, goToToday, setSelectedContentId, setAccountFilter
}
```

### 5. API 呼叫流程

```
載入 → useScheduledContents(weekStart, weekEnd) → GET /api/contents/scheduled
點擊卡片 → store.setSelectedContentId → Drawer 顯示
Drawer → useContentDetail(id) → GET /api/contents/{id}
拖拽放置 → useReschedule.mutate → PATCH /api/contents/{id}/reschedule → invalidate
週導覽 → store.setWeekStart → 自動 refetch
```

### 6. 響應式

| 斷點 | 行為 |
|------|------|
| ≥1024 | 週曆 7 欄，卡片含縮圖+標題+帳號 |
| 768-1023 | 7 欄壓縮，卡片只含色條+標題 |
| <768 | 日視圖（單日列表），左右滑切日 |
| Drawer | 桌面:右側 400px；手機:底部 sheet 70vh |

### 7. 測試

**後端**（4 個）：scheduled 日期範圍、reschedule 更新、非 APPROVED 回傳 400、不存在 404

**前端**（6 個）：ScheduleCard 帳號顏色、點擊、WeekCalendarGrid 7 天、衝突檢測、Drawer reasoning、store navigateWeek

### 8. 依賴

- ContentDAO 新增 `find_scheduled()` 方法
- Cycle 4 scheduler.py 產出 APPROVED 內容
- Drag & Drop：HTML5 原生 API + framer-motion（無新套件）

---

## 頁面 D：Curation（策展管理）— 評分 48

### 1. 頁面結構

```
CurationPage
├── PageTransition
│   ├── CurationHeader
│   │   └── TriggerCurationButton ("Run Daily Curation")
│   ├── CurationStatsBar
│   │   ├── StatCard (本日抓取量)
│   │   ├── StatCard (本週抓取量)
│   │   ├── StatCard (AI 通過率 %)
│   │   └── StatCard (DRAFT 總數)
│   ├── CurationFilters
│   │   ├── AccountFilterGroup (All / A / B / C)
│   │   ├── SourceFilterGroup (All / Football / Tech / PMP)
│   │   └── DateRangeFilter (Today / 7d / 30d)
│   ├── CurationProgressModal（觸發 curation 時顯示）
│   │   ├── ProgressBar + StepList
│   │   └── ResultSummary
│   └── DraftContentList
│       └── DraftContentRow[]
│           ├── AccountTag + SourceTag + Title + ContentTypeBadge
│           └── DraftDetailPanel (expandable)
│               ├── BodyText + ReasoningCard + ImagePreview
│               └── ApproveButton / RejectButton
```

### 2. 後端 API

#### `GET /api/contents/drafts?account=A&source=hacker_news&days=7&limit=50`

DRAFT 內容列表，支援篩選。

**需 ContentDAO 新增**: `find_drafts(account, source, days, limit)`

#### `POST /api/curation/trigger`

手動觸發策展，SSE 串流回傳進度：

```
data: {"type": "start", "accounts": ["A","B","C"]}
data: {"type": "fetching", "account": "A", "scraper": "TechScraper"}
data: {"type": "account_done", "account": "A", "drafted": 3}
data: {"type": "account_error", "account": "B", "error": "..."}
data: {"type": "done", "total_drafted": 5}
```

#### `PATCH /api/contents/{id}/status`

Request: `{ "status": "PENDING_REVIEW" }` 或 `{ "status": "REJECTED" }`

使用 `content.transition_to()` 確保狀態機合法性。

#### `GET /api/curation/stats`

回傳：`{ today_fetched, week_fetched, ai_pass_rate, total_drafts, by_account, by_source }`

**需 ContentDAO 新增**: `get_curation_stats()`

### 3. Zustand Store

```typescript
// stores/useCurationStore.ts
interface CurationState {
  accountFilter: string | null
  sourceFilter: string | null
  daysFilter: number | null  // null=all, 1=today, 7, 30
  isCurating: boolean
  curationSteps: CurationStep[]
  // Actions: setAccountFilter, setSourceFilter, setDaysFilter, setIsCurating, addCurationStep, reset
}
```

### 4. 響應式

| 斷點 | 行為 |
|------|------|
| ≥1024 | 統計卡片 4 欄，列表正常 |
| 768-1023 | 統計 2×2，列表壓縮 |
| <768 | 統計單欄堆疊，列表改卡片模式 |

### 5. 測試

**後端**（4 個）：drafts 篩選、status 合法轉換、非法轉換 400、stats 統計

**前端**（4 個）：DraftContentRow 展開收合、帳號顏色、ProgressModal 步驟顯示、ReasoningCard 空值

### 6. 依賴

- Cycle 2 爬蟲（`src/scrapers/`）+ `daily_curation.py`
- ContentDAO 新增 `find_drafts()` 和 `get_curation_stats()`

---

## 頁面 E：Account Settings（帳號設定）— 評分 45

### 1. 頁面結構

```
AccountSettingsPage
├── PageTransition
│   ├── SettingsHeader + SaveAllButton
│   └── AccountCardGrid
│       └── AccountCard ×3 (A/B/C)
│           ├── AccountCardHeader (頭像 + 名稱 + 展開按鈕)
│           └── AccountEditForm (AnimatePresence 展開)
│               ├── NameField (text)
│               ├── PlatformsField (checkbox: threads/x/instagram/linkedin)
│               ├── PublishTimeField (time "HH:MM")
│               ├── ColorMoodField
│               │   └── ColorSwatchGrid (5 mood 色票)
│               ├── ToneField (textarea)
│               ├── PromptEditorSection (textarea 或 Monaco)
│               ├── SaveButton
│               └── CardPreview (即時圖卡預覽)
```

### 2. 後端 API

#### `GET /api/accounts`

回傳三帳號配置。

#### `GET /api/accounts/{id}/prompt`

讀取帳號 Prompt 文件內容。

#### `PUT /api/accounts/{id}`

Request:
```json
{
  "name": "AI 自動化",
  "platforms": ["threads", "x"],
  "publish_time": "12:30",
  "color_mood": "dark_tech",
  "tone": "技術宅幽默",
  "prompt_content": "..."  // 可選，同時寫回 prompt 檔案
}
```

寫回 `accounts.toml` + prompt 文件。

#### `POST /api/accounts/{id}/preview`

Request: `{ "color_mood": "dark_tech" }`

用指定 color_mood 生成預覽圖卡，回傳 `{ "image_url": "/output/preview_xxx.png" }`

### 3. Zustand Store

```typescript
// stores/useSettingsStore.ts
interface SettingsState {
  expandedAccountId: string | null
  dirtyAccounts: Set<string>
  previewUrls: Record<string, string | null>
  // Actions: setExpandedAccountId, markDirty, markClean, setPreviewUrl
}
```

表單狀態在 `AccountCard` 內部用 `useState` 管理。

### 4. API 呼叫流程

```
載入 → useAccounts() → GET /api/accounts
展開帳號 → useAccountPrompt(id) → GET /api/accounts/{id}/prompt
修改 color_mood → debounce 500ms → POST /api/accounts/{id}/preview → 更新預覽
Save → PUT /api/accounts/{id} → invalidate → toast
```

### 5. 響應式

| 斷點 | 行為 |
|------|------|
| ≥1024 | 3 帳號卡片橫排，展開佔滿整列 |
| 768-1023 | 2+1 排列 |
| <768 | 單欄堆疊，Prompt 編輯器高度 200px |
| CardPreview | 桌面:右浮 240px；手機:表單底部 |

### 6. 測試

**後端**（5 個）：accounts 列表、PUT 寫回 TOML、PUT 含 prompt_content、preview 回傳 image_url、不存在 404

**前端**（4 個）：AccountCard 展開收合、表單雙向綁定、ColorMoodField 選中、PlatformsField 多選

### 7. 依賴

- `~/.imggen/accounts.toml` 存在
- `LevelUpConfig` 類別
- 需擴展 `config.py` 新增 TOML 寫入功能（或使用 `tomli-w` 套件）
- 可選：`@monaco-editor/react`（Phase 2 升級）

---

## 交付物總覽

### 後端

| 檔案 | 動作 |
|------|------|
| `web/api.py` | 修改：+10 endpoint |
| `src/db.py` | 修改：+3 DAO 方法 (find_scheduled, find_drafts, get_curation_stats) |
| `src/config.py` | 修改：+TOML 寫入擴展 |
| `tests/test_scheduling_api.py` | 新建 |
| `tests/test_curation_api.py` | 新建 |
| `tests/test_accounts_api.py` | 新建 |

### 前端

| 檔案 | 動作 |
|------|------|
| `App.tsx` | 修改：+3 Route |
| `Sidebar.tsx` | 修改：+3 NavItem |
| `api/queries.ts` | 修改：+10 hooks |
| `constants/accounts.ts` | 新建 |
| `pages/SchedulingPage.tsx` | 新建 |
| `pages/CurationPage.tsx` | 新建 |
| `pages/AccountSettingsPage.tsx` | 新建 |
| `features/scheduling/*.tsx` | 新建：11 元件 |
| `features/curation/*.tsx` | 新建：10 元件 |
| `features/settings/*.tsx` | 新建：9 元件 |
| `stores/useSchedulingStore.ts` | 新建 |
| `stores/useCurationStore.ts` | 新建 |
| `stores/useSettingsStore.ts` | 新建 |
| 前端測試 | 新建：14 個 |
| store 測試 | 新建：3 個 |

### 實施優先順序

| Phase | 頁面 | 原因 |
|-------|------|------|
| 1 | Account Settings (45) | 最少依賴，只需 LevelUpConfig |
| 2 | Curation (48) | 依賴 Cycle 2 爬蟲，但 UI 可先 mock |
| 3 | Scheduling (80) | 依賴 APPROVED 內容 + Drag & Drop 複雜度最高 |

---

## 風險與緩解

| 風險 | 頁面 | 緩解 |
|------|------|------|
| TOML 寫入不支援 array | E | 擴展 `_write_toml()` 或改用 `tomli-w` |
| Drag & Drop 跨瀏覽器 | C | HTML5 DnD + pointer events fallback |
| SSE 策展連線中斷 | D | 前端 retry + 後端 task 不中止 |
| accounts.toml 不存在 | E | API 回傳空帳號 + 引導 UI |
| 圖卡預覽速度慢 | E | debounce 500ms + loading skeleton |
