# 產品 Roadmap — Cycle 1（v1.1 → v2.0）
**工具**: imgGen
**週期**: 2026 Q2 — 2027 Q1
**維護者**: 一人

---

## North Star 指標

**每次執行成功率 >= 95%，且輸出圖卡無需後製即可直接發布。**

---

## v1.1 — CLI 體驗打磨

**一句話描述**: 讓每次使用都更順手，消除小摩擦。

**核心功能:**
- `--lang` 參數：指定摘要輸出語言（zh / en / ja），預設 zh
- 進度顯示改善：每個步驟加上耗時計時，讓使用者知道卡在哪
- URL 解析強化：整合 `trafilatura` 或 `readability-lxml` 取代 regex 剝 HTML
- 更好的錯誤訊息：API key 遺失、網路錯誤、模板遺失都給出明確的修復建議
- `--dry-run` 模式：只跑 AI 摘要不截圖，快速確認摘要品質

**複雜度**: S

---

## v1.2 — 設定檔支援

**一句話描述**: 把常用偏好存起來，不必每次都打一長串參數。

**核心功能:**
- `~/.imggen/config.toml` 設定檔：設定預設 provider、theme、lang、output 路徑
- `imggen config set <key> <value>` 子命令：快速更新設定
- `imggen config show` 子命令：印出目前設定
- 設定優先順序：CLI 參數 > 環境變數 > config 檔 > 預設值
- 設定檔版本控制：config schema 版本追蹤，升級時自動 migrate

**複雜度**: S

---

## v1.3 — 多主題擴充包

**一句話描述**: 提供更多視覺風格選擇，讓圖卡不單調。

**核心功能:**
- 新增 5 個主題：`neon`（霓虹風）、`minimal`（極簡白）、`forest`（自然綠）、`sunset`（暖橘色）、`newspaper`（報紙黑白）
- `imggen themes` 子命令：列出所有可用主題及預覽說明
- 自訂主題目錄：支援 `~/.imggen/themes/` 放入自製 HTML 模板
- 主題預覽模式：`--preview` 輸出一張含所有主題縮圖的比較圖
- 主題快取：避免每次都重新 compile Jinja2 環境

**複雜度**: M

---

## v1.4 — 批次處理

**一句話描述**: 一個指令處理多篇文章，解鎖週報、月報場景。

**核心功能:**
- `--file` 接受目錄路徑：處理目錄內所有 `.txt` 檔
- `--urls-file` 參數：讀取一個純文字 URL 清單，逐一處理
- 並行處理：URL fetch 和 API 呼叫使用 asyncio 並發（可設定最大並發數）
- 批次摘要報告：完成後輸出 `batch_report.json`，含每個檔案的狀態和輸出路徑
- 失敗重試：單篇失敗不中斷整批，失敗項目記錄後可用 `--retry-failed` 重跑

**複雜度**: M

---

## v1.5 — 輸出格式多樣化

**一句話描述**: 支援不同社群平台的最佳圖片比例。

**核心功能:**
- `--format` 參數：`square`（1:1, 1080x1080）、`story`（9:16, 1080x1920）、`landscape`（16:9, 1920x1080）、`twitter`（2:1, 1200x600）
- 模板自動適配：每個主題模板對應多種 format 的 CSS breakpoints
- `--scale` 參數：輸出解析度倍率（1x / 2x），2x 適合 Retina 螢幕
- 輸出 WebP 選項：`--format-output webp` 在 PNG 之外支援 WebP（更小的檔案）
- 檔名自動加上 format 後綴：`card_dark_20260328_square.png`

**複雜度**: M

---

## v1.6 — 個人品牌化

**一句話描述**: 在每張圖卡上加上自己的 logo 和個人識別。

**核心功能:**
- `--logo` 參數：指定 logo 圖片路徑，嵌入圖卡角落（支援 PNG / SVG）
- `--watermark` 參數：加入文字浮水印（例如 `@username`）
- 設定檔支援 logo / watermark 路徑，不必每次帶參數
- `--accent-color` 參數：覆蓋主題的強調色（十六進位色碼）
- Logo 位置控制：`--logo-position` 接受 `top-left / top-right / bottom-left / bottom-right`

**複雜度**: S

---

## v1.7 — 歷史記錄與 Gallery

**一句話描述**: 讓過去生成的圖卡可以被搜尋和檢視，不再是一堆無名 PNG。

