# imgGen 擴展功能 — 詳細技術設計

**Version**: v1
**Date**: 2026-03-28
**Status**: Design

---

## 設計原則

1. **自動化優先** — imgGen 是內容自動化引擎，不是設計工具。每個新功能都要減少人工介入
2. **Pipeline 複用** — 所有功能複用 `extract → render_card → take_screenshot` 骨幹，不建平行系統
3. **向後兼容** — DB 用 `ALTER TABLE ADD COLUMN`，API 新增 endpoint 不改現有簽名
4. **漸進式** — 每個 Sprint 獨立可交付，不需要等後續 Sprint 才能使用

---

# Sprint 1: 快速勝利

---

## 1.1 Smart URL 提取 (trafilatura)

### 現狀問題

`src/fetcher.py` 的 `_strip_html()` 用 4 層 regex 清理 HTML：
```python
text = re.sub(r"<script[^>]*>.*?</script>", " ", text, ...)
text = re.sub(r"<style[^>]*>.*?</style>", " ", text, ...)
text = re.sub(r"<[^>]+>", " ", text)
text = re.sub(r"\s+", " ", text).strip()
```
問題：nav、footer、sidebar、廣告文字全部混入正文，AI 提取品質下降。

### 設計

**改動範圍**: 僅 `src/fetcher.py`，不影響任何其他模組

**依賴**: `trafilatura>=1.12.0`（MIT license，專注文章正文提取）

**改動方式**:

```python
# src/fetcher.py

import trafilatura

def _extract_article_text(html: str, url: str) -> str:
    """用 trafilatura 提取文章正文，失敗時 fallback 到 regex strip。"""
    result = trafilatura.extract(
        html,
        url=url,
        include_comments=False,
        include_tables=False,
        favor_precision=True,    # 寧可少提取，不要混入垃圾
    )
    if result and len(result) > 50:
        return result
    # Fallback
    return _strip_html(html)
```

**修改 `fetch_url_content()`**:
```python
def fetch_url_content(url: str) -> str:
    # ... (保留 Threads.com 特殊處理不變)

    # 一般 URL：先拿完整 HTML
    response = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    response.raise_for_status()
    html = response.text

    # 用 trafilatura 提取正文（取代原本的 _strip_html）
    return _extract_article_text(html, url)
```

**保留 `_strip_html()`** 作為 private fallback，不刪除。

### CLI / API 影響

無。`fetch_url_content()` 的簽名和返回值不變，對上層完全透明。

### 測試

```python
# tests/test_fetcher.py
def test_trafilatura_extracts_clean_text():
    """真實 HTML 頁面應該只返回正文，不含 nav/footer。"""
    html = '<html><nav>Menu</nav><article><p>Article body here.</p></article><footer>Footer</footer></html>'
    result = _extract_article_text(html, "https://example.com")
    assert "Article body" in result
    assert "Menu" not in result
    assert "Footer" not in result

def test_trafilatura_fallback_on_failure():
    """trafilatura 失敗時 fallback 到 regex strip。"""
    result = _extract_article_text("<div>Short</div>", "https://x.com")
    assert "Short" in result
```

---

## 1.2 提取 Prompt 自定義

### 現狀問題

`SYSTEM_PROMPT` 硬編碼中文，提取結果固定為：
- 標題 ≤15 字（中文）
- 3-5 個重點，每個 30-50 字（中文）
- 無法控制語言、語氣、重點數量

### 設計

#### 1. 新 Dataclass: `ExtractionConfig`

```python
# src/extractor.py 新增

@dataclass(frozen=True)
class ExtractionConfig:
    """用戶可控的提取參數。"""
    language: str = "zh-TW"           # 輸出語言
    tone: str = "professional"         # professional | casual | academic | marketing
    max_points: int = 5                # 3-8
    min_points: int = 3                # 1-max_points
    title_max_chars: int = 15          # 標題字數上限
    point_max_chars: int = 50          # 每個重點字數上限
    custom_instructions: str = ""      # 用戶自定義附加指令
```

#### 2. Prompt 模板化

```python
# 取代硬編碼的 SYSTEM_PROMPT

def _build_system_prompt(config: ExtractionConfig) -> str:
    lang_name = {
        "zh-TW": "繁體中文", "zh-CN": "简体中文", "en": "English",
        "ja": "日本語", "ko": "한국어",
    }.get(config.language, config.language)

    tone_desc = {
        "professional": "專業、簡潔、客觀",
        "casual": "輕鬆、口語化、親切",
        "academic": "學術、嚴謹、引用數據",
        "marketing": "吸引眼球、強調價值、行動導向",
    }.get(config.tone, config.tone)

    return f"""你是一位專業的文章摘要分析師。

使用 {lang_name} 輸出。語氣風格：{tone_desc}。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{{
  "title": "文章的核心標題（{config.title_max_chars}字以內）",
  "key_points": [
    {{"text": "重點內容（{config.point_max_chars}字以內）"}}
  ],
  "source": "來源信息（如果有，否則留空字串）",
  "theme_suggestion": "dark 或 light 或 gradient 或 warm_sun 或 cozy"
}}

規則：
- key_points 必須有 {config.min_points} 到 {config.max_points} 個重點
- title 要簡潔有力，能夠概括文章核心
{f'- 附加要求：{config.custom_instructions}' if config.custom_instructions else ''}
- 只返回 JSON，不要有任何前言或後語"""
```

#### 3. 修改 `extract_key_points()` 簽名

```python
def extract_key_points(
    article_text: str,
    provider: str = "claude",
    config: ExtractionConfig | None = None,   # 新增，None = 使用預設
) -> dict[str, Any]:
    cfg = config or ExtractionConfig()
    system_prompt = _build_system_prompt(cfg)
    # ... 其餘邏輯不變，只是用 system_prompt 取代 SYSTEM_PROMPT 常量
```

**向後兼容**: `config=None` 時行為與現在完全一致（中文、3-5點、15字標題）。

#### 4. 擴展 `PipelineOptions`

```python
@dataclass(frozen=True)
class PipelineOptions:
    # ... 現有欄位不變
    extraction_config: ExtractionConfig | None = None   # 新增
```

#### 5. API 變更

```python
# web/api.py — 擴展 GenerateRequest

class ExtractionConfigRequest(BaseModel):
    language: str = "zh-TW"
    tone: str = "professional"
    max_points: int = 5
    min_points: int = 3
    title_max_chars: int = 15
    point_max_chars: int = 50
    custom_instructions: str = ""

class GenerateRequest(BaseModel):
    # ... 現有欄位不變
    extraction_config: ExtractionConfigRequest | None = None   # 新增
```

