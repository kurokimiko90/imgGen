# PRD: imgGen — 文章轉圖卡工具
**Status**: Approved
**Author**: Alex (PM)
**Last Updated**: 2026-03-29
**Version**: 6.1

---

## 1. 產品願景

imgGen 是一個專為**個人使用**設計的**零設計介入內容自動化引擎**，服務對象是獨立工作者或一人公司經營者。
核心價值主張：**從內容源到社交平台，全程自動，人只做最後微調。**

這個工具不是 Canva，不是設計編輯器，不是 SaaS。它是個人內容管線——像是 `ffmpeg` 之於影音處理，imgGen 之於內容圖卡的自動化生產。支援 CLI 和 Web UI 兩種介面，護城河在於「內容接入 → AI 處理 → 多形態輸出 → 自動分發 → 效果回饋」的完整管道。

---

## 2. 問題陳述

### 痛點

社群媒體上的純文字貼文缺乏視覺吸引力，閱讀者的注意力正在縮短。一人公司的內容創作者每天閱讀大量文章，希望把這些閱讀心得或精華轉化成視覺內容分享出去，但：

- 手動用 Canva / Figma 製作圖卡，每張要花 10–20 分鐘
- 要整理重點再排版，過程繁瑣、有摩擦
- 沒有 API 的自動化能力，無法嵌入個人工作流

### 使用者

**單一使用者：獨立工作者 / 一人公司經營者**

- 日常閱讀大量英文或中文文章（科技、商業、文化類）
- 有社群媒體發布習慣（Twitter/X、LinkedIn、Instagram）
- 熟悉 CLI 工具，有技術背景
- 重視效率，不想為輸出圖卡而切換應用程式
- 已擁有 Anthropic / Google / OpenAI API 金鑰

### 不解決此問題的代價

繼續用手工方式製作圖卡，每週花費 1–3 小時在重複性排版工作上，或乾脆放棄圖卡內容，損失社群觸及率。

---

## 3. 目標與成功指標

這是個人工具，不追蹤 MAU 或 MRR。成功的定義是：使用者自己覺得這工具省了時間、輸出的圖好看到可以直接發。

| 目標 | 衡量方式 | 基準（v4.5） | 目標 |
|------|----------|-------------|------|
| 端到端流暢執行 | 成功率（無 exception） | 待測 | 95%+ |
| 生成速度（單張） | 平均每張秒數（含 API 呼叫） | 待測 | < 30 秒 |
| 批次吞吐量 | 10 篇文章總耗時 | 待測 | < 60 秒（3 workers） |
| 輸出品質 | 使用者主觀評分（自評） | — | 可直接發布 |
| 格式覆蓋率 | 支援的社群格式數量 | 4 種 | 所有主流平台 |
| 主題多樣性 | 可選視覺主題數量 | **31 種 + article 模板** | 涵蓋 19 種內容類型 + article 條理化模式 |
| 內容類型覆蓋率 | 支援的社群圖文內容類型數 | **19 / 23 種** | 排名、蛻變對比、概念解釋、精選推薦、觀點、清單、FAQ、里程碑等 |
| 設計系統一致性 | 所有主題共享相同字體比例與動畫規格 | **已實現** | 零碎片化 |
| 工作流效率 | 常用參數組合一鍵套用（preset） | 支援 | 零重複輸入常用旗標 |
| 內容運營覆蓋 | 從輸入到發布的管線完整度 | **已實現** | 抓取→摘要→圖卡→文案→發布 |
| 歷史可追溯性 | 歷史紀錄與統計 | **已實現** | 所有生成紀錄可查詢、可視覺化 |
| 文章提取品質 | trafilatura vs regex 成功率 | **trafilatura** | 乾淨主文提取，無導航 / 廣告噪音 |
| 多語言支援 | ExtractionConfig 語言選項 | **5 語言** | zh-TW, zh-CN, en, ja, ko |
| 介面覆蓋率 | CLI + Web UI 功能對等程度 | **Web UI 已上線** | 雙介面可用 |

---

## 4. 目標使用者 Persona

**使用者：自己（一人公司）**

- 每天看 5–15 篇文章
- 想把精華文章轉成圖卡，發布到 Twitter/X 或 LinkedIn
- 有時希望批次處理一週內收藏的文章
- 習慣在 terminal 工作，對 Python、CLI 工具不陌生；也使用 Web UI 進行視覺化操作
- 使用 macOS，偶爾也在 Linux 環境執行

---

## 5. 核心使用場景

### 場景 A：單篇文章快速圖卡化
讀完一篇文章後，複製 URL 或文字，執行一行指令，30 秒內拿到 PNG，直接上傳。

```bash
python main.py --url https://example.com/article --theme gradient
```

### 場景 B：本地文章檔案轉換
有一份存好的 .txt 筆記或剪報，想快速視覺化。

```bash
python main.py --file notes/article.txt --theme dark --output weekly_digest.png
```

### 場景 C：測試不同 AI 提供者
想比較 Claude 和 Gemini 的摘要品質，或 API 費用。

```bash
python main.py --text "..." --provider gemini --theme light
```

### 場景 D：嵌入個人自動化腳本
把 imgGen 的 stdout（輸出路徑）接給 shell script，自動上傳到 Buffer 或存進 Notion。

```bash
OUTPUT=$(python main.py --url $URL)
echo "Generated: $OUTPUT"
```

### 場景 E：正方形 PPT / 簡報圖卡（v3.0 新增）
製作適合簡報或 Threads 使用的方形溫馨風格圖卡。

```bash
python main.py --url https://example.com --theme cozy --format square
python main.py --url https://example.com --theme warm_sun --format square
```

### 場景 F：一次生成多格式圖卡（v4.0 新增）
一篇文章同時輸出 story、square、twitter 三種尺寸，只做一次 AI 呼叫。

```bash
python main.py --url $URL --formats story,square,twitter
```

### 場景 G：生成圖卡並複製到剪貼簿（v4.0 新增）
生成後直接貼到 Slack、Notion 或郵件。

```bash
python main.py --url $URL --clipboard
```

### 場景 H：一篇文章拆成 Thread 連續卡（v4.0 新增）
每個重點獨立一張卡，帶 1/5、2/5 編號，適合 Twitter thread 或 IG 輪播。

```bash
python main.py --url $URL --thread --format twitter
```

### 場景 I：生成圖卡 + 社群文案（v4.0 新增）
圖卡與 Twitter/LinkedIn 文案同步輸出，免去手寫貼文的摩擦。

```bash
python main.py --url $URL --caption twitter,linkedin
```

### 場景 J：一鍵發推（v4.0 新增）
生成圖卡 + 文案，直接發布到 Twitter/X。

```bash
python main.py --url $URL --post twitter --caption twitter
```

### 場景 K：查閱歷史紀錄與統計（v4.0 新增）
回顧過去一週生成了什麼、用了哪些主題，或生成一張統計圖卡。

```bash
imggen history list --days 7
imggen history search "AI"
imggen history stats --visual
```

### 場景 L：每週內容彙整（v4.0 新增）
將過去 7 天的生成紀錄交給 AI 合成一張週報圖卡。

```bash
imggen digest --days 7 --theme gradient
```

### 場景 M：資料夾監控自動生成（v4.0 新增）
丟檔案到指定資料夾，自動觸發圖卡生成，適合結合 RSS 或自動化腳本。

```bash
imggen watch ~/articles/ --theme dark --format story
```

### 場景 N：Web UI 生成卡片（v4.5 新增）
在瀏覽器中操作圖卡生成，可視化預覽、調整提取設定、瀏覽歷史紀錄。

1. 打開 Web UI（`http://localhost:8000`）
2. 輸入文章文字或 URL
3. 展開 Advanced Options → Extraction Settings，調整語言、語氣、重點數量
4. 點擊 Generate，即時預覽圖卡
5. 下載 PNG 或導出 HTML

### 場景 O：多語言 / 自定義提取（v4.5 新增）
針對不同受眾調整 AI 摘要的語言、語氣和字數限制。

```bash
# CLI（透過 Web UI 的 Extraction Settings 面板操作更直覺）
# Web UI: Advanced Options → Language: English, Tone: Casual, Max Points: 4
```

### 場景 P：導出 HTML 嵌入 Newsletter（v4.5 新增）
將已生成的圖卡以 HTML 格式下載，嵌入 blog 或 newsletter。

