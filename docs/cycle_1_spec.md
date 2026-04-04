# Cycle 1 實施規格 — 基礎建設

**版本**: 1.0
**日期**: 2026-03-31
**評分**: 地基，可行性 5/5
**時程**: 第 1-2 週
**PM Agent 輸出**

---

## 執行目標

為 LevelUp 內容管理系統建立數據基礎層，擴展現有 `history.db` 以支持：
- 三帳號內容分類（A / B / C）
- 內容狀態機（DRAFT → PENDING_REVIEW → APPROVED → PUBLISHED → ANALYZED → REJECTED）
- AI 選材理由記錄（`reasoning` 欄位）
- 跨平台發布狀態追蹤（`platform_status` JSON）
- 帳號配置管理（accounts.toml）

**成功指標**：DB 遷移無損、狀態機拒絕非法轉換、三帳號配置可正確載入

---

## 任務分解

### 任務 1：SQLite Schema 遷移

**檔案**: `src/migrations/001_add_levelup_columns.sql`

**涉及檔案**: `~/.imggen/history.db` (existing `generations` table)

**變更內容**：

```sql
-- 確保向後相容，所有欄位有 DEFAULT 值
ALTER TABLE generations ADD COLUMN account_type TEXT DEFAULT 'A';
ALTER TABLE generations ADD COLUMN status TEXT DEFAULT 'DRAFT';
ALTER TABLE generations ADD COLUMN content_type TEXT DEFAULT 'NEWS_RECAP';
ALTER TABLE generations ADD COLUMN reasoning TEXT DEFAULT '';
ALTER TABLE generations ADD COLUMN scheduled_time TEXT;  -- ISO 8601 or NULL
ALTER TABLE generations ADD COLUMN published_at TEXT;    -- ISO 8601 or NULL
ALTER TABLE generations ADD COLUMN platform_status TEXT DEFAULT '{}';  -- JSON string
ALTER TABLE generations ADD COLUMN engagement_data TEXT DEFAULT '{}';  -- JSON string
ALTER TABLE generations ADD COLUMN source_url TEXT;      -- Original article URL
```

**驗收標準**:
- [ ] 遷移指令無誤（可在 SQLite 終端機測試）
- [ ] 現有 N 筆記錄完整保留，新欄位預設值正確
- [ ] 不刪除任何既存欄位（純增量）

**依賴**: 無

---

### 任務 2：Content 數據模型 + 狀態機

**檔案**: `src/content.py`（新建）

**內容**：

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Literal, Optional
from enum import Enum
import json

class ContentStatus(str, Enum):
    DRAFT = 'DRAFT'
    PENDING_REVIEW = 'PENDING_REVIEW'
    APPROVED = 'APPROVED'
    PUBLISHED = 'PUBLISHED'
    ANALYZED = 'ANALYZED'
    REJECTED = 'REJECTED'

class ContentType(str, Enum):
    NEWS_RECAP = 'NEWS_RECAP'
    PREDICTION = 'PREDICTION'
    EDUCATIONAL = 'EDUCATIONAL'

class AccountType(str, Enum):
    A = 'A'  # AI 自動化
    B = 'B'  # PMP 職涯
    C = 'C'  # 足球英文

# 合法狀態轉換表
VALID_TRANSITIONS = {
    ContentStatus.DRAFT: {ContentStatus.PENDING_REVIEW, ContentStatus.REJECTED},
    ContentStatus.PENDING_REVIEW: {ContentStatus.APPROVED, ContentStatus.REJECTED},
    ContentStatus.APPROVED: {ContentStatus.PUBLISHED},
    ContentStatus.PUBLISHED: {ContentStatus.ANALYZED},
}

