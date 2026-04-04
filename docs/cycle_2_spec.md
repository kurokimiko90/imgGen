# Cycle 2 實施規格 — 策展大腦

**版本**: 1.0
**日期**: 2026-03-31
**評分**: 80（高度衝擊力）
**時程**: 第 3-4 週（與 Cycle 3 並行）
**PM Agent 輸出**

---

## 執行目標

建立內容策展系統，自動從多個來源爬取信息，經由 AI 分析（帳號特定 Prompt），生成每日內容草稿。

**成功指標**：
- 三帳號各日均生成 ≥ 1 篇 DRAFT 進入 DB
- 每篇 DRAFT 含非空的 `reasoning` 欄位（AI 選材理由）
- 單個爬蟲失敗不影響其他帳號

---

## 任務分解

### 任務 1：爬蟲架構 + 基類

**檔案**: `src/scrapers/base_scraper.py`（新建）

**內容**：

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class RawItem:
    """通用原始素材格式"""
    title: str
    url: str
    summary: str  # 原始來源的簡述（如有）
    published_at: datetime
    source: str   # "hacker_news" | "bbc_sport" | "techcrunch" 等

class BaseScraper(ABC):
    """爬蟲基類，定義通用介面"""

    @abstractmethod
    def fetch(self) -> list[RawItem]:
        """
        抓取最新內容。
        子類實作該方法，回傳 RawItem 列表。
        """
        pass

    def validate_items(self, items: list[RawItem]) -> list[RawItem]:
        """
        驗證 RawItem 的完整性。
        篩除沒有 title / url 的項目。
        """
        return [
            item for item in items
            if item.title and item.url and item.published_at
        ]
```

**驗收標準**:
- [ ] BaseScraper 是抽象類別，fetch() 必須實作
- [ ] RawItem dataclass 包含所需欄位
- [ ] validate_items() 可篩除不完整項目

**依賴**: 無

---

### 任務 2：三個爬蟲實作

#### 2a. 足球爬蟲 (Football Scraper)

**檔案**: `src/scrapers/football_scraper.py`

**數據源**：
- API-Football（https://api-football-v3.p.rapidapi.com/fixtures，免費 100 req/day）
- BBC Sport RSS（https://www.bbc.com/sport/football/rss.xml）

**實作**：

```python
import httpx
import feedparser
from datetime import datetime, timedelta
from src.scrapers.base_scraper import BaseScraper, RawItem

class FootballScraper(BaseScraper):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("API_FOOTBALL_KEY")

    def fetch(self) -> list[RawItem]:
        items = []

        # 從 BBC Sport RSS 爬取最近 5 天比賽
        try:
            feed = feedparser.parse("https://www.bbc.com/sport/football/rss.xml")
            for entry in feed.entries[:10]:  # 限制 10 筆防止超量
                items.append(RawItem(
                    title=entry.title,
                    url=entry.link,
                    summary=entry.get("summary", ""),
                    published_at=datetime(*entry.published_parsed[:6]),
                    source="bbc_sport"
                ))
        except Exception as e:
            print(f"BBC RSS error: {e}")

        # API-Football 若有 API Key，額外爬取比賽賽程
        if self.api_key:
            try:
                # 未來 3 天的比賽
                for days_ahead in range(3):
                    date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                    # API 呼叫邏輯...（簡化，實際需完整實作）
            except Exception as e:
                print(f"API-Football error: {e}")

        return self.validate_items(items)
```

**驗收標準**:
- [ ] `fetch()` 回傳 ≥ 1 RawItem（BBC RSS 至少）
- [ ] 每個 RawItem 含有效的 url 和 published_at
- [ ] RSS 解析失敗不拋出異常，仍回傳空列表

**依賴**: httpx, feedparser 套件

---

#### 2b. 科技爬蟲 (Tech Scraper)

**檔案**: `src/scrapers/tech_scraper.py`

**數據源**：
- Hacker News API（https://hacker-news.firebaseio.com/v0/）
- TechCrunch RSS（https://feeds.techcrunch.com/...）
- GitHub Trending（https://github.com/trending）

**實作重點**：

```python
class TechScraper(BaseScraper):
    def fetch(self) -> list[RawItem]:
        items = []

        # Hacker News: 取前 30 則新聞
        try:
            response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
            story_ids = response.json()[:30]

            for story_id in story_ids:
                story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                story_data = httpx.get(story_url).json()

                items.append(RawItem(
                    title=story_data.get("title", ""),
                    url=story_data.get("url", ""),
                    summary="",
                    published_at=datetime.fromtimestamp(story_data["time"]),
                    source="hacker_news"
                ))
        except Exception as e:
            print(f"Hacker News error: {e}")

        # TechCrunch RSS + GitHub Trending...
        # （類似 FootballScraper 的模式）

        return self.validate_items(items)
