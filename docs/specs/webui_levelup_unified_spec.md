# Web UI LevelUp 統一規格：融合方案

**版本**: 2.0（融合新規劃簡化設計 + 舊規劃 5 頁面架構）
**日期**: 2026-04-04
**技術棧**: React 19 + Vite + Zustand 5 + TanStack Query 5 + Framer Motion + Tailwind CSS 4 + lucide-react

---

## 整體架構

```
5 頁面：Review → Curation → Scheduling → Settings → Dashboard
├─ Review     — 審核待發內容（DRAFT/PENDING_REVIEW → APPROVED）
├─ Curation   — 觸發策展爬蟲，SSE 顯示逐步進度（爬蟲→AI→圖卡→DRAFT）
├─ Scheduling — 視覺化日曆排期，可拖拽調整發布時間
├─ Settings   — 管理帳號配置、爬蟲 prompt、發布時間、色彩心情
└─ Dashboard  — 統計儀表板（已實作）
```

---

## 融合優化點

### 1️⃣ API 聚合（新規劃）

**原則**：減少前端查詢邏輯，邏輯集中在後端

| API 類別 | 舊規劃 | 新規劃合併 | 效果 |
|---------|--------|-----------|------|
| Review 列表 | `GET /api/content/pending` | `GET /api/content/review?status=,limit=` | 支援多狀態篩選 |
| 核准流程 | `POST /api/content/{id}/approve?force=` | `POST /api/content/{id}/approve` | 不用 force 參數 |
| Curation 進度 | SSE 無明確格式 | SSE + progress_callback | 逐步顯示爬蟲→AI→圖卡 |

### 2️⃣ Preflight 檢查（新規劃單次往返）

**舊規劃流程**：
```
核准 (force=false)
  → 檢查 ERROR 級警告
  → 回傳 needs_confirmation: true
  → 前端彈對話框
  → 用戶確認
  → 再核准 (force=true)  ← 第二次 HTTP 往返
```

**新規劃流程（融合採用）**：
```
核准
  → preflight_check() 自動執行
  → 回傳 {status: "OK"|"WARNING"|"ERROR", warnings: [...]}
  → 前端彈對話框（本地邏輯）
  → 用戶確認 → 上傳 → 完成  ← 單次 HTTP 往返
```

### 3️⃣ Progress Callback（新規劃 Phase B）

**daily_curation.py 改動（10 行）**：

```python
async def curate_for_account(
    account_type,
    scraper,
    config,
    dao,
    dry_run=False,
    progress_callback=None  # ← 新增：callback(type, **kwargs)
) -> int:
    count = 0
    for item in scraper.fetch():
        if progress_callback:
            progress_callback("item_fetched", account=account_type, title=item.title, source=item.source)
        
        result = call_claude_api(...)
        
        if result["should_publish"]:
            if progress_callback:
                progress_callback("generating_image", account=account_type)
            image_path = generate_image(...)
            dao.create(Content(...))
            if progress_callback:
                progress_callback("saved_draft", account=account_type, title=result["title"])
            count += 1
        else:
            if progress_callback:
                progress_callback("item_skipped", account=account_type, reason=result.get("reasoning"))
    return count
```

**後端 SSE 端點（Phase B）**：

```python
@app.post("/api/curation/run")
async def api_curation_run(req: CurationRunRequest):
    async def stream():
        yield sse("start", accounts=req.accounts)
        
        for acct_id in req.accounts:
            yield sse("account_start", account=acct_id)
            
            scraper = get_scraper_for_account(acct_id)
            config = LevelUpConfig()
            dao = ContentDAO()
            
            def emit(type, **kw):
                # 非同步生成器無法直接 yield，需要用全域隊列或 asyncio Queue
                events_queue.put_nowait({"type": type, **kw})
            
            count = await curate_for_account(
                acct_id, scraper, config, dao,
                progress_callback=emit
            )
            
            yield sse("account_done", account=acct_id, drafted=count)
        
        yield sse("done", total_drafted=total)
    
    return StreamingResponse(stream(), media_type="text/event-stream")
```

**前端收到的 SSE 流**：