```
# Web UI: 生成圖卡後 → 點擊 </> 按鈕 → 下載 imggen_{id}.html
# API:  GET /api/export/html/{gen_id}
```

### 場景 Q：文章精簡條理化輸出（v6.1 新增）
將一篇筆記或文章精簡為結構化的學習心得圖卡，以段落式排版取代條列要點，適合知識整理和閱讀筆記。

```bash
python main.py --file notes/tmux_habits.md --mode article --theme light
python main.py --url $URL --mode article --theme dark --watermark logo.svg
```

---

## 6. 已實現功能 (Implemented Features)

### v1.0 基準功能

#### CLI 介面
- `--text / -t`: 直接輸入文字
- `--file / -f`: 讀取本地文字檔
- `--url / -u`: 抓取網址並解析 HTML
- `--theme`: 選擇視覺主題（dark / light / gradient）
- `--provider / -p`: 選擇 AI 提供者（claude / gemini / gpt / cli）
- `--output / -o`: 指定輸出檔名

#### AI 提供者
- **Claude API**: Anthropic claude-sonnet-4-6，使用 ANTHROPIC_API_KEY
- **Gemini API**: Google gemini-2.0-flash，使用 GOOGLE_API_KEY
- **OpenAI GPT**: gpt-4o-mini，使用 OPENAI_API_KEY
- **Claude CLI**: 呼叫本機 claude binary，不需 API key

#### 輸出格式
- 3 個視覺主題的 Jinja2 HTML 模板（dark, light, gradient）
- Playwright 截圖輸出 PNG
- 自動時間戳命名：`output/card_{theme}_{timestamp}.png`

#### AI 摘要結構（v1.0）
- `title`：15 字以內的核心標題
- `key_points`：3–5 個帶 emoji 的重點（每點 30–50 字）
- `source`：來源資訊
- `theme_suggestion`：AI 建議的主題色（dark / light / gradient）

---

### v1.5 多社群格式輸出（已實現）

#### 新增 CLI 選項
- `--format`: 指定輸出尺寸格式
  - `story`：限時動態格式（9:16 直向）
  - `square`：方形貼文格式（1:1）
  - `landscape`：橫向寬版格式（16:9）
  - `twitter`：Twitter/X 貼文格式
- `--scale`: 輸出解析度倍數
  - `1`：標準解析度（1x）
  - `2`：高解析度（2x，Retina 適用）
- `--webp`: 輸出 WebP 格式（預設仍為 PNG）

---

### v1.6 Config File 支援（已實現）

#### 新增 CLI 選項
- `--config PATH`: 指定自訂設定檔路徑

#### 設定檔機制
- 格式：TOML（`~/.imggenrc`）
- 優先順序（高到低）：
  1. CLI 參數（最高優先）
  2. 當前目錄的 `.imggenrc`
  3. 家目錄的 `~/.imggenrc`
  4. 程式內建預設值（最低優先）

---

### v1.8 浮水印與個人品牌（已實現）

#### 新增 CLI 選項
- `--watermark PATH`: 指定浮水印圖片路徑（PNG / SVG）
- `--watermark-position`: 浮水印位置
  - `bottom-right`（預設）
  - `bottom-left`
  - `top-right`
  - `top-left`
- `--watermark-opacity`: 浮水印不透明度（0.0–1.0，預設 0.3）
- `--brand-name TEXT`: 品牌名稱文字，顯示於圖卡角落（與 `--watermark` 二擇一或並用）

#### 設定檔新增 Config Keys
在 `~/.imggenrc`（TOML）中可設定以下鍵值：
```toml
watermark = "~/assets/logo.png"
watermark_position = "bottom-right"
watermark_opacity = 0.3
brand_name = "你的品牌名稱"
```

---

### v2.0 批次處理（已實現）

#### 新增 CLI 選項
- `--batch FILE`: 指定批次清單檔案（每行一筆 URL 或本地檔案路徑）
- `--workers N`: 並發工作數（預設 3）
- `--output-dir DIR`: 指定批次輸出目錄

#### 批次處理機制
- 讀取 `--batch` 指定的清單檔，逐行解析 URL 或本地路徑
- 以 `asyncio.Semaphore` 控制並發上限，預設同時最多 3 個任務
- 所有任務完成後，於 `--output-dir` 目錄下生成 `batch_report.json`，紀錄每筆輸入的處理結果（成功路徑 / 錯誤訊息）

---

### v2.4 Preset System 預設參數組合（已實現）

#### 新增 CLI 選項
- `--preset NAME`: 套用已儲存的預設值（CLI 旗標可覆蓋預設中的值）

#### 優先順序（高到低）
1. CLI 參數（最高優先）
2. `--preset` 指定的預設值
3. `~/.imggenrc` [defaults] 段落
4. 程式內建預設值

#### preset 子命令群組
```bash
imggen preset save <名稱> [options]   # 儲存當前參數為預設
imggen preset load <名稱>              # 輸出預設參數（stdout）
imggen preset list                     # 列出所有預設
imggen preset delete <名稱>            # 刪除指定預設
```

#### 設定檔格式（TOML）
```toml
[preset.weekly-ig]
theme = "gradient"
format = "story"
provider = "claude"
brand_name = "我的品牌"
scale = 2
webp = true
```

---

### v2.5 版面系統統一（已實現）

統一 `light` 和 `gradient` 主題採用與 `dark` 相同的 Viewport 與字體比例，消除舊有的固定像素方案。

#### 變更內容

**Viewport 方案**（`light`, `gradient`）
- 舊：`<meta name="viewport" content="width=1080" />`、CSS `width: 1080px; height: 1920px`
- 新：`<meta name="viewport" content="width=430" />`、CSS `max-width: 430px; min-height: 100vh`

**字體比例統一**（`light`, `gradient`，與 `dark` 對齊）

| 元素 | 舊值 | 新值 |
|------|------|------|
| `--fs-title` | `32px` | `clamp(26px, 7vw, 34px)` |
| `--fs-body` | `15px` | `18px` |
| `--fs-label` | `11px` | `12px` |
| `--fs-secondary` | — | `16px`（新增） |
| `--circle-size` | `20px` | `22px` |

**Footer 重構**（`light`, `gradient`）
- 移除 `padding-right: 160px` 的 absolute 定位 hack
- Nozomi badge 改為 footer flex row 右側 inline 元素

---

### v2.6 新主題：warm_sun & cozy（已實現）

新增 2 個針對**正方形（1:1）**格式優化的溫馨風格主題，適用於 PPT 簡報插圖、Threads 方形貼文。

#### 主題規格

| 主題 | 風格定義 | 背景 | 字體（標題）| 要點樣式 |
|------|---------|------|------------|---------|
| `warm_sun` | 橙金暖陽、活潑正能量 | 橙→米白 radial gradient | Outfit（Sans） | 卡片 + 橙色左邊框 |
| `cozy` | 奶茶棕米白、溫潤質感 | 米白 `#fdf8f0` + 斜線紙紋 | Noto Serif TC | 行列 + 橫線分隔 |

#### 新增 `--theme` 選項
```bash
--theme warm_sun   # 暖陽系（方形最佳）
--theme cozy       # 奶茶系（方形最佳）
```

#### 技術細節
- 兩者均採用 `max-width: 430px; min-height: 100vh` 版面
- `warm_sun` 的太陽圖示使用純 SVG path（8 條射線），無 emoji
- 已加入 `src/renderer.py` 的 `VALID_THEMES`

---

### v3.0 Taste-Skill 設計系統優化（已實現）

以 `taste-skill`（DESIGN_VARIANCE: 8 / MOTION_INTENSITY: 6 / VISUAL_DENSITY: 4）對全項目執行設計審查，消除所有 AI 設計反模式。

#### 字體系統（全 5 個主題）

| 舊字體 | 新字體 | 原因 |
|--------|--------|------|
| `Inter` | `Outfit` | Inter 在 taste-skill 中被明確禁止（AI 設計 cliché） |

`Noto Serif TC` 保留用於 `light`（標題）和 `cozy`（標題），符合 editorial 例外規則。

#### 色彩系統修正

**dark 主題 — THE LILA BAN**