**核心功能:**
- 本地 SQLite 資料庫：記錄每次生成的 title、來源 URL、主題、路徑、timestamp
- `imggen history` 子命令：列出最近 N 筆記錄（支援 `--limit`、`--theme`、`--provider` 篩選）
- `imggen history search <keyword>` 子命令：用關鍵字搜尋過去生成的標題
- `imggen history open <id>` 子命令：用系統預設程式開啟指定圖卡
- 自動清理：設定保留期限（例如 90 天），過期紀錄自動清除（但不刪圖檔）

**複雜度**: M

---

## v1.8 — 自訂 Prompt 與風格設定

**一句話描述**: 調整 AI 的摘要風格，讓輸出更符合個人口吻。

**核心功能:**
- `~/.imggen/prompt.md` 自訂 system prompt：完全覆蓋預設摘要指令
- `--style` 參數：預設風格選項 `analytical`（分析型）、`narrative`（敘事型）、`punchy`（短打重點型）
- `--points` 參數：指定摘要重點數量（3 / 4 / 5，預設 3）
- `--max-chars` 參數：每個重點的最大字數限制
- Prompt 模板變數支援：在自訂 prompt 中使用 `{article_text}`、`{lang}` 等佔位符

**複雜度**: S

---

## v1.9 — Watch 模式與工作流自動化

**一句話描述**: 監看一個資料夾，有新檔案就自動生成圖卡。

**核心功能:**
- `imggen watch <dir>` 子命令：使用 `watchdog` 監看目錄，偵測新 `.txt` 或 `.url` 檔案
- 自動處理新檔案並輸出到對應的 output 子目錄
- `.url` 格式支援：一個純文字檔內放一行 URL，watch 模式自動 fetch 並處理
- `--on-success` hook：生成成功後執行自訂 shell 指令（例如複製到 Dropbox）
- `--on-failure` hook：失敗時執行指令（例如發送桌面通知）

**複雜度**: M

---

## v2.0 — 快速預設組合（Preset System）

**一句話描述**: 把常用的參數組合存成命名預設，一個字叫出完整設定。

**核心功能:**
- `imggen preset save <name>` 子命令：把目前的所有參數（theme、format、provider、logo、style）存成預設
- `imggen preset list` 子命令：列出所有已存預設
- `imggen --preset <name>` 使用預設執行
- 內建預設範本：`tweet`（dark + twitter + claude + punchy）、`linkedin`（gradient + landscape + gpt + analytical）
- 預設匯出 / 匯入：`imggen preset export / import`，方便備份或在不同機器間同步

**複雜度**: S

---

## 功能選擇矩陣

以下從 10 個版本的功能中選出 **5 個候選明星功能**，進行量化評估。

評分維度：
- **使用者衝擊** (User Impact, 1–5)：這功能對日常使用頻率和品質的提升程度
- **可行性** (Feasibility, 1–5)：技術難度低、依賴少、容易實作的程度（5 = 最容易）
- **WOW Factor** (1–5)：第一次用到時讓人驚喜的程度

**最終分數 = 使用者衝擊 × 可行性 × WOW Factor**

| 功能 | 版本 | 使用者衝擊 | 可行性 | WOW Factor | 總分 |
|------|------|-----------|--------|------------|------|
| 批次處理（URL 清單 + 並行） | v1.4 | 5 | 3 | 4 | **60** |
| 多社群格式輸出（square/story/landscape） | v1.5 | 4 | 4 | 5 | **80** |
| 個人品牌化（logo + 浮水印） | v1.6 | 4 | 5 | 4 | **80** |
| 快速預設組合系統 | v2.0 | 5 | 5 | 3 | **75** |
| 多主題擴充包（+5 主題 + 自訂主題） | v1.3 | 4 | 3 | 5 | **60** |

### 共同第一名分析

**多社群格式輸出（v1.5）** 和 **個人品牌化（v1.6）** 並列 80 分。

**選定贏家：多社群格式輸出（v1.5）**

原因：

格式輸出直接解決了最高頻的摩擦點——每個社群平台的圖片比例不同（Twitter 是 2:1，Instagram Story 是 9:16，LinkedIn 是 16:9），現在每次都要手動裁切或留黑邊。這個功能讓一篇文章可以直接輸出三種格式、立刻全平台發布，WOW Factor 最高（5 分），且技術實作上只需要修改 Playwright 的 viewport 設定和 CSS，可行性高（4 分）。

個人品牌化（v1.6）雖然同分，但它屬於**一次性設定後就忘掉的功能**——設定完就固定了，後續衝擊遞減。格式輸出則是**每次使用都有感知價值**的功能，長期使用頻率更高，優先實作報酬率更高。

建議開發順序：先做 v1.5，再立刻接 v1.6（兩者可在同一個 sprint 組合進行，因為 v1.6 依賴 v1.5 的模板架構改動）。