```
data: {"type": "start", "accounts": ["A", "B", "C"]}
data: {"type": "account_start", "account": "A"}
data: {"type": "item_fetched", "account": "A", "title": "Claude 新功能", "source": "hacker_news"}
data: {"type": "generating_image", "account": "A"}
data: {"type": "saved_draft", "account": "A", "title": "Claude 新功能"}
data: {"type": "item_fetched", "account": "A", "title": "...", "source": "techcrunch"}
data: {"type": "item_skipped", "account": "A", "reason": "..."}
data: {"type": "account_done", "account": "A", "drafted": 1}
data: {"type": "account_start", "account": "B"}
...
data: {"type": "done", "total_drafted": 5}
```

### 4️⃣ 統一 ContentDetail 型別

所有 Review/Scheduling/Curation 頁回傳同樣的內容結構：

```python
class ContentDetail(BaseModel):
    id: str
    account_type: str  # "A" | "B" | "C"
    status: str  # "DRAFT" | "PENDING_REVIEW" | "APPROVED" | "PUBLISHED" | "REJECTED"
    content_type: str | None
    title: str
    body: str
    reasoning: str
    image_url: str | None  # /output/{filename}
    source_url: str | None
    source: str | None  # "hacker_news" | "techcrunch" | "bbc_sport" 等
    scheduled_time: str | None  # ISO 8601
    created_at: str
    updated_at: str
    # Review 頁專用
    preflight_warnings: list[str]  # 自動計算
    # 帳號信息（便於前端顯示）
    account_name: str
    platforms: list[str]
```

### 5️⃣ 清晰的 Zustand Store

**useReviewStore**：
```typescript
interface ReviewState {
  // 篩選
  filterAccount: string | null
  filterStatus: string[]  // ['DRAFT', 'PENDING_REVIEW']
  
  // 批次選擇
  batchMode: boolean
  selectedIds: Set<string>
  
  // 編輯模式
  editingId: string | null
  
  // Actions
  setFilterAccount, setFilterStatus, toggleBatchMode, toggleSelect, setEditingId
}
```

**useCurationStore**：
```typescript
interface CurationState {
  // 篩選
  accountFilter: string | null
  sourceFilter: string | null  // "hacker_news" | "techcrunch" | "bbc_sport" | "hbr" | "pmi"
  daysFilter: number | null  // null=all, 1=today, 7, 30
  
  // 進行中狀態
  isRunning: boolean
  progress: {
    type: string
    account: string
    title?: string
    count?: number
  }[]
  
  // Actions
  setFilters, reset, addProgress
}
```

---

## 後端 API 端點（融合後）

### Phase A：Review API（簡化版）

| 方法 | 路由 | 說明 | Request |
|------|------|------|---------|
| GET | `/api/content/review` | 列待審內容 | `?status=DRAFT,PENDING_REVIEW&account=A&limit=50` |
| GET | `/api/content/{id}/detail` | 單篇詳情 | — |
| POST | `/api/content/{id}/approve` | 核准（含 preflight） | `{publish_time?: "HH:MM"}` |
| POST | `/api/content/{id}/reject` | 捨棄 | `{reason?: string}` |
| PUT | `/api/content/{id}` | 編輯標題/內文 | `{title?, body?}` |
| POST | `/api/content/batch` | 批次核准/捨棄 | `{ids: [], action: "approve"\|"reject"}` |

### Phase B：Curation API（進度回調版）

| 方法 | 路由 | 說明 | Request |
|------|------|------|---------|
| POST | `/api/curation/run` | 觸發策展（SSE） | `{accounts: ["A","B","C"], dry_run: false}` |
| GET | `/api/curation/status` | 查詢狀態 | — |

**需改動**：`daily_curation.py` 加 progress_callback 參數（10 行）

### Phase C：Scheduling API

| 方法 | 路由 | 說明 | Request |
|------|------|------|---------|
| GET | `/api/content/scheduled` | 日期範圍排程 | `?start=2026-03-30&end=2026-04-06&account=A` |
| PATCH | `/api/content/{id}/reschedule` | 拖拽調整時間 | `{scheduled_time: "ISO8601"}` |

**需 ContentDAO 新增**：`find_scheduled(start, end, account)`

### Phase D：Curation 內容列表