| 項目 | 舊值 | 新值 |
|------|------|------|
| `--accent` | `#7B6CF6`（AI Purple）| `#2563eb`（Electric Blue）|
| `--accent-dim` | `rgba(123,108,246,0.18)` | `rgba(37,99,235,0.18)` |
| 背景 radial | `#16103a`（深紫）| `#0f1f4a`（深海軍藍）|
| powered-pill 顏色 | `#6a5fd4` | `#3b6fd4` |

**gradient 主題 — LILA BAN 全面清除**

| 項目 | 舊值 | 新值 |
|------|------|------|
| 背景漸層 | `#3b0764 → #4c1d95 → #3730a3`（全紫）| `#071a20 → #0d2b35 → #0f3349`（深海藍青）|
| `--accent-bright` | `#e879f9`（霓虹紫）| `#06b6d4`（Cyan 500）|
| `--accent-warm` | `#f0abfc`（淺紫）| `#67e8f9`（Cyan 300）|
| bg-mesh 顏色 | `rgba(192,38,211,...)`（紫色光暈）| `rgba(6,182,212,...)`（青色光暈）|

#### Liquid Glass 修正（gradient 主題）

舊版只用 `backdrop-filter: blur()`，缺少物理折射感。

新增至所有 glass card、brand-pill、header-chip、stat-box：
```css
border: 1px solid rgba(255,255,255,0.16);
box-shadow: inset 0 1px 0 rgba(255,255,255,0.08);
```

#### Motion 系統（全 5 個主題）

MOTION_INTENSITY: 6 要求 CSS 流暢動畫。新增 staggered 要點出現動畫：

```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 每個要點透過 Jinja2 注入 --i 變數驅動 delay */
.point-card {
  animation: fadeUp 0.32s cubic-bezier(0.16,1,0.3,1) calc(var(--i) * 0.08s) both;
  will-change: transform;
}
```

```html
<!-- Jinja2 模板 -->
<div class="point-card" style="--i: {{ loop.index }};">
```

#### 陰影色調修正（全主題）

所有 card shadow 由純黑改為對應主題色調：

| 主題 | 舊 shadow | 新 shadow |
|------|-----------|-----------|
| light | `rgba(0,0,0,0.08)` | `rgba(2,132,199,0.08)`（藍調）|
| warm_sun | `rgba(0,0,0,0.08)` | `rgba(249,115,22,0.10)`（橙調）|

#### ANTI-EMOJI POLICY — 提取器層面修正

`src/extractor.py` 系統提示詞中原本強制要求 AI 輸出 emoji，但所有模板均未渲染 `point.emoji` 欄位。

**變更內容：**

| 項目 | 舊值 | 新值 |
|------|------|------|
| JSON schema | `{"emoji": "...", "text": "..."}` | `{"text": "..."}` |
| 系統提示規則 | `每個重點的 emoji 必須與內容高度相關` | 已移除 |
| CLI prompt schema | `{{"emoji":"emoji","text":"..."}}` | `{{"text":"..."}}` |
| `_validate_extracted_data` | `"emoji" not in point or "text" not in point` | `"text" not in point` |

#### 主題覆蓋範圍擴充（`src/extractor.py`）

```python
# 舊
valid_themes = {"dark", "light", "gradient"}
# theme_suggestion 指引：科技/商業→dark，生活/文化→light，創意/娛樂→gradient

# 新
valid_themes = {"dark", "light", "gradient", "warm_sun", "cozy"}
# 科技商業→dark，財經分析→gradient，生活文化→light，溫馨日常→cozy，創意娛樂→warm_sun
```

#### Screenshotter 動畫時序修正（`src/screenshotter.py`）

```python
# 舊：500ms（5 個要點最後動畫完成時間 720ms > 500ms → 截圖時動畫未完成）
await page.wait_for_timeout(500)

# 新：850ms（覆蓋最多 5 個要點：5×0.08s + 0.32s = 0.72s，加 buffer）
await page.wait_for_timeout(850)
```

#### Design Token 文件化（全 5 個模板）

每個模板 `<style>` 頂部加入共享設計規格 comment header：

```css
/*
 * ── DESIGN TOKENS (taste-skill baseline: DESIGN_VARIANCE=8 / MOTION_INTENSITY=6 / VISUAL_DENSITY=4)
 * Typography scale — shared across all imgGen themes:
 *   --fs-title:     clamp(26px, 7vw, 34px)   Hero headline
 *   --fs-body:      18px                       Primary point text
 *   --fs-secondary: 16px                       Secondary / footer text
 *   --fs-label:     12px                       ALL-CAPS labels, badges
 * Motion: fadeUp 0.32s cubic-bezier(0.16,1,0.3,1) with --i * 0.08s stagger
 * Shadows: always tinted to theme accent color — never pure rgba(0,0,0,...)
 * Liquid glass: border + box-shadow inset 0 1px 0 rgba(255,255,255,0.10)
 */
```

#### `/taste` 指令（Claude Code 自訂命令）

建立全域 slash command `~/.claude/commands/taste.md`。

- **觸發**：在任何項目中輸入 `/taste`
- **執行流程**：讀取 taste-skill → 掃描 templates/ + 相關 Python 檔案 → 修復所有違規 → 生成測試截圖 → 報告變更
- **適用範圍**：HTML/CSS 模板、prompt engineering 中的 emoji 政策、screenshotter 動畫時序

---

### v4.0 內容運營管線擴展（已實現）

將 imgGen 從「單次圖卡生成器」升級為**個人內容運營系統**，補齊輸入端摩擦（手動貼 URL）和輸出端摩擦（手動上傳）兩側的缺口，並加入狀態累積能力（歷史紀錄）。

#### 架構變更：Pipeline 提取

從 `main.py`（656 行）提取核心管線至 `src/pipeline.py`，防止主檔案膨脹超過 800 行，並使所有新功能共用同一個 extract → render → screenshot 流程。

```python
# src/pipeline.py
@dataclass(frozen=True)
class PipelineOptions:
    theme: str = "dark"
    format: str = "story"
    provider: str = "cli"
    scale: int = 2
    webp: bool = False
    watermark_data: str | None = None
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8
    brand_name: str | None = None
    extraction_config: ExtractionConfig | None = None  # v4.5 新增

def extract(article_text, provider, extraction_config) -> dict  # AI 摘要提取
def render_and_capture(data, options, output_path) -> Path      # 渲染 + 截圖
def run_pipeline(article_text, options, output_path) -> tuple[dict, Path]  # 完整管線
```

---

#### Feature 1: `--formats` 多格式一次輸出

一次 AI 呼叫，多個格式同步渲染輸出。

```bash
python main.py --url $URL --formats story,square,twitter
```

- 與 `--format`（單數）互斥
- 輸出檔名含格式後綴：`card_dark_20260328_story.png`
- 所有路徑皆印至 stdout

#### Feature 2: `--clipboard` macOS 剪貼簿

生成後自動將圖片複製到系統剪貼簿。

```bash
python main.py --url $URL --clipboard
```

- 新增模組：`src/clipboard.py`
- 使用 `osascript` 設定剪貼簿為 TIFF picture
- 僅支援 macOS

#### Feature 3: `--caption` 社群文案生成

獨立的 AI 呼叫（不與摘要提取合併），針對不同平台生成文案。

```bash
python main.py --url $URL --caption twitter,linkedin,instagram
python main.py --url $URL --caption all
```

- 新增模組：`src/caption.py`
- 平台規則：

| 平台 | 字數上限 | 風格 |
|------|---------|------|
| `twitter` | 280 | 精簡有力，附 2–3 個 hashtag |
| `linkedin` | 3000 | 思想領袖語調，結尾提問 |
| `instagram` | 2200 | 故事感，底部 8–12 個 hashtag |

- 文案存為 `.captions.txt`，與圖片同目錄

#### Feature 4: `--thread` 連續編號卡片

每個重點獨立一張卡，固定右上角顯示 `1 / 5` 編號徽章。

```bash
python main.py --url $URL --thread --format twitter
```

- 與 `--formats` 互斥
- 輸出：`thread_01_dark_*.png`, `thread_02_dark_*.png`, ...
- 所有 5 個主題模板均新增 thread badge（`position: fixed; top: 12px; right: 12px`）

```html
{% if thread_index %}
<div class="thread-badge">{{ thread_index }} / {{ thread_total }}</div>
{% endif %}
```

#### Feature 5: `history` 子命令群組（SQLite 歷史紀錄）

