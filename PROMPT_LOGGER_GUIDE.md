# Prompt Logger — 完整提示詞追踪系統

## 概述

Prompt Logger 自動記錄所有 LLM 呼叫的完整系統提示詞和用戶提示詞到本地 SQLite 資料庫，支持查詢、統計、匯出。

**核心特性：**
- ✅ 自動記錄 — 無需手動配置，所有提取和字幕生成呼叫自動記錄
- ✅ 本地存儲 — 完整提示詞存儲在 `.tmp/prompts.db`，隱私保護
- ✅ Web UI — 直觀的 `/prompts` 頁面查看所有記錄
- ✅ API 查詢 — RESTful API 支持程式化存取
- ✅ 版本控制 — SHA256 哈希追踪提示詞版本
- ✅ 匯出支持 — JSON 匯出用於外部分析

---

## 快速開始

### 1. 查看 Web UI

打開 http://localhost:5173/prompts 即可看到：

| 區域 | 內容 |
|------|------|
| **頂部統計卡** | Total Calls、Success Rate、Unique Prompts |
| **左欄記錄列表** | 所有 LLM 呼叫，按時間倒序；支持 Stage 篩選 |
| **右欄詳細面板** | 選中記錄的完整提示詞、輸出、錯誤訊息；支持複製 |

### 2. 生成示例記錄

如果資料庫為空，先運行一次提取：

```bash
# 方式 A：透過 API
curl -X POST http://localhost:8001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Artificial intelligence transforms industries. Machine learning enables personalization, autonomous systems, and predictive analytics.",
    "theme": "dark",
    "format": "story",
    "provider": "cli"
  }'

# 方式 B：透過 CLI
python main.py --text "AI article text" --theme dark
```

### 3. API 查詢示例

```bash
# 最新 50 筆記錄（快速列表）
curl http://localhost:8001/api/prompts/latest?limit=50 | jq .

# 特定 stage 的完整記錄（含提示詞）
curl http://localhost:8001/api/prompts/stage/extraction/extract-key-points | jq .

# 統計資訊
curl http://localhost:8001/api/prompts/stats/extraction/extract-key-points | jq .

# 匯出為 JSON
curl -X POST http://localhost:8001/api/prompts/export \
  -F "pipeline_id=extraction" \
  -F "stage=extract-key-points" \
  -o prompts_export.json
```

---

## 使用場景

### 1. 提示詞版本控制
追踪 system prompt 的演變。

### 2. 除錯
查看失敗呼叫的完整上下文和錯誤訊息。

### 3. 成本分析
統計每個 stage 的平均 output 長度、成功率、model 分布。

### 4. 合規記錄
所有 LLM 呼叫的完整追踪，支持查詢和匯出。

---

## API 端點

### GET `/api/prompts/latest?limit=50`
最新 N 筆記錄（不含完整提示詞）

### GET `/api/prompts/stage/{pipeline_id}/{stage}?limit=100`
特定 stage 的完整記錄（含完整提示詞和輸出）

### GET `/api/prompts/stats/{pipeline_id}/{stage}`
統計資訊（total_calls、success_rate、unique_prompts）

### POST `/api/prompts/export`
匯出特定 stage 的記錄為 JSON

---

## Web UI 組件

- **PromptStatsBar** — 頂部統計卡（Total Calls、Success Rate、Unique Prompts）
- **PromptLogList** — 左欄記錄列表，支持 Stage 篩選和點擊選擇
- **PromptDetailPanel** — 右欄詳細面板，展示完整提示詞、輸出、錯誤訊息，支持複製

---

## 資料庫

**表名：** `prompt_logs`

主要欄位：
- `id`, `timestamp`, `pipeline_id`, `stage`
- `system_prompt`, `user_prompt`, `system_hash`, `user_hash`
- `model`, `provider`, `output`, `output_length`
- `success`, `error_message`

**索引：** `timestamp DESC`, `(pipeline_id, stage)`, `system_hash`

---

## 故障排查

### 日誌為空
1. 確認後端正在運行：`curl http://localhost:8001/api/meta`
2. 確認資料庫存在：`ls -la .tmp/prompts.db`
3. 運行一次提取：`curl -X POST http://localhost:8001/api/generate ...`
4. 查詢 API：`curl http://localhost:8001/api/prompts/latest`

### 前端無法連接 API
1. 確認後端港口：`lsof -i :8001`
2. 確認前端代理設定：`cat web/frontend/vite.config.ts | grep proxy`

---

## 擴展

### 添加新 Stage
1. 在相應模組中加入 `log_prompt_call()` 呼叫
2. 設定正確的 `pipeline_id` 和 `stage` 值
3. Web UI 會自動反映新 stage

### 自訂統計
修改 `src/prompt_logger.py` 中的 `get_statistics()` 函數

---

## 效能

- 每筆記錄約 2-5 KB
- 索引支持秒級查詢（即使數千筆記錄）
- 後台線程記錄，不影響主流程

建議定期清理舊記錄：
```python
from src.prompt_logger import clear_old_logs
clear_old_logs(days=30)
```