API response 不變。

#### 6. Web UI

在 GeneratePage 的 `AdvancedOptions` 折疊區內新增「提取設定」子區塊：

```
┌─ Advanced Options ────────────────────────────┐
│ Scale: [1x] [2x]     WebP: [toggle]          │
│ Brand Name: [________]                         │
│ Watermark: [position ▼] [opacity slider]      │
│ Thread Mode: [toggle]                          │
│                                                │
│ ─── Extraction Settings ───                    │
│ Language: [繁體中文 ▼]  Tone: [Professional ▼] │
│ Points: [3] ~ [5]      Title max: [15] chars  │
│ Custom instructions: [__________________]      │
└────────────────────────────────────────────────┘
```

**Store 變更** (`useGenerateStore.ts`):
```typescript
interface GenerateState {
  // ... 現有欄位
  extractionLanguage: string        // default "zh-TW"
  extractionTone: string            // default "professional"
  extractionMaxPoints: number       // default 5
  extractionMinPoints: number       // default 3
  extractionTitleMaxChars: number   // default 15
  extractionPointMaxChars: number   // default 50
  extractionCustomInstructions: string  // default ""
}
```

Persist to localStorage（已有 `partialize` 機制）。

#### 7. Validation

```python
def _validate_extraction_config(config: ExtractionConfig) -> None:
    if config.min_points < 1 or config.max_points > 8:
        raise ValueError("Points range must be 1-8")
    if config.min_points > config.max_points:
        raise ValueError("min_points must be <= max_points")
    if config.title_max_chars < 5 or config.title_max_chars > 100:
        raise ValueError("title_max_chars must be 5-100")
    if config.point_max_chars < 10 or config.point_max_chars > 200:
        raise ValueError("point_max_chars must be 10-200")
```

同時更新 `_validate_extracted_data()` 以使用 config 中的 min/max 而非硬編碼 3-5。

### 測試

```python
def test_extraction_config_english():
    config = ExtractionConfig(language="en", max_points=3, title_max_chars=10)
    prompt = _build_system_prompt(config)
    assert "English" in prompt
    assert "10" in prompt

def test_extraction_config_backwards_compatible():
    """None config 應該產生與原本相同的 prompt。"""
    default_prompt = _build_system_prompt(ExtractionConfig())
    assert "繁體中文" in default_prompt
    assert "15" in default_prompt
```

---

## 1.3 導出 HTML

### 設計

**改動極小** — `render_card()` 已經返回 HTML string，只需要暴露出來。

#### API

```python
# web/api.py 新增

@app.get("/api/export/html/{gen_id}")
def export_html(gen_id: int):
    """返回渲染後的 HTML 供下載或嵌入。"""
    row = history.get_generation_by_id(gen_id)
    if not row:
        raise HTTPException(404, "Generation not found")

    extracted = json.loads(row["extracted_data"]) if row["extracted_data"] else None
    if not extracted:
        raise HTTPException(400, "No extracted data available for this generation")

    options = PipelineOptions(
        theme=row["theme"],
        format=row["format"],
    )
    html_content = renderer.render_card(
        data=extracted,
        theme=options.theme,
        format=options.format,
    )

    return Response(
        content=html_content,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="imggen_{gen_id}.html"',
        },
    )
```

#### Web UI

在 `PreviewPanel.tsx` 的 action bar 增加一個「HTML」按鈕：

```typescript
// PreviewPanel.tsx — 在 Download 和 Copy 按鈕旁邊

const handleExportHtml = () => {
  if (!historyId) return
  const a = document.createElement('a')
  a.href = `/api/export/html/${historyId}`
  a.download = `imggen_${historyId}.html`
  a.click()
}

// 按鈕（僅在有 historyId 時顯示）
{historyId && (
  <button onClick={handleExportHtml} className="...">
    <Code size={16} />
  </button>
)}
```

#### Store 變更

`PreviewPanel` 需要讀取 `historyId`：
```typescript
const historyId = useGenerateStore((s) => s.historyId)
```

### 測試

```python
def test_export_html_returns_html(client):
    # 先生成一張卡片
    gen = client.post("/api/generate", json={"text": "test", "theme": "dark", "format": "story"})
    history_id = gen.json()["history_id"]

    resp = client.get(f"/api/export/html/{history_id}")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "核心要點" in resp.text or "<html" in resp.text

def test_export_html_404(client):
    resp = client.get("/api/export/html/99999")
    assert resp.status_code == 404
```

---

# Sprint 2: 現代內容接入管道

---

## 2.1 Telegram Bot

### 概覽

Telegram Bot 是 imgGen 最自然的個人自動化入口。用戶轉發文章或貼上連結，Bot 自動生成卡片並回傳圖片。

### 架構

```
Telegram App
    │
    ▼ (webhook or polling)
src/telegram_bot.py
    │
    ├─ 文字訊息 → pipeline.run_pipeline()
    ├─ URL 訊息 → fetcher.fetch_url_content() → pipeline.run_pipeline()
    ├─ 圖片訊息 → Vision API OCR → pipeline.run_pipeline()  (Phase 2.3)
    └─ PDF 檔案 → pdf_reader.extract_text() → pipeline.run_pipeline()  (Phase 2.3)
    │
    ▼
history.record_generation() → 回傳圖片到 Telegram
```

### 模組設計

```python
# src/telegram_bot.py

"""
Telegram bot for imgGen — forward articles, receive card images.

Usage:
    # Polling mode (development)
    python -m src.telegram_bot

    # Webhook mode (production, integrated with FastAPI)
    # Configured via /api/telegram/webhook endpoint
"""

from dataclasses import dataclass
from pathlib import Path
from telegram import Update, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes,
)

from src.pipeline import PipelineOptions, run_pipeline, render_and_capture
from src.fetcher import fetch_url_content
from src.history import record_generation
from src.extractor import ExtractionConfig

@dataclass(frozen=True)
class BotConfig:
    """Bot 運行時配置。"""
    token: str                          # TELEGRAM_BOT_TOKEN env var
    default_theme: str = "dark"
    default_format: str = "story"
    default_provider: str = "cli"
    allowed_chat_ids: set[int] | None = None  # None = allow all
```

### 命令設計