| 方法 | 路由 | 說明 | Request |
|------|------|------|---------|
| GET | `/api/content/drafts` | DRAFT 列表 + 篩選 | `?account=A&source=hacker_news&days=7` |
| PATCH | `/api/content/{id}/status` | 狀態轉換 | `{status: "PENDING_REVIEW"\|"REJECTED"}` |
| GET | `/api/curation/stats` | 統計（今日/週/通過率） | — |

**需 ContentDAO 新增**：`find_drafts(account, source, days)`、`get_curation_stats()`

### Phase E：Account Settings API

| 方法 | 路由 | 說明 | Request |
|------|------|------|---------|
| GET | `/api/accounts` | 三帳號配置 | — |
| GET | `/api/accounts/{id}/prompt` | 讀 prompt 檔 | — |
| PUT | `/api/accounts/{id}` | 寫回配置 | `{name, platforms, publish_time, color_mood, tone, prompt_content?}` |
| POST | `/api/accounts/{id}/preview` | 生成預覽圖卡 | `{color_mood: "dark_tech"}` |

---

## 實作順序

```
Phase A（Review API + ReviewPage）
  ↓
Phase B（Curation API + progress_callback + CurationPage）
  ↓
Phase C（Scheduling API + SchedulingPage）
  ↓
Phase D（Curation 內容列表擴展）
  ↓
Phase E（Settings API + SettingsPage）
  ↓
路由整合（5 個頁面 + Sidebar）
```

---

## 前端架構

### Pages（5）
- `ReviewPage.tsx`
- `CurationPage.tsx`
- `SchedulingPage.tsx`
- `AccountSettingsPage.tsx`
- `DashboardPage.tsx`（已實作）

### Stores（4）
- `useReviewStore.ts`
- `useCurationStore.ts`
- `useSchedulingStore.ts`
- `useSettingsStore.ts`

### Hooks（共用）
- `useSSE.ts` — 通用 SSE 連線管理

---

## 估算

| 層級 | 項目 | 估算 |
|------|------|------|
| **後端** | Phase A-E API | ~250 行 Python |
| | daily_curation.py progress_callback | 10 行改動 |
| | DAO 新增方法 | ~80 行 |
| **前端** | 5 個 Page + 30+ 元件 | ~1200 行 TSX |
| | 4 個 Store | ~150 行 TypeScript |
| | 5 個 hooks | ~100 行 TypeScript |
| **測試** | 後端 API 測試 | ~20 個 |
| | 前端元件 + Store 測試 | ~25 個 |

---

## 關鍵差異總結

| 改進點 | 新規劃貢獻 | 效果 |
|--------|----------|------|
| API 聚合 | Review 用統一端點 | 減少前端複雜度 |
| Preflight 單次往返 | 核准不用 force 參數 | 更簡潔的核准流程 |
| Progress Callback | daily_curation.py 加 10 行 | 運營者看實時進度（爬蟲→AI→圖卡→保存） |
| ContentDetail 型別 | 所有頁共用同樣結構 | 統一數據格式 |
| Zustand 明確定義 | 每頁專有 store | 狀態管理不分散 |

---

## 驗收標準

### Review 頁
- [ ] 可篩選 DRAFT/PENDING_REVIEW，按帳號篩選
- [ ] 核准時自動 preflight，ERROR 級阻擋
- [ ] 單次 HTTP 往返完成核准
- [ ] 批次操作可一次核准多篇

### Curation 頁
- [ ] SSE 實時顯示逐步進度（爬蟲→AI→圖卡→保存）
- [ ] 可篩選帳號、來源、日期
- [ ] DRAFT 列表可直接在頁面轉為 PENDING_REVIEW

### Scheduling 頁
- [ ] 週曆和月曆視圖切換
- [ ] 可拖拽調整發布時間
- [ ] 顯示同時段衝突提示

### Settings 頁
- [ ] 修改帳號名稱、平台、發布時間
- [ ] 修改色彩心情並實時預覽圖卡
- [ ] Prompt 編輯器可修改爬蟲規則

### Dashboard
- [ ] 三帳號狀態卡片 ✅
- [ ] 今日排程時間表 ✅
- [ ] 最近內容列表 ✅

