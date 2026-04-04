# imgGen 產品路線圖 — Cycle 4（v1.9 → v2.8）

**製作日期**: 2026-03-28
**基準版本**: v1.8（已實作功能：CLI 完整參數組、4 種 AI 供應商、4 種輸出格式、3 種視覺主題、浮水印系統、品牌名稱、TOML 設定檔）
**使用場景**: 單人本機工具，無雲端、無多用戶

---

## 版本規劃

---

### v1.9 — Smart Fetch（智慧擷取）

**一句話描述**: 以 trafilatura 取代正規表達式的 HTML 剝除，讓從 URL 擷取的文章內容品質大幅提升。

**主要功能**:
- 整合 trafilatura 作為 URL 內容擷取後端（自動去廣告、去導覽列、去 boilerplate）
- 保留 fallback 機制：trafilatura 失敗時退回原有 regex 方法
- 擷取文章標題並自動帶入卡片標題欄位
- 擷取文章發布日期（若可得）顯示於卡片底部
- 新增 `--fetch-method [auto|trafilatura|regex]` 參數供進階用戶手動指定

**複雜度**: S

---

### v2.0 — Batch Mode（批次處理）

**一句話描述**: 一次輸入多個 URL 或文字檔案，自動平行產生所有圖卡，大幅提升大量製作時的效率。

**主要功能**:
- `--batch FILE` 接受每行一個 URL 或文字路徑的純文字清單檔
- 平行處理（`asyncio` + Semaphore 控制並發數，預設 3）
- 自動命名輸出檔（以 slug 或序號為檔名）
- 批次摘要報告：成功 N 筆、失敗 N 筆，並列出失敗原因
- 支援 `--output-dir` 指定批次輸出目錄

**複雜度**: M

---

### v2.1 — Preset System（命名預設組合）

**一句話描述**: 將常用的 `--theme + --format + --brand-name + --provider` 參數組合儲存為具名 preset，一個旗標取代六個參數。

**主要功能**:
- `--save-preset NAME` 將目前所有參數快照寫入 `~/.imggenrc` 的 `[preset.NAME]` 區塊
- `--preset NAME` 套用已儲存的 preset（任何同場明確傳入的參數仍可覆蓋）
- `--list-presets` 列出所有已儲存 preset 及其關鍵設定摘要
- `--delete-preset NAME` 刪除指定 preset
- 內建 3 組示範 preset：`news`、`essay`、`quote`，隨安裝附帶

**複雜度**: S

---

### v2.2 — Prompt Styles（AI 提示風格預設）

**一句話描述**: 提供多種 AI 摘要風格（新聞式、學術式、社群行銷式等），讓輸出文案語調與用途精準匹配。

**主要功能**:
- `--style [news|academic|marketing|tweet|tldr|custom]` 切換提示模板
- 每種風格對應不同的 system prompt 與 user prompt 結構（字數限制、語氣、重點提取策略各異）
- `--style custom --prompt-file PATH` 支援完全自訂 prompt 檔（Jinja2 模板格式）
- 風格可寫入 preset，與 v2.1 整合
- 新增 `--dry-run` 旗標：只輸出 AI 產生的摘要文字，不執行截圖（方便審閱文案）

**複雜度**: M

---

### v2.3 — Output History（輸出歷史紀錄）

**一句話描述**: 以本機 SQLite 資料庫記錄每次產生的圖卡元資料，提供簡易查詢與重新產生功能。

**主要功能**:
- 每次成功產出後自動寫入 `~/.imggen_history.db`（記錄：時間戳、來源 URL/文字摘要、參數快照、輸出路徑）
- `imggen history list` 子命令：列出最近 N 筆紀錄（預設 20）
- `imggen history show ID` 顯示單筆完整參數
- `imggen history regenerate ID` 以相同參數重新產生（支援 `--output` 覆蓋路徑）
- `imggen history clear [--before DATE]` 清除歷史紀錄

**複雜度**: M

---

### v2.4 — Custom Themes（自訂主題系統）

**一句話描述**: 讓用戶以 TOML 設定檔定義自己的色彩、字型、排版主題，徹底擺脫內建主題限制。

**主要功能**:
- `~/.imggen_themes/` 目錄下存放 `.toml` 主題檔，`--theme NAME` 自動搜尋此目錄
- 主題 TOML 支援：背景色/漸層、文字色、字型族（本機已安裝）、行高、內距、強調色
- `imggen theme validate PATH` 驗證主題檔語法與必填欄位
- `imggen theme export NAME` 將內建主題匯出為 TOML 以供修改參考
- 主題名稱可寫入 `~/.imggenrc` 作為預設

**複雜度**: M

---

### v2.5 — Watch Mode（監看模式）

**一句話描述**: 監看指定目錄或剪貼簿，偵測到新文字檔或 URL 時自動觸發圖卡產生，實現零中斷工作流。

**主要功能**:
- `imggen watch --dir PATH` 監看目錄，偵測 `.txt` 新增檔案自動處理
- `imggen watch --clipboard` 輪詢剪貼簿，偵測到 URL 自動處理（macOS `pbpaste`，可設定輪詢間隔）
- 處理完成後系統通知（macOS `osascript`）
- `--watch-preset NAME` 搭配 v2.1 preset 使用，固定輸出風格
- `Ctrl+C` 優雅退出，顯示本次 watch session 統計（處理筆數、成功率、平均耗時）