| 命令 | 說明 | 範例 |
|------|------|------|
| `/start` | 歡迎訊息 + 使用說明 | |
| `/theme <name>` | 設定預設主題 | `/theme gradient` |
| `/format <name>` | 設定預設格式 | `/format square` |
| `/provider <name>` | 設定 AI provider | `/provider gemini` |
| `/settings` | 顯示當前設定 | |
| `/history` | 最近 5 筆生成記錄 | |

### 訊息處理流程

```python
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理所有非命令訊息。"""
    msg = update.message
    chat_id = msg.chat_id

    # 1. 取得用戶設定（存在 context.user_data 中）
    user_settings = context.user_data.get("settings", {})
    theme = user_settings.get("theme", "dark")
    fmt = user_settings.get("format", "story")
    provider = user_settings.get("provider", "cli")

    # 2. 判斷輸入類型
    text = msg.text or msg.caption or ""

    # 檢查是否為 URL
    urls = _extract_urls(text)

    # 3. 發送「生成中」提示
    progress_msg = await msg.reply_text("⏳ 生成中...")

    try:
        if urls:
            # URL 模式：抓取內容
            article_text = fetch_url_content(urls[0])
        elif len(text) > 20:
            # 文字模式：直接使用
            article_text = text
        else:
            await progress_msg.edit_text("❌ 請傳送文章文字（>20字）或 URL")
            return

        # 4. 執行 pipeline
        options = PipelineOptions(theme=theme, format=fmt, provider=provider)
        output_path = _build_output_path(theme, fmt)
        data, final_path = run_pipeline(article_text, options, output_path)

        # 5. 記錄到 history
        record_generation(
            url=urls[0] if urls else None,
            title=data["title"],
            theme=theme,
            format=fmt,
            provider=provider,
            output_path=str(final_path),
            file_size=final_path.stat().st_size,
            key_points_count=len(data["key_points"]),
            source=data.get("source", ""),
            extracted_data=json.dumps(data, ensure_ascii=False),
        )

        # 6. 回傳圖片
        await msg.reply_photo(
            photo=open(final_path, "rb"),
            caption=f"📋 {data['title']}\n🎨 {theme} | 📐 {fmt}",
        )
        await progress_msg.delete()

    except Exception as e:
        await progress_msg.edit_text(f"❌ 生成失敗：{str(e)[:200]}")
```

### 用戶設定持久化

每個 chat_id 的設定存在 `~/.imggen/telegram_users.toml`：

```toml
[chat.123456789]
theme = "gradient"
format = "square"
provider = "gemini"
```

### 環境變量

```bash
TELEGRAM_BOT_TOKEN=xxx        # 必須
TELEGRAM_ALLOWED_CHATS=       # 可選，逗號分隔的 chat_id，空 = 允許所有
```

### CLI 集成

```python
# main.py 新增 subcommand

@main.command()
@click.option("--webhook", is_flag=True, help="Use webhook mode instead of polling")
@click.option("--port", default=8443, help="Webhook port")
def telegram(webhook: bool, port: int):
    """Start the Telegram bot."""
    from src.telegram_bot import run_bot
    run_bot(webhook=webhook, port=port)
```

### FastAPI 集成（Webhook 模式）

```python
# web/api.py 新���

@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request):
    """Telegram webhook endpoint — 用於生產環境。"""
    from src.telegram_bot import get_application
    app_instance = get_application()
    update = Update.de_json(await request.json(), app_instance.bot)
    await app_instance.process_update(update)
    return {"ok": True}
```

### 安全考量

- `allowed_chat_ids` 白名單限制誰能使用 bot
- 單 chat 限速：每分鐘最多 5 次生成（避免 abuse）
- 文字長度上限：10000 字（防止過大 payload）
- Bot token 不寫入代碼，只從環境變量讀取

### 測試

```python
def test_url_extraction():
    urls = _extract_urls("看看這篇 https://example.com/article 很好")
    assert urls == ["https://example.com/article"]

def test_message_too_short():
    """短於 20 字的純文字應該被拒絕。"""
    # mock update with text "hi"
    # assert reply contains "請傳送文章文字"

def test_generate_from_text():
    """長文字應該觸發 pipeline 並回傳圖片。"""
    # mock update with 200-char article text
    # assert reply_photo was called
```

---

## 2.2 Webhook API

### 概覽

通用 Webhook endpoint，讓 imgGen 接入任何自動化工具（Zapier、n8n、IFTTT、iOS Shortcuts、自定義腳本）。

### API 設計

#### 認證：API Key

```python
# src/api_keys.py

"""API Key 管理 — 存儲在 ~/.imggen/keys.toml"""

import secrets
import toml
from pathlib import Path

KEYS_PATH = Path.home() / ".imggen" / "keys.toml"

def generate_key() -> str:
    """生成 imggen_ 前綴的 API key。"""
    return f"imggen_{secrets.token_urlsafe(32)}"

def create_key(name: str) -> str:
    """創建並存儲新 key，返回 key 值。"""
    key = generate_key()
    keys = _load_keys()
    keys[key] = {"name": name, "created_at": datetime.now().isoformat()}
    _save_keys(keys)
    return key

def validate_key(key: str) -> bool:
    """驗證 key 是否有效。"""
    return key in _load_keys()

def list_keys() -> list[dict]:
    """列出所有 key（隱藏實際值，只顯示前 12 字元）。"""
    return [
        {"key_prefix": k[:16] + "...", "name": v["name"], "created_at": v["created_at"]}
        for k, v in _load_keys().items()
    ]

def revoke_key(key_prefix: str) -> bool:
    """透過 prefix 撤銷 key。"""
    keys = _load_keys()
    to_delete = [k for k in keys if k.startswith(key_prefix)]
    if not to_delete:
        return False
    for k in to_delete:
        del keys[k]
    _save_keys(keys)
    return True
```

#### Webhook Endpoint