class InvalidTransitionError(Exception):
    """State machine violation"""
    pass

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
    published_at: Optional[datetime] = None
    source_url: Optional[str] = None
    platform_status: dict = field(default_factory=dict)  # {"threads": "ok", "x": "pending"}
    engagement_data: dict = field(default_factory=dict)  # {"likes": 0, "replies": 0}
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def transition_to(self, new_status: ContentStatus) -> None:
        """Validate and apply state transition"""
        if new_status not in VALID_TRANSITIONS.get(self.status, set()):
            raise InvalidTransitionError(
                f"Cannot transition from {self.status} to {new_status}"
            )
        self.status = new_status
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Serialize to dict, handling datetime and Enum"""
        data = asdict(self)
        data['status'] = self.status.value
        data['account_type'] = self.account_type.value
        data['content_type'] = self.content_type.value
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        data['scheduled_time'] = self.scheduled_time.isoformat() if self.scheduled_time else None
        data['published_at'] = self.published_at.isoformat() if self.published_at else None
        return data

    @staticmethod
    def from_dict(data: dict) -> 'Content':
        """Deserialize from dict"""
        data = data.copy()
        # Convert string values to Enums
        if isinstance(data.get('status'), str):
            data['status'] = ContentStatus(data['status'])
        if isinstance(data.get('account_type'), str):
            data['account_type'] = AccountType(data['account_type'])
        if isinstance(data.get('content_type'), str):
            data['content_type'] = ContentType(data['content_type'])

        # Convert ISO strings to datetime
        for field_name in ['created_at', 'updated_at', 'scheduled_time', 'published_at']:
            if data.get(field_name) and isinstance(data[field_name], str):
                data[field_name] = datetime.fromisoformat(data[field_name])

        return Content(**data)
```

**驗收標準**:
- [ ] 所有合法轉換可執行（不引發異常）
- [ ] 所有非法轉換拋出 `InvalidTransitionError`
- [ ] `to_dict()` / `from_dict()` 往返無損失
- [ ] datetime 和 Enum 序列化正確

**依賴**: 無

---

### 任務 3：帳號配置管理

**檔案**: `src/config.py`（擴展現有或新建）

**新增部分**：

```python
import tomllib  # Python 3.11+ 內建
from pathlib import Path
from dataclasses import dataclass

@dataclass
class AccountConfig:
    name: str
    platforms: list[str]  # ["threads", "x", "instagram"]
    publish_time: str     # "HH:MM" format
    color_mood: str       # "dark_tech" | "warm_earth" | "clean_light" | "bold_contrast" | "soft_pastel"
    prompt_file: str      # "prompts/account_a.txt"
    tone: str             # 帳號風格描述

class LevelUpConfig:
    """Load LevelUp multi-account configuration from ~/.imggen/accounts.toml"""

    def __init__(self, config_path: str = "~/.imggen/accounts.toml"):
        self.config_path = Path(config_path).expanduser()
        self._accounts = {}
        self._load()

    def _load(self) -> None:
        """Load and parse accounts.toml"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path, 'rb') as f:
            config = tomllib.load(f)

        for account_id, account_data in config.get('account', {}).items():
            self._accounts[account_id] = AccountConfig(**account_data)

    def get_account(self, account_type: str) -> AccountConfig:
        """Retrieve account config by type (A, B, or C)"""
        if account_type not in self._accounts:
            raise ValueError(f"Unknown account type: {account_type}")
        return self._accounts[account_type]

    def list_accounts(self) -> dict[str, AccountConfig]:
        """List all configured accounts"""
        return self._accounts.copy()
```

**TOML 樣板** (`~/.imggen/accounts.toml`):

```toml
[account.A]
name = "AI 自動化"
platforms = ["threads", "x"]
publish_time = "12:30"
color_mood = "dark_tech"
prompt_file = "prompts/account_a.txt"
tone = "技術宅幽默，帶崩潰感"

[account.B]
name = "PMP 職涯"
platforms = ["threads", "linkedin"]
publish_time = "07:30"
color_mood = "clean_light"
prompt_file = "prompts/account_b.txt"
tone = "專業但帶無奈幽默，實戰血淚"

