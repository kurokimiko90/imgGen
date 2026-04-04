# 前端架構文檔

**項目**: LevelUp Web UI  
**技術棧**: React 19 + Vite + Zustand 5 + TanStack Query 5 + Tailwind CSS 4 + Framer Motion + lucide-react  
**本文檔日期**: 2026-04-04

---

## 目錄結構

```
web/frontend/src/
├── pages/
│   ├── GeneratePage.tsx           # 生成主頁（原有）
│   ├── DashboardPage.tsx          # 統計儀表板（原有）
│   ├── CaptionsPage.tsx           # 字幕功能（原有）
│   ├── HistoryPage.tsx            # 歷史記錄（原有）
│   ├── ToolsPage.tsx              # 工具頁面（原有）
│   ├── PresetsPage.tsx            # 預設頁面（原有）
│   ├── ReviewPage.tsx             # ✨ 待審內容審核（新）
│   ├── CurationPage.tsx           # ✨ 實時策展進度（新）
│   ├── SchedulingPage.tsx         # ✨ 視覺化排期（新）
│   └── AccountSettingsPage.tsx    # ✨ 帳號設定（新）
│
├── stores/
│   ├── useAppStore.ts             # 全局應用狀態（主題、折疊菜單）
│   ├── useReviewStore.ts          # ✨ Review 頁狀態（篩選、選擇）
│   ├── useCurationStore.ts        # ✨ Curation 頁狀態（進度）
│   ├── useSchedulingStore.ts      # ✨ Scheduling 頁狀態（日期、視圖）
│   └── useSettingsStore.ts        # ✨ Settings 頁狀態（面板、預覽）
│
├── api/
│   └── queries.ts                 # ✨ TanStack Query hooks（所有 API 調用）
│
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx            # ✨ 導航側邊欄（已添加 4 個新 nav item）
│   │   ├── NavItem.tsx
│   │   ├── PageTransition.tsx
│   │   ├── GlassCard.tsx
│   │   ├── ThemeSwitcher.tsx
│   │   └── ...
│   │
│   ├── features/
│   │   ├── review/                # ✨ Review 頁元件
│   │   │   ├── ReviewCard.tsx         待審內容卡片
│   │   │   ├── ReviewFilterBar.tsx    篩選條件欄
│   │   │   ├── EditDrawer.tsx         側邊編輯抽屜
│   │   │   ├── PreflightDialog.tsx    核准警告對話框
│   │   │   └── BatchBar.tsx           批次操作欄
│   │   │
│   │   ├── curation/               # ✨ Curation 頁元件
│   │   │   ├── CurationProgressFeed.tsx    SSE 進度動態
│   │   │   ├── DraftContentList.tsx        DRAFT 內容清單
│   │   │   └── CurationStatsBar.tsx        統計數據
│   │   │
│   │   ├── scheduling/             # ✨ Scheduling 頁元件
│   │   │   └── WeekCalendar.tsx         週曆視圖（可拖拽）
│   │   │
│   │   └── settings/               # ✨ Settings 頁元件
│   │       ├── AccountPanel.tsx         帳號設定面板
│   │       └── PromptEditor.tsx         Prompt 編輯器
│   │
│   └── ...其他共用元件
│
├── hooks/
│   ├── useSSE.ts                  # SSE 連線管理（可選）
│   └── ...其他 React hooks
│
├── test/
│   ├── setup.ts                   # Vitest setup
│   └── ...測試文件
│
├── App.tsx                        # ✨ 根應用（已添加 4 個新 route）
├── main.tsx
├── index.css
└── types.ts                       # TypeScript 類型定義
```

---

## 數據流架構

### 1. 狀態管理層級

```
┌─────────────────────────────────────┐
│       React Router (pages)          │
│  ReviewPage / CurationPage / ...    │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        ▼              ▼
    Zustand       TanStack Query
    Store         (Server State)
    (UI State)    
    │              │
    ├─ Review     ├─ useReviewContent
    ├─ Curation   ├─ useCurationStatus
    ├─ Scheduling ├─ useScheduledRange
    └─ Settings   └─ useAccountPrompt
```

### 2. Zustand Store 設計

**useReviewStore.ts** — Review 頁面本地狀態

