# Cycle 4 實施規格：HITL 審核系統

**版本**: 1.0（Planner Agent 產出，基於原始碼驗證）
**日期**: 2026-03-31
**評分**: 100
**時程**: 第 5-6 週

---

## 1. 執行目標與成功指標

### 目標
建立終端機互動式審核系統（`scripts/audit.py`），讓操作者可在 15 分鐘內完成 21 篇內容的批次審核，包含核准、編輯、捨棄操作，並在核准時自動執行 Pre-flight Check 與排程。

### 成功指標
- 週日 15 分鐘內可完成 21 篇批次審核
- 核准後 `scheduled_time` 自動對應帳號黃金時段（`AccountConfig.publish_time`）
- IG 無圖時 Pre-flight 攔截並顯示警告
- Markdown 匯出後可在手機編輯、回寫後正確更新 DB
- 測試覆蓋率 >= 80%

---

## 2. 前置依賴盤點

### Cycle 1 交付物（已完成，直接使用）

| 交付物 | 路徑 | 使用方式 |
|--------|------|---------|
| Content dataclass | `src/content.py` | 讀取欄位、呼叫 `transition_to()` |
| ContentDAO | `src/db.py` | `find_by_status()`、`update()` |
| LevelUpConfig + AccountConfig | `src/config.py` | `get_account()` 取得 `platforms`、`publish_time` |

### Cycle 2 交付物（必須先完成）

| 交付物 | 為何需要 |
|--------|---------|
| `scripts/daily_curation.py` | 產出 DRAFT → PENDING_REVIEW 狀態的內容 |

**注意**: 開發時可用手動插入的測試資料，不需真正等 Cycle 2 完成。

---

## 3. 現有 API 真實簽名盤點（Planner Agent 實際讀取）

### Content 模型

```python
class ContentStatus(str, Enum):
    DRAFT = 'DRAFT'
    PENDING_REVIEW = 'PENDING_REVIEW'
    APPROVED = 'APPROVED'
    PUBLISHED = 'PUBLISHED'
    ANALYZED = 'ANALYZED'
    REJECTED = 'REJECTED'

VALID_TRANSITIONS = {
    ContentStatus.DRAFT: {ContentStatus.PENDING_REVIEW, ContentStatus.REJECTED},
    ContentStatus.PENDING_REVIEW: {ContentStatus.APPROVED, ContentStatus.REJECTED},
    ContentStatus.APPROVED: {ContentStatus.PUBLISHED},
    ContentStatus.PUBLISHED: {ContentStatus.ANALYZED},
}

@dataclass
class Content:
    id: str
    account_type: AccountType
    status: ContentStatus = ContentStatus.DRAFT
    content_type: ContentType = ContentType.NEWS_RECAP
    title: str = ""
    body: str = ""
    image_path: Optional[str] = None
    reasoning: str = ""
    scheduled_time: Optional[datetime] = None
    ...

    def transition_to(self, new_status: ContentStatus) -> None:
        # mutating 方法，直接修改 self.status + self.updated_at
        # 非法轉換拋 InvalidTransitionError
```

### ContentDAO

```python
class ContentDAO:
    def find_by_status(self, status: ContentStatus, account_type: str | None = None) -> list[Content]
        # account_type 是 str | None（不是 AccountType enum），需用 AccountType.A.value
    def update(self, content: Content) -> None  # 整筆覆寫
    def find_by_id(self, content_id: str) -> Content | None
```

### LevelUpConfig / AccountConfig

```python
@dataclass
class AccountConfig:
    name: str
    platforms: list[str]   # ["threads", "x", "instagram"]
    publish_time: str      # "HH:MM" 格式
    color_mood: str
    prompt_file: str
    tone: str

class LevelUpConfig:
    def get_account(self, account_type: str) -> AccountConfig
    def list_accounts(self) -> dict[str, AccountConfig]
```

---

## 4. 架構變更總覽