每次成功生成都自動寫入 `~/.imggen/history.db`（WAL 模式），支援查詢、搜尋、統計。

```bash
imggen history list --days 7          # 列出近 7 天的生成紀錄
imggen history search "AI"            # 搜尋標題或 URL
imggen history stats                  # 文字統計摘要
imggen history stats --visual         # 生成統計圖卡（stats.html 模板）
```

- 新增模組：`src/history.py`
- 新增模板：`templates/stats.html`（CSS-only 橫條圖，遵循設計系統）
- 資料表結構：`generations (id, url, title, theme, format, provider, created_at, output_path, file_size, key_points_count, source, mode)`

#### Feature 6: `digest` 子命令（週報彙整卡片）

從歷史紀錄中取出過去 N 天的文章，交給 AI 合成一張週報圖卡。

```bash
imggen digest --days 7 --theme gradient
```

- 新增模組：`src/digest.py`
- 新增模板：`templates/digest.html`（多文章列表佈局，編號 + 標題 + 洞察）
- 依賴 Feature 5（歷史紀錄）

#### Feature 7: `--post twitter` 發布到 Twitter/X

生成圖卡後直接發推。

```bash
python main.py --url $URL --post twitter --caption twitter
```

- 新增模組：`src/publisher.py`
- 使用 tweepy v2 API（v1.1 上傳圖片 + v2 建立推文）
- 環境變數：`TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET`
- 若同時使用 `--caption twitter`，自動附帶文案

#### Feature 8: `watch` 子命令（資料夾監控）

監控指定資料夾，偵測到新的 `.txt` / `.md` / `.url` 檔案時自動觸發管線。

```bash
imggen watch ~/articles/ --theme dark --format story
```

- 新增模組：`src/watcher.py`
- 優先使用 `watchdog` 套件，未安裝時自動降級為 polling 模式
- 2 秒 debounce 防止重複觸發
- `.url` 檔案內容視為 URL，自動抓取後生成
- 生成結果自動寫入歷史紀錄（mode=`watch`）
- `Ctrl+C` 停止

---

### v4.5 Web UI + 品質提升（已實現）

將 imgGen 從純 CLI 擴展為 **CLI + Web UI 雙介面**，新增 FastAPI 後端和 React 前端，同時提升文章提取品質、開放 AI 提取參數自定義、支援 HTML 導出。

#### 架構變更：Web UI 技術棧

- **後端**：FastAPI（`web/api.py`），掛載靜態檔案，複用現有 pipeline
- **前端**：React 19 + TypeScript + Vite 8 + Tailwind CSS v4 + Framer Motion 12 + Zustand 5 + TanStack Query
- **路由**：Generate（主頁面）、History（歷史紀錄）

#### Feature 1: Smart URL 提取（trafilatura）

用 `trafilatura` 替換 `fetcher.py` 中的 regex HTML 清理，更乾淨的文章提取 = 更好的 AI 摘要。

```python
# src/fetcher.py
def _extract_article_text(html: str, url: str) -> str:
    result = trafilatura.extract(html, url=url, favor_precision=True)
    if result and len(result) > 50:
        return result
    return _strip_html(html)  # regex fallback
```

- `trafilatura` 自動處理 boilerplate 移除、主文提取
- 保留 `_strip_html()` 作為 fallback
- Threads URL 仍走專用 Googlebot UA 路徑，不受影響

#### Feature 2: ExtractionConfig — AI 提取參數自定義

新增 `ExtractionConfig` frozen dataclass，將原本固定的中文 prompt 模板化，解鎖多語言和不同場景。

```python
# src/extractor.py
@dataclass(frozen=True)
class ExtractionConfig:
    language: str = "zh-TW"          # zh-TW, zh-CN, en, ja, ko
    tone: str = "professional"       # professional, casual, academic, marketing
    max_points: int = 5              # 1–10
    min_points: int = 3              # 1–10
    title_max_chars: int = 15        # 5–100
    point_max_chars: int = 50        # 10–500
    custom_instructions: str = ""    # max 500 chars
```

- `_build_system_prompt(config)` 根據 config 動態生成系統提示詞
- `PipelineOptions` 新增 `extraction_config` 欄位
- API `GenerateRequest` 新增 `extraction_config` 參數（含 Pydantic 欄位驗證 + min≤max 校驗）
- Web UI：Generate 頁面 → Advanced Options → Extraction Settings 折疊區

#### Feature 3: HTML 導出

將已生成的圖卡以 HTML 格式下載，可嵌入 newsletter 或 blog。

```
GET /api/export/html/{gen_id}
→ Response: text/html; charset=utf-8
→ Header: Content-Disposition: attachment; filename="imggen_{id}.html"
```

- 從歷史紀錄取出 `extracted_data`，呼叫 `render_card()` 渲染 HTML
- 404: generation 不存在；400: 無 extracted_data
- Web UI：PreviewPanel 生成圖片後，底部操作列增加 `</>` 按鈕

#### Web UI 頁面功能

**Generate 頁面**（主頁面）
- 輸入方式：文字輸入 / URL 輸入 / 檔案上傳（tab 切換）
- 主題選擇：5 個視覺主題卡片
- 格式選擇：4 種社群格式
- AI Provider 選擇
- Advanced Options 折疊區：Scale、WebP、Brand Name、Watermark、Thread Mode、**Extraction Settings（新增）**
- 預覽面板：即時顯示生成結果，支援下載 PNG、複製到剪貼簿、**導出 HTML（新增）**

**History 頁面**
- 歷史紀錄列表、搜尋、統計

---

### v4.6 社交媒體卡片系統（已實現）

新增 6 個以社交媒體傳播為目標設計的主題，全部採用 **430×430 square 格式優化**，完整套用 taste-skill 設計規範（無純黑、無純白、飽和度 < 80%、tinted shadow、LILA BAN、禁 emoji）。

#### 新增主題

| 主題 | 風格 | 概念 | Accent |
|------|------|------|--------|
| `hook` | Noir Brutalist | 黑底大字鉤子問句，製造懸念 | 暖金 `#D4B848` |
| `quote` | Serif Quote Card | 白底精緻語錄卡，書法感引號 | 天藍 `#0C6EA4` |
| `quote_dark` | Noir Blossom | 深底語錄卡，白色大引號裝飾 | 暖玫瑰 `#C8726A` |
| `data_impact` | Terminal Glow | 暗底終端數據視覺化，螢幕綠發光英雄數字 | `#4ADE80` |
| `versus` | VS Battle | 黑底 vs 紅底雙欄對比，VS 徽章置中 | 磚紅 `#CC2200` |
| `thread_card` | Thread System | 連載卡片系統，右上角 N/N 徽章 | Electric Blue `#2563EB` |

#### 技術細節

- 全部主題支援 `body[data-format="square"]` CSS 覆蓋模式，固定 `height: 430px; overflow: hidden`
- `hook`、`quote_dark` 使用大型裝飾字符作為背景視覺元素（非 emoji）
- `data_impact` 支援 `data-format` attribute selector，同時相容 story / square
- `versus` VS 徽章使用 `position: fixed; top: 50%; left: 50%; transform: translate(-50%,-50%)`，在 430×430 完美置中
- 所有主題 `screenshotter.py` wait_for_timeout 已從 850ms 延長至符合最多 7 條要點的 stagger 時間

#### Extractor 更新

```python
# src/extractor.py
valid_themes = {"dark", "light", "gradient", "warm_sun", "cozy",
                "hook", "quote", "quote_dark", "data_impact", "versus", "thread_card"}
# 科技商業→dark，財經/數據→data_impact，語錄名言→quote/quote_dark，
# 對比辯論→versus，生活文化→light，溫馨日常→cozy，創意娛樂→warm_sun，
# 連載系列→thread_card，鉤子問句→hook
```

---

### v5.0 視覺模板系統大擴展（已實現）

以「**淺色底擴展**」為主軸，新增 8 個主題（第二批 4 個 + 第三批 4 個），將模板庫從 11 個擴展至 **19 個**，全面覆蓋暗底科技、淺色編輯、印刷報紙、柔粉社群、波普藝術、奢華數據、AI 劇場等視覺場景。

#### 第二批：強風格視覺卡（4 個）