[account.C]
name = "足球英文"
platforms = ["threads", "x", "instagram"]
publish_time = "20:00"
color_mood = "bold_contrast"
prompt_file = "prompts/account_c.txt"
tone = "球迷熱情，資深觀賽心得"
```

**驗收標準**:
- [ ] `LevelUpConfig()` 能無誤載入 accounts.toml
- [ ] `get_account('A')` 回傳正確的 AccountConfig 物件
- [ ] 配置不存在時拋出 FileNotFoundError

**依賴**: accounts.toml 需事先建立在 `~/.imggen/`

---

### 任務 4：資料庫層 (DAO Pattern)

**檔案**: `src/db.py`（新建或擴展現有）

**新增方法**：

```python
import sqlite3
from datetime import datetime
from src.content import Content, ContentStatus

class ContentDAO:
    """Data Access Object for Content"""

    def __init__(self, db_path: str = "~/.imggen/history.db"):
        self.db_path = db_path
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Run migration if needed (idempotent)"""
        # 檢查欄位是否存在，若不存在則執行 ALTER TABLE
        # 這邊簡化為假設已執行過遷移
        pass

    def create(self, content: Content) -> str:
        """Insert new content, return id"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            data = content.to_dict()
            # 移除 id 讓 DB 自動指派
            del data['id']
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?'] * len(data))
            cursor.execute(
                f"INSERT INTO generations ({columns}) VALUES ({placeholders})",
                tuple(data.values())
            )
            content_id = cursor.lastrowid
            conn.commit()
            return str(content_id)
        finally:
            conn.close()

    def find_by_id(self, content_id: str) -> Content | None:
        """Retrieve content by id"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM generations WHERE id = ?", (content_id,))
            row = cursor.fetchone()
            if row:
                return Content.from_dict(dict(row))
            return None
        finally:
            conn.close()

    def find_by_status(self, status: ContentStatus, account_type: str | None = None) -> list[Content]:
        """Find all content with given status"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if account_type:
                cursor.execute(
                    "SELECT * FROM generations WHERE status = ? AND account_type = ? ORDER BY created_at DESC",
                    (status.value, account_type)
                )
            else:
                cursor.execute(
                    "SELECT * FROM generations WHERE status = ? ORDER BY created_at DESC",
                    (status.value,)
                )
            return [Content.from_dict(dict(row)) for row in cursor.fetchall()]
        finally:
            conn.close()

    def update(self, content: Content) -> None:
        """Update existing content"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            data = content.to_dict()
            content_id = data.pop('id')

            columns = ', '.join([f"{k} = ?" for k in data.keys()])
            values = list(data.values()) + [content_id]

            cursor.execute(
                f"UPDATE generations SET {columns} WHERE id = ?",
                values
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, content_id: str) -> None:
        """Delete content by id"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM generations WHERE id = ?", (content_id,))
            conn.commit()
        finally:
            conn.close()
```

**驗收標準**:
- [ ] CRUD 操作全部可用
- [ ] 查詢結果正確反序列化為 Content 物件
- [ ] 無 SQL injection 漏洞

**依賴**: 任務 1 (schema), 任務 2 (Content model)

---

### 任務 5：測試套件 (TDD)

**檔案**: `tests/test_content.py`, `tests/test_db.py`

**測試清單**:

#### test_content.py

```python
import pytest
from src.content import Content, ContentStatus, InvalidTransitionError, AccountType, ContentType
from datetime import datetime

