# LevelUp API 參考指南

**基礎 URL**: `http://localhost:8000`  
**後端服務**: FastAPI (`web/api.py`)

---

## Phase A：Review API

### GET /api/content/review

取得待審內容列表（支援多狀態篩選）

**Query Parameters:**
```
?status=DRAFT,PENDING_REVIEW      # 逗號分隔的狀態列表
&account=A                        # 帳號篩選 (A|B|C)
&limit=50                         # 結果數量限制
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "content_001",
      "account_type": "A",
      "status": "DRAFT",
      "content_type": "news",
      "title": "AI 新進展",
      "body": "詳細內容...",
      "reasoning": "摘要理由...",
      "image_url": "/output/card_001.png",
      "source_url": "https://example.com/article",
      "source": "hacker_news",
      "scheduled_time": null,
      "created_at": "2026-04-04T10:30:00Z",
      "updated_at": "2026-04-04T10:30:00Z",
      "preflight_warnings": [],
      "account_name": "Account A",
      "platforms": ["twitter", "instagram"]
    }
  ],
  "total": 5
}
```

**Frontend 調用:**
```typescript
const { data, isLoading, isError } = useReviewContent({
  status: filterStatus.join(','),
  account: filterAccount,
  limit: 50
})
```

---

### GET /api/content/{id}/detail

取得單篇內容詳情

**Path Parameters:**
```
{id}    # 內容 ID
```

**Response (200 OK):**
```json
{
  "id": "content_001",
  "account_type": "A",
  "status": "DRAFT",
  // ... 同 /api/content/review 中的單項結構
}
```

**Frontend 調用:**
```typescript
const { data } = useContentDetail(id)
```

---

### POST /api/content/{id}/approve

核准待發內容（自動執行 preflight 檢查，單次往返）

**Path Parameters:**
```
{id}    # 內容 ID
```

**Request Body:**
```json
{
  "publish_time": "14:30"    // 可選，HH:MM 格式
}
```

**Response (200 OK) — 成功通過檢查:**
```json
{
  "status": "OK",
  "id": "content_001",
  "warnings": []
}
```

**Response (200 OK) — 有警告但可繼續:**
```json
{
  "status": "WARNING",
  "id": "content_001",
  "warnings": [
    "[WARNING] Twitter 字數接近上限 (276/280 字)"
  ]
}
```

**Response (200 OK) — 有阻擋性錯誤:**
```json
{
  "status": "ERROR",
  "id": "content_001",
  "warnings": [
    "[ERROR] Instagram 必須包含圖片",
    "[ERROR] 標題不能為空"
  ]
}
```

**Frontend 邏輯:**
```typescript
const handleApprove = async (id: string, publishTime?: string) => {
  const result = await approveMutation.mutateAsync({
    id,
    publish_time: publishTime
  })
  
  if (result.status === 'ERROR') {
    // 顯示對話框阻擋
    showPreflightDialog(result.warnings)
  } else if (result.status === 'WARNING') {
    // 顯示警告但可繼續
    showWarningDialog(result.warnings)
  } else {
    // 成功，刷新列表
    invalidateQuery('review-content')
  }
}
```

---

### POST /api/content/{id}/reject

捨棄待發內容

**Path Parameters:**
```
{id}    # 內容 ID
```

**Request Body:**
```json
{
  "reason": "不符合主題"    // 可選
}
```

**Response (200 OK):**
```json
{
  "id": "content_001",
  "status": "REJECTED",
  "updated_at": "2026-04-04T11:00:00Z"
}
```

---

### PUT /api/content/{id}

編輯內容（標題、內文）

**Path Parameters:**
```
{id}    # 內容 ID
```

**Request Body:**
```json
{
  "title": "新標題",      // 可選
  "body": "新內文..."     // 可選
}
```

**Response (200 OK):**
```json
{
  "id": "content_001",
  "title": "新標題",
  "body": "新內文...",
  "updated_at": "2026-04-04T11:05:00Z"
}
```

---

### POST /api/content/batch

批次核准或捨棄

**Request Body:**
```json
{
  "ids": ["content_001", "content_002", "content_003"],
  "action": "approve"     // "approve" | "reject"
}
```

**Response (200 OK):**
```json
{
  "processed": 3,
  "succeeded": 3,
  "failed": 0
}
```

**Frontend 調用:**
```typescript
const handleBatchApprove = async () => {
  await batchMutation.mutateAsync({
    ids: Array.from(selectedIds),
    action: 'approve'
  })
  clearSelection()
}
```

---

## Phase B：Curation API

### POST /api/curation/run

觸發策展爬蟲，串流化進度（SSE）

**Request Body:**
```json
{
  "accounts": ["A", "B", "C"],    // 帳號列表
  "dry_run": false                 // 布林值，不保存到 DB
}
```

**Response: Server-Sent Events (SSE)**

連線建立後，伺服器持續推送事件流：