### 新建檔案

| 檔案 | 角色 |
|------|------|
| `scripts/audit.py` | 終端機互動式審核主程式 |
| `src/preflight.py` | Pre-flight check 邏輯 |
| `src/scheduler.py` | scheduled_time 計算邏輯 |
| `src/markdown_io.py` | Markdown 匯出/回寫邏輯 |
| `tests/test_audit.py` | 審核流程測試 |
| `tests/test_preflight.py` | Pre-flight check 測試 |
| `tests/test_scheduler.py` | 排程計算測試 |
| `tests/test_markdown_io.py` | Markdown 匯出/回寫測試 |

### 修改檔案

**無**。Cycle 4 是純消費者，不改動 Cycle 1 的交付物。

---

## 5. 任務分解

### Phase 1：Pre-flight Check 模組

#### 任務 1.1：`src/preflight.py`（新建）

```python
def preflight_check(content: Content, platforms: list[str]) -> list[str]:
    """驗證內容是否符合各平台發布限制，回傳警告列表。"""
```

**完整規則清單**：

| 規則 | 平台 | 條件 | 警告訊息 | 嚴重度 |
|------|------|------|---------|--------|
| R1 | x | `len(body) > 280` | `"X 字數超限（{actual} / 280）"` | WARNING |
| R2 | threads | `len(body) > 500` | `"Threads 字數超限（{actual} / 500）"` | WARNING |
| R3 | instagram | `image_path is None` | `"IG 需要圖片，目前無附圖"` | ERROR |
| R4 | instagram | `image_path exists but file not found` | `"IG 圖片路徑不存在"` | ERROR |
| R5 | 全平台 | `not title.strip()` | `"標題為空"` | ERROR |
| R6 | 全平台 | `not body.strip()` | `"內文為空"` | ERROR |
| R7 | linkedin | `len(body) > 3000` | `"LinkedIn 字數超限（{actual} / 3000）"` | WARNING |

#### 任務 1.2：`tests/test_preflight.py`（9 個測試）

```
test_preflight_passes_clean_content()
test_preflight_warns_x_overlength()
test_preflight_warns_threads_overlength()
test_preflight_warns_ig_no_image()
test_preflight_warns_ig_image_not_exists()
test_preflight_warns_empty_title()
test_preflight_warns_empty_body()
test_preflight_multiple_platforms_multiple_warnings()
test_preflight_warns_linkedin_overlength()
```

---

### Phase 2：排程計算模組

#### 任務 2.1：`src/scheduler.py`（新建）

```python
def calculate_scheduled_time(
    publish_time: str,        # "HH:MM" from AccountConfig
    base_date: date | None = None  # None = 明天
) -> datetime:
    """計算下一個可用的發布時間。過去的時間自動順延到隔天。"""

def assign_scheduled_times(
    contents: list[Content],
    publish_time: str,
    base_date: date | None = None,
    interval_minutes: int = 60,
) -> list[Content]:
    """為一批內容分配排程時間，每篇間隔 interval_minutes。
    回傳新 Content 物件列表（不修改原始物件）。"""
```

#### 任務 2.2：`tests/test_scheduler.py`（7 個測試）

```
test_calculate_scheduled_time_basic()
test_calculate_scheduled_time_defaults_to_tomorrow()
test_calculate_scheduled_time_past_rolls_to_next_day()
test_assign_scheduled_times_single()
test_assign_scheduled_times_multiple_with_interval()
test_assign_scheduled_times_immutability()
test_calculate_scheduled_time_invalid_format()
```

---

### Phase 3：Markdown 匯出/回寫模組

#### 任務 3.1：`src/markdown_io.py`（新建）