```python
# web/api.py 新增

class WebhookGenerateRequest(BaseModel):
    text: str | None = None
    url: str | None = None
    theme: str = "dark"
    format: str = "story"
    provider: str = "cli"
    scale: int = 2
    webp: bool = False
    brand_name: str | None = None
    callback_url: str | None = None     # 完成後 POST 結果到此 URL
    extraction_config: ExtractionConfigRequest | None = None

class WebhookResponse(BaseModel):
    ok: bool
    job_id: str
    message: str = "Generation queued"

class WebhookCallbackPayload(BaseModel):
    job_id: str
    ok: bool
    image_url: str | None = None
    title: str | None = None
    extracted_data: dict | None = None
    history_id: int | None = None
    error: str | None = None

def _verify_api_key(request: Request) -> str:
    """從 header 驗證 API key。"""
    key = request.headers.get("X-API-Key", "")
    if not key or not api_keys.validate_key(key):
        raise HTTPException(401, "Invalid or missing API key")
    return key

@app.post("/api/webhook/generate", response_model=WebhookResponse)
async def webhook_generate(
    req: WebhookGenerateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """異步生成卡片。立即返回 job_id，背景處理完成後 POST 到 callback_url。"""
    _verify_api_key(request)

    job_id = f"job_{uuid4().hex[:12]}"

    background_tasks.add_task(
        _process_webhook_job,
        job_id=job_id,
        req=req,
    )

    return WebhookResponse(ok=True, job_id=job_id)


async def _process_webhook_job(job_id: str, req: WebhookGenerateRequest):
    """背景任務：執行生成並回呼。"""
    try:
        # 1. 取得文字
        if req.url:
            article_text = fetch_url_content(req.url)
        elif req.text:
            article_text = req.text
        else:
            raise ValueError("Must provide text or url")

        # 2. 建立選項
        extraction_config = None
        if req.extraction_config:
            extraction_config = ExtractionConfig(**req.extraction_config.model_dump())

        options = PipelineOptions(
            theme=req.theme, format=req.format, provider=req.provider,
            scale=req.scale, webp=req.webp, brand_name=req.brand_name,
            extraction_config=extraction_config,
        )
        output_path = _build_output_path(req.theme, req.format, req.webp)

        # 3. 執行 pipeline
        data, final_path = run_pipeline(article_text, options, output_path)

        # 4. 記錄 history
        history_id = record_generation(
            url=req.url,
            title=data["title"],
            theme=req.theme, format=req.format, provider=req.provider,
            output_path=str(final_path),
            file_size=final_path.stat().st_size,
            key_points_count=len(data["key_points"]),
            source=data.get("source", ""),
            extracted_data=json.dumps(data, ensure_ascii=False),
        )

        # 5. 回呼
        if req.callback_url:
            payload = WebhookCallbackPayload(
                job_id=job_id, ok=True,
                image_url=f"/output/{final_path.name}",
                title=data["title"],
                extracted_data=data,
                history_id=history_id,
            )
            async with httpx.AsyncClient() as client:
                await client.post(req.callback_url, json=payload.model_dump(), timeout=10)

    except Exception as e:
        if req.callback_url:
            payload = WebhookCallbackPayload(job_id=job_id, ok=False, error=str(e))
            async with httpx.AsyncClient() as client:
                await client.post(req.callback_url, json=payload.model_dump(), timeout=10)
```

#### 同步模式（簡單場景）

部分工具（如 iOS Shortcuts）不支持 callback，需要同步返回：

```python
@app.post("/api/webhook/generate/sync")
async def webhook_generate_sync(req: WebhookGenerateRequest, request: Request):
    """同步生成（阻塞直到完成）。適合 iOS Shortcuts 等簡單工具。"""
    _verify_api_key(request)
    # ... 直接執行 pipeline，同步返回結果
    # timeout: 60 秒
```

#### API Key 管理 Endpoints

```python
@app.post("/api/keys")
def create_api_key(body: dict, request: Request):
    """創建新 API Key。需要 Web UI 認證（同機器訪問）。"""
    name = body.get("name", "unnamed")
    key = api_keys.create_key(name)
    return {"ok": True, "key": key, "name": name}

@app.get("/api/keys")
def list_api_keys():
    return {"ok": True, "keys": api_keys.list_keys()}

@app.delete("/api/keys/{key_prefix}")
def revoke_api_key(key_prefix: str):
    success = api_keys.revoke_key(key_prefix)
    if not success:
        raise HTTPException(404, "Key not found")
    return {"ok": True}
```

#### Web UI: Settings 頁面

新增 `/settings` 路由：

```
┌─────────────────────────────────────────────────────┐
│ ⚙️ Settings                                         │
├─────────────────────────────────────────────────────┤
│                                                     │
│ API Keys                                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ imggen_a3f8k2...  │ "Zapier"   │ Mar 28 │ [🗑] │ │
│ │ imggen_x9m2p7...  │ "n8n"      │ Mar 25 │ [���] │ │
│ └─────────────────────────────────────────────────┘ │
│ [+ Create New Key]                                  │
│                                                     │
│ Webhook URL                                         │
│ POST http://localhost:8000/api/webhook/generate      │
│ Header: X-API-Key: <your-key>                       │
│                                                     │
│ Example (curl):                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ curl -X POST .../api/webhook/generate \         │ │
│ │   -H "X-API-Key: imggen_xxx" \                  │ │
│ │   -H "Content-Type: application/json" \         │ ���
│ │   -d '{"url":"https://...","theme":"dark"}'     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Telegram Bot                                        │
│ Token: [●●●●●●●●●●] [Save]                        │
│ Status: 🟢 Running (polling mode)                   │
│ Allowed chats: [________] (空 = 允許所有)            │
└���────────────────────────────────────────────────────┘
```

### Zapier / n8n 使用範例

**Zapier**:
```
Trigger: New item in Pocket
Action: Webhooks by Zapier → POST
  URL: http://your-server:8000/api/webhook/generate/sync
  Headers: X-API-Key = imggen_xxx
  Body: {"url": "{{url}}", "theme": "dark", "format": "story"}
```

**n8n**:
```json
{
  "nodes": [
    {"type": "n8n-nodes-base.httpRequest", "parameters": {
      "method": "POST",
      "url": "http://your-server:8000/api/webhook/generate",
      "headers": {"X-API-Key": "imggen_xxx"},
      "body": {"url": "={{$json.url}}", "callback_url": "http://n8n:5678/webhook/imggen-done"}
    }}
  ]
}
```

### 安全考量

- API Key 存在本地 TOML，不進 DB（避免 SQL 注入風險）
- Key 前綴 `imggen_` 方便在日誌中識別
- 限速：每 key 每分鐘 10 次請求
- Callback URL 驗證：只允許 HTTP/HTTPS scheme
- Sync endpoint timeout 60 秒，避免長時間占用連接

---

## 2.3 PDF 和圖片輸入

### PDF 輸入