| 主題 | 風格 | 背景色 | Accent | 設計特色 |
|------|------|--------|--------|---------|
| `pop_split` | Pop Art Silk Screen | 珊瑚 `#F5A88A` / 薄荷 `#A8D8C0` | 深棕黑 `#1A1208` | 雙欄波普，kaomoji 角色，halftone 點陣背景，斜刀片分隔 |
| `editorial` | Morandi Editorial | 亞麻 `#EAE5DE` | 可可棕 `#6B5A4E` | 三線系統（3px/1px/0.5px），Noto Serif TC，inline SVG 圖示 |
| `luxury_data` | Ruby Dark Data | 深炭 `#0D0D10` | 紅寶石 `#B91C3A` | Liquid Glass 英雄卡片（`backdrop-filter: blur(16px)`），SVG 放射格線背景，發光數字 |
| `ai_theater` | AI Cinema Bear | 深太空 `#080C10` | 信號藍 `#1E6FD9` | 掃描線紋理，CSS 北極熊 `ʕ•ᴥ•ʔ`（底部置中），Roboto Mono 資料流 |

**Liquid Glass 規格**（`luxury_data`）：
```css
backdrop-filter: blur(16px);
border: 1px solid rgba(185,28,58,0.20);
border-top: 2px solid rgba(229,38,79,0.60);
box-shadow: inset 0 1px 0 rgba(237,232,228,0.06);
```

**資料模型特殊格式**（`luxury_data`）：`key_points[0..2].text` 格式為 `"數字 | 說明"`，前端自動 split 渲染英雄卡片；`key_points[3+]` 渲染為支撐資料行。

#### 第三批：淺色底傳播系列（4 個）

**設計動機：** 暗底截圖在 Line / WeChat 聊天室顯得突兀；淺色卡片在日間螢幕對比更穩定，印刷 / PDF 友好，社群儲存率高約 18%。

| 主題 | 風格 | 背景色 | Accent | 設計特色 |
|------|------|--------|--------|---------|
| `studio` | Minimal Studio | 暖米白 `#F8F6F2` | 森林綠 `#2C5F2E` | 藝廊極簡，圓形 bullet，3px accent 短線，Noto Serif TC |
| `broadsheet` | Editorial Broadsheet | 新聞紙 `#FDFAF4` | 社論紅 `#B82020` | 印刷報頭黑底（50px），0.5px 分隔線，數字前綴 |
| `pastel` | Pastel Bloom | 淡玫瑰粉 `#FDF0F4` | 暗玫瑰 `#C25A7A` | 外粉底 + 內圓角白卡（14px radius），花瓣 bullet，柔光陰影 |
| `paper_data` | Paper Terminal | 冷米白 `#F4F7F2` | 深森林綠 `#1D6340` | `data_impact` 的淺色鏡像，格線底紋，Roboto Mono，同等資料密度 |

**Taste-Skill 三批次合規確認：**
- 無純黑（`#000000`）、無純白（`#FFFFFF`）：全部改為 tinted 值
- LILA BAN：19 個主題均無 purple/violet accent
- 飽和度 < 80%：所有 accent 飽和度已驗證
- Liquid Glass：含 tinted border + inset box-shadow，無 outer glow
- 禁 emoji：模板 markup、提取器 prompt、JSON schema 均無 emoji

#### 資料模型對應表

| 主題 | title | key_points 用途 | source |
|------|-------|-----------------|--------|
| `hook` | 鉤子問句（懸念型） | 3 條主要論點 | 文章來源 |
| `quote` / `quote_dark` | 書籍 / 作者資訊 | 1 條長語錄 | 作者名 |
| `data_impact` / `paper_data` | 核心數據 headline | 3 條數據解讀 | 研究機構 |
| `versus` | 對比議題 | 3 條左側觀點 + 3 條右側觀點（共 6 條） | 來源 |
| `pop_split` | 對比標題 | [0] 左側描述，[1] 右側描述（共 2 條） | 來源 |
| `luxury_data` | 主 headline | [0–2] 英雄卡（"數字\|說明"），[3+] 支撐資料 | 研究機構 |
| `editorial` / `studio` / `broadsheet` / `pastel` | 文章標題 | 3–4 條要點 | 來源 |
| `ai_theater` | AI 能力標題 | 3–4 條 monospace 資料字串 | 模型 / 工具名 |
| `thread_card` | 系列主題 | 最多 7 條要點（自動 scroll 顯示） | 系列名 |

#### Extractor 更新

```python
# src/extractor.py（v5.0）
valid_themes = {
    "dark", "light", "gradient", "warm_sun", "cozy",
    "hook", "quote", "quote_dark", "data_impact", "versus", "thread_card",
    "pop_split", "editorial", "luxury_data", "ai_theater",
    "studio", "broadsheet", "pastel", "paper_data",
}
# 主題建議指引：
# 數據/統計 → data_impact / paper_data / luxury_data
# 語錄/名言 → quote / quote_dark
# 對比/辯論 → versus / pop_split
# 新聞/財經 → broadsheet
# 書摘/思維 → editorial / studio
# 正能量/生活 → pastel / cozy / warm_sun
# AI/科技工具 → ai_theater / dark
# 鉤子問句   → hook
# 連載系列   → thread_card
```

---

### v6.0 內容類型矩陣完整覆蓋（已實現）

從「**視覺風格驅動**」轉向「**內容類型完整覆蓋**」——新增 12 個主題，將模板庫從 19 個擴展至 **31 個**，並以 23 種社群圖文內容類型為框架系統性補齊空白。

#### 設計策略

前五版以視覺風格為主軸，導致同類內容有多個視覺版本、但大量高傳播力內容類型無對應模板。v6.0 建立「視覺家族 × 內容類型」矩陣：每個新模板繼承一個既有淺色視覺家族的色彩系統，並為全新內容類型優化版面。

#### 第四批：淺色內容變體（4 個）

繼承第三批淺色視覺家族，為目前只有深色版本的內容類型補齊淺色選項，並新增第一個步驟教程類型。

| 主題 | 視覺家族 | 內容類型 | Accent | 設計特色 |
|------|---------|---------|--------|---------|
| `bulletin_hook` | Broadsheet | Hook 問句（淺色版） | 社論紅 `#B82020` | 報頭黑底 44px，大問句佔 40% 高度，`→` 揭曉要點 |
| `gallery_quote` | Studio | 語錄金句（淺色版） | 森林綠 `#2C5F2E` | 超大引號裝飾（opacity 0.11，背景層），作者居中 |
| `soft_versus` | Pastel | 柔性雙欄對比 | 暗玫瑰 `#C25A7A` | 左欄 `#FDF8FA` / 右欄 `#F8EDF2` 色差，花瓣 bullet |
| `trace` | Paper Terminal | 步驟教程 / How-to | 森林綠 `#1D6340` | `[01][02]` Roboto Mono 序號，奇偶行交替 accent/accent-alt |

#### 第五批：高傳播力缺口（4 個）

填補 P1 四個社群高頻內容類型，全新視覺語言，不依附既有家族。

| 主題 | 內容類型 | 背景 | Accent | 設計特色 |
|------|---------|------|--------|---------|
| `ranking` | Top N 排名 | 暖羊皮 `#F6F4F0` | 琥珀橙 `#C4540A` | `#01` 最大（26px）→往下漸縮，`條目名｜說明` 資料格式 |
| `before_after` | 蛻變前後對比 | 米褐 `#F2F0EC` | 草地綠 `#2C6E32` | BEFORE 灰調 / AFTER 綠調雙欄，CSS 圓形箭頭 badge |
| `concept` | 概念定義解釋 | 暖奶油 `#F5F3EF` | 鋼藍 `#1C5282` | 4px 左色條全高貫穿，定義框（淺藍底），方塊 CSS bullet，`概念｜英文名` 雙語標題 |
| `picks` | 精選策展推薦 | 象牙白 `#FAF8F4` | 琥珀棕 `#A05A20` | 每條目為帶邊框迷你卡片，`★`（U+2605）星評分，`★數|名稱|說明` 資料格式 |

#### 第六批：完整覆蓋長尾（4 個）

填補 P2 四個高頻但尚無模板的內容類型。