```

**驗收標準**:
- [ ] `fetch()` 回傳 ≥ 3 個 RawItem（多源混合）
- [ ] 每個來源的抓取失敗不阻滯其他來源

**依賴**: httpx, feedparser 套件

---

#### 2c. PMP 爬蟲 (PMP Scraper)

**檔案**: `src/scrapers/pmp_scraper.py`

**數據源**：
- Harvard Business Review RSS（https://hbr.org/...）
- PMI Blog RSS（https://www.pmi.org/blog/...）

**實作重點**：

```python
class PMPScraper(BaseScraper):
    def fetch(self) -> list[RawItem]:
        items = []

        # HBR RSS
        try:
            feed = feedparser.parse("https://feeds.hbr.org/...")
            for entry in feed.entries[:8]:
                items.append(RawItem(
                    title=entry.title,
                    url=entry.link,
                    summary=entry.get("summary", ""),
                    published_at=datetime(*entry.published_parsed[:6]),
                    source="hbr"
                ))
        except Exception as e:
            print(f"HBR error: {e}")

        # PMI Blog RSS...

        return self.validate_items(items)
```

**驗收標準**:
- [ ] `fetch()` 回傳 ≥ 2 個 RawItem（至少來自 2 個 RSS）

**依賴**: feedparser 套件

---

### 任務 3：三帳號 AI Prompt + 轉換函數

**檔案**:
- `prompts/account_a.txt`
- `prompts/account_b.txt`
- `prompts/account_c.txt`

**Prompt 樣板**（強制 JSON 輸出 + reasoning 欄位）：

```
# Prompt 樣板結構
---SYSTEM---
You are a content curator for [帳號名稱] account.

Your task: Given a news item, decide whether to feature it and how to present it.

Return a JSON object with REQUIRED fields:
{
  "should_publish": true|false,  # 這則內容是否值得發佈
  "title": "15字以內的標題",
  "body": "符合[平台]字數限制的貼文",
  "content_type": "NEWS_RECAP|PREDICTION|EDUCATIONAL",
  "reasoning": "為什麼這則素材值得發？預期它會火的理由（至少 50 字）",
  "tags": ["#tag1", "#tag2"],
  "image_suggestion": "圖卡版型（可選，如：dark/quote/data_impact）"
}

---CONTEXT---
[帳號設定：tone, color_mood, target_audience 等]

---ITEM---
Title: {title}
URL: {url}
Summary: {summary}
Source: {source}

---INSTRUCTION---
1. Analyze whether this item fits the account's voice and audience
2. If yes (should_publish: true), draft the content
3. If no, return {"should_publish": false, "reasoning": "..."}
4. Always include non-empty reasoning field
```

**Prompt 具體例子**：

**prompts/account_a.txt**:
```
You are a content curator for the "AI 自動化" (AI Automation) account.
Target audience: AI practitioners, developers building with AI, engineering managers.
Tone: Technical humor, self-deprecating about AI/engineering struggles, Build-in-Public mindset.
Platforms: Threads (500 chars), X (280 chars).
Color mood: dark_tech.

[Rest of template with account-specific guidance]
```

**驗收標準**:
- [ ] 三個 Prompt 文件存在且含 JSON schema
- [ ] 每個 Prompt 強制 `reasoning` 欄位非空
- [ ] 測試：給定 news item → JSON 解析成功 → reasoning 非空

**依賴**: Prompt 設計（手工編寫）

---

### 任務 4：daily_curation.py 主控腳本

**檔案**: `scripts/daily_curation.py`（新建）

**流程**：

```python
import asyncio
from datetime import datetime
from src.scrapers.football_scraper import FootballScraper
from src.scrapers.tech_scraper import TechScraper
from src.scrapers.pmp_scraper import PMPScraper
from src.config import LevelUpConfig
from src.db import ContentDAO
from src.content import Content, ContentStatus, ContentType, AccountType
from src.pipeline import run_pipeline