```python
# src/pdf_reader.py

"""PDF 文字提取 — 用 PyMuPDF (fitz)。"""

import fitz  # PyMuPDF
from pathlib import Path

def extract_text_from_pdf(pdf_path: Path | str, max_pages: int = 20) -> str:
    """提取 PDF 前 N 頁的文字。"""
    doc = fitz.open(str(pdf_path))
    pages = min(len(doc), max_pages)
    text_parts = []

    for i in range(pages):
        page = doc[i]
        text_parts.append(page.get_text("text"))

    doc.close()
    full_text = "\n\n".join(text_parts)

    # 清理：移除過多空行，限制總長度
    full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()
    return full_text[:15000]  # AI 輸入上限
```

### 圖片輸入（Vision API）

```python
# src/extractor.py 新增

def extract_from_image(
    image_path: Path,
    provider: str = "claude",
    config: ExtractionConfig | None = None,
) -> dict[str, Any]:
    """用 Vision API 從圖片中提取結構化內容（OCR + 摘要一步完成）。"""
    cfg = config or ExtractionConfig()
    system_prompt = _build_system_prompt(cfg)

    # 讀取圖片為 base64
    import base64
    image_data = base64.standard_b64encode(image_path.read_bytes()).decode()
    media_type = "image/png" if image_path.suffix == ".png" else "image/jpeg"

    if provider in ("claude", "cli"):
        return _extract_image_with_claude(image_data, media_type, system_prompt)
    elif provider == "gpt":
        return _extract_image_with_gpt(image_data, media_type, system_prompt)
    elif provider == "gemini":
        return _extract_image_with_gemini(image_data, media_type, system_prompt)
    else:
        raise ValueError(f"Unsupported provider for image: {provider}")


def _extract_image_with_claude(
    image_b64: str, media_type: str, system_prompt: str
) -> dict[str, Any]:
    """Claude Vision API 提取。"""
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": media_type, "data": image_b64},
                },
                {"type": "text", "text": "請分析這張圖片中的內容並提取關鍵重點。"},
            ],
        }],
    )
    return _parse_json_response(message.content[0].text)
```

### API 變更

```python
# web/api.py — 修改 /api/generate 支持 file upload

@app.post("/api/generate")
async def generate(
    # 保留 JSON body 模式（向後兼容）
    req: GenerateRequest | None = None,
    # 新增 file upload 模式
    file: UploadFile | None = File(None),
    theme: str = Form("dark"),
    format: str = Form("story"),
    provider: str = Form("cli"),
    # ... 其他 form fields
):
    if file:
        # 判斷檔案類型
        suffix = Path(file.filename).suffix.lower()
        temp_path = Path(f"/tmp/imggen_{uuid4().hex}{suffix}")
        temp_path.write_bytes(await file.read())

        try:
            if suffix == ".pdf":
                article_text = pdf_reader.extract_text_from_pdf(temp_path)
                data, final_path = run_pipeline(article_text, options, output_path)
            elif suffix in (".png", ".jpg", ".jpeg", ".webp"):
                data = extractor.extract_from_image(temp_path, provider)
                final_path = render_and_capture(data, options, output_path)
            else:
                # .txt, .md — 直接讀取
                article_text = temp_path.read_text(encoding="utf-8")
                data, final_path = run_pipeline(article_text, options, output_path)
        finally:
            temp_path.unlink(missing_ok=True)
    else:
        # 原有 JSON body 邏輯
        ...
```

### Web UI

完善現有的 file upload tab（`InputTabs.tsx` 中已有 `inputMode: 'file'` 的 dropzone placeholder）：

```
┌─ File Upload ──────────────────────────────────┐
│                                                 │
│    ┌─────────────────────────────────────────┐  │
│    │         📄 Drop file here               │  │
│    │                                         │  │
│    │    PDF, TXT, MD, PNG, JPG              │  │
│    │    or click to browse                   │  │
│    └─────────────────────────────────────────┘  │
│                                                 │
│    Selected: article.pdf (2.3 MB)  [✕]         │
└───────────���──────────────────────────���──────────┘
```

### 依賴

```
PyMuPDF>=1.24.0    # PDF 文字提取
```

Claude/GPT Vision API 已在現有依賴中。

---

# Sprint 3: 輸出格式擴展

---

## 3.1 輪播圖

### 提取 Prompt

```python
CAROUSEL_SYSTEM_PROMPT = """你是一位社交媒體內容策劃師。

將文章拆分為適合輪播圖的格式：一個封面標題 + 4-6 個獨立觀點頁 + 一個結語/CTA 頁。

JSON 格式：
{
  "cover_title": "吸引眼球的封面標題（10字以內）",
  "cover_subtitle": "副標題（20字以內）",
  "slides": [
    {"heading": "小標題（8字以內）", "body": "正文（60-80字）"}
  ],
  "cta": {"text": "行動號召（15字以內）", "subtext": "補充說明（20字以內）"},
  "source": "來源",
  "theme_suggestion": "dark|light|gradient|warm_sun|cozy"
}

規則：
- slides 必須 4-6 個
- 每頁一個獨立觀點，讀者不需要看前後頁也能理解
- 封面要足夠吸引人，讓人想左滑看下去
"""
```

### 模板設計

3 個新模板（都用 CSS 變量適配主題）：

**`templates/carousel_cover.html`**
```
┌─────────────────────┐
│                     │
│  [LOGO]             │
│                     │
│  cover_title        │
│  (大字，居中)        │
│                     │
│  cover_subtitle     │
│                     │
│  ← SWIPE           │
│  [source]           │
└─────────────────────┘
```

**`templates/carousel_slide.html`**
```
┌─────────────────────┐
│  [slide_number/total]│
│                     │
│  heading            │
│  ────────           │
│                     │
│  body               │
│  (正文，左對齊)      │
│                     │
│                     │
│  [brand_name]       │
└─────────────────────┘
```

**`templates/carousel_cta.html`**
```
┌─────────────────────┐
│                     │
│                     │
│  cta.text           │
│  (大字，居中)        │
│                     │
│  cta.subtext        │
│                     │
│  [LOGO]             │
│  [brand_name]       │
└─────────────────────┘
```

### Pipeline