```
data: {"type": "start", "accounts": ["A", "B", "C"]}

data: {"type": "account_start", "account": "A"}

data: {"type": "item_fetched", "account": "A", "title": "Claude 新功能", "source": "hacker_news"}

data: {"type": "generating_image", "account": "A"}

data: {"type": "saved_draft", "account": "A", "title": "Claude 新功能", "drafted_count": 1}

data: {"type": "item_fetched", "account": "A", "title": "OpenAI o1", "source": "techcrunch"}

data: {"type": "item_skipped", "account": "A", "reason": "not relevant"}

data: {"type": "account_done", "account": "A", "drafted": 2}

data: {"type": "account_start", "account": "B"}

... (account B 和 C 的進度) ...

data: {"type": "done", "total_drafted": 5}
```

**事件型別說明:**

| 事件 | 欄位 | 說明 |
|------|------|------|
| `start` | accounts | 策展開始，列出所有帳號 |
| `account_start` | account | 開始策展某帳號 |
| `item_fetched` | account, title, source | 爬蟲取得一篇文章 |
| `generating_image` | account | 開始生成圖卡 |
| `saved_draft` | account, title | 圖卡已保存為 DRAFT |
| `item_skipped` | account, reason | 文章不符合條件 |
| `item_error` | account, error | 處理文章時出錯 |
| `account_done` | account, drafted | 該帳號完成，共草稿 N 篇 |
| `done` | total_drafted | 全部完成 |

**Frontend SSE 邏輯:**
```typescript
useEffect(() => {
  if (!isRunning) return
  
  const eventSource = new EventSource('/api/curation/run?accounts=A,B,C')
  
  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse(event.data)
    useCurationStore.getState().addProgress(data)
  })
  
  eventSource.addEventListener('error', () => {
    eventSource.close()
    useCurationStore.getState().setRunning(false)
  })
  
  return () => eventSource.close()
}, [isRunning])
```

---

### GET /api/curation/status

查詢當前策展狀態

**Response (200 OK):**
```json
{
  "is_running": false,
  "accounts": ["A", "B", "C"],
  "drafted_today": 5,
  "drafted_this_week": 23
}
```

---

### GET /api/curation/stats

取得策展統計（今日/本週/通過率）

**Response (200 OK):**
```json
{
  "accounts": {
    "A": {
      "today": 2,
      "this_week": 8,
      "approval_rate": 0.75
    },
    "B": {
      "today": 1,
      "this_week": 5,
      "approval_rate": 0.60
    },
    "C": {
      "today": 2,
      "this_week": 10,
      "approval_rate": 0.80
    }
  },
  "total_today": 5,
  "total_this_week": 23
}
```

**Frontend 調用:**
```typescript
const { data: stats } = useCurationStats()

// 顯示在 CurationStatsBar 中
stats?.accounts.A.today  // 帳號 A 今日草稿數
```

---

## Phase C：Scheduling API

### GET /api/content/scheduled

取得日期範圍內的排定內容

**Query Parameters:**
```
?start=2026-04-04              # 開始日期 (YYYY-MM-DD)
&end=2026-04-11                # 結束日期
&account=A                     # 帳號篩選 (可選)
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "content_005",
      "account_type": "A",
      "status": "APPROVED",
      "title": "每週總結",
      "image_url": "/output/card_005.png",
      "scheduled_time": "2026-04-05T14:30:00Z",
      // ... 其他欄位
    }
  ],
  "total": 12
}
```

**Frontend 日曆邏輯:**
```typescript
const startOfWeek = getMonday(new Date())
const endOfWeek = addDays(startOfWeek, 7)

const { data: scheduled } = useScheduledRange({
  start: formatISO(startOfWeek),
  end: formatISO(endOfWeek),
  account: filterAccount
})

// 按日期分組
const byDate = groupBy(scheduled?.items, (item) => {
  return item.scheduled_time?.split('T')[0]
})
```

---

### PATCH /api/content/{id}/reschedule

調整排定時間（從拖拽）

**Path Parameters:**
```
{id}    # 內容 ID
```

**Request Body:**
```json
{
  "scheduled_time": "2026-04-06T16:00:00Z"    // ISO 8601
}
```

**Response (200 OK):**
```json
{
  "id": "content_005",
  "scheduled_time": "2026-04-06T16:00:00Z",
  "updated_at": "2026-04-04T11:15:00Z"
}
```

**Frontend 拖拽實現:**
```typescript
const handleDrop = async (contentId: string, newDate: Date) => {
  const newISO = newDate.toISOString()
  
  await reschedule.mutateAsync({
    id: contentId,
    scheduled_time: newISO
  })
  
  // 刷新日曆
  queryClient.invalidateQueries({ queryKey: ['scheduled-range'] })
}
```

---

## Phase D：Drafts 列表 + 統計

### GET /api/content/drafts

取得 DRAFT 狀態的內容列表

