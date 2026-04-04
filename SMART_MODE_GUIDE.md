# Smart Mode 使用指南

## 概述

Smart Mode 是 imgGen 的最新功能，使用 AI（Claude Sonnet/Opus）為每個內容動態生成獨特的 HTML+CSS 佈局，而不是使用預定義的模板。

每個輸出就像一個精心設計的 PPT 幻燈片，根據內容類型和情緒自動優化設計。

---

## 快速開始

### 1. 設置環境變數

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. 使用 Smart Mode

```bash
# 使用 Sonnet 模型（默認，性能好、成本低）
python main.py --file article.txt --mode smart --format story

# 使用 Opus 模型（更深度的推理，設計質量更高）
python main.py --text "內容..." --mode smart --format square --model opus

# 多格式輸出
python main.py --url https://example.com --mode smart --formats story,square,twitter
```

---

## 命令行選項

### `--mode smart`
啟用 Smart Mode（AI 驅動的動態佈局）。

### `--model <sonnet|opus>`
選擇 Claude 模型變體（僅用於 Smart Mode）：
- **`sonnet`** (默認) — 最佳平衡，快速且成本低
- **`opus`** — 更深度的推理，設計質量更高

### `--format <story|square|landscape|twitter>`
選擇輸出格式：
- `story` (430×764px) — Instagram Story / TikTok
- `square` (430×430px) — 社交媒體信息流
- `landscape` (430×242px) — Web / Email 標題
- `twitter` (430×215px) — Twitter 卡片

### `--provider <claude|gemini|gpt|cli>`
AI 提供商（默認 `cli`）：
- `claude` — 使用 Anthropic API（推薦用於 Smart Mode）
- `gemini` — Google Gemini API
- `gpt` — OpenAI GPT API
- `cli` — Claude CLI（本地）

---

## 工作流程

### 提取 → 渲染 → 截圖

```
1. 提取階段 (extraction)
   - AI 分析內容
   - 輸出結構化數據：標題、要點、內容類型、佈局提示、顏色心情

2. 設計系統階段 (design system)
   - CSS 變數注入：字體大小、顏色調色板、動畫
   - 共享基礎 CSS（所有 Smart Mode 輸出都使用）

3. 佈局生成階段 (layout generation)
   - Claude 根據提示生成完整 HTML+CSS
   - AI 自動選擇最優佈局模式和顏色組合

4. 截圖階段 (screenshot)
   - Playwright 將 HTML 截圖為 PNG/WebP
   - 注入浮水印和線程標籤
```

---

## 提取輸出格式（Smart Mode）

```json
{
  "title": "簡潔的標題",
  "key_points": [
    {"text": "最重要的要點", "importance": 1.0},
    {"text": "次要要點", "importance": 0.9},
    {"text": "支持要點", "importance": 0.7}
  ],
  "content_type": "news",
  "layout_hint": "hero_list",
  "color_mood": "dark_tech",
  "source": "來源信息"
}
```

### 字段說明

| 字段 | 值 | 說明 |
|------|-----|------|
| `content_type` | news, opinion, howto, data, comparison, quote, timeline, ranking | 內容分類 |
| `layout_hint` | hero_list, grid, timeline, comparison, quote_centered, data_dashboard, numbered_ranking | 建議的佈局模式 |
| `color_mood` | dark_tech, warm_earth, clean_light, bold_contrast, soft_pastel | 顏色和情緒 |
| `importance` | 0.0–1.0 | 要點的視覺優先級（影響大小和位置） |

---

## 設計系統

### 色彩調色板（5 個選項）

#### 1. **dark_tech**（科技深藍）
```css
--bg: #090d1a;
--accent: #2563eb;
--text-primary: #dde2f0;
--text-secondary: #8a90aa;
```
✓ 科技、商業、分析類內容
✓ 現代感強、專業

#### 2. **warm_earth**（溫暖大地）
```css
--bg: #EAE5DE;
--accent: #6B5A4E;
--text-primary: #2C2420;
```
✓ 生活、健康、設計類內容
✓ 有機感、親切

#### 3. **clean_light**（清爽明亮）
```css
--bg: #f8f7f4;
--accent: #0284c7;
--text-primary: #1c1917;
```
✓ 編輯、文化、新聞類
✓ 簡潔、易讀