```python
def export_markdown(
    contents: list[Content],
    output_path: Path,
    account_configs: dict[str, AccountConfig] | None = None,
) -> Path:
    """匯出 Content 列表為 Markdown 檔案。"""

def parse_markdown(file_path: Path) -> list[dict]:
    """解析 review.md，回傳 [{id, action, body}, ...]"""

def import_markdown(
    file_path: Path,
    dao: ContentDAO,
    config: LevelUpConfig,
) -> dict:
    """讀取 review.md 並批次更新 DB。
    回傳 {"approved": int, "rejected": int, "skipped": int, "errors": list}"""
```

**Markdown 格式規格**：

```markdown
# Content Review - 2026-04-01

---

## [PENDING_REVIEW] ID:42 · 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: Claude 4.5 支援原生工具呼叫
**內文**:
Claude 4.5 正式發布...

**Reasoning**: Claude 升版是 AI 帳號核心受眾...
**圖卡**: output/draft_042.png
**Action**: SKIP  <!-- 改成 APPROVE / REJECT / SKIP -->

---
```

解析邏輯：
1. `---` 分割區塊
2. Regex 提取 `ID:(\d+)` → id
3. Regex 提取 `\*\*Action\*\*:\s*(APPROVE|REJECT|SKIP)` → action
4. Regex 提取 body（若有修改）

#### 任務 3.2：`tests/test_markdown_io.py`（11 個測試）

```
test_export_md_writes_all_pending()
test_export_md_format_correct()
test_export_md_default_action_is_skip()
test_parse_md_approve()
test_parse_md_reject()
test_parse_md_skip()
test_parse_md_modified_body()
test_parse_md_unmodified_body()
test_import_md_updates_db_correctly()
test_import_md_returns_summary()
test_import_md_invalid_id_reports_error()
```

---

### Phase 4：終端機互動式審核主程式

#### 任務 4.1：`scripts/audit.py`（新建）

**CLI 介面**：

```bash
python scripts/audit.py                        # 互動式審核
python scripts/audit.py --account A            # 只審帳號 A
python scripts/audit.py --batch                # 快速批次模式
python scripts/audit.py --export-md            # 匯出 review.md
python scripts/audit.py --import-md review.md  # 回寫 DB
```

**函數清單**：

```python
def audit(account, batch, export_md, import_md, db_path, config_path):
    """HITL 內容審核系統 — Click CLI 入口"""

def _run_interactive(contents, dao, config) -> dict:
    """互動式審核主迴圈，回傳 {approved, rejected, skipped}"""

def _display_content(content, index, total, account_config) -> None:
    """顯示單篇內容審核畫面"""

def _handle_action(action, content, dao, account_config) -> str:
    """處理使用者操作 (a/e/d/s/q)，回傳結果描述"""

def _open_editor(body: str) -> str:
    """開啟 $EDITOR 編輯 body"""

def _print_summary(summary: dict) -> None:
    """印出審核摘要"""
```

**完整互動流程**：

```
════════════════════════════════════════
[3/21]  帳號 A · NEWS_RECAP · 2026-04-01
════════════════════════════════════════
標題：Claude 4.5 支援原生工具呼叫

內文：
Claude 4.5 正式發布，首度支援原生工具呼叫...

Reasoning：
Claude 升版是 AI 帳號核心受眾每週必看話題，
預計互動率高於平均 2×

圖卡：output/draft_042.png
────────────────────────────────────────
(A) 核准  (E) 編輯並核准  (D) 捨棄  (S) 跳過  (Q) 離開
```

**操作邏輯**：

| 按鍵 | 動作 |
|------|------|
| A | preflight_check → 有 warning 則詢問確認 → `transition_to(APPROVED)` → 計算 `scheduled_time` → `dao.update()` |
| E | `_open_editor(body)` → 更新 body → 同 A 流程 |
| D | `transition_to(REJECTED)` → `dao.update()` |
| S | 不動，前進下一篇 |
| Q | 印出摘要，離開 |

**批次模式（`--batch`）**：
- 自動 APPROVE 所有 PENDING_REVIEW
- 有 ERROR 級 preflight 警告的自動 SKIP
- 結束後印出摘要

