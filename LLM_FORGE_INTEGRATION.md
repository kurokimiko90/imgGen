# imggen × LLM-Forge 集成指南

## 概述

imggen 已配置為：
1. **本地記錄完整提示詞** → `.tmp/prompts.db`（支持完整查詢）
2. **自動上報到 llm-forge Hub** → 中央版本統計（只上報哈希值）

→ 詳見 [PROMPT_LOGGER_GUIDE.md](PROMPT_LOGGER_GUIDE.md) 查詢本地完整提示詞

## 配置步驟

### 1️⃣ 更新 `.env` 文件

在項目根目錄創建/編輯 `.env`：

```bash
# 複製示例
cp .env.example .env

# 編輯 .env，添加：
LLM_FORGE_ENABLED=true
LLM_FORGE_HUB_URL=http://localhost:8765
LLM_FORGE_PROJECT_ID=imggen
```

### 2️⃣ 確保 Hub 運行中

```bash
cd ~/Documents/project/llm-forge
bun run hub
# 應看到：🔥 LLM-Forge Hub running on http://localhost:8765
```

### 3️⃣ 啟動 imggen API

```bash
cd ~/Documents/project/imggen
python web/api.py
```

## 代碼集成

### 在任何 LLM 調用後記錄

```python
from src.llm_forge_reporter import record_llm_call

# 在您的代碼中：
try:
    start_time = time.time()
    response = await call_llm(system_prompt, user_prompt, model)
    duration_ms = (time.time() - start_time) * 1000
    
    await record_llm_call(
        pipeline_id="web-api",
        stage="caption-generation",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output=response.content,
        tokens_in=response.usage.input_tokens,
        tokens_out=response.usage.output_tokens,
        model=response.model,
        duration_ms=int(duration_ms),
        success=True,
    )
except Exception as e:
    await record_llm_call(
        pipeline_id="web-api",
        stage="caption-generation",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        output="",
        tokens_in=0,
        tokens_out=0,
        model="unknown",
        duration_ms=0,
        success=False,
        error_message=str(e),
    )
    raise
```

## API 啟動時初始化

在 `web/api.py` 中：

```python
from src.llm_forge_reporter import init_llm_forge_auto_report

@app.on_event("startup")
async def startup():
    await init_llm_forge_auto_report()
    # ... 其他初始化代碼
```

## 環境變數

| 變數 | 説明 | 示例 |
|-----|------|------|
| `LLM_FORGE_ENABLED` | 啟用自動上報 | `true` / `false` |
| `LLM_FORGE_HUB_URL` | Hub 服務器地址 | `http://localhost:8765` |
| `LLM_FORGE_PROJECT_ID` | 項目識別符 | `imggen` |

## 離線容錯

如果 Hub 不可用，調用記錄會自動保存到 `.tmp/llm-forge-queue.json`。

當 Hub 再次可用時，隊列會自動刷新。

## 查看結果

### 檢查 Hub 健康

```bash
curl http://localhost:8765/health
```

### 查詢最新版本

```bash
curl http://localhost:8765/api/hub/versions-latest?limit=5
```

### 查看儀表盤（可選）

```bash
cd ~/Documents/project/llm-forge
bun run packages/dashboard/server.ts
# 打開 http://localhost:8766
```

## 故障排除

### 問題：「連接 Hub 失敗」

**檢查清單：**
1. Hub 服務器運行中？ `curl http://localhost:8765/health`
2. `.env` 中 `LLM_FORGE_ENABLED=true`？
3. 防火牆是否阻止 8765 端口？

### 問題：離線隊列堆積

**解決：**
1. 啟動 Hub
2. 重啟 imggen
3. 檢查日誌中 `[llm-forge]` 消息

## 數據清理

清除所有記錄並重新開始：

```bash
# 刪除 Hub 數據庫
rm ~/Documents/project/llm-forge/data/hub.db

# 刪除 imggen 離線隊列
rm ~/Documents/project/imggen/.tmp/llm-forge-queue.json

# 重啟 Hub 和 imggen
```