**Query Parameters:**
```
?account=A                # 帳號篩選 (可選)
&source=hacker_news       # 來源篩選 (可選)
&days=7                   # 天數篩選 (1|7|30，可選)
```

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": "content_002",
      "account_type": "A",
      "status": "DRAFT",
      "title": "新聞標題",
      "source": "hacker_news",
      "image_url": "/output/card_002.png",
      "created_at": "2026-04-04T09:45:00Z"
      // ... 其他欄位
    }
  ],
  "total": 3,
  "account": "A",
  "source": "hacker_news",
  "days": 7
}
```

---

### PATCH /api/content/{id}/status

更新內容狀態

**Path Parameters:**
```
{id}    # 內容 ID
```

**Request Body:**
```json
{
  "status": "PENDING_REVIEW"    // 或 "REJECTED"
}
```

**Response (200 OK):**
```json
{
  "id": "content_002",
  "status": "PENDING_REVIEW",
  "updated_at": "2026-04-04T11:20:00Z"
}
```

---

## Phase E：Account Settings API

### GET /api/accounts/{id}

取得帳號配置

**Path Parameters:**
```
{id}    # 帳號 ID (A|B|C)
```

**Response (200 OK):**
```json
{
  "id": "A",
  "name": "Account A",
  "platforms": ["twitter", "instagram"],
  "publish_time": "14:30",
  "color_mood": "dark_tech",
  "tone": "professional"
}
```

---

### GET /api/accounts/{id}/prompt

讀取帳號的策展 Prompt

**Path Parameters:**
```
{id}    # 帳號 ID
```

**Response (200 OK):**
```json
{
  "id": "A",
  "content": "你是一位科技新聞編輯...\n\n評估標準：\n1. 與 AI/ML 相關\n2. 標題在 50 字以內\n3. ..."
}
```

**Frontend 編輯邏輯:**
```typescript
const { data: prompt } = useAccountPrompt(accountId)

// 在 PromptEditor textarea 中顯示
<textarea value={prompt?.content} onChange={...} />
```

---

### PUT /api/accounts/{id}

更新帳號配置並寫回 TOML

**Path Parameters:**
```
{id}    # 帳號 ID
```

**Request Body:**
```json
{
  "name": "新帳號名稱",
  "platforms": ["twitter", "instagram", "tiktok"],
  "publish_time": "16:00",
  "color_mood": "bold_contrast",
  "tone": "casual"
}
```

**Response (200 OK):**
```json
{
  "id": "A",
  "updated_at": "2026-04-04T11:30:00Z"
}
```

**後端實現:**
```python
@app.put("/api/accounts/{id}")
def update_account(id: str, updates: AccountUpdateRequest):
    config = LevelUpConfig()
    # 白名單過濾 + 更新
    config.save_account(id, updates.dict(exclude_unset=True))
    return {"id": id, "updated_at": datetime.now().isoformat()}
```

---

### POST /api/accounts/{id}/preview

生成帳號的預覽圖卡

**Path Parameters:**
```
{id}    # 帳號 ID
```

**Request Body:**
```json
{
  "color_mood": "warm_earth"    // 可選，測試特定色彩心情
}
```

**Response (200 OK):**
```json
{
  "image_url": "/output/preview_A_20260404.png",
  "generated_at": "2026-04-04T11:35:00Z"
}
```

**Frontend 預覽邏輯:**
```typescript
const handlePreview = async (accountId: string, colorMood?: string) => {
  const result = await preview.mutateAsync({
    accountId,
    color_mood: colorMood
  })
  
  useSettingsStore.getState().setPreviewUrl(accountId, result.image_url)
}
```

---

## 錯誤回應

### 400 Bad Request

```json
{
  "detail": "Invalid status value"
}
```

### 404 Not Found

```json
{
  "detail": "Content not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## 常用 Frontend 模式

### 查詢 Hook 模式

```typescript
// 查詢
const { data, isLoading, isError, error } = useReviewContent({
  status: 'DRAFT,PENDING_REVIEW',
  limit: 50
})

// 檢查狀態
if (isLoading) return <Spinner />
if (isError) return <ErrorAlert error={error} />
if (!data?.items.length) return <EmptyState />

// 顯示數據
return data.items.map((item) => <ReviewCard key={item.id} item={item} />)
```

### Mutation Hook 模式

```typescript
const mutation = useMutation({
  mutationFn: async (data) => {
    const res = await fetch(url, {
      method: 'POST',
      body: JSON.stringify(data)
    })
    return res.json()
  },
  onSuccess: () => {
    // 刷新相關查詢
    queryClient.invalidateQueries({ queryKey: ['content'] })
    // 顯示成功訊息
    showToast('Success!')
  },
  onError: (error) => {
    showToast('Error: ' + error.message, 'error')
  }
})

// 調用
const handleClick = () => {
  mutation.mutate({ id: '123', ... })
}

// 按鈕狀態
<button disabled={mutation.isPending}>
  {mutation.isPending ? 'Loading...' : 'Submit'}
</button>
```

---

## 相關文檔

- `ARCHITECTURE.md` — 前端架構設計
- `../../docs/LEVELUP_IMPLEMENTATION.md` — 實作完成檔
- `../../CLAUDE.md` — 項目整體資訊