| 主題 | 內容類型 | 背景 | Accent | 設計特色 |
|------|---------|------|--------|---------|
| `opinion` | 個人觀點評論 | 溫奶白 `#FDFBF6` | 燒褐 `#7A3B1E` | 作者 byline 圓點 badge，論據框（左 3px 色條），空心圓 CSS bullet |
| `checklist` | 核查清單 | 暖白 `#F8F6F2` | 森林綠 `#1E6B3A` | SVG inline 勾框 icon，CSS 正方形核取框，偶數行淺底，底部進度計數 |
| `faq` | 問答 FAQ | 溫石 `#F4F2EE` | 鋼藍 `#1C5282` | Q 行 accent 底色 / A 行白底縮排，`問題｜答案` 資料格式（全形 `｜` 分隔） |
| `milestone` | 里程碑成就展示 | 暖象牙 `#FDFBF4` | 琥珀金 `#A06418` | 超大 Roboto Mono 數字（clamp 44–58px），amber 點陣背景紋，鑽石形 CSS bullet，`數字｜單位` 標題格式 |

#### 資料模型擴充

新增 8 個特殊資料格式，Jinja2 在模板中自動解析：

| 主題 | title 格式 | key_points 格式 | 解析方式 |
|------|-----------|-----------------|---------|
| `ranking` | 排名主題 | `條目名｜一句說明` | Jinja2 `split('｜')` |
| `before_after` | 蛻變主題 | `[0..2]` = BEFORE，`[3..5]` = AFTER | slice |
| `concept` | `概念名｜英文名` | `[0]` = 定義句；`[1+]` = `標籤｜說明` | `split('｜')` |
| `picks` | 推薦清單標題 | `星數|名稱|說明`（半形 `\|`） | `split('\|')` |
| `soft_versus` | 對比主題 | `[0..2]` = 左欄，`[3..5]` = 右欄 | slice |
| `faq` | 問答標題 | `Q：問題｜A：答案` | `split('｜')` |
| `milestone` | `數字｜單位說明` | `[0]` = 副標題，`[1+]` = 感悟 | `split('｜')` |
| `gallery_quote` | 引語全文 | `[0]` = 作者名，`[1]` = 出處（可選） | index |

#### Extractor 更新

```python
# src/extractor.py（v6.0）
valid_themes = {
    "dark", "light", "gradient", "warm_sun", "cozy",
    "hook", "quote", "quote_dark", "data_impact", "versus", "thread_card",
    "pop_split", "editorial", "luxury_data", "ai_theater",
    "studio", "broadsheet", "pastel", "paper_data",
    # v6.0 — Batch 4
    "bulletin_hook", "gallery_quote", "soft_versus", "trace",
    # v6.0 — Batch 5
    "ranking", "before_after", "concept", "picks",
    # v6.0 — Batch 6
    "opinion", "checklist", "faq", "milestone",
}
# 主題建議指引（v6.0 更新）：
# 數據/統計       → data_impact / paper_data / luxury_data
# 語錄/名言       → quote / quote_dark / gallery_quote
# 對比/辯論       → versus / pop_split / soft_versus / before_after
# 新聞/財經       → broadsheet / bulletin_hook
# 書摘/思維框架   → editorial / studio / concept
# 正能量/生活     → pastel / cozy / warm_sun
# AI/科技工具     → ai_theater / dark
# 鉤子問句        → hook / bulletin_hook
# 連載系列        → thread_card
# 步驟教程        → trace
# Top N 排名      → ranking
# 精選推薦        → picks
# 個人觀點        → opinion
# 核查清單        → checklist
# 問答 FAQ        → faq
# 里程碑成就      → milestone
```

#### Taste-Skill 合規（第四–六批）

- 無純黑（`#000000`）、無純白（`#FFFFFF`）：全部使用 tinted 值
- LILA BAN：所有 12 個新主題均無 purple/violet accent
- 飽和度 < 80%：最高為 `bulletin_hook` 社論紅 `#B82020`（sat≈74%）✓
- 禁 emoji：`→`（U+2192）、`★`（U+2605）、`[ ]` 均為 Unicode 符號或 ASCII，非 emoji
- CSS-only 圖示：checklist 使用 SVG inline 勾框，concept 使用 CSS `div` 方塊，milestone 使用 CSS `div` 旋轉 45°
- Liquid Glass：不適用（第四–六批均為扁平卡片設計）

---

### v6.1 Article Mode — 精簡條理化模式（已實現）

新增 `--mode article` 提取模式，將原文精簡為結構化段落輸出，取代傳統的條列式要點提取。搭配通用 `article.html` 模板，透過 CSS variables 支援所有 5 個核心主題配色。

#### 新增 CLI 選項

```bash
--mode [card|article]   # 提取模式（預設 card）
```

- `card`（預設）：提取 3-5 個條列式 key_points（現有行為）
- `article`：精簡原文為 3 段結構化段落，每段含小標題 + 分項要點

#### ExtractionConfig 變更

```python
@dataclass(frozen=True)
class ExtractionConfig:
    # ... 現有欄位 ...
    mode: str = "card"  # "card" | "article"
```

#### Article Mode 提取 Schema

```json
{
  "title": "15字內標題",
  "sections": [
    {
      "heading": "4-8字小標題",
      "body": ["要點1（15-25字）", "要點2（15-25字）"]
    }
  ],
  "source": "來源或空字串",
  "theme_suggestion": "dark|light|gradient|warm_sun|cozy"
}
```

- 固定 3 個 sections，每段 2-3 個要點
- 三段結構：核心概念 → 具體做法 → 關鍵細節
- body 為字串陣列（相容舊版單一字串，自動正規化）

#### 新增模板：`article.html`

通用 article 模板，透過 `data-theme` 屬性切換 5 種主題配色：

| 主題 | 背景 | Hero 卡片 | Accent |
|------|------|-----------|--------|
| `dark`（預設）| `#090d1a` | `rgba(37,99,235,0.06)` | Electric Blue |
| `light` | `#ffffff` | `#eff6ff`（淺藍） | `#3b82f6` |
| `gradient` | `#0f0a1a` | `rgba(168,85,247,0.06)` | Purple |
| `warm_sun` | `#1a1408` | `rgba(245,158,11,0.06)` | Amber |
| `cozy` | `#1a080f` | `rgba(236,72,153,0.06)` | Pink |

佈局結構：
- 第一段使用 Hero 卡片（accent 左邊框 + 背景 + glow 光暈）
- 後續段落使用 border-left 邊線 + 序號圓點
- 每個要點前方帶圓點，獨立換行顯示
- 共享 fadeUp stagger 動畫

#### 渲染器變更（`src/renderer.py`）

`render_card()` 自動偵測 data 結構：
- 含 `sections` 且無 `key_points` → 載入 `article.html`
- 含 `key_points` → 載入 `{theme}.html`（現有行為）

新增 `sections` 變數傳入模板。

#### 驗證器變更（`src/extractor.py`）

- 新增 `_validate_article_data()`：檢查 sections 結構、body 陣列
- `_validate_extracted_data()` 依 mode 分派至對應驗證函式
- body 正規化：字串自動轉為單元素陣列

---

## 7. 非目標（明確不做）

以下功能在可預見的未來都**不在範疇內**：

| 非目標 | 原因 |
|--------|------|
| 多使用者支援 / 帳號系統 | 這是個人工具，沒有多人需求 |
| 雲端服務 / SaaS 化 | 不打算對外提供服務或收費 |
| 雲端儲存 / 同步 | 輸出檔案在本機就夠了 |
| 團隊協作 / 權限管理 | 沒有團隊 |
| 行動端 App | 需求場景都在桌面 terminal |
| 付費牆 / 訂閱制 | 個人工具，不做商業化 |
| 圖片編輯器 / Canva 化 | 這是自動化引擎，不是設計工具 |

---

## 8. 技術約束

