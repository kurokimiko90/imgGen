# imggen × llm-forge 配置完成 ✅

## 已完成的配置

### 1. 環境變數 (.env)
- ✅ `LLM_FORGE_ENABLED=true` （默認啟用）
- ✅ `LLM_FORGE_HUB_URL=http://localhost:8765`
- ✅ `LLM_FORGE_PROJECT_ID=imggen`

### 2. 本地提示詞日誌系統
- ✅ 創建 `src/prompt_logger.py` - 本地 SQLite 數據庫
  - 存儲位置：`.tmp/prompts.db`
  - 記錄完整系統提示詞 + 用戶提示詞
  - 支持查詢和匯出

### 3. 集成到所有 LLM 調用模塊

#### `src/caption.py` - 社交媒體字幕生成
- ✅ 導入 `prompt_logger`
- ✅ 在 `_call_provider()` 中添加提示詞記錄
- ✅ 支持所有提供者：claude, gemini, gpt, cli
- **Pipeline ID**: `caption-generation`
- **Stage**: `caption`

#### `src/extractor.py` - 文章提取和摘要
- ✅ 導入 `prompt_logger`
- ✅ 修改所有提取函數添加日誌記錄：
  - `_extract_with_claude()`
  - `_extract_with_gemini()`
  - `_extract_with_gpt()`
  - `_extract_with_claude_cli_sync()`
- **Pipeline ID**: `extraction`
- **Stage**: `extract-key-points`

### 4. Web API 查詢端點
在 `web/api.py` 中添加了新 API：

```
GET /api/prompts/latest?limit=50
  → 獲取最新 N 個 LLM 調用

GET /api/prompts/stage/{pipeline_id}/{stage}?limit=100
  → 查詢特定 stage 的所有調用

GET /api/prompts/stats/{pipeline_id}/{stage}
  → 查看版本統計信息

POST /api/prompts/export
  → 匯出提示詞為 JSON
```

### 5. 文檔
- ✅ `PROMPT_LOGGER_GUIDE.md` - 完整使用指南
- ✅ `LLM_FORGE_INTEGRATION.md` - llm-forge 集成指南
- ✅ `.env.example` - 環境變數示例

## 快速開始

### 1️⃣ 啟動 llm-forge Hub
```bash
cd ~/Documents/project/llm-forge
bun run hub
# 輸出：🔥 LLM-Forge Hub running on http://localhost:8765
```

### 2️⃣ 啟動 imggen
```bash
cd ~/Documents/project/imggen
python web/api.py
```

### 3️⃣ 查詢本地完整提示詞

**通過 API：**
```bash
curl http://localhost:8000/api/prompts/latest?limit=10
```

**通過 SQLite 直接查詢：**
```bash
sqlite3 .tmp/prompts.db << 'EOF'
SELECT id, timestamp, model, provider,
       system_prompt, user_prompt
FROM prompt_logs
ORDER BY timestamp DESC
LIMIT 5;
EOF
```

## 數據流向

```
imggen LLM 調用
    ↓
    ├→ 記錄到 .tmp/prompts.db（完整提示詞）
    │
    └→ 上報到 llm-forge Hub（通過 llm-forge-reporter）
         ├→ 計算 systemPromptHash（SHA256 前 16 字）
         └→ POST /api/hub/call-record
              ↓
         llm-forge 數據庫
              ├→ llm_calls（所有調用）
              └→ llm_versions（版本聚合）
```

## 關鍵特性

### ✨ 本地隐私
- 完整提示詞只存儲在 imggen 本地
- llm-forge Hub 只看到哈希值
- 敏感數據不離開本項目

### 📊 版本追蹤
- 自動識別 systemPrompt 版本（基於哈希）
- 記錄每個版本的成功率、成本、性能
- 跨項目版本統計（在 llm-forge 中）

### 🔍 完整可查詢性
- 本地 SQLite：支持複雜 SQL 查詢
- Web API：標準 REST 接口
- JSON 匯出：便於分析和備份

## 完整提示詞查詢示例

### 查看最近失敗的調用
```bash
sqlite3 .tmp/prompts.db << 'EOF'
SELECT id, timestamp, model, error_message,
       substr(user_prompt, 1, 200) as prompt_preview
FROM prompt_logs
WHERE success = 0
ORDER BY timestamp DESC;
EOF
```

### 分析版本變化
```bash
sqlite3 .tmp/prompts.db << 'EOF'
-- 查看同一用戶提示詞的系統提示詞演化
SELECT DISTINCT
  user_hash,
  system_hash,
  COUNT(*) as version_calls,
  AVG(CASE WHEN success THEN 1 ELSE 0 END) as success_rate,
  MAX(timestamp) as last_used
FROM prompt_logs
WHERE pipeline_id = 'extraction'
GROUP BY user_hash, system_hash
ORDER BY last_used DESC;
EOF
```

### 導出特定階段的所有提示詞
```bash
curl -X POST http://localhost:8000/api/prompts/export \
  -d "pipeline_id=extraction&stage=extract-key-points"
# → .tmp/prompts_extraction_extract-key-points.json
```

## 故障排除

### 沒有看到日誌記錄？
1. 確認 API 運行中：`python web/api.py`
2. 檢查 .tmp/prompts.db 是否存在
3. 查詢：`sqlite3 .tmp/prompts.db "SELECT COUNT(*) FROM prompt_logs;"`
4. 檢查最新：`curl http://localhost:8000/api/prompts/latest`

### 數據庫被鎖定？
```bash
rm .tmp/prompts.db
# API 重啟時自動重建
```

## 下一步

1. **本地分析**：使用 SQLite 查詢完整提示詞
2. **llm-forge 儀表盤**：查看多項目版本演化
3. **自動優化**：（可選）使用 Opus 分析提示詞差異
4. **A/B 測試**：對比不同系統提示詞的效果

---

✅ 配置完成！所有 LLM 調用現在都被完整記錄。