#### 4. **bold_contrast**（大膽對比）
```css
--bg: #F6F4F0;
--accent: #C4540A;
--text-primary: #1E1C18;
```
✓ 營銷、創意、廣告
✓ 高衝擊力

#### 5. **soft_pastel**（柔和粉彩）
```css
--bg: #FDF0F4;
--accent: #C25A7A;
--text-primary: #2E1F28;
```
✓ 女性向、品牌故事、正能量
✓ 溫柔、精緻

### 字型

- **拉丁字** → `Outfit` (無襯線、現代)
- **中文** → `Noto Sans TC` (清晰、友好)

### 響應式排版

```css
--fs-title: clamp(22px, 6vw, 32px);      /* 標題：自適應 */
--fs-subtitle: clamp(16px, 4vw, 20px);   /* 副標題 */
--fs-body: 16px;                         /* 正文 */
--fs-secondary: 14px;                    /* 次要文本 */
--fs-label: 11px;                        /* 標籤 */
```

### 動畫

```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
/* 應用於內容元素：.animated class with --i CSS 變數 */
```

---

## 佈局模式（7 種）

### 1. **hero_list** — 英雄列表
```
┌─────────────────┐
│   HERO SECTION  │  ← 最重要的要點（大字體、強調）
├─────────────────┤
│ 1. 次要要點     │
│ 2. 支持要點     │
│ 3. 補充信息     │
└─────────────────┘
```
✓ 新聞、重點總結、排名榜單

### 2. **grid** — 網格佈局
```
┌──────┬──────┐
│ Card │ Card │
├──────┼──────┤
│ Card │ Card │
└──────┴──────┘
```
✓ 並行項目、特點列表、團隊成員

### 3. **timeline** — 時間軸
```
  ◯ 第一步
  ◯ 第二步
  ◯ 第三步
```
✓ 流程、演化、步驟

### 4. **comparison** — 對比
```
┌──────────┬──────────┐
│  Before  │  After   │
│    A     │    B     │
└──────────┴──────────┘
```
✓ 對比分析、優缺點、新舊對照

### 5. **quote_centered** — 居中引言
```
      " 核心引言 "

      —— 出處信息
```
✓ 名言、觀點、評論

### 6. **data_dashboard** — 數據儀表板
```
┌────────┐ ┌────────┐
│ 12.5M  │ │  98%   │
│ users  │ │success │
└────────┘ └────────┘
```
✓ 統計數據、指標、數字

### 7. **numbered_ranking** — 排名列表
```
01  第一名 ⭐ 最強調
02  第二名
03  第三名
```
✓ Top-N 榜單、排名、評分

---

## 實際示例

### 例子 1：新聞文章（dark_tech + hero_list）

**命令：**
```bash
python main.py --url https://news.example.com/article \
  --mode smart --format story --provider claude
```

**提取輸出：**
```json
{
  "title": "AI 突破邊界",
  "key_points": [
    {"text": "新模型超越人類基準", "importance": 1.0},
    {"text": "推理速度提升 5 倍", "importance": 0.8}
  ],
  "content_type": "news",
  "layout_hint": "hero_list",
  "color_mood": "dark_tech"
}
```

**生成結果：**深藍背景、英雄區域展示核心突破、下方列表支持要點。

### 例子 2：品牌故事（soft_pastel + quote_centered）

**命令：**
```bash
python main.py --text "我們的使命是..." \
  --mode smart --format square --model opus
```

**設計風格：**柔和粉彩、居中布局、簡潔優雅。

---

## Sonnet vs Opus 對比

| 維度 | Sonnet 4.6 | Opus 4.6 |
|------|-----------|---------|
| **速度** | ⚡⚡⚡ 快速 | ⚡ 中等 |
| **設計質量** | ⭐⭐⭐⭐ 優秀 | ⭐⭐⭐⭐⭐ 完美 |
| **成本** | 💰 低 | 💰💰 較高 |
| **推理深度** | 中等 | 深度 |
| **最佳用途** | 日常使用、快速迭代 | 關鍵內容、特殊設計 |