| 項目 | 約束 |
|------|------|
| 執行環境 | macOS（主要），Linux（次要）|
| 語言 | Python 3.11+（後端）；TypeScript 5+（前端）|
| CLI 框架 | Click |
| Web 框架 | FastAPI（後端 API）|
| 前端框架 | React 19 + Vite 8 + Tailwind CSS v4 + Zustand 5 + TanStack Query |
| 模板引擎 | Jinja2 |
| 截圖工具 | Playwright（需本機安裝 Chromium）|
| 截圖等待時間 | 850ms（覆蓋最多 10 個要點：10×60ms+80ms+400ms buffer，checklist 最長）|
| 文章提取 | `trafilatura`（v4.5 起），fallback 至 regex strip |
| AI 相依 | 至少需要一個有效的 API key 或 claude CLI binary |
| 輸出格式 | PNG（主要），WebP（`--webp`），HTML（v4.5 起 `/api/export/html`）|
| 網路 | URL 模式需要網路；Google Fonts 載入需要網路 |
| 設定管理 | `.env` 檔管理 API keys；TOML `.imggenrc` 管理執行偏好（v1.6 起支援）|
| 本地資料庫 | SQLite WAL 模式，`~/.imggen/history.db`（v4.0 起）|
| 選用依賴 | `tweepy>=4.14.0`（`--post twitter`）；`watchdog>=4.0.0`（`watch`）；`trafilatura>=2.0.0`（Smart URL）|
| 字體規範 | 所有主題使用 `Outfit`（標題/內文），部分主題搭配 `Noto Serif TC`（editorial 標題）|
| 設計系統 | taste-skill 基準：DESIGN_VARIANCE=8 / MOTION_INTENSITY=6 / VISUAL_DENSITY=4 |
| Emoji 政策 | 全面禁止：模板、提取器 prompt、JSON schema 均不含 emoji |
| API 輸入驗證 | Pydantic Field 約束 + model_validator（ExtractionConfig min≤max 校驗）|

---

## 9. 附錄

### 模組清單

**CLI 核心**
- 主程式進入點：`main.py`
- 核心管線：`src/pipeline.py`（extract → render → screenshot 共用流程）
- AI 摘要模組：`src/extractor.py`（含 `ExtractionConfig` dataclass，v4.5 新增模板化 prompt）
- HTML 渲染模組：`src/renderer.py`
- 截圖模組：`src/screenshotter.py`
- 設定與 Preset 模組：`src/config.py`
- 批次處理模組：`src/batch.py`
- URL 擷取模組：`src/fetcher.py`（v4.5 新增 trafilatura 整合）
- 剪貼簿模組：`src/clipboard.py`
- 社群文案模組：`src/caption.py`
- 歷史紀錄模組：`src/history.py`
- 週報彙整模組：`src/digest.py`
- 社群發布模組：`src/publisher.py`
- 資料夾監控模組：`src/watcher.py`

**Web UI**（v4.5 新增）
- Web API：`web/api.py`（FastAPI，含 `/api/generate`、`/api/generate/multi`、`/api/export/html/{gen_id}`、`/api/digest` 等）
- 前端：`web/frontend/`（React 19 + TypeScript + Vite 8）
  - Store：`src/stores/useGenerateStore.ts`（Zustand，含 extraction config 狀態管理）
  - Generate 頁面：`src/pages/GeneratePage.tsx`
  - History 頁面：`src/pages/HistoryPage.tsx`
  - Extraction Settings 元件：`src/features/generate/ExtractionSettings.tsx`（v4.5 新增）
  - Preview Panel 元件：`src/features/generate/PreviewPanel.tsx`（v4.5 新增 HTML 導出按鈕）

### 模板清單（`templates/`）

**原始主題（v1.0–v2.6）**

| 檔案 | 主題名 | 風格 | 最佳格式 |
|------|--------|------|---------|
| `dark.html` | `dark` | 深海軍藍，Electric Blue 強調色 | story |
| `light.html` | `light` | 米白編輯風，藍色 banner | story |
| `gradient.html` | `gradient` | 深海藍青漸層，Cyan 玻璃態 | story |
| `warm_sun.html` | `warm_sun` | 橙金暖陽，SVG 太陽圖示 | square |
| `cozy.html` | `cozy` | 奶茶棕紙紋，Serif 標題 | square |

**社交媒體卡片系統（v4.6）**

| 檔案 | 主題名 | 風格 | 最佳格式 |
|------|--------|------|---------|
| `hook.html` | `hook` | Noir Brutalist，黑底大字鉤子問句 | square |
| `quote.html` | `quote` | Serif Quote，白底精緻語錄卡 | square |
| `quote_dark.html` | `quote_dark` | Noir Blossom，深底白引號語錄 | square |
| `data_impact.html` | `data_impact` | Terminal Glow，螢幕綠發光數據 | square / story |
| `versus.html` | `versus` | VS Battle，黑紅雙欄對比 | square |
| `thread_card.html` | `thread_card` | Thread System，連載編號卡片 | square |

**視覺擴展第二批（v5.0）**

| 檔案 | 主題名 | 風格 | 最佳格式 |
|------|--------|------|---------|
| `pop_split.html` | `pop_split` | Pop Art 珊瑚/薄荷雙欄，kaomoji | square |
| `editorial.html` | `editorial` | Morandi 亞麻米，三線系統 | square |
| `luxury_data.html` | `luxury_data` | Ruby Dark，Liquid Glass 英雄數字卡 | square |
| `ai_theater.html` | `ai_theater` | AI Cinema，掃描線 + CSS 北極熊 | square |

**淺色底傳播系列（v5.0）**

| 檔案 | 主題名 | 風格 | 最佳格式 |
|------|--------|------|---------|
| `studio.html` | `studio` | Minimal Studio，暖米白森林綠 | square |
| `broadsheet.html` | `broadsheet` | Editorial Broadsheet，印刷報頭紅 | square |
| `pastel.html` | `pastel` | Pastel Bloom，淡粉圓角卡 | square |
| `paper_data.html` | `paper_data` | Paper Terminal，冷米白森林綠（data_impact 淺色版） | square |

**淺色內容變體（v6.0 Batch 4）**

| 檔案 | 主題名 | 內容類型 | 視覺家族 |
|------|--------|---------|---------|
| `bulletin_hook.html` | `bulletin_hook` | Hook 問句（淺色版）| Broadsheet |
| `gallery_quote.html` | `gallery_quote` | 語錄金句（淺色版）| Studio |
| `soft_versus.html` | `soft_versus` | 柔性雙欄對比 | Pastel |
| `trace.html` | `trace` | 步驟教程 / How-to | Paper Terminal |

**高傳播力缺口（v6.0 Batch 5）**

| 檔案 | 主題名 | 內容類型 | 特色 |
|------|--------|---------|------|
| `ranking.html` | `ranking` | Top N 排名 | amber 漸進數字大小 |
| `before_after.html` | `before_after` | 蛻變前後對比 | 雙欄色差 + 圓形箭頭 badge |
| `concept.html` | `concept` | 概念定義解釋 | 4px 左色條 + 定義框 |
| `picks.html` | `picks` | 精選策展推薦 | 迷你卡片 + ★ 星評分 |

**完整覆蓋長尾（v6.0 Batch 6）**

| 檔案 | 主題名 | 內容類型 | 特色 |
|------|--------|---------|------|
| `opinion.html` | `opinion` | 個人觀點評論 | 作者 byline + 論據框 |
| `checklist.html` | `checklist` | 核查清單 | SVG 核取框 + 進度計數 |
| `faq.html` | `faq` | 問答 FAQ | Q/A 交替底色 + `｜` 分隔 |
| `milestone.html` | `milestone` | 里程碑成就 | 超大數字 + amber 點陣底紋 |

**功能性模板（非 theme，不在 VALID_THEMES）**

| 檔案 | 用途 | 版本 |
|------|------|------|
| `article.html` | Article mode 精簡條理化模板（透過 `data-theme` 支援 5 種配色） | v6.1 |
| `stats.html` | 歷史紀錄統計儀表板（CSS-only 橫條圖） | v4.0 |
| `digest.html` | 週報彙整，多文章列表佈局 | v4.0 |

### 共享設計規格（Design Tokens）

```
字體：   --fs-title clamp(26px,7vw,34px) / --fs-body 18px / --fs-secondary 16px / --fs-label 12px
動畫：   fadeUp 0.32s cubic-bezier(0.16,1,0.3,1)，--i × 0.08s stagger
陰影：   tinted to accent hue（禁用純黑 rgba(0,0,0,...)）
Liquid glass：border 1px solid rgba(255,255,255,0.16) + inset 0 1px 0 rgba(255,255,255,0.08)
```

### Claude Code 自訂指令
- `/taste`：`~/.claude/commands/taste.md`（全域可用）
  - 以 taste-skill 對當前項目執行設計審查並自動修復