```typescript
interface ReviewState {
  // 篩選狀態
  filterAccount: string | null              // 帳號篩選
  filterStatus: string[]                    // 多狀態篩選
  
  // 批次選擇模式
  batchMode: boolean
  selectedIds: Set<string>
  
  // 編輯/核准對話框
  editingId: string | null
  preflightWarnings: string[]
  pendingApproveId: string | null
  
  // Actions
  setFilterAccount: (account: string | null) => void
  setFilterStatus: (statuses: string[]) => void
  toggleBatchMode: () => void
  toggleSelect: (id: string) => void
  selectAll: (ids: string[]) => void
  clearSelection: () => void
  setEditingId: (id: string | null) => void
  showPreflightWarnings: (id: string, warnings: string[]) => void
  clearPreflightWarnings: () => void
}
```

**useCurationStore.ts** — Curation 頁面本地狀態

```typescript
interface CurationState {
  // 篩選
  accountFilter: string | null          // 帳號篩選
  sourceFilter: string | null           // 來源 (hacker_news 等)
  daysFilter: number | null             // 天數篩選
  
  // 進行中狀態
  isRunning: boolean
  progress: CurationProgress[]
  
  // Actions
  setAccountFilter: (account: string | null) => void
  setSourceFilter: (source: string | null) => void
  setDaysFilter: (days: number | null) => void
  setRunning: (running: boolean) => void
  addProgress: (event: CurationProgress) => void
  resetProgress: () => void
}

interface CurationProgress {
  type: string     // "item_fetched" | "generating_image" | "saved_draft" | "account_done" 等
  account: string
  title?: string
  source?: string
  count?: number
  timestamp: number
}
```

**useSchedulingStore.ts** — Scheduling 頁面本地狀態

```typescript
interface SchedulingState {
  // 視圖設定
  view: 'week' | 'month'
  weekStart: string                     // ISO date (YYYY-MM-DD)
  
  // 選擇
  selectedContentId: string | null
  accountFilter: string | null
  
  // Actions
  setView: (view: 'week' | 'month') => void
  setWeekStart: (date: string) => void
  selectContent: (id: string | null) => void
  setAccountFilter: (account: string | null) => void
  prevWeek: () => void
  nextWeek: () => void
}
```

**useSettingsStore.ts** — Settings 頁面本地狀態

```typescript
interface SettingsState {
  // 面板展開狀態
  expandedAccountId: string | null
  
  // 追蹤髒數據
  dirtyAccounts: Set<string>
  
  // 預覽 URL 快取
  previewUrls: Record<string, string>   // account_id → image_url
  
  // Actions
  setExpanded: (id: string | null) => void
  markDirty: (accountId: string) => void
  markClean: (accountId: string) => void
  setPreviewUrl: (accountId: string, url: string) => void
}
```

### 3. TanStack Query Hooks（api/queries.ts）

所有伺服器狀態查詢通過 `api/queries.ts` 中央管理：

```typescript
// Review 頁查詢
export function useReviewContent(params: {
  status: string
  account?: string
  limit?: number
}) {
  return useQuery({
    queryKey: ['review-content', params],
    queryFn: async () => {
      const res = await fetch(`/api/content/review?...`)
      return res.json() as { items: ContentDetail[] }
    }
  })
}

export function useApproveContent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { id: string; publish_time?: string }) => {
      const res = await fetch(`/api/content/${data.id}/approve`, {
        method: 'POST',
        body: JSON.stringify(data)
      })
      return res.json() as ApproveResponse
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-content'] })
    }
  })
}

// Curation 頁查詢
export function useCurationStatus() {
  return useQuery({
    queryKey: ['curation-status'],
    queryFn: async () => {
      const res = await fetch('/api/curation/status')
      return res.json()
    },
    refetchInterval: 5000  // 5 秒輪詢
  })
}

// Scheduling 頁查詢
export function useScheduledRange(params: {
  start: string
  end: string
  account?: string
}) {
  return useQuery({
    queryKey: ['scheduled-range', params],
    queryFn: async () => {
      const res = await fetch(`/api/content/scheduled?...`)
      return res.json() as { items: ContentDetail[] }
    }
  })
}

// Settings 頁查詢
export function useAccountPrompt(accountId: string) {
  return useQuery({
    queryKey: ['account-prompt', accountId],
    queryFn: async () => {
      const res = await fetch(`/api/accounts/${accountId}/prompt`)
      return res.json() as { content: string }
    }
  })
}

export function useUpdateAccount() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      accountId: string
      updates: Partial<AccountConfig>
    }) => {
      const res = await fetch(`/api/accounts/${data.accountId}`, {
        method: 'PUT',
        body: JSON.stringify(data.updates)
      })
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['account-settings'] })
    }
  })
}
```

---

## 元件設計

### ReviewPage 元件樹