async def curate_for_account(
    account_type: str,
    scraper,
    levelup_config: LevelUpConfig,
    dao: ContentDAO
) -> int:
    """
    一個帳號的策展流程。
    回傳新建的 DRAFT 數量。
    """
    account_config = levelup_config.get_account(account_type)
    raw_items = scraper.fetch()

    drafted = 0
    for item in raw_items:
        # 呼叫帳號特定 Prompt，轉換為 Content
        try:
            ai_output = call_claude_api(
                prompt_file=account_config.prompt_file,
                item=item
            )

            if not ai_output.get("should_publish"):
                continue

            # 呼叫 imgGen pipeline 生成圖卡
            image_path = run_pipeline(
                text=ai_output["body"],
                theme=account_config.color_mood,
                mode="smart"
            )

            # 建立 Content 並存入 DB
            content = Content(
                id=None,  # DAO 會指派
                account_type=AccountType(account_type),
                status=ContentStatus.DRAFT,
                content_type=ContentType(ai_output.get("content_type", "NEWS_RECAP")),
                title=ai_output["title"],
                body=ai_output["body"],
                image_path=image_path,
                reasoning=ai_output["reasoning"],
                source_url=item.url
            )

            content_id = dao.create(content)
            drafted += 1

        except Exception as e:
            print(f"Error curating {item.title} for {account_type}: {e}")

    return drafted

async def main():
    config = LevelUpConfig()
    dao = ContentDAO()

    scrapers = {
        'A': TechScraper(),
        'B': PMPScraper(),
        'C': FootballScraper()
    }

    # 並發執行三帳號策展
    tasks = [
        curate_for_account(account_type, scraper, config, dao)
        for account_type, scraper in scrapers.items()
    ]

    results = await asyncio.gather(*tasks)

    total = sum(results)
    print(f"Daily curation complete: {total} new DRAFTs created")
    return total

if __name__ == "__main__":
    asyncio.run(main())
```

**執行**：
```bash
python scripts/daily_curation.py
# Output: Daily curation complete: 5 new DRAFTs created
```

**驗收標準**:
- [ ] 三帳號並發執行，各自獨立
- [ ] 單個爬蟲失敗不影響其他帳號（try-except 保護）
- [ ] 所有 DRAFT 有非空 `reasoning` 欄位

**依賴**: 任務 1-3, 爬蟲實作, Prompt 設計

---

### 任務 5：測試套件

**檔案**:
- `tests/scrapers/test_football_scraper.py`
- `tests/scrapers/test_tech_scraper.py`
- `tests/test_daily_curation.py`

**測試清單**：

#### test_football_scraper.py

```python
import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.football_scraper import FootballScraper
from src.scrapers.base_scraper import RawItem

class TestFootballScraper:
    def test_fetch_returns_raw_items(self):
        """fetch() 應回傳 RawItem 列表"""
        scraper = FootballScraper(api_key=None)  # 只用 RSS
        items = scraper.fetch()
        assert isinstance(items, list)
        # BBC RSS 應回傳至少 1 筆（或 0 如果 RSS 失敗，仍要 validate）

    def test_rss_parsing_failure_handled(self):
        """RSS 解析失敗應返回空列表，不拋異常"""
        scraper = FootballScraper()
        # Mock feedparser 失敗
        with patch('feedparser.parse', side_effect=Exception("Network error")):
            items = scraper.fetch()
            assert items == []

    def test_raw_item_validation(self):
        """validate_items() 應篩除不完整項"""
        scraper = FootballScraper()
        items = [
            RawItem(title="Valid", url="http://...", summary="", published_at=..., source="test"),
            RawItem(title="", url="http://...", summary="", published_at=..., source="test"),  # 無 title
        ]
        valid = scraper.validate_items(items)
        assert len(valid) == 1
```

#### test_daily_curation.py

```python
import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from scripts.daily_curation import curate_for_account, main