```python
# src/pipeline.py 新增

def run_carousel_pipeline(
    article_text: str,
    options: PipelineOptions,
    output_dir: Path,
) -> tuple[dict, list[Path]]:
    """生成輪播圖：封面 + N 張內容頁 + CTA。"""
    # 1. 用輪播專用 prompt 提取
    data = extract_carousel(article_text, options.provider)

    # 2. 生成封面
    paths = []
    cover_html = renderer.render_carousel_cover(data, options.theme, options.format)
    cover_path = output_dir / f"carousel_cover_{timestamp}.png"
    screenshotter.take_screenshot(cover_html, cover_path, options.format, options.scale)
    paths.append(cover_path)

    # 3. 生成每頁內容
    total = len(data["slides"])
    for i, slide in enumerate(data["slides"]):
        slide_html = renderer.render_carousel_slide(
            slide, i + 1, total, options.theme, options.format,
        )
        slide_path = output_dir / f"carousel_slide_{i+1}_{timestamp}.png"
        screenshotter.take_screenshot(slide_html, slide_path, options.format, options.scale)
        paths.append(slide_path)

    # 4. 生成 CTA 頁
    cta_html = renderer.render_carousel_cta(data, options.theme, options.format)
    cta_path = output_dir / f"carousel_cta_{timestamp}.png"
    screenshotter.take_screenshot(cta_html, cta_path, options.format, options.scale)
    paths.append(cta_path)

    return data, paths
```

### PDF 組裝

```python
# src/pdf_assembler.py

from PIL import Image
from pathlib import Path

def images_to_pdf(image_paths: list[Path], output_path: Path) -> Path:
    """將多張圖片合成為一個 PDF。"""
    images = [Image.open(p).convert("RGB") for p in image_paths]
    images[0].save(
        output_path, save_all=True, append_images=images[1:],
        resolution=144.0,
    )
    return output_path
```

### API

```python
@app.post("/api/generate/carousel")
async def generate_carousel(req: GenerateRequest):
    # ... 提取文字
    options = PipelineOptions(theme=req.theme, format=req.format, ...)
    output_dir = OUTPUT_DIR / f"carousel_{timestamp}"
    output_dir.mkdir(exist_ok=True)

    data, image_paths = run_carousel_pipeline(article_text, options, output_dir)

    # 組裝 PDF
    pdf_path = output_dir / "carousel.pdf"
    images_to_pdf(image_paths, pdf_path)

    return {
        "ok": True,
        "slides": [{"url": f"/output/{p.parent.name}/{p.name}", "index": i}
                    for i, p in enumerate(image_paths)],
        "pdf_url": f"/output/{pdf_path.parent.name}/{pdf_path.name}",
        "title": data["cover_title"],
        "extracted_data": data,
    }
```

### Web UI

輪播預覽器組件：

```
┌─────────────────────────────────────────────────┐
│  Carousel Preview                    1 / 7      │
│  ┌───────────────────────────────────────────┐  │
│  │                                           │  │
│  │         [Current Slide Image]             │  │
│  │                                           │  │
│  └───────────────────────────────────────────┘  │
│          [◀] ● ● ● ○ ○ ○ ○ [▶]               │
│                                                 │
│  [Download All] [Download PDF] [Copy Slide]     │
└────��────────────────────────────��───────────────┘
```

---

## 3.2 動態卡片 (GIF/MP4)

### 設計

利用 Playwright 的 video recording 功能捕獲 CSS 動畫。

```python
# src/screenshotter.py 新增

async def _record_animation_async(
    html_content: str,
    output_path: Path,
    format: str = "story",
    scale: int = 2,
    duration_ms: int = 3000,
) -> Path:
    """錄製卡片動畫為 MP4/GIF。"""
    width, height = FORMAT_DIMENSIONS.get(format, (430, 764))

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 開啟錄影
        context = await browser.new_context(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
            record_video_dir=str(output_path.parent),
            record_video_size={"width": width * scale, "height": height * scale},
        )
        page = await context.new_page()
        await page.set_content(html_content, wait_until="domcontentloaded")

        # 等待動畫播放完成
        await page.wait_for_timeout(duration_ms)

        await context.close()
        await browser.close()

    # Playwright 生成的是 .webm，需要轉換
    webm_files = list(output_path.parent.glob("*.webm"))
    if webm_files:
        webm_path = webm_files[0]
        if output_path.suffix == ".gif":
            _webm_to_gif(webm_path, output_path)
        else:
            _webm_to_mp4(webm_path, output_path)
        webm_path.unlink()

    return output_path


def _webm_to_gif(webm_path: Path, gif_path: Path) -> None:
    """WebM → GIF，使用 ffmpeg。"""
    import subprocess
    subprocess.run([
        "ffmpeg", "-i", str(webm_path),
        "-vf", "fps=15,scale=430:-1:flags=lanczos",
        "-y", str(gif_path),
    ], check=True, capture_output=True)


def _webm_to_mp4(webm_path: Path, mp4_path: Path) -> None:
    """WebM → MP4。"""
    import subprocess
    subprocess.run([
        "ffmpeg", "-i", str(webm_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-y", str(mp4_path),
    ], check=True, capture_output=True)
```

### API

```python
class GenerateRequest(BaseModel):
    # ... 現有欄位
    animated: bool = False              # 新增
    animation_format: str = "mp4"       # "mp4" | "gif"
    animation_duration: int = 3000      # ms
```

### 依賴

```
ffmpeg  # 系統級依賴，用於 WebM → MP4/GIF 轉換
```

---

## 3.3 新卡片類型

### Card Type System

```python
# src/renderer.py 擴展

VALID_CARD_TYPES = {"summary", "quote", "compare", "stats"}

def render_card(
    data: dict[str, Any],
    theme: str = "dark",
    format: str = "story",
    card_type: str = "summary",    # 新增
    # ... 其他參數不變
) -> str:
    if card_type == "summary":
        template_name = f"{theme}.html"           # 現有模板
    else:
        template_name = f"{card_type}.html"       # 新模板，用 CSS 變量
    # ...
```

### Quote Card 提取 Schema

```json
{
  "quote": "The best way to predict the future is to invent it.",
  "author": "Alan Kay",
  "context": "1971, Xerox PARC presentation",
  "theme_suggestion": "dark"
}
```

### Compare Card 提取 Schema

```json
{
  "title": "AI 開發：2024 vs 2026",
  "left": {"label": "Before", "points": ["手動編碼", "人工測試", "文檔寫不完"]},
  "right": {"label": "After", "points": ["AI 生成", "自動測試", "AI 文檔"]},
  "verdict": "效率提升 3 倍",
  "theme_suggestion": "gradient"
}
```

### Stats Card 提取 Schema

```json
{
  "stat_value": "73%",
  "stat_label": "的開發者每天使用 AI 工具",
  "context": "根據 2026 年 Stack Overflow 調查",
  "trend": "up",
  "source": "stackoverflow.com",
  "theme_suggestion": "dark"
}
```

