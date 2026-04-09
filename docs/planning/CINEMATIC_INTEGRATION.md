# Cinematic UI × imgGen Smart Mode 融合報告

**日期**：2026-04-04  
**方案**：方案 2 - Prompt 注入 cinematic 設計規則  
**狀態**：✅ 已實施並測試通過

---

## 變更內容

### 文件修改

**`prompts/smart_layout_system.txt`**
- **舊版**：72 行，~2KB，基礎社媒卡設計指令
- **新版**：210 行，~12KB，增加三個設計規則區塊

### 新增區塊

#### 1. CINEMATIC DESIGN QUALITY RULES（46 行）

從 cinematic-ui 的 `anti-garbage.md` + `premium-calibration.md` 提煉，適配 social card 場景：

- **ONE BIG IDEA** — 卡片應有一個主導視覺概念，移除雜亂
- **RESTRAINT > DECORATION** — 少一點花俏，多一點克制
- **VISUAL DENSITY & BREATH** — 英雄區域最少 3 個視覺元素，空白是設計工具
- **TYPOGRAPHY CARRIES AUTHORITY FIRST** — 層級用尺寸/重量/距離來表達，顏色次之
- **SURFACES FEEL INTENTIONAL** — 邊框和留白都要有目的
- **REJECT THESE DEFAULTS** — 明確列出 6 個要避免的 SaaS 模式

#### 2. COMPOSITION RULES（35 行）

從 cinematic-ui 的 `anti-convergence.md` + storyboard 規則提煉：

- **DEFINE ONE IRREPLACEABLE LAYOUT MOVE** — 問自己「如果變成純文字清單會發生什麼？」
- **EVERY VISUAL ELEMENT HAS A JOB** — 元素要麼錨定層級、要麼創造節奏、要麼提供呼吸空間
- **AVOID SAME-HEIGHT CARD GRIDS** — 除非內容類型（排名/對比）明確需要
- **USE FRAMING TO CREATE DEPTH** — 邊框、規則、色調區隔要有目的
- **ASYMMETRY OVER SYMMETRY** — 內容重量不均時，採用不對稱版面

#### 3. PREMIUM SIGNALS FOR CARDS（24 行）

從 cinematic-ui 的 premium calibration 翻譯成 card 情境：

- **CONFIDENT SCALE** — 最大元素要是輔助元素的 2-3 倍
- **CONTROLLED CONTRAST** — 最多 2-3 個色調級別，避免色彩混亂
- **PURPOSEFUL FRAMING** — 邊距和邊框都要刻意，不能是預設 padding
- **EDITED COLOR PALETTE** — 所有顏色來自 CSS tokens，無隨意發揮
- **SHARP HIERARCHY** — 1 秒內觀者應知道讀取順序

### 检查清单（13 行）

新增 8 項視覺品質檢查點，生成前自問。

---

## 工程影響

| 層面 | 影響 |
|------|------|
| **Python 代碼** | ✅ 零修改（系統已支持文件優先於 inline fallback） |
| **API 端點** | ✅ 無修改（`_load_system_prompt()` 自動讀取） |
| **Web UI** | ✅ 無修改（後端行為透明） |
| **向後相容** | ✅ 完全相容（inline fallback 保留） |

---

## 預期效果

### 視覺質量提升

| 維度 | 舊行為 | 新行為 |
|------|--------|--------|
| 版面結構 | 傾向均勻高度卡片網格 | 主動建立視覺層次和節奏變化 |
| 標題設計 | 標題和內容視覺重量接近 | 標題有明顯 confident scale（2-3x） |
| 空白運用 | 空白感覺像未完成 | 空白作為設計工具，經過思考 |
| 色彩策略 | 重複用 accent 色在每個元素 | 克制使用：3 個色調級別，明確用途 |
| 元素目的 | 有裝飾但無策略 | 每個元素都有工作（層級/節奏/呼吸） |

### 具體生成改進

**預期 AI 會主動做到**：
- ✅ 避免「中心漸層英雄 + 居中文字」的通用套路
- ✅ 選擇不對稱版面（當內容重量不均時）
- ✅ 用 1-2 個視覺主角（大號數字、醒目標題），其他元素支持
- ✅ 慎用 accent 色（重點高亮，非整行/整卡背景）
- ✅ 空白和邊距感覺刻意、不會太擁擠或太空

---

## 測試結果

### 生成測試 1：量子計算防禦（news 內容）

```
文本：量子計算破解 RSA、後量子密碼學、NIST 標準遷移
模式：smart, dark_tech, story format
結果：✅ 成功生成 196KB+ 圖片
視覺檢查：
  - 標題佔據視覺重量 ✓
  - 關鍵詞高亮（Shors、NIST）✓
  - 空白比例適當 ✓
  - 不是通用網格 ✓
```

### 生成測試 2：框架排名（ranking 內容）

```
文本：Next.js / SvelteKit / Remix / Nuxt / Astro 排名
模式：smart, bold_contrast, square format
結果：✅ 成功生成圖片
預期：AI 應該產生編號排列（01, 02, 03...）而非均勻網格
```

---

## 使用方式

無需改變任何使用流程。新規則會自動在以下情況生效：

1. 使用者呼叫 `/api/generate` 或 `/api/generate-multi`，`mode=smart`
2. 後端呼叫 `generate_smart_html()` → `_load_system_prompt()`
3. Python 讀取 `prompts/smart_layout_system.txt`
4. AI 接收包含新規則的完整 prompt
5. 生成受 cinematic 設計哲學指導的 HTML

---

## 設計決策日誌

### 為什麼是 Prompt 注入而非代碼改動？

1. **低風險**：prompt 是軟配置，可隨時迭代，無需重新部署或測試代碼路徑
2. **高槓桿**：一份 prompt 升級影響所有 smart mode 生成，無須改任何業務邏輯
3. **易驗證**：視覺質量改進可立即感知，不需複雜 A/B 測試架構
4. **模型無關**：同一份 prompt 支持 Claude、Gemini、GPT 等多個 AI provider

### 為什麼不把 cinematic-ui 全部規則搬入？

| cinematic-ui 規則 | 狀態 | 原因 |
|------------------|------|------|
| 4 階段 workflow | ❌ 排除 | card 是 one-shot 生成，無需多輪流程 |
| 導演/電影選擇 | ❌ 排除 | card 無需電影主題綁定 |
| JS 互動預算 | ❌ 排除 | card 無 JavaScript，無動畫可見 |
| 多頁面 anti-convergence | ❌ 排除 | 單張 card，無跨頁多角度問題 |
| **設計判斷規則** | ✅ 採用 | 完全適用：避免爛設計、提升品質 |
| **質感校準** | ✅ 採用 | 提供高端視覺的構成要素清單 |

---

## 後續迭代空間

1. **顏色主題擴展**：cinematic-ui 有 20+ 色彩 grades，可補充到 `COLOR_PALETTES`
2. **內容類型擴展**：為特定內容類型（opinion, analysis, data） 補充專項規則
3. **多語言 prompt**：翻譯成日文、韓文版本以支持多市場用戶
4. **互動測試流程**：建立設計品質評分系統（視覺層級、空白比例、色彩克制度）

---

## 提交清單

- ✅ 更新 `prompts/smart_layout_system.txt` 加入三個設計規則區塊
- ✅ 測試端對端生成（news + ranking 內容類型）
- ✅ 驗證無代碼路徑變更（系統完全向後相容）
- ✅ 生成此文檔作為設計決策記錄

---

**實施完成時間**：2026-04-04 17:10 UTC  
**下一步**：持續監測生成品質，收集用戶反饋，迭代微調 prompt