class TestDailyCuration:
    @pytest.mark.asyncio
    async def test_curate_creates_draft_content(self):
        """策展應建立 DRAFT 內容"""
        # Mock scraper, API, DB
        mock_scraper = MagicMock()
        mock_scraper.fetch.return_value = [
            RawItem(title="News", url="http://...", ...)
        ]

        # Mock AI API 回應
        ai_output = {
            "should_publish": True,
            "title": "Title",
            "body": "Body",
            "content_type": "NEWS_RECAP",
            "reasoning": "Good content"
        }

        with patch('call_claude_api', return_value=ai_output):
            with patch('run_pipeline', return_value="/path/to/image.png"):
                with patch('ContentDAO') as mock_dao:
                    drafted = await curate_for_account('A', mock_scraper, config, mock_dao)
                    assert drafted >= 1

    @pytest.mark.asyncio
    async def test_single_failure_does_not_block_others(self):
        """一帳號失敗不影響其他帳號"""
        with patch('curate_for_account', side_effect=[1, Exception("Error"), 2]):
            # 應該只有 A 和 C 成功，B 失敗被捕捉
            pass
```

**驗收標準**:
- [ ] 所有爬蟲測試通過（mocked 網絡請求）
- [ ] daily_curation 測試覆蓋 happy path + 異常情況
- [ ] 覆蓋率 ≥ 80%

**依賴**: 任務 1-4

---

## 交付物總覽

| 交付物 | 類型 | 路徑 | 狀態 |
|--------|------|------|------|
| 爬蟲基類 | Python | `src/scrapers/base_scraper.py` | 待建 |
| 足球爬蟲 | Python | `src/scrapers/football_scraper.py` | 待建 |
| 科技爬蟲 | Python | `src/scrapers/tech_scraper.py` | 待建 |
| PMP 爬蟲 | Python | `src/scrapers/pmp_scraper.py` | 待建 |
| 帳號 A Prompt | Text | `prompts/account_a.txt` | 待建 |
| 帳號 B Prompt | Text | `prompts/account_b.txt` | 待建 |
| 帳號 C Prompt | Text | `prompts/account_c.txt` | 待建 |
| 策展控制器 | Python | `scripts/daily_curation.py` | 待建 |
| 爬蟲測試 | Python | `tests/scrapers/test_*.py` (3 files) | 待建 |
| 策展測試 | Python | `tests/test_daily_curation.py` | 待建 |
| 本文檔 | MD | `docs/cycle_2_spec.md` | ✅ |

---

## 依賴關係

```
Task 1 (BaseScraper)
    ↓
Task 2a-2c (具體爬蟲) ← depends on Task 1
    ↓
Task 3 (Prompts) ← independent
    ↓
Task 4 (daily_curation) ← depends on Task 1-3, Cycle 1 完成
    ↓
Task 5 (Tests) ← depends on Task 1-4
```

**實施順序**:
1. Task 1: BaseScraper 基類
2. Task 2a-2c: 並行開發三個爬蟲
3. Task 3: 編寫三個 Prompt（與爬蟲並行）
4. Task 4: daily_curation 主控腳本
5. Task 5: 測試套件

---

## 工作流程

### Phase 1: TDD RED
```bash
pytest tests/scrapers/ tests/test_daily_curation.py -v
# → 所有測試失敗（RED）
```

### Phase 2: Implementation (GREEN)
依序實作上述檔案，直到所有測試通過

### Phase 3: IMPROVE
- 驗證三帳號各自獨立且並發無誤
- 檢查 Prompt 的 reasoning 欄位強制性
- 驗證 DB 寫入正確

---

## 風險 & 緩解

| 風險 | 緩解策略 |
|------|---------|
| RSS 源不穩定或下線 | Try-except 保護，實裝降級方案 |
| API 速率限制 | 實裝 backoff + 快取機制 |
| AI Prompt 生成失敗 | Fallback to 預設內容，記錄錯誤 |
| Cycle 1 DB 尚未準備 | **前置依賴**：Cycle 1 必須完成 |

---

## 驗收檢查清單

- [ ] 三個爬蟲各自 ≥ 1 個有效 RawItem
- [ ] daily_curation 執行後 DB 中新增 ≥ 3 DRAFT（每帳號 1 篇）
- [ ] 每篇 DRAFT 的 reasoning 非空
- [ ] 單一爬蟲或 Prompt 失敗不影響其他帳號
- [ ] 所有測試通過，覆蓋率 ≥ 80%

---

## 下一步

Cycle 2 完成後，進入 Cycle 3（Smart Mode + Design Review Loop）：
- 整合 Smart Mode 至 CLI / Web UI
- 實作 Design Review Loop 自動化視覺品控

**Cycle 2 與 Cycle 3 時程重疊**（週 3-4），可並行開發。