### PipelineOptions 擴展

```python
@dataclass(frozen=True)
class PipelineOptions:
    # ... 現有欄位
    card_type: str = "summary"    # summary | quote | compare | stats
```

---

# Sprint 4: 自動分發

---

## 4.1 多平台發布

### DB Schema

```sql
CREATE TABLE IF NOT EXISTS publications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id      INTEGER NOT NULL REFERENCES generations(id),
    platform        TEXT NOT NULL,              -- twitter | linkedin | threads
    post_url        TEXT,                        -- 發布後的 URL
    caption         TEXT,
    status          TEXT NOT NULL DEFAULT 'published',  -- published | failed | scheduled
    published_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    -- 互動指標（Phase 5.1 填入）
    likes           INTEGER,
    comments        INTEGER,
    shares          INTEGER,
    impressions     INTEGER,
    metrics_updated_at TEXT
);
```

### Publisher 擴展

```python
# src/publisher.py 擴展

def publish_to_linkedin(image_path: Path, caption: str = "") -> str:
    """發布到 LinkedIn。需要 LINKEDIN_ACCESS_TOKEN。"""
    # LinkedIn API:
    # 1. Register upload → get upload URL
    # 2. Upload image binary
    # 3. Create post with image asset
    ...
    return post_url

def publish_to_threads(image_path: Path, caption: str = "") -> str:
    """發布到 Threads。需要 THREADS_ACCESS_TOKEN。"""
    # Threads API (Meta):
    # 1. Create media container with image URL
    # 2. Publish container
    ...
    return post_url
```

### API

```python
class PublishRequest(BaseModel):
    history_id: int
    platforms: list[str]                    # ["twitter", "linkedin"]
    captions: dict[str, str] | None = None  # {"twitter": "...", "linkedin": "..."}
    # 如果 captions 為 None，自動調用 caption 生成

@app.post("/api/publish")
async def publish(req: PublishRequest):
    row = history.get_generation_by_id(req.history_id)
    if not row:
        raise HTTPException(404)

    image_path = Path(row["output_path"])
    results = {}

    for platform in req.platforms:
        caption = (req.captions or {}).get(platform, "")
        try:
            if platform == "twitter":
                url = publisher.publish_to_twitter(image_path, caption)
            elif platform == "linkedin":
                url = publisher.publish_to_linkedin(image_path, caption)
            elif platform == "threads":
                url = publisher.publish_to_threads(image_path, caption)
            else:
                results[platform] = {"ok": False, "error": f"Unknown platform: {platform}"}
                continue

            # 記錄到 publications 表
            _record_publication(req.history_id, platform, url, caption)
            results[platform] = {"ok": True, "post_url": url}
        except Exception as e:
            results[platform] = {"ok": False, "error": str(e)}

    return {"ok": True, "results": results}
```

---

## 4.2 定時發布

### DB Schema

```sql
CREATE TABLE IF NOT EXISTS scheduled_posts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    history_id      INTEGER NOT NULL REFERENCES generations(id),
    platform        TEXT NOT NULL,
    caption         TEXT,
    scheduled_at    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',  -- pending | published | failed | cancelled
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    published_at    TEXT,
    error           TEXT
);
```

### Scheduler

```python
# src/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger

scheduler = AsyncIOScheduler()

def schedule_post(history_id: int, platform: str, caption: str, scheduled_at: datetime) -> int:
    """排程一篇發布。返回 scheduled_post id。"""
    post_id = _insert_scheduled_post(history_id, platform, caption, scheduled_at.isoformat())

    scheduler.add_job(
        _execute_scheduled_post,
        trigger=DateTrigger(run_date=scheduled_at),
        args=[post_id],
        id=f"post_{post_id}",
    )
    return post_id

async def _execute_scheduled_post(post_id: int):
    """執行排程的發布。"""
    post = _get_scheduled_post(post_id)
    if post["status"] != "pending":
        return

    try:
        row = history.get_generation_by_id(post["history_id"])
        image_path = Path(row["output_path"])

        if post["platform"] == "twitter":
            url = publisher.publish_to_twitter(image_path, post["caption"])
        elif post["platform"] == "linkedin":
            url = publisher.publish_to_linkedin(image_path, post["caption"])
        # ...

        _update_scheduled_post(post_id, status="published", published_at=datetime.now().isoformat())
        _record_publication(post["history_id"], post["platform"], url, post["caption"])
    except Exception as e:
        _update_scheduled_post(post_id, status="failed", error=str(e))
```

### API

```python
class ScheduleRequest(BaseModel):
    history_id: int
    platform: str
    caption: str = ""
    scheduled_at: str          # ISO 8601 datetime

@app.post("/api/schedule")
def create_schedule(req: ScheduleRequest):
    dt = datetime.fromisoformat(req.scheduled_at)
    if dt <= datetime.now():
        raise HTTPException(400, "scheduled_at must be in the future")
    post_id = scheduler.schedule_post(req.history_id, req.platform, req.caption, dt)
    return {"ok": True, "id": post_id}

@app.get("/api/schedule")
def list_schedules(status: str = "pending"):
    return {"ok": True, "posts": scheduler.list_posts(status)}

@app.delete("/api/schedule/{post_id}")
def cancel_schedule(post_id: int):
    scheduler.cancel_post(post_id)
    return {"ok": True}
```

---

## 4.3 End-to-End 自動化

### Telegram Bot `/auto` 模式

```python
# Telegram Bot 擴展

async def handle_auto_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自動模式：收到 → 生成 → 自動發布。"""
    user_settings = context.user_data.get("settings", {})
    auto_platforms = user_settings.get("auto_publish", [])  # e.g. ["twitter", "linkedin"]

    if not auto_platforms:
        await update.message.reply_text("❌ 請先用 /auto twitter,linkedin 設定自動發布平台")
        return

    # 1. 生成卡片（同 handle_message）
    data, final_path, history_id = await _generate_card(update, context)

    # 2. 自動生成 caption
    captions = {}
    for platform in auto_platforms:
        caption_result = caption.generate_captions(
            platforms=[platform], provider=user_settings.get("provider", "cli"), data=data,
        )
        captions[platform] = caption_result.get(platform, "")

    # 3. 自動發布
    results = []
    for platform in auto_platforms:
        try:
            url = _publish(platform, final_path, captions[platform])
            results.append(f"✅ {platform}: {url}")
        except Exception as e:
            results.append(f"❌ {platform}: {e}")

    # 4. 回報結果
    await update.message.reply_photo(
        photo=open(final_path, "rb"),
        caption=f"📋 {data['title']}\n\n" + "\n".join(results),
    )
```