### 輸出目錄與資料儲存
- 圖卡輸出：`output/`
- 歷史資料庫：`~/.imggen/history.db`
- Thread 輸出：`output/thread_01_dark_*.png`, `thread_02_dark_*.png`, ...
- 統計圖卡：`output/stats_*.png`
- 週報圖卡：`output/digest_*.png`
- 文案檔案：與圖片同目錄，`.captions.txt` 後綴

---

## 10. v7.0 Smart Mode — AI 驅動動態布局生成（規劃中）

### 核心概念

Smart Mode 是一個 AI 驅動的佈局生成系統，取代靜態的 Jinja2 模板。每張圖卡都由 AI 根據內容動態設計，就像為每篇文章單獨製作一張 PPT 幻燈片。

### 架構對比

| 層面 | Template Mode（v1.0–v6.1） | Smart Mode（v7.0+） |
|------|---------------------------|----------------------|
| 布局設計 | 28 個預定義 Jinja2 模板 | 無限制，AI 動態生成 |
| 自定義程度 | 中（主題選擇） | 高（內容感知設計） |
| 文字適應 | 受限（固定行高、字體） | 自動排版（clamp, flex） |
| 視覺層次 | 固定（所有內容等權重） | 動態（根據 importance 調整） |
| 擴展性 | 低（新布局需手工製作） | 高（AI 自動處理） |
| 生成速度 | 快（< 2 秒） | 慢（5–30 秒，含 API 呼叫） |

### 核心特性

#### 1. 智能佈局模式
AI 自動選擇或設計最適當的佈局模式：

| 模式 | 適用場景 | 特徵 |
|------|---------|------|
| `hero_list` | 一主多輔 | 大標題 + 列表要點 |
| `grid` | 並列內容 | 2–4 欄網格卡片 |
| `timeline` | 流程步驟 | 垂直時間軸 + 節點 |
| `comparison` | 對比分析 | 雙欄對立色調 |
| `quote_centered` | 金句摘錄 | 大引言 + 歸屬 |
| `data_dashboard` | 數據密集 | 指標卡片 + 統計 |
| `numbered_ranking` | Top-N 列表 | 大排名序號 + 項目 |

#### 2. 內容感知設計
根據抽取的資料自動調整：

```json
{
  "title": "文章標題",
  "key_points": [
    {"text": "關鍵點", "importance": 5},  // 最重要 → 大字、強調色
    {"text": "支撑点", "importance": 3}   // 中等 → 中字、列表
  ],
  "layout_hint": "hero_list",
  "color_mood": "dark_tech",
  "content_type": "news"
}
```

AI 根據 `importance` 分數（1–5）動態調整：
- 字體大小（clamp 響應式）
- 色彩飽和度
- 版面佔比
- 視覺強調（陰影、邊框、背景）

#### 3. 預定義色彩心情
5 種設計心情，對應 CSS 變數系統：

| 心情 | 背景 | 強調色 | 適用主題 |
|------|------|--------|---------|
| `dark_tech` | `#090d1a` 深藍黑 | `#2563eb` 電光藍 | 科技、商業 |
| `warm_earth` | `#EAE5DE` 暖米白 | `#6B5A4E` 棕褐 | 生活、文化 |
| `clean_light` | `#f8f7f4` 冷米白 | `#0284c7` 天空藍 | 內容、說明 |
| `bold_contrast` | `#F6F4F0` 亮米白 | `#C4540A` 燃火橙 | 新聞、突出 |
| `soft_pastel` | `#FDF0F4` 淡粉白 | `#C25A7A` 暗玫瑰 | 創意、溫馨 |

#### 4. 設計系統 CSS 基礎
所有 AI 生成的 HTML 都遵循統一設計規格：

```css
:root {
  --fs-title:      clamp(22px, 6vw, 32px);
  --fs-subtitle:   clamp(16px, 4vw, 20px);
  --fs-body:       16px;
  --fs-secondary:  14px;
  --fs-label:      11px;
  /* 顏色變數：--bg, --bg-card, --accent, --text-primary 等 */
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

#### 5. 驗證與容錯機制
AI 生成失敗時自動降級：

1. **嘗試 1**：正常 AI 生成 → 驗證 HTML 結構
2. **嘗試 2**：失敗則重試 + 更嚴格的指令 → 再次驗證
3. **回退**：雙重失敗 → 自動使用對應的 Template Mode 主題

```python
try:
    html = generate_smart_html(data, provider="claude")
except ValidationError:
    html = fallback_to_template(data, theme=mood_to_theme[color_mood])
```

#### 6. Watermark & Thread Badge
支援動態注入浮水印和連載編號：

```html
<!-- 自動注入 -->
<div class="watermark-overlay watermark-bottom-right">
  <img src="data:image/svg+xml;..." alt="" />
  <span>Brand Name</span>
</div>
<div class="thread-badge">2 / 5</div>
```

### CLI 與 Web UI 整合

#### CLI 模式
```bash
# 智能生成（使用 Claude API）
python main.py --url https://example.com --mode smart --provider claude

# 覆蓋顏色心情
python main.py --url https://example.com --mode smart --color-mood warm_earth

# 指定 AI 提供者（claude / gemini / gpt / cli）
python main.py --text "..." --mode smart --provider gemini
```

#### Web UI 控制面板
在 Web UI 新增 **Smart Mode 切換**：
- Smart Layout（AI 動態）vs Template（預定義）
- 色彩心情選擇器（5 個 mood）
- 佈局建議預覽（7 個模式）
- 即時預覽 + 編輯 AI 生成的 HTML

### 效能與成本

| 指標 | 預期值 |
|------|--------|
| 單張生成時間 | 5–30 秒（含 API 延遲） |
| 批次 10 篇（同步） | 50–300 秒（取決於 provider） |
| API 呼叫成本 | ~$0.01–0.03 / 張（claude-sonnet-4-6） |
| HTML 大小 | < 50 KB（validation 上限） |

### 降級策略

Smart Mode 失敗時的處理優先級：

1. **Attempt 1 失敗** → 重試 + 更嚴格指令
2. **Attempt 2 失敗** → 回退至 Template Mode
   - 色彩心情自動對應至最近的主題
   - 例：`dark_tech` → `dark` 主題，`warm_earth` → `editorial` 主題

### 成功指標

| 指標 | 目標 |
|------|------|
| 一次成功率（無回退） | ≥ 75% |
| 兩次成功率（含重試） | ≥ 95% |
| HTML 驗證通過率 | 100%（回退保證）|
| 使用者主觀品質評分 | ≥ 4/5 |
| 比 Template Mode 好用程度 | ≥ 60% 使用者偏好 |

---

## 11. 擴展路線圖

imgGen 的核心定位是**自動化內容管道**。擴展方向是加深管道深度，而非往設計編輯器方向走。

```
內容接入  →  AI 處理  →  多形態輸出  →  自動分發  →  效果回饋
```

| Sprint | 功能 | 核心理由 | 狀態 |
|--------|------|---------|------|
| **Sprint 1** | Smart URL + ExtractionConfig + HTML 導出 | 快速勝利，立即提升品質 | **已完成 (v4.5)** |
| **Sprint 2** | 社交媒體卡片系統（6 主題）+ taste-skill 全面套用 | 傳播力提升，設計系統成熟 | **已完成 (v4.6)** |
| **Sprint 3** | 視覺模板大擴展（8 主題，含淺色底系列）| 場景覆蓋，淺底傳播率優化 | **已完成 (v5.0)** |
| **Sprint 3.5** | Article Mode 精簡條理化模式 | 知識整理場景，段落式排版 | **已完成 (v6.1)** |
| **Sprint 4** | Smart Mode — AI 動態布局生成 | 無限布局、內容感知設計、PPT 般的創意輸出 | **規劃中 (v7.0)** |
| **Sprint 5** | Telegram Bot + Webhook API + PDF/圖片輸入 | 現代內容接入管道 | 規劃中 |
| **Sprint 6** | Web UI 主題選擇器更新（19 主題 + Smart Mode）+ 輪播圖 / 動態卡片 | 介面對等 + 輸出格式擴展 | 規劃中 |
| **Sprint 7** | 多平台發布 + 定時發布 + 自動化串聯 | 分發閉環 | 規劃中 |
| **Sprint 8** | 互動追蹤 + A/B 測試 + AI 內容洞察 | 智能回饋層 | 規劃中 |

詳細技術設計見 `docs/expansion-design.md`。
UX 設計見 `docs/ux-architecture.md`。