**建議：**
- 開發/測試 → **Sonnet**（成本低、速度快）
- 生產發布 → **Sonnet**（足夠優秀）
- 特殊設計 → **Opus**（更精細的設計細節）

---

## 故障排除

### 問題 1：生成失敗，自動回退到模板

**原因：** AI 輸出格式無效

**解決方案：**
```bash
# 1. 確保有 API key
echo $ANTHROPIC_API_KEY

# 2. 嘗試用 Opus 模型（推理更深）
python main.py --file article.txt --mode smart --model opus

# 3. 檢查網絡連接
```

### 問題 2：HTML 包含 JavaScript 或外部圖片

**原因：** AI 違反了安全規則

**解決方案：**
- 系統自動拒絕（不會崩潰）
- 自動回退到 Jinja2 模板
- 檢查日誌了解詳情

### 問題 3：文字被縮寫或改變

**原因：** AI 沒有遵守「保留原文」的指示

**解決方案：**
```bash
# 使用 Opus 模型（更遵守指示）
python main.py --text "..." --mode smart --model opus
```

---

## 性能建議

### 並發限制
```bash
# 批量處理時
python main.py --batch urls.txt --workers 3
```

### 成本估算（使用 Claude API）

**Sonnet 模型：**
- 輸入：~$0.003 / 1K tokens
- 輸出：~$0.015 / 1K tokens
- 平均每張卡片：$0.05–0.10

**Opus 模型：**
- 輸入：~$0.015 / 1K tokens
- 輸出：~$0.075 / 1K tokens
- 平均每張卡片：$0.20–0.40

---

## 進階使用

### 多格式並發生成
```bash
python main.py --file article.txt --mode smart \
  --formats story,square,twitter,landscape
```

### 線程模式（每個要點一張卡片）
```bash
python main.py --file article.txt --mode smart --thread
```
生成 4 張卡片（假設 4 個要點），自動標號 1/4, 2/4, 3/4, 4/4

### 配置文件預設
```toml
# ~/.imggenrc
[smart_mode]
model = "opus"           # 默認用 Opus
format = "story"
provider = "claude"
```

```bash
python main.py --file article.txt --mode smart
# 自動使用 opus + story + claude
```

---

## 常見問題

**Q: Smart Mode 和 Card Mode 有什麼區別？**

A:
- **Card Mode** — 預定義的 28 個模板，固定設計
- **Smart Mode** — AI 為每個內容動態生成獨特設計

**Q: 可以混合使用 Sonnet 和 Opus 嗎？**

A: 可以，為不同內容選擇不同模型：
```bash
python main.py --text "快速內容" --mode smart --model sonnet
python main.py --text "重要內容" --mode smart --model opus
```

**Q: 色彩調色板可以自訂嗎？**

A: 目前不支持，但 AI 會根據 `color_mood` 選擇最佳調色板。

**Q: 生成的 HTML 可以修改嗎？**

A: 可以，截圖前生成的 HTML 已保存在內存中，可以通過擴展代碼來修改。

---

## 最佳實踐

✓ **使用 Claude API** 而不是 CLI（更快、更可靠）

✓ **為不同內容選擇合適的顏色** 基於情感和類型

✓ **線程模式用於長篇內容** 多要點分解為多張卡片

✓ **Sonnet 用於日常** Opus 用於關鍵發布

✓ **監控成本** 大規模批處理時追蹤 API 使用量

---

## 技術細節

### 設計系統 CSS 大小
- 基礎設計系統：~2KB
- 彩色調色板：~500 bytes 每個
- 動畫和響應式：~1KB

### HTML 驗證
- 最大大小：50 KB（防止過大的生成）
- 禁止：`<script>` 標籤、外部圖片、不安全的內容
- 保證：完全自包含、可離線渲染

### 重試機制
- 首次失敗 → 自動重試帶更嚴格指示
- 二次失敗 → 回退到 Jinja2 模板
- 不會拋出錯誤，提供優雅降級

---

## 更新和反饋

如有問題或建議，請參閱：
- 代碼：`/src/smart_renderer.py`
- 配置：`/src/pipeline.py`
- 命令行：`/main.py --help`

祝使用愉快！🚀
