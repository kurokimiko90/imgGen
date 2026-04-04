# LLM API 完全遷移至 Claude CLI - 實施計劃

**目標**：所有 LLM 調用都使用 Claude Code CLI，無需 API key

**狀態**：進行中 - 已完成 70%

---

## ✅ 已完成

### 1. scripts/daily_curation.py - AI 策展模塊
- ✅ 移除 `import anthropic`
- ✅ 新增 `_call_claude()` 函數，支持 CLI 和 API 雙模式
- ✅ `call_claude_api()` 改用 `_call_claude(provider="cli")`（預設）
- ✅ `generate_image()` 改用 `provider="cli"`
- ✅ 測試結果：**AI 策展成功**（2/5 items passed filter）

### 2. src/caption.py - 圖文標題生成
- ✅ 改造 `_call_provider()` 支持 CLI
- ✅ 改為硬編碼 CLI 路徑 → 使用 `shutil.which("claude")`
- ✅ 添加 `--output-format`, `--model` 參數
- ✅ `generate_captions()` 預設改用 `provider="cli"`

### 3. src/extractor.py - 内容提取
- ✅ 已支持 CLI（設為預設 provider="cli"）
- ✅ 通過 `_extract_with_claude_cli()` 使用 asyncio

---

## ⚠️ 進行中 - 需修復

### 1. 資料庫架構不匹配
**問題**：Content 類有 `body` 欄位，但 DB 表沒有  
**狀態**：生成圖片時崩潰  
**方案**：
- [ ] 添加 migration 文件：`002_add_body_column.sql`
- [ ] 改進 `db.py._ensure_schema()` 執行 migrations
- [ ] 重建本地測試 DB

### 2. asyncio 事件迴圈衝突
**問題**：daily_curation.py (同步) 調用 extractor._extract_with_claude_cli() (異步)  
**狀態**：`asyncio.run() cannot be called from a running event loop`  
**方案**：
- [ ] 在 daily_curation.py 中改用同步 CLI 呼叫（參考 smart_renderer.py）
- [ ] 或改造 extractor.py 提供同步版本

---

## 測試驗證結果

### ✅ AI 策展通過
```
[A] DRY-RUN draft: Claude Code 被砍功能
[A] DRY-RUN draft: LLM 也有情緒系統？
Daily curation (dry-run) complete: 2 new DRAFTs created
```

### ❌ 圖片生成失敗
```
[daily_curation] Image generation failed: 
  asyncio.run() cannot be called from a running event loop
  table generations has no column named body
```

---

## 待做清單

### Phase 1: 修復資料庫架構（1小時）
1. 建立 `src/migrations/002_add_body_column.sql`
2. 改進 `src/db.py._ensure_schema()` 自動執行 migration
3. 清除本地 DB 或運行 migration
4. 測試 Content.create() 是否成功

### Phase 2: 修復 asyncio 衝突（30分鐘）
1. 在 daily_curation.py 中改用同步 CLI 呼叫
   - 改造 extractor.py 或建立同步包裝
   - 或在 daily_curation 中直接用 subprocess
2. 測試圖片生成是否成功

### Phase 3: 端對端測試（30分鐘）
1. `python scripts/daily_curation.py --account A --dry-run` ✅（已過）
2. `python scripts/daily_curation.py --account A` 實際生成圖片和保存 DB
3. Web UI ReviewPage 驗證 DRAFT 是否可見
4. 測試完整流程：爬蟲 → AI 策展 → 圖片 → DB → 審核

---

## 技術細節

### CLI 呼叫統一格式
```python
result = subprocess.run(
    [claude_cli, "-p", "--output-format", "text", "--model", model],
    input=prompt,
    capture_output=True,
    text=True,
    timeout=60,
    env=env,  # 過濾 ANTHROPIC_API_KEY 避免干擾
)
```

### Provider 參數優先級（全項目一致）
1. `provider="cli"` **（預設）** - 無需 API key，推薦
2. `provider="claude"` - 需要 ANTHROPIC_API_KEY
3. `provider="gemini"` - 需要 GOOGLE_API_KEY
4. `provider="gpt"` - 需要 OPENAI_API_KEY

---

## 後續效果

完成後，整個自動化管道都無需 API key：

```
爬蟲（自動）✅
  ↓
AI 策展（自動，CLI）✅
  ↓
圖片生成（自動，CLI）⚠️ 待修復
  ↓
保存 DRAFT（自動）✅
  ↓
Web UI 審核（手動）✅
  ↓
自動排期發佈 ✅
```