```
ReviewPage
├─ 標題行 + 圖表
├─ ReviewFilterBar
│  ├─ AccountSelect
│  └─ StatusMultiSelect
├─ BatchBar (conditional)
│  ├─ SelectedCount
│  ├─ ApproveButton
│  ├─ RejectButton
│  └─ CancelButton
├─ ReviewCard (list)
│  ├─ ContentHeader (title, account badge)
│  ├─ ContentBody (preview text + image)
│  ├─ PrefightWarnings (if any)
│  ├─ PublishTimeInput (optional)
│  └─ ActionButtons (approve, reject, edit)
├─ EditDrawer (modal)
│  ├─ TitleInput
│  ├─ BodyTextarea
│  └─ SaveButton
└─ PreflightDialog (modal)
   ├─ ErrorList
   ├─ ActionButtons
   └─ CloseButton
```

### ReviewCard 詳細設計

```typescript
interface ReviewCardProps {
  item: ContentDetail
  selectable: boolean                 // 批次模式時為 true
  selected: boolean
  onApprove: (id: string, time?: string) => void
  onReject: (id: string) => void
  onEdit: (id: string) => void
  isApproving: boolean
  isRejecting: boolean
}

// 顯示內容
- 狀態徽章 (DRAFT / PENDING_REVIEW)
- 帳號徽章 (A / B / C)
- 來源徽章 (hacker_news / techcrunch)
- 標題 (可編輯)
- 摘要文本 (前 150 字)
- 縮圖圖片 (if image_url)
- Preflight 警告 (若有)
- 發布時間輸入框 (可選)
- 批次選擇框 (若 selectable)
- 操作按鈕 (approve, reject, edit)
```

### CurationPage 元件樹

```
CurationPage
├─ CurationControlBar
│  ├─ AccountFilter
│  ├─ SourceFilter
│  ├─ DaysFilter
│  └─ RunButton (觸發 SSE)
├─ CurationProgressFeed
│  ├─ EventItem (repeated)
│  │  ├─ Icon (各類事件)
│  │  ├─ EventText
│  │  └─ Timestamp
│  └─ ScrollToBottom
├─ CurationStatsBar
│  ├─ AccountA Stats (today/week/approval_rate)
│  ├─ AccountB Stats
│  └─ AccountC Stats
└─ DraftContentList
   ├─ FilterBar (optional)
   ├─ DraftItem (repeated)
   │  ├─ Thumbnail
   │  ├─ Metadata (account, source, title)
   │  ├─ SendToReviewButton
   │  └─ RejectButton
   └─ EmptyState
```

### SchedulingPage 元件樹

```
SchedulingPage
├─ ViewControls
│  ├─ ViewToggle (Week / Month)
│  ├─ WeekNavigation (← prev | date range | next →)
│  └─ TodayButton
├─ WeekCalendar
│  ├─ DayHeader (Mon, Tue, ..., Sun)
│  ├─ DayColumn (repeated × 7)
│  │  ├─ DayLabel (date)
│  │  ├─ TimeSlots
│  │  └─ ContentCard (draggable, repeated)
│  │     ├─ Title
│  │     ├─ AccountBadge (color by account)
│  │     └─ PublishTime
│  └─ DropZones (hidden, on drag)
└─ ContentDetail (side panel)
   ├─ FullContent
   ├─ EditButton
   └─ PublishButton
```

### AccountSettingsPage 元件樹

```
AccountSettingsPage
├─ PageHeader ("Account Settings")
├─ SettingsPanelA (collapsible)
│  ├─ ExpandButton
│  ├─ AccountName (editable)
│  ├─ PlatformCheckboxes (Twitter, Instagram, TikTok)
│  ├─ PublishTimeSelect
│  ├─ ColorMoodSelect
│  ├─ PromptEditor (expandable textarea)
│  ├─ PreviewButton
│  └─ SaveButton
├─ SettingsPanelB (same structure)
└─ SettingsPanelC (same structure)

// 預覽區域
PreviewSection
├─ ColorMoodSelector
├─ PreviewImage (if generated)
└─ LoadingSpinner (during generation)
```

---

## 狀態轉換示例

### Review → Approve 流程