**複雜度**: L

---

### v2.6 — Clipboard Output（剪貼簿輸出）

**一句話描述**: 圖卡產生後直接複製到剪貼簿，讓貼入社群媒體或簡報的動作從三步變成一步。

**主要功能**:
- `--clipboard` 旗標：產生圖卡後自動複製圖片到剪貼簿（macOS 使用 `osascript`/`pbcopy`）
- 支援同時輸出檔案並複製（`--output FILE --clipboard` 兩者並存）
- PNG 與 WebP 均支援剪貼簿（WebP 自動轉 PNG 再複製，因 macOS 剪貼簿限制）
- 批次模式（v2.0）下剪貼簿僅複製最後一張，並提示用戶
- 複製成功後終端顯示確認訊息及圖片尺寸

**複雜度**: S

---

### v2.7 — Gallery TUI（終端圖庫瀏覽器）

**一句話描述**: 在終端機以 Textual 框架呈現歷史輸出圖庫，支援鍵盤瀏覽、快速重新產生與刪除。

**主要功能**:
- `imggen gallery` 啟動 TUI 圖庫（基於 v2.3 SQLite 歷史資料）
- 網格縮圖預覽（以 terminal 像素藝術或 Sixel/iTerm2 inline image protocol 呈現）
- 方向鍵瀏覽，`Enter` 查看完整參數，`R` 重新產生，`D` 刪除記錄，`O` 在 Finder 開啟
- 搜尋篩選：依日期範圍、主題、格式、關鍵字
- `Q` / `Esc` 退出，所有操作均有確認提示

**複雜度**: L

---

### v2.8 — Plugin API（外掛擴充介面）

**一句話描述**: 公開穩定的 Python 插件介面，讓進階用戶自行新增 AI 供應商、HTML 主題或內容擷取器，無需修改核心程式碼。

**主要功能**:
- 定義 `ProviderPlugin`、`ThemePlugin`、`FetcherPlugin` 三個 ABC（抽象基底類別）介面
- `~/.imggen_plugins/` 目錄下的 `.py` 檔自動被探索與載入（importlib 動態載入）
- `imggen plugins list` 列出已載入插件及其類型與版本
- 完整插件開發文件（`docs/plugin_authoring.md`）含三個範例插件
- 版本化介面：`PLUGIN_API_VERSION` 常數防止不相容插件載入時靜默損壞

**複雜度**: L

---

## 功能選擇矩陣

以下針對本 Cycle 中最具代表性的「候選突破功能」進行評分，協助決定優先衝刺順序。

評分標準（各項 1–5 分）:
- **用戶衝擊 (U)**: 對日常使用體驗的實質改善程度
- **可行性 (F)**: 技術實作難度低、依賴少、不易出錯（5 = 最易實作）
- **WOW 因子 (W)**: 第一次看到時的驚艷感、分享慾、差異化程度

| 功能 | 版本 | 用戶衝擊 (U) | 可行性 (F) | WOW 因子 (W) | 總分 U×F×W |
|------|------|:-----------:|:---------:|:-----------:|:----------:|
| 智慧 URL 擷取（trafilatura） | v1.9 | 5 | 5 | 3 | 75 |
| **批次處理（Batch Mode）** | **v2.0** | **5** | **4** | **4** | **80** |
| 命名 Preset 系統 | v2.1 | 4 | 5 | 3 | 60 |
| AI 提示風格 + --dry-run | v2.2 | 4 | 4 | 4 | 64 |
| 剪貼簿輸出 | v2.6 | 4 | 5 | 4 | 80 |

### 勝出功能：**v2.0 批次處理** 與 **v2.6 剪貼簿輸出**（並列 80 分）

**決策說明**:

兩個功能並列最高分，但性質互補，建議依序實作：

**v2.0 批次處理**（首選衝刺）代表對核心工作流的結構性升級。單人工具最常見的痛點是「要處理一批 URL，卻必須一條條手動執行」。批次模式將工具從「每次一張」變成「一次一批」，直接乘數化現有所有功能的價值，且每個新功能（preset、風格、主題）都能立刻搭配批次受益——複合回報高。

**v2.6 剪貼簿輸出**（次選，可作為 v2.0 之後的快速勝利）可行性最高（macOS 一行 shell 指令即可實作），用戶體驗提升立竿見影：從「產生 → 打開 Finder → 拖拉」縮短為「產生 → 直接貼上」。WOW 因子高但工程成本極低，是兩個大版本之間的理想緩衝功能。

**v1.9 智慧擷取**雖可行性最高（5），但 WOW 因子偏低（3）——它是基礎建設改善，用戶感知為「修好了一個本來就該正確的東西」，而非全新能力。仍應作為 v1.9 優先完成，但不是最令人興奮的 Cycle 亮點。

**v2.2 AI 提示風格**總分 64，排名第三，但策略價值不可低估——它是唯一能影響輸出「靈魂」（文案語調）的功能，差異化潛力強。建議在 v2.0 批次模式穩定後列為下一個 M 複雜度版本目標。