**$EDITOR 處理**：
- 依序嘗試 `$EDITOR` → `$VISUAL` → `vim` → `nano`
- 全部失敗則印出錯誤訊息並跳過編輯

#### 任務 4.2：`tests/test_audit.py`（9 個測試）

```
test_approve_sets_status_approved()
test_approve_sets_scheduled_time()
test_reject_sets_status_rejected()
test_skip_preserves_status()
test_approve_with_preflight_warnings_shows_warnings()
test_edit_updates_body()
test_batch_mode_processes_all_drafts()
test_batch_mode_skips_preflight_errors()
test_run_interactive_returns_summary()
```

---

## 6. 依賴關係圖

```
Phase 1: preflight.py ────────────┐
                                   ├→ Phase 4: audit.py
Phase 2: scheduler.py ────────────┤
                                   │
Phase 3: markdown_io.py ──────────┘
         (depends on Phase 1 + Phase 2)

Phase 1 和 Phase 2 可並行開發。

外部依賴：
  Cycle 1 (已完成): content.py, db.py, config.py
  Cycle 2 (進行中): daily_curation.py 產出 DRAFT 資料
```

**建議實施順序**：
1. Phase 1 + Phase 2（並行）
2. Phase 3
3. Phase 4

---

## 7. 測試策略

| 檔案 | 測試數 | 類型 |
|------|--------|------|
| `tests/test_preflight.py` | 9 | Unit |
| `tests/test_scheduler.py` | 7 | Unit |
| `tests/test_markdown_io.py` | 11 | Unit + Integration |
| `tests/test_audit.py` | 9 | Integration |
| **合計** | **36** | |

**覆蓋率目標**：

| 模組 | 目標 |
|------|------|
| `src/preflight.py` | 100% |
| `src/scheduler.py` | 100% |
| `src/markdown_io.py` | >= 90% |
| `scripts/audit.py` | >= 80% |

---

## 8. 風險與緩解

| 風險 | 嚴重度 | 緩解 |
|------|--------|------|
| DB 中無 PENDING_REVIEW 資料 | 中 | 啟動時檢查，無資料印出提示。測試用 fixture 建立 |
| `Content.transition_to()` 是 mutating 方法 | 低 | 已知例外，直接 mutate + `dao.update()` 最簡潔 |
| `$EDITOR` 未設定 | 中 | 依序 fallback：`$EDITOR` → `$VISUAL` → `vim` → `nano` |
| Markdown 手機編輯格式不一致 | 中 | 寬鬆 regex，無法解析的區塊記入 errors |
| `accounts.toml` 不存在 | 低 | try/except `FileNotFoundError`，印出設定指引 |

---

## 9. 向後相容性影響

**零破壞性**。Cycle 4 是純新增模組，不修改任何現有檔案。

---

## 10. 驗收檢查清單

### 互動式審核
- [ ] `python scripts/audit.py` 啟動，顯示待審清單
- [ ] `--account A` 只顯示帳號 A
- [ ] A 核准 → status=APPROVED，scheduled_time 自動填入
- [ ] E 編輯 → $EDITOR 開啟 → 儲存後核准
- [ ] D 捨棄 → status=REJECTED
- [ ] S 跳過 → status 不變
- [ ] Q 離開 → 顯示摘要

### Pre-flight Check
- [ ] IG 無圖顯示警告
- [ ] X 字數超 280 顯示警告
- [ ] 空標題/內文顯示 ERROR

### 批次模式
- [ ] `--batch` 自動核准（有 ERROR 的跳過）

### Markdown 匯出/回寫
- [ ] `--export-md` 產出 review.md，格式正確
- [ ] 手動修改 Action 和內文
- [ ] `--import-md review.md` 回寫 DB 正確

### 測試
- [ ] 36 個新測試全過
- [ ] 覆蓋率 >= 80%
- [ ] Cycle 1 的 69 個測試零回歸