```typescript
// 用戶點擊「核准」按鈕
const handleApprove = async (id: string, publishTime?: string) => {
  // 1. 發出 mutation（帶著 publish_time）
  const result = await approveMutation.mutateAsync({
    id,
    publish_time: publishTime
  })
  
  // 2. 後端執行 preflight，回傳 {status, warnings}
  if (result.status === 'ERROR') {
    // 3. 若有 ERROR 級警告，顯示對話框
    useReviewStore.getState().showPreflightWarnings(id, result.warnings)
  } else if (result.status === 'WARNING') {
    // 4. 若有 WARNING，也顯示但可繼續
    useReviewStore.getState().showPreflightWarnings(id, result.warnings)
  } else {
    // 5. 成功，自動刷新列表
    queryClient.invalidateQueries({ queryKey: ['review-content'] })
  }
}
```

### Curation → SSE 進度流程

```typescript
// CurationPage.tsx 中的 SSE 邏輯
useEffect(() => {
  if (!isRunning) return
  
  // 1. 打開 EventSource 連線
  const eventSource = new EventSource('/api/curation/run')
  
  // 2. 監聽進度事件
  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data)
    
    // 3. 更新 store 的進度列表
    useCurationStore.getState().addProgress({
      type: data.type,
      account: data.account,
      title: data.title,
      timestamp: Date.now()
    })
  })
  
  // 4. 完成或錯誤時關閉
  eventSource.addEventListener('error', () => {
    eventSource.close()
    useCurationStore.getState().setRunning(false)
  })
  
  return () => eventSource.close()
}, [isRunning])
```

---

## 路由配置（App.tsx）

```typescript
<Routes>
  <Route path="/" element={<GeneratePage />} />
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/review" element={<ReviewPage />} />
  <Route path="/curation" element={<CurationPage />} />
  <Route path="/scheduling" element={<SchedulingPage />} />
  <Route path="/settings" element={<AccountSettingsPage />} />
  <Route path="/captions" element={<CaptionsPage />} />
  <Route path="/history" element={<HistoryPage />} />
  <Route path="/tools" element={<ToolsPage />} />
  <Route path="/presets" element={<PresetsPage />} />
</Routes>
```

側邊欄導航項 (Sidebar.tsx)：
```typescript
const NAV_ITEMS = [
  { to: '/', label: 'Generate', icon: Sparkles },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/review', label: 'Review', icon: ClipboardCheck },
  { to: '/curation', label: 'Curation', icon: Rss },
  { to: '/scheduling', label: 'Scheduling', icon: Calendar },
  { to: '/settings', label: 'Settings', icon: Settings },
  // ... 其他
]
```

---

## 開發工作流程

### 新增頁面的標準步驟

1. **建立 Page 元件** (`pages/PageName.tsx`)
2. **建立 Zustand Store** (`stores/usePageStore.ts`)
3. **在 api/queries.ts 新增查詢 hooks**
4. **新增路由** (App.tsx)
5. **新增導航項** (Sidebar.tsx)
6. **建立元件** (components/features/pagename/)
7. **撰寫測試** (if applicable)

### TypeScript 型別

```typescript
// ContentDetail — 統一的內容詳情型別
interface ContentDetail {
  id: string
  account_type: 'A' | 'B' | 'C'
  status: ContentStatus
  content_type?: string
  title: string
  body: string
  reasoning: string
  image_url?: string
  source_url?: string
  source?: string
  scheduled_time?: string  // ISO 8601
  created_at: string
  updated_at: string
  preflight_warnings: string[]
  account_name: string
  platforms: string[]
}

type ContentStatus = 'DRAFT' | 'PENDING_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'ANALYZED'
```

---

## 性能優化

### 1. Lazy Loading

```typescript
const ReviewPage = lazy(() => import('./ReviewPage'))
const CurationPage = lazy(() => import('./CurationPage'))
const SchedulingPage = lazy(() => import('./SchedulingPage'))
const AccountSettingsPage = lazy(() => import('./AccountSettingsPage'))
```

### 2. React Query 快取

```typescript
// 30 秒內不重新獲取
queryClient.setDefaultOptions({
  queries: {
    staleTime: 1000 * 30,
    gcTime: 1000 * 60 * 5
  }
})
```

### 3. Memoization

```typescript
const ReviewCard = memo(function ReviewCard(props: ReviewCardProps) {
  // 只在 props 改變時重新渲染
  return ...
})
```

---

## 測試策略

### 單元測試
- Store actions
- Utility functions
- Hook 邏輯

### 整合測試
- Component + Store 交互
- API 調用 mock

### E2E 測試
- Review → Approve 完整流程
- Curation SSE 進度
- Scheduling 拖拽

---

## 相關文檔

- `docs/LEVELUP_IMPLEMENTATION.md` — 實作完成檔
- `API_GUIDE.md` — API 端點參考（本目錄）
- `../../CLAUDE.md` — 項目整體命令與架構