class TestContentStateMachine:
    def test_draft_to_pending_review(self):
        """DRAFT → PENDING_REVIEW should succeed"""
        c = Content(id="1", account_type=AccountType.A)
        c.transition_to(ContentStatus.PENDING_REVIEW)
        assert c.status == ContentStatus.PENDING_REVIEW

    def test_pending_review_to_approved(self):
        """PENDING_REVIEW → APPROVED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PENDING_REVIEW)
        c.transition_to(ContentStatus.APPROVED)
        assert c.status == ContentStatus.APPROVED

    def test_approved_to_published(self):
        """APPROVED → PUBLISHED should succeed"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.APPROVED)
        c.transition_to(ContentStatus.PUBLISHED)
        assert c.status == ContentStatus.PUBLISHED

    def test_draft_to_rejected(self):
        """DRAFT → REJECTED should succeed"""
        c = Content(id="1", account_type=AccountType.A)
        c.transition_to(ContentStatus.REJECTED)
        assert c.status == ContentStatus.REJECTED

    def test_invalid_transition_approved_to_draft(self):
        """APPROVED → DRAFT should fail"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.APPROVED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.DRAFT)

    def test_invalid_transition_published_to_draft(self):
        """PUBLISHED → DRAFT should fail"""
        c = Content(id="1", account_type=AccountType.A, status=ContentStatus.PUBLISHED)
        with pytest.raises(InvalidTransitionError):
            c.transition_to(ContentStatus.DRAFT)

class TestContentSerialization:
    def test_to_dict_preserves_all_fields(self):
        """to_dict() should include all fields"""
        now = datetime.now()
        c = Content(
            id="1",
            account_type=AccountType.B,
            title="Test",
            body="Body",
            reasoning="Good content",
            scheduled_time=now
        )
        d = c.to_dict()
        assert d['id'] == "1"
        assert d['account_type'] == 'B'
        assert d['title'] == "Test"
        assert d['reasoning'] == "Good content"

    def test_from_dict_reconstruction(self):
        """from_dict() should reconstruct Content identically"""
        c1 = Content(
            id="1",
            account_type=AccountType.C,
            status=ContentStatus.PENDING_REVIEW,
            content_type=ContentType.PREDICTION,
            title="Title",
            body="Body"
        )
        d = c1.to_dict()
        c2 = Content.from_dict(d)
        assert c2.id == c1.id
        assert c2.account_type == c1.account_type
        assert c2.status == c1.status
        assert c2.title == c1.title
```

#### test_db.py

```python
import pytest
import sqlite3
from pathlib import Path
from src.db import ContentDAO
from src.content import Content, ContentStatus, AccountType

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary test database"""
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))

    # Create schema
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE generations (
        id INTEGER PRIMARY KEY,
        account_type TEXT DEFAULT 'A',
        status TEXT DEFAULT 'DRAFT',
        content_type TEXT DEFAULT 'NEWS_RECAP',
        title TEXT,
        body TEXT,
        image_path TEXT,
        reasoning TEXT DEFAULT '',
        scheduled_time TEXT,
        published_at TEXT,
        source_url TEXT,
        platform_status TEXT DEFAULT '{}',
        engagement_data TEXT DEFAULT '{}',
        created_at TEXT,
        updated_at TEXT
    )
    """)
    conn.commit()
    conn.close()
    return str(db_path)

class TestContentDAO:
    def test_create_inserts_content(self, temp_db):
        """create() should insert and return id"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.A, title="Test", body="Body")
        content_id = dao.create(c)
        assert content_id is not None

    def test_find_by_id_retrieves_content(self, temp_db):
        """find_by_id() should retrieve inserted content"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.B, title="Test", body="Body")
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        assert retrieved is not None
        assert retrieved.title == "Test"
        assert retrieved.account_type == AccountType.B

    def test_find_by_status_filters_correctly(self, temp_db):
        """find_by_status() should return only matching status"""
        dao = ContentDAO(temp_db)

        c1 = Content(id="t1", account_type=AccountType.A, status=ContentStatus.DRAFT)
        c2 = Content(id="t2", account_type=AccountType.A, status=ContentStatus.PENDING_REVIEW)

        dao.create(c1)
        dao.create(c2)

        drafts = dao.find_by_status(ContentStatus.DRAFT)
        assert len(drafts) == 1
        assert drafts[0].status == ContentStatus.DRAFT

    def test_update_modifies_content(self, temp_db):
        """update() should modify existing content"""
        dao = ContentDAO(temp_db)
        c = Content(id="temp", account_type=AccountType.C, title="Original")
        content_id = dao.create(c)

        retrieved = dao.find_by_id(content_id)
        retrieved.title = "Modified"
        dao.update(retrieved)

        updated = dao.find_by_id(content_id)
        assert updated.title == "Modified"
```

**驗收標準**:
- [ ] 所有測試通過
- [ ] 覆蓋率 ≥ 80%
- [ ] 狀態機測試完整（合法 + 非法轉換）
- [ ] 序列化測試往返無損

**依賴**: 任務 2 (Content), 任務 4 (DAO)

---

## 交付物總覽

| 交付物 | 類型 | 路徑 | 狀態 |
|--------|------|------|------|
| Migration SQL | Script | `src/migrations/001_add_levelup_columns.sql` | 待建 |
| Content Model | Python | `src/content.py` | 待建 |
| Config Manager | Python | `src/config.py` (extend) | 待建 |
| DAO Layer | Python | `src/db.py` | 待建 |
| Unit Tests | Python | `tests/test_content.py` | 待建 |
| Integration Tests | Python | `tests/test_db.py` | 待建 |
| Accounts Config | TOML | `~/.imggen/accounts.toml` | 待建 |
| 本文檔 | MD | `docs/cycle_1_spec.md` | ✅ |

---

## 依賴關係

```
Task 1 (Schema)
    ↓
Task 2 (Content Model) ← Task 4 (DAO) requires Task 2
    ↓
Task 5 (Tests) ← requires Task 2, Task 4

Task 3 (Config) ← independent
```

**實施順序**:
1. Task 1: 遷移 SQL 腳本（無依賴）
2. Task 2: Content 模型（無依賴）
3. Task 3: Config 加載器（無依賴）
4. Task 4: DAO 層（依賴 Task 2）
5. Task 5: 測試（依賴 Task 2, Task 4）

---

## 工作流程

### Phase 1: TDD RED
```bash
pytest tests/test_content.py tests/test_db.py -v
# → 所有測試失敗（RED）
```

### Phase 2: Implementation (GREEN)
依序實作上述檔案，直到所有測試通過

### Phase 3: IMPROVE
- 檢查程式碼品質（變數命名、函數長度、複雜度）
- 檢查邊界情況（NULL、empty list、invalid enum）
- 整合測試（DB WAL mode 驗證）

---

## 風險 & 緩解

| 風險 | 緩解策略 |
|------|---------|
| ALTER TABLE 失敗破壞既存資料 | 事先備份 history.db，測試遷移指令 |
| 狀態機邏輯錯誤導致無效轉換 | 完整 test coverage，鉅細靡遺測試合法和非法轉換 |
| accounts.toml 路徑錯誤 | 使用 `~/.imggen/` 而非相對路徑，測試 FileNotFoundError 處理 |
| DAO 實作 SQL injection | 使用參數化查詢（`?` placeholders），禁止字串插值 |

---

## 驗收檢查清單

- [ ] Migration SQL 腳本驗證無誤（SQLite 終端機測試）
- [ ] Content 模型所有狀態轉換測試通過
- [ ] DAO CRUD 測試全過，無 SQL 注入
- [ ] accounts.toml 能被 LevelUpConfig 正確解析
- [ ] 整合測試：DB 寫入 → 讀出 → Content 反序列化結果正確
- [ ] 測試覆蓋率 ≥ 80%
- [ ] 無遺漏的邊界情況（NULL、invalid enum、constraint violation）

---

## 下一步

Cycle 1 完成後，進入 Cycle 2（策展大腦）：
- 建立三個爬蟲（RSS、API）
- 設計三帳號 AI Prompt（強制 reasoning 欄位）
- 實作 `scripts/daily_curation.py`