### Webhook `auto_publish` 參數

```python
class WebhookGenerateRequest(BaseModel):
    # ... 現有欄位
    auto_publish: list[str] | None = None    # 新增: ["twitter", "linkedin"]
    auto_caption: bool = True                 # 自動生成 caption
```

---

# Sprint 5: 效果回饋

---

## 5.1 互動追蹤

### Metrics Polling

```python
# src/analytics.py

async def poll_metrics(publication_id: int) -> dict:
    """從平台 API 獲取最新互動指標。"""
    pub = _get_publication(publication_id)

    if pub["platform"] == "twitter":
        metrics = await _poll_twitter_metrics(pub["post_url"])
    elif pub["platform"] == "linkedin":
        metrics = await _poll_linkedin_metrics(pub["post_url"])
    # ...

    _update_publication_metrics(publication_id, metrics)
    return metrics

async def _poll_twitter_metrics(post_url: str) -> dict:
    """Twitter API v2 — 獲取推文互動數據。"""
    tweet_id = post_url.split("/")[-1]
    # GET /2/tweets/{id}?tweet.fields=public_metrics
    return {
        "likes": data["public_metrics"]["like_count"],
        "comments": data["public_metrics"]["reply_count"],
        "shares": data["public_metrics"]["retweet_count"],
        "impressions": data["public_metrics"]["impression_count"],
    }
```

### API

```python
@app.get("/api/analytics")
def get_analytics(days: int = 30):
    """返回發布內容的互動數據匯總。"""
    return {
        "ok": True,
        "total_publications": ...,
        "total_engagement": ...,
        "by_platform": [...],
        "by_theme": [...],           # 哪個主題效果最好
        "by_format": [...],          # 哪個格式效果最好
        "by_card_type": [...],       # 哪種卡片類型效果最好
        "top_posts": [...],          # 互動最高的 5 篇
        "trend": [...],              # 每日互動趨勢
    }
```

### Web UI: Analytics Dashboard

新增 `/analytics` 路由（或在 History 的 Stats tab 中整合）：

```
┌─────────────────────────────────────────────────────┐
│ 📊 Analytics                          [7d] [30d]    │
├─────────────────────────────────────────────────────┤
│                                                     │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│ │ 156      │ │ 2.3K     │ │ 89       │ │ 12.5K   │ │
│ │ Posts    │ │ Likes    │ │ Comments │ │ Views   │ │
│ └──────────┘ └──────────┘ └──────────┘ └─────────┘ │
│                                                     │
│ Best Performing Theme:   [gradient] avg 45 likes    │
│ Best Performing Format:  [square]   avg 38 likes    │
│ Best Performing Type:    [quote]    avg 52 likes    │
│                                                     │
│ Top Posts:                                          │
│  1. "AI 改變開發" — 234 likes — Twitter — dark      │
│  2. "73% 開發者"  — 189 likes — LinkedIn — gradient │
│  3. ...                                             │
└─────────────────────────────────��───────────────────┘
```

---

## 5.2 A/B 主題測試

### API

```python
class ABTestRequest(BaseModel):
    text: str | None = None
    url: str | None = None
    themes: list[str]           # ["dark", "gradient", "light"]
    format: str = "story"
    provider: str = "cli"
    auto_publish: dict[str, list[str]] | None = None
    # e.g. {"dark": ["twitter"], "gradient": ["linkedin"]}

@app.post("/api/generate/ab")
async def generate_ab(req: ABTestRequest):
    """A/B 測試：同一篇文章，多個主題，返回所有版本。"""
    article_text = _resolve_text_from_req(req)

    # 提取一次，渲染多次
    data = extract(article_text, req.provider)

    results = []
    for theme in req.themes:
        options = PipelineOptions(theme=theme, format=req.format)
        output_path = _build_output_path(theme, req.format)
        final_path = render_and_capture(data, options, output_path)

        history_id = record_generation(...)
        results.append({
            "theme": theme,
            "image_url": f"/output/{final_path.name}",
            "history_id": history_id,
        })

    return {
        "ok": True,
        "extracted_data": data,
        "variants": results,
    }
```

---

## 5.3 AI 內容洞察

### API

```python
@app.get("/api/insights")
async def get_insights(days: int = 30, provider: str = "cli"):
    """AI 分析互動數據，生成內容建議。"""
    analytics_data = _get_analytics_summary(days)

    prompt = f"""分析以下社交媒體發布數據，給出 3-5 條具體可行的內容策略建議。

數據：
- 總發布：{analytics_data['total']} 篇
- 表現最好的主題：{analytics_data['best_theme']}（平均 {analytics_data['best_theme_avg']} 互動）
- 表現最好的格式：{analytics_data['best_format']}
- 表現最好的卡片類型：{analytics_data['best_card_type']}
- 互動趨勢：{analytics_data['trend_direction']}
- 最佳發布時段：{analytics_data['best_time_slots']}

請用 JSON 返回：
{{"insights": [{{"title": "建議標題", "description": "具體說明", "action": "可執行的行動"}}]}}
"""

    result = _call_provider(prompt, provider)
    return {"ok": True, "insights": result["insights"]}
```

---

## Sidebar 導航更新

新增頁面後的完整導航：

| Route | Label | Icon | Sprint |
|-------|-------|------|--------|
| `/` | Generate | Sparkles | 現有 |
| `/captions` | Captions | MessageSquare | 現有 |
| `/history` | History | Clock | 現有 |
| `/tools` | Tools | Wrench | 現有 |
| `/presets` | Presets | Bookmark | 現有 |
| `/settings` | Settings | Settings | Sprint 2 |
| `/analytics` | Analytics | BarChart3 | Sprint 5 |

---

## 新增依賴匯總

| 依賴 | 用途 | Sprint |
|------|------|--------|
| `trafilatura>=1.12.0` | 文章正文提取 | 1 |
| `python-telegram-bot>=21.0` | Telegram Bot | 2 |
| `PyMuPDF>=1.24.0` | PDF 文字提取 | 2 |
| `Pillow>=10.0.0` | PDF 組裝 | 3 |
| `ffmpeg` (系統) | WebM → MP4/GIF | 3 |
| `apscheduler>=3.10.0` | 定時發布 | 4 |
