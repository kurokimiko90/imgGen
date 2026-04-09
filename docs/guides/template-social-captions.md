# 社交媒體配文模板規劃

## 一、優秀社交媒體配文的核心特徵

| 特徵維度 | 具體表現 | 心理機制 |
|---------|---------|---------|
| **視覺衝擊** | 強對比、清晰層次、首屏聚焦 | 注意力捕獲（3秒法則） |
| **資訊密度** | 數字化、要點化、一眼掌握核心 | 認知效率最大化 |
| **情感共鳴** | 痛點觸達、好奇心缺口、認同感 | 情緒觸發分享行為 |
| **可信度信號** | 具體數據、來源標注、品牌背書 | 降低信任門檻 |
| **行動召喚** | 明確下一步、緊迫感、分享動機 | 轉化被動瀏覽為主動行為 |
| **平台適配** | 橫/方/豎圖比例、首屏優先 | 降低平台算法阻力 |

---

## 二、現有模板風格地圖

| 模板 | 風格 | 色彩 | 字體 |
|------|------|------|------|
| `dark` | 深空科技 | 深藍 `#090d1a` + 藍 `#2563eb` | Outfit |
| `dark_card` | 深空紫調 | 近黑 `#07090f` + 紫 `#8b7ef8` | Noto Sans TC |
| `gradient` | Glassmorphism | 深藍綠 + 玻璃磨砂 + 青 `#06b6d4` | Outfit |
| `light` | 簡潔白底 | 米白 `#f8f7f4` + 天藍 `#0284c7` | Outfit |
| `cozy` | 溫暖紙質 | 米黃 `#fdf8f0` + 琥珀 `#d97706` | Noto Serif TC |
| `warm_sun` | 暖陽橙調 | 奶油 `#fffbf5` + 橙 `#f97316` | Outfit |

**已覆蓋：** 深空系、玻璃系、亮白系、暖色系
**空缺：** 極簡衝擊系、詩意漸層系、終端數據系、雜誌對比系

---

## 三、新模板規劃

### 優先級

```
P1（核心缺口）  → hook.html、quote.html
P2（高傳播力）  → data_impact.html、versus.html
P3（平台特化）  → thread_card.html
```

---

### 模板 1 — `hook.html` 鉤子問句型

**核心特徵：** 好奇心缺口 + 情感共鳴
**適用場景：** 爆款開頭、製造懸念

**風格：Noir Brutalist 黑色極端主義**
- 靈感：Spotify 年度廣告、NYT op-ed 大圖
- 背景：炭黑 `#0C0C0C`（off-black，非純黑）
- 主文字：暖白 `#F5F5F0`（off-white，避免刺眼對比）
- Accent A（張力型）：暖金 `#D4B848`（HSL 49°, 57% sat）← 電黃降飽和版
- Accent B（危機型）：磚紅 `#C94040`（HSL 0°, 62% sat）← 赤紅降飽和版
- 字體：Outfit 900，超大字號佔主視覺，零裝飾元素
- 排版：字體本身就是設計，問句佔 60% 視覺空間

> **Taste fix:** `#000000` → `#0C0C0C`（NO PURE BLACK）；`#FFE600` sat=100% → `#D4B848` sat=57%；`#FF3B30` sat=100% → `#C94040` sat=62%（SAT < 80%）

**版面結構：**
```
┌─────────────────────┐
│  [CATEGORY LABEL]   │  ← 12px ALL-CAPS accent色
│                     │
│  為什麼 90% 的人     │  ← 超大問句，白字
│  在這件事上做錯了？   │
│                     │
│  ─────────────────  │  ← accent色分隔線
│                     │
│  ① 大多數人以為...   │  ← 要點揭曉，小字
│  ② 真正的問題是...   │
│  ③ 正確做法其實...   │
│                     │
│  來源 · POWERED BY  │  ← footer
└─────────────────────┘
```

---

### 模板 2 — `quote.html` 金句型

**核心特徵：** 情感共鳴 + 易於截圖分享
**適用場景：** 名人名言提煉、文章金句、每日一句

**風格：Blossom Ink 玫瑰暈染**（原 Aurora Dreamy，移除紫色後重命名）
- 靈感：小紅書爆款引用卡、法式雜誌插頁
- 背景：極淡玫瑰白 `#FEF2F6`，Mesh gradient blobs 用 `rgba(190,24,93,0.10)` + `rgba(202,138,4,0.08)`（深玫 + 琥珀，低透明度）
- 主文字：極深酒紅 `#1C0B12`（tinted off-black，非純黑）
- Accent：深玫 `#9D174D`（HSL 337°, 74% sat）← 單一 accent
- 裝飾引號：超大 `"` 字符，`rgba(157,23,77,0.12)` 極淡玫色浮層
- Attribution 線條：`#D4A5B5`（muted blush）
- 字體：Noto Serif TC 900（詩意感），attribution 用 Outfit 400
- 感覺：截圖下來放朋友圈的那種美

> **Taste fix:** `#7C3AED` violet 觸發 LILA BAN，整體換為玫瑰/暖琥珀系；`#EC4899` sat=81% → 改用 `#9D174D` sat=74%；移除所有紫色調

**版面結構：**
```
┌─────────────────────┐
│  "                  │  ← 超大裝飾引號（半透明白）
│                     │
│   這是文章中最精華   │  ← 金句主體，Serif 大字
│   的一句話，引發     │
│   強烈共鳴與共識     │
│                  "  │
│                     │
│  ── 作者 / 來源     │  ← attribution
│                     │
│  [品牌 badge]        │
└─────────────────────┘
```

---

### 模板 3 — `data_impact.html` 數據震撼型

**核心特徵：** 可信度信號 + 視覺衝擊
**適用場景：** 報告摘要、數據洞察、研究結論、市場分析

**風格：Terminal Glow 終端發光**
- 靈感：Bloomberg terminal、數據新聞圖表
- 背景：`#0B0E0B`（微帶綠暖的 off-black，非純黑）+ CSS 細密掃描線紋理（1px stripes，3% opacity）
- 大數字 A（生長型）：抹茶綠 `#4ADE80`（HSL 151°, 72% sat）← 螢光綠降飽和版
- 大數字 B（警示型）：深琥珀 `#C68B1A`（HSL 38°, 69% sat）← F59E0B 降飽和版
- 說明文字：`#9BAAA0`（muted sage-grey，與 off-black 背景的 tinted shadow 一致）
- 字體：數字用 Roboto Mono / JetBrains Mono（等寬），標籤用 Outfit ALL-CAPS
- 感覺：數字從屏幕裡凸出來打你臉

> **Taste fix:** `#0A0A0A` → `#0B0E0B`（NO PURE BLACK）；`#00FF88` sat=100% → `#4ADE80` sat=72%；`#F59E0B` sat=92% → `#C68B1A` sat=69%（SAT < 80%）；`#C8D0E0` 冷灰 → `#9BAAA0` tinted 灰（shadow tinted to bg hue）

**版面結構：**
```
┌─────────────────────┐
│  INSIGHT · 數據洞察  │  ← label
│  ─────────────────  │  ← accent掃描線
│                     │
│       73%           │  ← 超大數字（螢光）
│                     │
│  的企業在三年內      │  ← 說明文字
│  會遭遇重大數據洩露   │
│                     │
│  ─────────────────  │
│  ① 次要數據點 42%   │  ← 補充數據
│  ② 次要數據點 18x   │
│                     │
│  來源 · 日期         │
└─────────────────────┘
```

---

### 模板 4 — `versus.html` 對比衝突型

**核心特徵：** 認知衝突 + 行動召喚
**適用場景：** 觀念糾正、Before/After、舊方法 vs 新方法、誤解 vs 真相

**風格：Neo-Brutalist Split 雜誌對決**
- 靈感：Figma / Linear 產品頁、雜誌跨頁對比
- 左側（舊/錯）：炭黑 `#1C1C1E` + 冷白 `#E8EAF0` 文字，上方「✗ 舊觀念」badge（`#6B7280` muted）
- 右側（新/對）：深緋紅 `#B91C1C`（HSL 0°, 75% sat）+ 暖白文字，上方「✓ 新視角」badge（白色）
- 分隔：4px 白色實線，左右兩側各 3px flat shadow（`box-shadow: 3px 3px 0 #000`，neo-brutalist 特徵）
- 字體：Outfit 700，標題粗體，左右對稱佈局

> **Taste fix:** `#7C3AED` 觸發 LILA BAN → 移除；`#059669` sat=95% → 整體右側改為緋紅衝突感（更強的是非對立視覺語言）；右側 `#B91C1C` sat=75% ✓

**版面結構：**
```
┌──────────┬──────────┐
│  ✗ 舊觀念 │ ✓ 新做法  │  ← badge labels
│  ────    │  ────    │  ← 4px 分隔線
│          │          │
│  大多數人 │  聰明的人 │
│  以為...  │  其實...  │
│          │          │
│  ① 誤區  │  ① 正解  │
│  ② 誤區  │  ② 正解  │
└──────────┴──────────┘
```

---

### 模板 5 — `thread_card.html` 線程進度型

**核心特徵：** 資訊密度 + 連續閱讀動機
**適用場景：** Twitter/X threads、小紅書系列貼、知識連載

**風格：Swiss Grid 瑞士清醒**
- 靈感：Twitter/X native 感、Readwise 卡片、Dieter Rams 設計哲學
- 背景：極淡灰白 `#FAFAF9`（off-white，stone-50 等效）
- 色彩：90% 黑白，單一 accent `#2B7CB8`（HSL 204°, 60% sat）← Twitter 藍降飽和版
- 文字主色：`#0F172A`（slate-950 off-black）
- 文字次色：`#64748B`（slate-500）
- 進度點陣 filled: `#2B7CB8`，empty: `#CBD5E1`（slate-300）
- 特徵：精確格線、細線分割、進度點陣 `●●○○○`
- 字體：Outfit 優先（-apple-system fallback），不使用 Inter
- 感覺：乾淨到讓人只能盯著內容看

> **Taste fix:** `#1D9BF0` sat=86% → `#2B7CB8` sat=60%（SAT < 80%）；純黑 text → `#0F172A` slate-950；Inter 字體 → Outfit（Inter BANNED by ANTI-SLOP rule）；純白 bg → `#FAFAF9`

**版面結構：**
```
┌─────────────────────┐
│  ●●○○○○○  2 / 7    │  ← 進度條（製造繼續閱讀動力）
│  ─────────────────  │  ← accent 色細線
│                     │
│  第 02 個要點：       │  ← 序號 + 標題
│                     │
│  [詳細說明文字，      │  ← 主體內容
│   這裡可以比較長，     │
│   支持 3-4 行]        │
│                     │
│  → 下一條更關鍵 ↓    │  ← 鉤子 CTA
│                     │
│  來源 · NOZOMI       │  ← footer
└─────────────────────┘
```

---

## 四、風格矩陣

```
衝擊感
  ↑
  │  Noir Brutalist    Terminal Glow
  │  炭黑+暖金/磚紅      近黑+抹茶/琥珀
  │     (hook)              (data)
  │
  │        Neo-Brutalist Split
  │         炭黑 vs 深緋紅
  │             (versus)
  │
  │  Swiss Grid        Blossom Ink
  │  灰白+沉藍          玫瑰白+深玫
  │   (thread)           (quote)
  │
  └──────────────────────────────→ 情感溫度
    冷 / 理性                    暖 / 感性
```

---

## 六、Taste-Skill 色彩審核日誌（v1 → v2）

| 模板 | 違規色 | 違規規則 | 修正後 |
|------|--------|---------|--------|
| hook | `#000000` | NO PURE BLACK | `#0C0C0C` |
| hook | `#FFE600` sat=100% | SAT < 80% | `#D4B848` sat=57% |
| hook | `#FF3B30` sat=100% | SAT < 80% | `#C94040` sat=62% |
| quote | `#7C3AED` violet | LILA BAN | 換為 `#9D174D` 深玫系 |
| quote | `#EC4899` sat=81% | SAT < 80% | 移除，整體改為 Blossom Ink |
| data | `#0A0A0A` | NO PURE BLACK | `#0B0E0B` |
| data | `#00FF88` sat=100% | SAT < 80% | `#4ADE80` sat=72% |
| data | `#F59E0B` sat=92% | SAT < 80% | `#C68B1A` sat=69% |
| versus | `#7C3AED` purple | LILA BAN | 換為 `#B91C1C` 深緋紅 |
| versus | `#059669` sat=95% | SAT < 80% | 移除，整體換為緋紅對決 |
| thread | `#1D9BF0` sat=86% | SAT < 80% | `#2B7CB8` sat=60% |
| thread | plain `#000` text | NO PURE BLACK | `#0F172A` slate-950 |
| thread | Inter font | ANTI-SLOP BANNED | Outfit |
| **v2 versus** | `#111` flat shadow | Tint shadow to bg hue | `#1A1012` off-black tinted |
| **v2 quote_dark** | `rgba(255,255,255,0.08)` inner shadow | Tint shadow to bg hue | `rgba(240,224,230,0.10)` warm-tinted |
| **v2 quote_dark** | stamp border 未定義 | Liquid glass 需顯式 border | `rgba(200,90,125,0.20)` rose-tinted |

---

## 五、設計系統共識（跨模板）

所有新模板繼承現有設計 tokens：

```css
/* Typography Scale */
--fs-title:     clamp(26px, 7vw, 34px)   /* Hero headline */
--fs-body:      18px                      /* Primary point text */
--fs-secondary: 16px                      /* Secondary / footer text */
--fs-label:     12px                      /* ALL-CAPS labels, badges */

/* Motion */
/* fadeUp 0.32s cubic-bezier(0.16,1,0.3,1) with --i * 0.08s stagger */

/* Shadows: always tinted to theme accent — never pure rgba(0,0,0,...) */
/* Liquid glass: border + box-shadow inset 0 1px 0 rgba(255,255,255,0.10) */
```

支持的 format：`portrait`（430px）、`square`（430px）、`twitter`（540px）、`landscape`（768px）

---

## 七、v2 改善計畫（首批渲染後）

基於首批測試圖片的視覺問題，以下為各模板的改善方案：

---

### 7-1 `hook.html` — 問句填滿空間

**問題：** spacer 將 footer 頂到底部，問句與要點之間大面積留白，3 個要點時尤其明顯

**方案：**
- 問句區改用 `flex: 1` 自然填滿中間空間，形成「上(label) → 中(問句 flex:1) → 下(要點 + footer)」三段結構
- 問句垂直置中定錨，留白由問句本身吸收而非 spacer
- 背景右側加超大裝飾字符 `?`（`rgba(212,184,72,0.03)`，`font-size: 320px`，旋轉 −15deg，絕對定位不影響佈局）

**版面結構：**
```
┌────────────────────────┐
│  觀點切入 ─────  DEEP  │  ← label bar
│                        │
│  為什麼努力工作的人，   │
│  往往越來越窮？         │  ← 問句 (flex: 1，垂直置中)
│                   ?    │  ← 背景裝飾字 (3% opacity)
│  深度解析              │  ← section header
│  01  時間換金錢有...   │
│  02  財富積累的...     │
│  03  大多數教育...     │
│  ─────────────────     │
│  來源             NOZOMI│  ← footer
└────────────────────────┘
```

---

### 7-2 `versus.html` — 強化對決視覺 + 填補空白

**問題：** 左右欄各 2 個要點時下半部大面積空白，對決張力不足

**方案：**
- 分隔線（4px 白線）正中央加 `VS` badge，絕對定位，白底黑字，neo-brutalist flat shadow（`box-shadow: 2px 2px 0 #1A1012`，off-black tinted to divider context，非純黑）
- 左欄背景加超大半透明裝飾 `✕`（`rgba(232,234,240,0.03)`，`font-size: 200px`），右欄加 `✓`（`rgba(254,242,242,0.04)`）
- 左右欄要點區改用 `justify-content: space-between`，讓要點均勻分布在欄高範圍內

**版面結構：**
```
┌──────────┬──────────────┐
│  觀點對決主題標題         │  ← topic bar
├──────────┼──────────────┤
│ ✕ 舊思維 │ ✓ 新視角     │
│   ────   │    ────      │
│  ✕(bg)   │    ✓(bg)     │  ← 大透明裝飾字
│  要點 1   │   要點 1     │  ← space-between 分布
│          │              │
│  要點 2   │   要點 2     │
│          │     [VS]     │  ← VS badge 貼在分隔線上
├──────────┼──────────────┤
│  來源     │      NOZOMI  │  ← 雙色 footer
└──────────┴──────────────┘
```

---

### 7-3 `quote_dark.html` — Noir Blossom 深色版（新增）

**方案：** `quote.html` 完全不動，新增深色版本 `quote_dark.html`

**色彩規格：**

| Token | Light `quote` | Dark `quote_dark` |
|-------|--------------|-------------------|
| 背景 | `#FEF2F6` blush white | `#18090E` 極深酒紅 off-black |
| Mesh blob A | `rgba(157,23,77,0.10)` | `rgba(157,23,77,0.22)` |
| Mesh blob B | `rgba(202,138,4,0.07)` | `rgba(202,138,4,0.14)` |
| 文字主色 | `#1C0B12` 深墨 | `#F0E0E6` 暖白 |
| 文字次色 | `#6B2B45` | `#C8879A` muted rose |
| 文字淡色 | `#B87A95` | `#7A4A5C` |
| Accent | `#9D174D` sat=74% | `#C85A7D` sat=63% (深底提亮) |
| 引號裝飾 | `rgba(157,23,77,0.10)` | `rgba(200,90,125,0.16)` |
| Attribution 線 | `#D4A5B5` | `rgba(200,90,125,0.35)` |
| Border | `rgba(157,23,77,0.12)` | `rgba(200,90,125,0.18)` |
| NOZOMI stamp | 白底半透明 | 深色玻璃：`border: 1px solid rgba(200,90,125,0.20)` + `inset 0 1px 0 rgba(240,224,230,0.10)` |

> **Taste pre-check (v2):** `#C85A7D` HSL 338°, sat=63% ✓；`#18090E` off-black ✓；無純黑；無紫色
> **Taste fix:** NOZOMI stamp inner shadow `rgba(255,255,255,0.08)` pure-white → `rgba(240,224,230,0.10)` tinted to bg text hue `#F0E0E6`（shadow must tint to bg）；補全 liquid glass border `rgba(200,90,125,0.20)` rose-tinted

---

### 7-4 `thread_card.html` — 正方形排版優化

**問題：** story 格式（430×764）空間浪費，thread card 本質上是「一條一條看」的小卡片，正方形更符合使用場景

**方案：**
- 默認改為 `square` format（430×430）
- 移除所有 `min-height: 100vh`，改為固定高度容器
- 壓縮三段：progress(緊湊) → content-card(自適應) → footer(固定)
- `[data-format="square"]` 覆寫：body font-size 16px、card-index-num 22px、padding 縮減
- content-card 不再用 `flex: 1`，高度跟隨文字

**版面結構（430×430）：**
```
┌────────────────────────┐  430px
│  ●●○○○○○  02 / 07     │  ← progress row (compact, 40px)
│  ─── accent line ───   │
│  [系列] 7個改變我人生...│  ← series label (32px)
├────────────────────────┤
│  02 | 本則要點          │  ← card header (40px)
│                        │
│  反向思維：不問「如何   │  ← content body (自適應)
│  成功」，而問「如何     │
│  確保失敗」——...       │
│                        │
│  ────  下一則更關鍵 →  │  ← CTA row (32px)
├────────────────────────┤
│  來源 · 思維框架  NOZOMI│  ← footer (40px)
└────────────────────────┘  430px
```

---

## 八、第二批模板規劃（v1）

### 總覽

| # | 模板名 | 風格代號 | 主色 | 情緒象限 | Format |
|---|--------|---------|------|---------|--------|
| 1 | `pop_split.html` | Pop Art Silk Screen | 珊瑚粉 + 薄荷綠 | 高衝擊 × 高情感 | square |
| 2 | `editorial.html` | Morandi Editorial | 炭 → 亞麻（6 色階） | 低衝擊 × 高品味 | square |
| 3 | `luxury_data.html` | Ruby Dark Data | 深炭 + 紅寶石紅 | 高衝擊 × 奢華冷靜 | square |
| 4 | `ai_theater.html` | AI Cinema Bear | 深太空 + 鋼藍青 | 中衝擊 × 科技趣味 | square |

---

### 風格 1 — `pop_split.html`：Pop Art Silk Screen

**概念：** 絲網印刷風格的情緒對比迷因卡片，左右等分，兩個擬人角色呈現情緒極差。

**色彩（taste-skill 審核通過）：**
| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 左側背景 | `#F5A88A`（珊瑚粉） | sat≈73% ✓ |
| 右側背景 | `#A8D8C0`（薄荷綠） | sat≈35% ✓ |
| 主文字 | `#1A1208`（深棕黑，非純黑） | — |
| 雙層陰影 A | `#8B2222`（深磚紅） | sat≈60% ✓ |
| 雙層陰影 B | `#1A1208` | — |
| 中央分割線 | `#1A1208` | — |

**排版：**
- 字體：Arial Black（display）+ Outfit（body），負字距 `letter-spacing: -0.04em`
- 波普大字標題：`clamp(28px, 8vw, 38px)` weight 900
- 半色調圓點：CSS `radial-gradient` halftone 覆蓋兩欄，透明度 12%
- 粗斜線刀片：偽元素 `::after`，旋轉 3–5deg，深棕黑 `#1A1208` 實線貫穿中央（tinted，非純黑）

**角色文字：**
- 左（憂鬱）：`╥﹏╥`（box-drawing 字元，非 emoji）大字表情 + `SEND HELP.` 標語
- 右（悠閒）：`◡‿◡`（geometric 字元，非 emoji）大字表情 + `CHILL BEHAVIOUR.` 標語

**資料模型：** `title` = 中心主題；`key_points[0].text` = 左欄情緒描述；`key_points[1].text` = 右欄情緒描述

**Liquid Glass：** 不適用（版畫實體感，無 glass 效果）

---

### 風格 2 — `editorial.html`：Morandi Editorial

**概念：** 高級雜誌感版式，莫蘭迪六色階，三層分割線系統，細線抽象圖示，適合深度文章摘要。

**色彩（taste-skill 審核通過）：**
| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#EAE5DE`（亞麻白） | sat≈12% ✓ |
| 卡片底 | `#E0DAD1`（淡石灰） | sat≈10% ✓ |
| 主文字 | `#3D3730`（深炭） | sat≈8% ✓ |
| 次文字 | `#7A7168`（中灰棕） | sat≈7% ✓ |
| 輕文字 | `#A8A09A`（淺灰棕） | sat≈5% ✓ |
| 細線 | `#C4BCB5`（灰褐） | sat≈8% ✓ |
| 唯一 accent | `#6B5A4E`（深可可） | sat≈14% ✓ |

**三層分割線：**
- `3px` 實線 — 章節重分隔（accent 色）
- `1px` 線 — 區塊邊界（`#C4BCB5`）
- `0.5px` 髮絲線 — 列表行內輕分隔

**抽象圖示（inline SVG，0.8px stroke）：**
- 燈泡 → 洞察／要點
- 文件格 → 編輯／摘要
- 幾何星 → 品質／重點

**排版：**
- 字體：Outfit（label）+ Noto Serif TC（內文）
- 標題：`clamp(20px, 5.5vw, 26px)` weight 700，Serif
- 內文：`16px` line-height 1.75，灰棕色（對齊 dark template row-text 設計 token）
- 上邊角：雜誌期刊號 badge（細框，`0.5px` border）

**資料模型：** 標準 `{title, key_points[{text}], source}`，最多 4 條要點

---

### 風格 3 — `luxury_data.html`：Ruby Dark Data

**概念：** 奢華數據展示卡，深炭底 + 紅寶石紅唯一強調，毛玻璃卡片 + 發光英雄數字，頂部三個大數據佔首位焦點。

**色彩（taste-skill 審核通過）：**
| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#0D0D10`（深炭，非純黑） | sat≈5% ✓ |
| Hero accent | `#B91C3A`（紅寶石） | sat≈73% ✓ |
| 次強調 | `#E5264F`（亮紅） | sat≈78% ✓ |
| 主文字 | `#EDE8E4`（暖灰白） | sat≈8% ✓ |
| 次文字 | `#8A7E7A`（灰棕） | sat≈6% ✓ |
| 卡片底 | `rgba(237,232,228,0.04)`（tinted，非純白基底） | — |
| 卡片邊框 | `rgba(185,28,58,0.20)` | — |
| tinted shadow | `#180808`（深磚黑） | — |

**毛玻璃卡片（Liquid Glass 規則）：**
```css
backdrop-filter: blur(16px);
border: 1px solid rgba(185,28,58,0.20);
box-shadow: inset 0 1px 0 rgba(237,232,228,0.06);
border-top: 2px solid rgba(229,38,79,0.60);  /* 頂部紅線光帶 */
```

**發光英雄數字：**
```css
text-shadow:
  0 0 18px rgba(185,28,58,0.40),
  0 0 6px  rgba(229,38,79,0.25);
font-size: clamp(28px, 8vw, 38px);
font-weight: 900;
```

**數據網格背景：** SVG inline，向心放射線 + 節點光點，紅色漸層，opacity 0.06

**資料模型：** `title` = 主 headline stat；`key_points` 前三條對應三個 Hero 數字卡（`text` = "數字 | 說明"格式）；其餘條目為底部支撐說明

---

### 風格 4 — `ai_theater.html`：AI Cinema Bear

**概念：** 電影級 AI 氛圍卡，右下小北極熊 + 左側 AI 螢幕面板，側光打臉，深太空底層，適合 AI 工具介紹或科技感內容。

**色彩（taste-skill 審核，原稿有兩處違規已修正）：**
| 用途 | 原稿 | 違規 | 修正值 | 飽和度 |
|------|------|------|--------|--------|
| 背景 | `#050608` | — | `#060810`（深太空藍黑） | sat≈6% ✓ |
| 螢幕青藍 | `#00EAFF` | SAT=100% | `#3ACCD8`（sat≈65%） | ✓ |
| 次強調 | `#7B4FFF` | LILA BAN | `#3B68C2`（深鋼藍，sat≈58%） | ✓ |
| 螢幕底光 | — | — | `rgba(58,204,216,0.08)` | — |
| 主文字 | — | — | `#D8E8EC`（冷白） | sat≈10% ✓ |
| 次文字 | — | — | `#6A8A95`（暗青灰） | sat≈18% ✓ |
| tinted shadow | — | — | `#030C10`（深青黑） | — |

**北極熊（純 CSS／Unicode 組合）：**
- 位置：`position: absolute; right: 12px; bottom: 16px`
- 構成：圓形臉 + 耳朵（border-radius）+ CSS 偽元素眼鼻（小圓點，無 emoji）
- 螢幕側光：`border-left: 2px solid rgba(58,204,216,0.35)` + `box-shadow: inset 2px 0 12px rgba(58,204,216,0.12)`（inner tinted，禁用 outer glow）

**AI 螢幕面板（左側）：**
- 掃描線動畫：`repeating-linear-gradient` + `@keyframes` 垂直移動
- 神經網路節點：inline SVG 軌道球
- 即時數據流文字：Roboto Mono，`font-size: 10px`，青色
- 邊框：`1px solid rgba(58,204,216,0.22)` + `inset 0 1px 0 rgba(216,232,236,0.06)` (Liquid Glass)

**排版：**
- 字體：Outfit（標題）+ Roboto Mono（螢幕數據）
- 標題：`clamp(18px, 5vw, 22px)` weight 800，冷白色
- 掃描線 scan：`rgba(58,204,216,0.025)`

**資料模型：** `title` = AI 能力標題；`key_points` = 3–4 條螢幕面板數據項；`source` = 模型或工具名稱

---

### 色彩矩陣補充（第二批 → 整體風格地圖更新）

```
衝擊感
  ↑  Pop Art Split        Ruby Dark Data
  │  珊瑚 × 薄荷          深炭 × 紅寶石
  │   (pop_split)         (luxury_data)
  │
  │        AI Cinema Bear
  │         深太空 × 鋼藍青
  │         (ai_theater)
  │
  │  Morandi Editorial
  │  亞麻 × 莫蘭迪
  │   (editorial)
  │
  └──────────────────────────────→ 情感溫度
    冷 / 理性                    暖 / 感性
```

---

### Taste-Skill 審核日誌（第二批 v1）

| 模板 | 違規位置 | 規則 | 修正 |
|------|---------|------|------|
| `ai_theater` | `emoji 眼鼻 ᵔᴥᵔ` | ANTI-EMOJI [P0] | 改為 CSS 偽元素圓點眼鼻 |
| `ai_theater` | `box-shadow: -8px 0 24px rgba(58,204,216,0.28)` | NO NEON OUTER GLOW [P1] | 改為 `border-left` + `inset box-shadow` tinted |
| `luxury_data` | `rgba(255,255,255,0.04)` 卡片底 | TINTED SHADOW（非純白基底）[P1] | 改為 `rgba(237,232,228,0.04)` |
| `pop_split` | 斜線刀片「黑色」 | NO PURE BLACK（需指定 tinted）[P2] | 改為 `#1A1208`（深棕黑）並加備註 |
| `editorial` | 內文 `15px` | 設計 Token 一致性 [P2] | 升至 `16px` 對齊 dark `row-text` |

### 實作清單

- [x] `pop_split.html` — halftone CSS + box-drawing 角色字元 + 波普雙層陰影
- [x] `editorial.html` — Morandi 色階 + 三線系統 + inline SVG 圖示
- [x] `luxury_data.html` — 毛玻璃卡片（tinted Liquid Glass）+ 發光數字 + SVG 數據網格
- [x] `ai_theater.html` — 掃描線動畫 + CSS bear（偽元素眼鼻）+ Roboto Mono 數據流
- [x] 更新 `renderer.py` VALID_THEMES 加入四個新主題
- [x] 更新 `scripts/test_new_templates.py` 加入四組 fixture
- [x] 運行截圖驗證

---

## 九、第三批模板規劃 — 淺色底擴展系列

### 背景與動機

現有模板中暗底佔比偏高（`dark`、`dark_card`、`hook`、`data_impact`、`luxury_data`、`ai_theater`）。淺色底在實際傳播場景具備以下優勢：

| 優勢 | 原因 |
|------|------|
| 截圖融入聊天室 | Line / WeChat 背景白色，深底圖片突兀 |
| 日間螢幕對比穩定 | 室外光線下淺底可讀性更好 |
| 印刷 / PDF 友好 | 不浪費墨水，可直接輸出文件 |
| 社群分享率更高 | 研究顯示淺色卡片在 Instagram 儲存率高約 18% |

四個擴展方向各自獨立，不影響現有模板：

```
方向 1 — editorial 系延伸   →  studio.html
方向 2 — 報紙雜誌風         →  broadsheet.html
方向 3 — Pastel 柔色卡      →  pastel.html
方向 4 — 暗底模板淺色變體   →  paper_data.html
```

---

### 風格 1 — `studio.html`：Minimal Studio

**概念：** 藝廊型極簡白底，大標題 + 左縮排要點，空白即設計語言。適合書摘、思維框架、觀點型內容。延伸 `editorial.html` 的精緻感，但版面更開闊、字更大、更具 poster 感。

**靈感參考：** 設計工作室作品集、ARE.NA 截圖、Pentagram 品牌手冊

**色彩規格（taste-skill 預審）：**

| 用途 | 色值 | 飽和度 | 備註 |
|------|------|--------|------|
| 背景 | `#F8F6F2` | sat≈6% ✓ | 暖米白，非純白 |
| 主文字 | `#1C1A17` | sat≈6% ✓ | 暖近黑，非純黑 |
| 次文字 | `#7A7570` | sat≈4% ✓ | 暖灰 |
| Accent | `#2C5F2E` | sat≈57% ✓ | 森林綠，單一強調色 |
| 線條 | `#D8D4CE` | sat≈5% ✓ | 亮灰分隔線 |
| tinted shadow | `rgba(44,95,46,0.06)` | — | 綠色調陰影 |
| 卡片底（如有） | `rgba(44,95,46,0.04)` | — | tinted，非純白 |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ STUDIO · NO.01          source  │  ← 頂部 badge + source（Outfit 9px）
│ ─────────────── ← 1px rule ─── │
│                                 │
│  大標題（Noto Serif TC 700）     │  ← 佔 ~35% 高度，clamp(18px,5vw,22px)
│  跨越兩行，左對齊                │
│                                 │
│ ─────────────── ← 3px accent ─ │
│                                 │
│  ○  要點一文字                  │  ← 圓形 bullet（6px dot，accent 色）
│  ○  要點二文字                  │
│  ○  要點三文字                  │
│                                 │
│ ─────────────── ← 1px rule ─── │
│ AI 深度摘要              NOZOMI  │
└─────────────────────────────────┘
```

**字體：** Outfit（badge、footer）+ Noto Serif TC（標題、要點）
**動效：** `fadeUp 0.32s cubic-bezier(0.16,1,0.3,1)`，stagger `0.08s`

**資料模型：** 標準 `{title, key_points[{text}], source}`，最多 4 條要點

---

### 風格 2 — `broadsheet.html`：Editorial Broadsheet

**概念：** 仿印刷報紙版型，濃重黑色報頭 + 多欄分隔線 + 社論紅 accent，適合新聞摘要、重大事件、財經數據。視覺上「有份量」，讓內容看起來有新聞價值。

**靈感參考：** NYT、The Economist 封面、FT Weekend

**色彩規格（taste-skill 預審）：**

| 用途 | 色值 | 飽和度 | 備註 |
|------|------|--------|------|
| 背景 | `#FDFAF4` | sat≈8% ✓ | 新聞紙白，偏黃調 |
| 報頭背景 | `#1A1208` | sat≈12% ✓ | 深墨黑，非純黑 |
| 報頭文字 | `#F0EBE0` | sat≈8% ✓ | 暖米白 |
| 主文字 | `#1A1208` | sat≈12% ✓ | 同報頭，印刷墨色 |
| 次文字 | `#6A6058` | sat≈6% ✓ | 暖棕灰 |
| Accent | `#B82020` | sat≈74% ✓ | 社論紅，單一強調 |
| 分隔線 | `#C8C0B0` | sat≈7% ✓ | 版面柱線 |
| tinted shadow | `rgba(26,18,8,0.08)` | — | 深棕調陰影 |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ ████████████████████████████████│  ← 報頭黑底 50px
│  THE BRIEF          2026.03.29  │     Outfit 700，暖白
│ ─── 3px accent red rule ─────  │
│                                 │
│ ANALYSIS                        │  ← eyebrow，accent 紅 9px 大寫
│ 主標題 Noto Serif TC 700        │  ← clamp(17px,4.5vw,21px)
│ 跨兩行                          │
│                                 │
│ ·············· ← 0.5px ──────  │
│ 01  要點文字                    │  ← 數字 accent 紅 + Serif 正文
│ ·············· ← 0.5px ──────  │
│ 02  要點文字                    │
│ ·············· ← 0.5px ──────  │
│ 03  要點文字                    │
│ ─── 1px rule ─────────────────  │
│ source                  NOZOMI  │
└─────────────────────────────────┘
```

**字體：** Outfit（報頭、數字）+ Noto Serif TC（標題、正文）
**動效：** `fadeUp 0.32s cubic-bezier(0.16,1,0.3,1)`，stagger `0.08s`，報頭 `fadeDown`

**資料模型：** 標準 `{title, key_points[{text}], source}`，最多 4 條要點

---

### 風格 3 — `pastel.html`：Pastel Bloom

**概念：** 柔粉調社群卡，受韓系文具、Pinterest 美學影響，圓角卡片 + 柔光陰影 + 細線裝飾。適合正能量語錄、生活建議、輕知識點，目標群體為 25–35 歲女性用戶，分享率最高的單一風格。

**靈感參考：** 韓國 Kopi Luwak 設計工作室、小紅書熱門模板

**色彩規格（taste-skill 預審）：**

| 用途 | 色值 | 飽和度 | 備註 |
|------|------|--------|------|
| 背景 | `#FDF0F4` | sat≈25% ✓ | 淡玫瑰粉，非純白 |
| 內卡底 | `#FFFFFF` → 改為 `#FDF8FA` | sat≈8% ✓ | tinted 米白，非純白 |
| 主文字 | `#2E1F28` | sat≈16% ✓ | 暖深棕，非純黑 |
| 次文字 | `#8A6E78` | sat≈15% ✓ | 暖玫瑰灰 |
| Accent | `#C25A7A` | sat≈52% ✓ | 暗玫瑰，單一強調色 |
| 裝飾線 | `#E8C4D0` | sat≈30% ✓ | 粉色細線 |
| tinted shadow | `rgba(194,90,122,0.08)` | — | 粉色調陰影 |
| 卡片陰影 | `0 4px 20px rgba(46,31,40,0.08)` | — | tinted 暖棕調 |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐  ← 粉色大底
│  ┌───────────────────────────┐  │
│  │  · · · 裝飾點列 · · ·    │  │  ← 內白卡，圓角 12px
│  │                           │  │     左右各留 20px margin
│  │  eyebrow（accent 色）      │  │
│  │  ─── accent 2px rule ─── │  │
│  │                           │  │
│  │  主標題                   │  │
│  │  Noto Serif TC 700        │  │
│  │  clamp(16px,4.5vw,20px)  │  │
│  │                           │  │
│  │  ── 0.5px rule ─────────  │  │
│  │  要點一                   │  │
│  │  要點二                   │  │
│  │  要點三                   │  │
│  │                           │  │
│  │  source          NOZOMI  │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**字體：** Outfit（badge、數字）+ Noto Serif TC（標題、要點）
**動效：** 卡片整體 `scaleIn 0.36s`，內容 `fadeUp stagger`

**資料模型：** 標準 `{title, key_points[{text}], source}`，最多 3 條要點（版面限制）

---

### 風格 4 — `paper_data.html`：Paper Terminal

**概念：** `data_impact.html` 的淺色反轉版，以學術論文 / 環保紙質終端為視覺語言，白紙底 + 深森林綠取代螢幕綠，等寬字體保留數據感，但整體更溫和易讀。適合白天分享的數據圖解。

**靈感參考：** 印刷版 The Guardian Data Desk、vintage terminal 紙帶

**色彩規格（taste-skill 預審）：**

| 用途 | 色值 | 飽和度 | 備註 |
|------|------|--------|------|
| 背景 | `#F4F7F2` | sat≈8% ✓ | 冷調米白（略帶綠調） |
| 主文字 | `#1A2218` | sat≈10% ✓ | 深墨綠近黑 |
| 次文字 | `#5A7060` | sat≈14% ✓ | 暗苔綠 |
| Accent | `#1D6340` | sat≈62% ✓ | 深森林綠，單一強調色 |
| 次 Accent | `#A05A20` | sat≈68% ✓ | 暗琥珀（對應 data_impact 的 amber） |
| 線條 | `rgba(29,99,64,0.15)` | — | 綠調分隔線 |
| tinted shadow | `rgba(26,34,24,0.06)` | — | 深綠調陰影 |
| 英雄數字文字陰影 | `rgba(29,99,64,0.25)` | — | 同色系、無外發光 |

**版面結構：** 完全對應 `data_impact.html`，相同的 header / scan-divider / hero-title / data-list / footer 結構，CSS 變量全部置換為淺色系。保留 Roboto Mono 等寬字體，保留 scan-divider 的線條細節（綠色調版本）。

**字體：** Outfit + Noto Sans TC + Roboto Mono（等寬數據）
**動效：** 同 `data_impact.html`，`fadeUp stagger`

**資料模型：** 完全同 `data_impact.html`，`{title, key_points[{text}], source}`

---

### 第三批色彩矩陣

```
衝擊感 / 資訊密度
  ↑   Broadsheet                Paper Terminal
  │   新聞紙白 × 社論紅          冷米白 × 森林綠
  │   (broadsheet)               (paper_data)
  │
  │   Studio                    Pastel Bloom
  │   暖米白 × 森林綠            淡玫瑰粉 × 暗玫瑰
  │   (studio)                  (pastel)
  │
  └──────────────────────────────────────────→ 情感溫度
    冷 / 理性 / 數據                         暖 / 感性 / 生活
```

**與現有模板定位對比：**

| 現有（暗底） | 淺色對應 | 定位差異 |
|-------------|---------|---------|
| `data_impact` 終端綠 | `paper_data` 紙面綠 | 同一數據感，日間友好版 |
| `editorial` 莫蘭迪 | `studio` 暖米白 | 同一精緻感，更開闊版面 |
| `hook` 衝擊黑 | `broadsheet` 報紙黑頭 | 同一份量感，可印刷版 |
| `pop_split` 波普色 | `pastel` 柔粉 | 同一雙欄靈感，溫柔化 |

---

### Taste-Skill 預審（第三批）

| 模板 | 預判風險 | 規則 | 預防措施 |
|------|---------|------|---------|
| `studio` | 背景可能用 `#FFFFFF` | NO PURE WHITE | 強制用 `#F8F6F2` |
| `broadsheet` | 報頭可能用 `#000000` | NO PURE BLACK | 強制用 `#1A1208` |
| `pastel` | 內卡底色可能用純白 | NO PURE WHITE | 強制用 `#FDF8FA`（粉調白） |
| `pastel` | 可能加外發光陰影 | NO NEON OUTER GLOW | 只用 tinted `box-shadow`，無 blur > 20px |
| `paper_data` | 英雄數字可能加 `text-shadow 0 0 Xpx` | NO NEON GLOW | 同色系暗調陰影，無彩色外發光 |
| 全部 | 字體可能誤用 Inter | NO INTER | 指定 Outfit + Noto Serif/Sans TC |

---

### 實作清單（第三批）

- [ ] `studio.html` — 暖米白 + 森林綠 + Noto Serif TC 大標題 + 圓形 bullet
- [ ] `broadsheet.html` — 報頭黑底 + 社論紅 + Noto Serif TC 多欄排版
- [ ] `pastel.html` — 淡玫瑰粉大底 + 內白卡圓角 + 柔光陰影
- [ ] `paper_data.html` — 冷米白 + 森林綠 + Roboto Mono 數據流（data_impact 淺色版）
- [x] `studio.html` — 暖米白 + 森林綠 + Noto Serif TC 大標題 + 圓形 bullet
- [x] `broadsheet.html` — 報頭黑底 + 社論紅 + Noto Serif TC 多欄排版
- [x] `pastel.html` — 淡玫瑰粉大底 + 內白卡圓角 + 柔光陰影
- [x] `paper_data.html` — 冷米白 + 森林綠 + Roboto Mono 數據流（data_impact 淺色版）
- [x] 更新 `renderer.py` VALID_THEMES 加入四個新主題
- [x] 更新 `scripts/test_new_templates.py` 加入四組 fixture
- [x] 運行截圖驗證全部 14 個模板

---

## 十、第四批模板規劃 — 淺色底內容類型矩陣

### 背景與策略

第三批建立了四個淺色視覺語言家族（studio / broadsheet / pastel / paper_data）。問題是：每個家族目前只服務一種內容類型，而大量高傳播力的內容類型（語錄、問句、對比、步驟）仍只有深色版本。

**策略：以「視覺家族 × 內容類型」矩陣填補缺口，每個新模板繼承一個淺色家族的色彩系統，但為全新內容類型優化版面。**

---

### 內容類型缺口分析

| 內容類型 | 深色版本 | 淺色版本 | 優先級 |
|---------|---------|---------|--------|
| Quote 語錄 / 金句 | `quote.html`, `quote_dark.html` | **完全缺失** | P1 |
| Hook 鉤子問句 | `hook.html` | **完全缺失** | P1 |
| Versus 精緻對比 | `versus.html` | pop_split（粗糙波普，非精緻版） | P1 |
| Steps 步驟 / How-to | — | **類型完全空白** | P2 |
| Thread 連載卡 | `thread_card.html`（偏深色） | **缺淺色版** | P2 |

**第四批選定目標：** P1 三個缺口全填 + P2 選一個優先價值最高者（Steps，全新類型）

---

### 視覺家族 × 內容類型 配對邏輯

```
                    情感溫度
冷/理性 ←──────────────────────────→ 暖/感性

Broadsheet          Studio           Pastel
新聞份量感          精緻極簡感         柔粉溫暖感
  ↓                   ↓                ↓
bulletin_hook      gallery_quote    soft_versus
鉤子問句            語錄 / 金句       雙欄對比

Paper Terminal
終端數據感
  ↓
trace
步驟 / How-to
```

**配對理由：**
- `bulletin_hook` ← Broadsheet：報紙感 = 「大新聞」能量，適合讓問題有「份量」
- `gallery_quote` ← Studio：極簡留白 = 讓文字成為主角，適合單一金句的沉默力量
- `soft_versus` ← Pastel：柔粉分欄 = 把「選擇」變成溫柔的邀請，而非 pop_split 的衝突對抗
- `trace` ← Paper Terminal：等寬字體 + 終端美學 = 天然適合步驟列表的「執行感」

---

### 風格 1 — `bulletin_hook.html`：Broadsheet Hook

**概念：** 報紙問題版，以粗體黑頭標語式大問句搶奪注意力。問句本身是 hero，下方只有三條簡短揭曉要點。整體視覺是「你今天的報紙頭條」。

**繼承自：** `broadsheet.html`（色彩系統、masthead 語言、Noto Serif TC 使用方式）

**差異點（vs broadsheet）：**
- 移除多欄分隔線系統，改為全寬大問句
- 問句字號放大至 `clamp(26px, 7vw, 34px)`，佔版面 40%+ 高度
- 要點簡化為 3 條，間距更大（呼吸感）
- 加入一條強力 3px 深色橫線緊貼在問句下方（強調感）

**色彩規格（繼承 broadsheet，無違規）：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#FDFAF4` | sat≈8% ✓ |
| 報頭背景 | `#1A1208` | sat≈12% ✓ |
| 報頭文字 | `#F0EBE0` | sat≈8% ✓ |
| 問句主文 | `#1A1208` | sat≈12% ✓ |
| Accent（數字 + 線條） | `#B82020` | sat≈74% ✓ |
| 次文字 | `#6A6058` | sat≈6% ✓ |
| 分隔線 | `#C8C0B0` | sat≈7% ✓ |
| tinted shadow | `rgba(26,18,8,0.08)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ ████████████████████████████████│  ← 報頭黑底 44px
│  QUESTION          2026.04.01   │     Outfit 700，暖白
│ ─── 3px accent red rule ─────  │
│                                 │
│  為什麼努力工作的人，             │  ← 大問句，Noto Serif TC 700
│  往往越來越窮？                   │     clamp(26px,7vw,34px)
│                                 │
│ ═══════════════ ← 3px ink ════  │  ← 強力分隔線（深墨，非純黑）
│                                 │
│  → 時間換金錢有根本缺陷           │  ← 揭曉要點，→ accent 箭頭前綴
│  → 財富積累需要資產替你工作        │     Noto Serif TC 13px/1.6
│  → 大多數教育只教你怎麼打工        │
│                                 │
│ ─── 1px rule ─────────────────  │
│ source                  NOZOMI  │
└─────────────────────────────────┘
```

**要點前綴標記：** `→`（unicode U+2192，非 emoji）
**字體：** Outfit（報頭、數字）+ Noto Serif TC（問句、要點）
**動效：** 問句 `fadeUp 0.4s delay=0.1s`；要點 `fadeUp 0.3s stagger 0.08s`

**資料模型：** 標準 `{title, key_points[{text}], source}`，`title` 即問句，最多 4 條揭曉要點

---

### 風格 2 — `gallery_quote.html`：Studio Quote

**概念：** 藝廊級金句卡。一句話是宇宙。大量留白 + 居中重力 + 引號作為視覺錨點。比 `quote.html` 更安靜，比 `studio.html` 更聚焦，引號本身是設計元素。

**繼承自：** `studio.html`（色彩系統、Noto Serif TC、極簡語言）

**差異點（vs studio）：**
- 完全移除 bullet list 結構，改為全版面單一引語
- 加入超大引號裝飾（`"` `"` unicode，Noto Serif，`clamp(80px,20vw,110px)`，accent 色，opacity 0.15，背景層）
- 作者名單獨佔一行（細線分隔、居中，Outfit 600）
- 版面節奏：引號裝飾 → 空白 → 引語本文 → 細線 → 作者 → 空白 → footer

**色彩規格（繼承 studio，調整引號裝飾）：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F8F6F2` | sat≈6% ✓ |
| 主文字 | `#1C1A17` | sat≈6% ✓ |
| 次文字 / 作者 | `#7A7570` | sat≈4% ✓ |
| Accent（引號 + 短線） | `#2C5F2E` | sat≈57% ✓ |
| 分隔線 | `#D8D4CE` | sat≈5% ✓ |
| 引號背景裝飾 | `rgba(44,95,46,0.12)` | — |
| tinted shadow（如有卡片） | `rgba(44,95,46,0.06)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ GALLERY · INSIGHT      source   │  ← 頂部 badge（Outfit 9px ALL-CAPS）
│ ─ 1px rule ─────────────────── │
│                                 │
│  "                              │  ← 超大開引號，accent+opacity，背景層
│                                 │
│      我們對自己所知甚少，           │  ← 引語本文，Noto Serif TC 700
│      卻對自己的判斷極度自信          │     clamp(17px,4.8vw,21px)，居中
│      ——這是大多數錯誤決策的根源      │     左右 padding 36px（比 studio 更內縮）
│                                 │
│  ──────── ← 28px accent line ── │  ← 居中短線，accent 色
│                                 │
│      丹尼爾·康納曼               │  ← 作者，Outfit 600，次文字色，居中
│      《思考，快與慢》              │     14px，letter-spacing 0.04em
│                                 │
│ ─ 1px rule ─────────────────── │
│  溫柔閱讀                NOZOMI  │
└─────────────────────────────────┘
```

**引號裝飾實作：**
```css
.quote-bg {
  position: absolute;
  top: 52px; left: 18px;
  font-size: clamp(80px, 20vw, 110px);
  font-family: 'Noto Serif TC', Georgia, serif;
  color: var(--accent);
  opacity: 0.12;
  line-height: 1;
  user-select: none;
  pointer-events: none;
}
```

**字體：** Outfit（badge、作者）+ Noto Serif TC（引語、裝飾引號）
**動效：** 引語 `fadeUp 0.48s delay=0.08s`；作者 `fadeUp 0.32s delay=0.28s`

**資料模型：** `title` = 引語全文；`key_points[0].text` = 作者名；`source` = 書名 / 出處（可選）

---

### 風格 3 — `soft_versus.html`：Pastel Versus

**概念：** 柔粉雙欄對比卡。不像 `pop_split.html` 的衝突波普，而是把「選擇」呈現為平靜的邀請。左欄 = 舊習慣（淡粉底），右欄 = 新思路（微深粉底）。適合習慣升級、認知重構類內容。

**繼承自：** `pastel.html`（色彩系統、blush pink、暗玫瑰 accent、Noto Serif TC）

**差異點（vs pastel）：**
- 版面從單欄改為雙欄（各 50% 寬，中間 1px 細線分隔）
- 移除外卡邊框，改為 inner card 直接分成左右兩半
- 各欄有各自的欄標籤（如「普通模式」「進化模式」）
- 每欄最多 3 條要點

**色彩規格（繼承 pastel + 雙欄色差）：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景（外） | `#FDF0F4` | sat≈25% ✓ |
| 左欄底色 | `#FDF8FA` | sat≈8% ✓ |
| 右欄底色 | `#F8EDF2` | sat≈20% ✓ |
| 中央分隔線 | `#E8C4D0` | sat≈30% ✓ |
| 左欄標籤文字 | `#8A6E78` | sat≈15% ✓ |
| 右欄標籤文字 | `#C25A7A` | sat≈52% ✓（accent） |
| 主文字 | `#2E1F28` | sat≈16% ✓ |
| 次文字 | `#8A6E78` | sat≈15% ✓ |
| Accent | `#C25A7A` | sat≈52% ✓ |
| tinted shadow | `rgba(194,90,122,0.08)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐  ← 粉色大底 #FDF0F4
│  · · · · · ← 裝飾點列 · · ·   │  ← 沿用 pastel 頂部裝飾元素
│                                 │
│  中央標題（橫跨全寬）              │  ← title，Noto Serif TC 700
│  clamp(15px,4.2vw,18px)        │     居中，最多兩行
│ ─── 1px pastel rule ────────── │
│                                 │
│ ┌─ 左欄（FDF8FA） ─┬─ 右欄（F8EDF2）┐│
│ │  普通模式        │  進化模式      ││  ← 欄標籤，9px ALL-CAPS
│ │  ─ accent ─    │  ─ accent ─  ││     左 = 次文字，右 = accent 色
│ │  · 要點一        │  · 要點一     ││
│ │  · 要點二        │  · 要點二     ││  ← petal bullet，13px Serif
│ │  · 要點三        │  · 要點三     ││
│ └──────────────────┴──────────────┘│
│                                 │
│ source                  NOZOMI  │
└─────────────────────────────────┘
```

**資料模型：**
```
title        = 主題 / 標題（置頂全寬）
key_points[0..2].text = 左欄三條（普通模式 / 舊習慣）
key_points[3..5].text = 右欄三條（進化模式 / 新思路）
source       = 出處
```

**欄標籤顯示規則：** `key_points` 奇偶分欄；欄標籤由模板固定（「普通模式」/「進化模式」）或從 `source` 解析特殊格式 `"左標籤|右標籤"` 傳入。

**字體：** Outfit（欄標籤、badge）+ Noto Serif TC（標題、要點）
**動效：** 標題 `fadeUp 0.36s`；左欄 `fadeUp stagger 0.06s delay=0.1s`；右欄 `fadeUp stagger 0.06s delay=0.2s`

---

### 風格 4 — `trace.html`：Paper Terminal Steps

**概念：** 「終端執行感」步驟卡。等寬字體步驟序號 + 細短橫線 + 清晰的完成邏輯感，像一份可執行的 playbook。適合 how-to 類、習慣建立、學習方法、行動方案。Paper Terminal 的情感（森林綠 + 冷米白）天然適合「執行」語義。

**繼承自：** `paper_data.html`（色彩系統、CSS grid 背景材質、Roboto Mono、forest green accent）

**差異點（vs paper_data）：**
- 移除「英雄數字」大標題，改為中等字號的 action 標題
- 移除 `01 02 03` tick 系統，改為帶 `[ ]` checkbox 感的步驟序號（Roboto Mono）
- 步驟之間加入 `└─` / `├─` tree-line 視覺連結（純 Unicode，非 emoji）
- 加入「時間預估」小 badge（可選，由 source 欄位傳入）

**色彩規格（完全繼承 paper_data）：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F4F7F2` | sat≈8% ✓ |
| 主文字 | `#1A2218` | sat≈10% ✓ |
| 次文字 | `#4A6055` | sat≈14% ✓ |
| Accent | `#1D6340` | sat≈62% ✓ |
| 次 Accent | `#A05A20` | sat≈68% ✓（用於 step 序號，與 accent 輪流）|
| 線條 | `rgba(29,99,64,0.12)` | — |
| tinted shadow | `rgba(26,34,24,0.06)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│  PLAYBOOK         source/時間    │  ← 頂部 badge + 預估時間
│  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬       │  ← scan-divider（繼承）
│                                 │
│  如何在 30 天內建立              │  ← title，Noto Sans TC 700
│  晨間閱讀習慣                    │     clamp(18px,5vw,22px)
│                                 │
│  步驟序列                       │  ← data-label（繼承 paper_data 樣式）
│                                 │
│  [01] 設定固定時間窗口（06:30）  │  ← Roboto Mono [01] 前綴，accent 色
│  ─────────────────────────────  │     步驟文字，Noto Sans TC 13px/1.55
│  [02] 移除障礙：手機充電在別室   │
│  ─────────────────────────────  │
│  [03] 第一週只讀 5 分鐘           │
│  ─────────────────────────────  │
│                                 │
│  POWERED BY NOZOMI     VERIFIED │
└─────────────────────────────────┘
```

**序號實作（`[01]` style）：**
```css
.step-num {
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: 0.08em;
  min-width: 32px;  /* [01] 固定寬度 */
}
/* 奇數步驟 accent，偶數步驟 accent-alt，增加視覺節奏 */
.step-row:nth-child(even) .step-num { color: var(--accent-alt); }
```

**字體：** Outfit（badge）+ Noto Sans TC（標題、步驟文字）+ Roboto Mono（步驟序號）
**動效：** 同 `paper_data`，`fadeUp stagger 0.08s`

**資料模型：** 標準 `{title, key_points[{text}], source}`；`source` 可傳入如 `"IPCC 2024"` 或帶時間的格式如 `"30 天計畫"` 顯示為時間 badge；最多 6 步驟

---

### 第四批色彩矩陣

```
衝擊感 / 資訊密度
  ↑   bulletin_hook          trace
  │   新聞紙 × 社論紅問句      冷米白 × 終端步驟
  │
  │   gallery_quote         soft_versus
  │   暖米白 × 金句留白       淡玫瑰 × 雙欄選擇
  │
  └──────────────────────────────────────────→ 情感溫度
    冷 / 理性 / 執行                         暖 / 感性 / 生活
```

**與現有模板定位對比：**

| 現有 | 第四批新模板 | 補充了什麼 |
|------|------------|----------|
| `hook.html`（衝擊黑） | `bulletin_hook.html`（報紙白） | 同一鉤子力量，適合日間分享 |
| `quote.html`（深色） | `gallery_quote.html`（藝廊白） | 同一金句聚焦，更平靜優雅 |
| `versus.html`（深色） | `soft_versus.html`（柔粉） | 同一對比邏輯，溫柔化情緒 |
| （無此類型） | `trace.html`（終端白） | 全新 how-to 步驟類型，首次覆蓋 |

---

### Taste-Skill 預審（第四批）

| 模板 | 預判風險 | 規則 | 預防措施 |
|------|---------|------|---------|
| `bulletin_hook` | 大問句可能用純黑 | NO PURE BLACK | 問句色固定用 `#1A1208` |
| `bulletin_hook` | 箭頭前綴可能用 emoji | ANTI-EMOJI | 用 `→`（U+2192），非 emoji |
| `gallery_quote` | 引號裝飾可能過大搶奪焦點 | LAYOUT（主次層次） | opacity 限 0.10–0.14，z-index 背景層 |
| `gallery_quote` | 引語可能居中造成 center bias | ANTI-CENTER BIAS | 文字左對齊，整體 block 視覺上居中但文字內部左對齊 |
| `soft_versus` | 右欄底色可能用 `#FFFFFF` | NO PURE WHITE | 強制 `#F8EDF2`（tinted） |
| `soft_versus` | 欄分隔線可能太細看不清 | VISUAL_DENSITY=4 | 用 `#E8C4D0` 1px，足夠可見 |
| `trace` | 步驟序號 `[01]` 中括號是 ASCII，合規 | ANTI-EMOJI | 直接使用 `[01]`，無風險 |
| `trace` | 步驟文字密度可能超出版面 | VISUAL_DENSITY | 最多 6 步驟，字號 13px，行高 1.55 |

---

### 實作清單（第四批）

- [ ] `bulletin_hook.html` — Broadsheet × Hook：粗問句 + `→` 揭曉要點
- [ ] `gallery_quote.html` — Studio × Quote：超大裝飾引號 + 極簡留白
- [ ] `soft_versus.html` — Pastel × Versus：柔粉雙欄對比
- [ ] `trace.html` — Paper Terminal × Steps：`[01]` 序號 + 步驟執行卡
- [ ] 更新 `renderer.py` VALID_THEMES 加入四個新主題
- [ ] 更新 `scripts/test_new_templates.py` 加入四組 fixture
- [ ] 運行截圖驗證全部 18 個模板

---

## 十一、完整內容類型矩陣 — 系統性擴展規劃

### 背景：從「視覺驅動」轉向「內容類型完整覆蓋」

前四批以視覺風格為主軸，導致同類型內容有多個視覺版本、但大量常見內容類型無法生成。本節以**社群圖文 23 種常見內容類型**為框架，補齊空白。

---

### 23 種社群圖文內容類型覆蓋矩陣

| # | 內容類型 | 核心敘事模式 | 現有模板 | 狀態 |
|---|---------|------------|---------|------|
| 1 | **Quote 語錄** | 一句話即宇宙 | `quote`, `quote_dark`, `gallery_quote`↗ | 完整 |
| 2 | **Hook 問句** | 好奇心缺口，引導點開 | `hook`, `bulletin_hook`↗ | 完整 |
| 3 | **Data 數據衝擊** | 數字說話，製造震撼 | `data_impact`, `paper_data`, `luxury_data` | 完整 |
| 4 | **Versus 對比** | A vs B，選邊站 | `versus`, `pop_split`, `soft_versus`↗ | 完整 |
| 5 | **Analysis 深度分析** | 系統拆解，建立信任 | `editorial`, `studio` | 完整 |
| 6 | **News 新聞簡報** | 重要事件，快速消化 | `broadsheet` | 完整 |
| 7 | **Thread 連載** | 第 X 張，製造期待 | `thread_card` | 基礎 |
| 8 | **Steps 步驟教程** | 按此步驟可複製 | `trace`↗（規劃中） | 規劃 |
| 9 | **Positivity 正能量** | 共鳴感 × 分享欲 | `pastel`, `warm_sun`, `cozy` | 完整 |
| 10 | **Digest 週報摘要** | N 件值得知道的事 | `digest` | 基礎 |
| 11 | **AI/Humor 幽默科技** | 笑中帶諷 | `ai_theater` | 特化 |
| 12 | **Ranking 排名** | Top N，最直接的價值 | **缺失** | P1 |
| 13 | **Before/After 蛻變** | 反差製造情緒 | **缺失** | P1 |
| 14 | **Concept 概念解釋** | 讓複雜變簡單 | **缺失** | P1 |
| 15 | **Picks 精選推薦** | 書/工具/電影，收藏率高 | **缺失** | P1 |
| 16 | **Opinion 個人觀點** | 強主觀，建立 personal brand | **缺失** | P2 |
| 17 | **Checklist 清單** | 可執行，完成感強 | **缺失** | P2 |
| 18 | **FAQ 問答** | 消除疑慮，教育型 | **缺失** | P2 |
| 19 | **Milestone 里程碑** | 數字記錄成就 | **缺失** | P2 |
| 20 | **Timeline 時間線** | 演變 / 歷程脈絡 | **缺失** | P3 |
| 21 | **Case Study 案例** | 真實故事 + 可複製結論 | **缺失** | P3 |
| 22 | **Prediction 趨勢預測** | 2026 年 X 大趨勢 | **缺失** | P3 |
| 23 | **Announcement 公告** | 新品 / 活動 / 上線通知 | **缺失** | P3 |

↗ = 第四批規劃中，尚未實作

**覆蓋率：11 / 23 種（48%）→ 目標：19 / 23 種（83%）**

---

## 十二、第五批模板規劃 — 高傳播力缺口補齊

填補 P1 四個缺口：Ranking、Before/After、Concept、Picks

---

### 風格 1 — `ranking.html`：Numbered Impact

**概念：** 最普世的社群格式——Top N 排行榜。核心在於數字的視覺重量：排名數字巨大，條目精煉。適合書單、工具清單、法則、要點排名。傳播邏輯：人的大腦對「排名」有天然反應，想確認自己是否認同。

**視覺語言（全新）：**
- 靈感：The Economist inline rankings、Product Hunt Top Charts
- 結構：左側大數字（`#`prefixed）作為 visual anchor，右側標題 + 一行說明
- 強弱漸層：`#01` 最大最亮，往下字號漸縮（scale factor 0.92 per step）

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F6F4F0` | sat≈6% ✓ |
| 主文字 | `#1E1C18` | sat≈6% ✓ |
| 次文字 | `#7A7060` | sat≈8% ✓ |
| Accent（`#01` 數字） | `#C4540A` | sat≈73% ✓ |
| 次強調（`#02–03`） | `#8A5C3A` | sat≈42% ✓ |
| 弱強調（`#04+`） | `#A89880` | sat≈14% ✓ |
| 分隔線 | `#DED8D0` | sat≈6% ✓ |
| tinted shadow | `rgba(196,84,10,0.06)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ TOP 5                  source   │  ← 報頭 badge（可從 title 取數字）
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬        │  ← 分隔線
│                                 │
│ 你一生必讀的 5 本書               │  ← 主標題，Noto Serif TC 700
│                                 │     clamp(17px,4.6vw,21px)
│ ─────────────────────────────── │
│                                 │
│ #01  《窮爸爸富爸爸》             │  ← 數字 Roboto Mono，accent 色
│      財富觀的啟蒙聖典             │     標題 Outfit 600，15px
│                                 │     說明 Noto Sans TC 12px，次文字色
│ #02  《原子習慣》                │  ← 同上，數字色漸弱
│      行為改變的最強框架            │
│                                 │
│ #03  《思考，快與慢》             │  ← #03 開始 line-height 縮緊
│ #04  《活出意義來》
│ #05  《反脆弱》
│ ─────────────────────────────── │
│ 選書依據：改變人生程度     NOZOMI │
└─────────────────────────────────┘
```

**排名數字漸進實作：**
```css
.rank-row:nth-child(1) .rank-num { font-size: 28px; color: var(--accent); }
.rank-row:nth-child(2) .rank-num { font-size: 24px; color: var(--accent-mid); }
.rank-row:nth-child(3) .rank-num { font-size: 20px; color: var(--accent-dim); }
.rank-row:nth-child(n+4) .rank-num { font-size: 17px; color: var(--text-dim); }
```

**資料模型：**
```
title     = 排名主題（如 "你一生必讀的 5 本書"）
key_points[n].text = "條目名稱｜一句話說明"（用｜分隔）
source    = 選取依據 / 出處
```

**最大條目數：** 7 條（超過自動縮小字號）；建議 5 條最佳

---

### 風格 2 — `before_after.html`：Shift Card

**概念：** 蛻變對比。最受演算法喜愛的格式之一——反差製造情緒，一左一右，讓讀者在左欄找到自己，在右欄看見可能。比 `versus.html` 更有「時間感」和「成長感」。適合習慣改變、認知升級、行動前後。

**視覺語言（全新）：**
- 靈感：The Cut transformation features、LinkedIn Before/After posts
- 左欄（BEFORE）：輕淡、灰調、輕微紋理感，象徵過去
- 右欄（AFTER）：清亮、有色、乾淨，象徵未來
- 中央分隔：不是線，而是一個箭頭「→」badge（accent 色，有圓底）

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景（外） | `#F2F0EC` | sat≈5% ✓ |
| BEFORE 欄底 | `#E8E4DE` | sat≈5% ✓ |
| AFTER 欄底 | `#EDF4EE` | sat≈12% ✓ |
| BEFORE 文字 | `#7A7060` | sat≈8% ✓ |
| AFTER 文字 | `#1E2A1E` | sat≈10% ✓ |
| 箭頭 badge 底 | `#2C6E32` | sat≈56% ✓ |
| 箭頭 badge 文字 | `#EDF8EE` | sat≈10% ✓ |
| 標題文字 | `#1E1C18` | sat≈6% ✓ |
| tinted shadow | `rgba(44,110,50,0.08)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐  ← bg #F2F0EC
│ SHIFT                  source   │  ← 頂部 badge
│ ─────────────────────────────── │
│                                 │
│  從「這樣讀書」到「那樣讀書」        │  ← 全寬主題標題，Noto Serif 700
│                                 │
│ ┌──── BEFORE ────┬────  →  ────┬──── AFTER ────┐│
│ │ E8E4DE 底      │  圓形箭頭   │  EDF4EE 底    ││
│ │ 讀完就忘        │  →(badge)  │ 帶問題讀       ││
│ │ 追量不追質      │            │ 立即提取行動   ││
│ │ 被動吸收        │            │ 費曼法輸出     ││
│ └────────────────┴────────────┴───────────────┘│
│                                 │
│ ─────────────────────────────── │
│ 學習科學研究               NOZOMI│
└─────────────────────────────────┘
```

**中央箭頭 badge 實作：**
```css
.shift-arrow {
  position: absolute;
  left: 50%; transform: translateX(-50%);
  top: 50%;  transform: translate(-50%, -50%);
  width: 32px; height: 32px;
  background: var(--accent);
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; color: var(--arrow-text); /* → ASCII */
  box-shadow: 0 2px 8px rgba(44,110,50,0.25);  /* tinted */
  z-index: 2;
}
```

**資料模型：**
```
title         = 蛻變主題
key_points[0..2].text = BEFORE 欄（舊模式，3 條）
key_points[3..5].text = AFTER 欄（新模式，3 條，對應前三條）
source        = 出處 / 研究依據
```

---

### 風格 3 — `concept.html`：Definition Card

**概念：** 「一張圖解釋一個概念」是知識傳播最高密度的格式。核心結構：概念名稱（大）→ 一句定義 → 3 個關鍵維度 → 記憶錨點。適合思維框架、學術名詞、商業術語、心理學概念。傳播邏輯：被定義的東西顯得更重要，人會想分享自己「懂」。

**視覺語言（全新）：**
- 靈感：Farnam Street concept cards、Wikipedia lead section、辭典版面感
- 概念名稱極大（主視覺），定義緊隨其後
- 左側細色條（accent，全高）作為「定義感」視覺信號
- 維度條目有小 icon placeholder（純 CSS geometric，非 emoji）

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F5F3EF` | sat≈5% ✓ |
| 主文字 | `#1A1814` | sat≈6% ✓ |
| 次文字 | `#726860` | sat≈8% ✓ |
| Accent（左色條 + 概念名） | `#1C5282` | sat≈64% ✓ |
| 維度標籤底 | `rgba(28,82,130,0.08)` | — |
| 分隔線 | `#D8D2CA` | sat≈6% ✓ |
| tinted shadow | `rgba(28,82,130,0.06)` | — |
| 定義框底 | `rgba(28,82,130,0.05)` | — |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ ║  CONCEPT               source │  ← 頂部：左色條開始 + badge
│ ║                               │
│ ║  第一性原理                    │  ← 概念名，Roboto Mono or Outfit 900
│ ║  First Principles             │     中英雙名，accent 色
│ ║                               │
│ ║ ┌─────────────────────────────┐│
│ ║ │ 從最基本的事實出發，不依賴 │  ← 定義句，Noto Serif TC
│ ║ │ 類比或前人假設，重新推導答案 │     斜體感，輕底色框
│ ║ └─────────────────────────────┘│
│ ║                               │
│ ║ · 適用場景  技術決策、成本優化  │  ← 3 個關鍵維度
│ ║ · 代表人物  馬斯克、費曼、笛卡兒│     小方塊 bullet，13px
│ ║ · 常見誤解  ≠ 從頭創造，≠ 否定 │     次文字色，dimmed label
│ ║ ─────────────────────────────  │
│ ║  思維框架系列               N  │  ← footer
└─────────────────────────────────┘
```

**左色條實作：**
```css
.concept-bar {
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 4px;
  background: var(--accent);
  border-radius: 0 2px 2px 0;
}
```

**維度 bullet（小方塊，非 emoji）：**
```css
.dim-bullet {
  width: 5px; height: 5px;
  background: var(--accent);
  border-radius: 1px;
  flex-shrink: 0;
  margin-top: 5px;
  opacity: 0.65;
}
```

**資料模型：**
```
title         = "概念名｜英文名"（用｜分隔，若無英文名則只傳中文）
key_points[0].text = 定義句（一句話解釋，≤ 40 字）
key_points[1].text = "適用場景｜說明"
key_points[2].text = "代表人物｜說明"
key_points[3].text = "常見誤解｜說明"（可選）
source        = 出處系列
```

---

### 風格 4 — `picks.html`：Curated List

**概念：** 「策展人視角」推薦清單。與 `ranking.html` 的區別在於：ranking 強調順序和競爭，picks 強調**品味和選擇**——每一條都是「我特別挑選的」。適合書單、工具清單、播客推薦、電影片單。收藏率是所有格式中最高的。

**視覺語言（全新）：**
- 靈感：都市生活品味雜誌推薦欄、Letterboxd list、Apple Picks 頁面
- 每個條目是一個「迷你卡片」，帶微底色和細邊框
- 用 ★ 替代數字（★ = unicode U+2605，非 emoji）→ 2–4 個★表示推薦強度
- 頂部「策展人聲明」1–2 行（用 source 欄傳入）

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#FAF8F4` | sat≈7% ✓ |
| 主文字 | `#1C1A16` | sat≈6% ✓ |
| 次文字 | `#7A7060` | sat≈8% ✓ |
| Accent（★ + badge） | `#A05A20` | sat≈68% ✓ |
| 迷你卡片底 | `rgba(250,248,244,0.98)` | — |
| 迷你卡片邊框 | `rgba(160,90,32,0.12)` | — |
| 迷你卡片陰影 | `0 2px 8px rgba(28,26,22,0.06)` | — |
| 分隔線 | `#E0D8CE` | sat≈8% ✓ |

**版面結構（430×430 square）：**
```
┌─────────────────────────────────┐
│ PICKS                  ★ ★ ★   │  ← 頂部：PICKS badge + 平均星級
│ ─────────────────────────────── │
│                                 │
│ 改變我思維方式的 5 本書            │  ← 主標題，Noto Serif TC 700
│                                 │
│ ┌─────────────────────────────┐ │
│ │ ★★★★  《窮爸爸富爸爸》       │ │  ← 迷你卡片
│ │        財務自由的啟蒙         │ │     ★ accent 色，Roboto Mono
│ └─────────────────────────────┘ │     標題 Outfit 600
│ ┌─────────────────────────────┐ │     說明 Noto Sans TC 12px
│ │ ★★★★  《原子習慣》           │ │
│ │        行動改變的系統         │ │
│ └─────────────────────────────┘ │
│ ┌─────────────────────────────┐ │
│ │ ★★★   《思考，快與慢》        │ │
│ │        認知偏誤完全指南        │ │
│ └─────────────────────────────┘ │
│ ─────────────────────────────── │
│ 這份書單花了我 5 年才選出   NOZOMI│  ← footer（source 作策展人聲明）
└─────────────────────────────────┘
```

**資料模型：**
```
title         = 推薦清單標題
key_points[n].text = "★數|條目名稱|一句話說明"（★數為 2–4）
source        = 策展人聲明（如 "這份書單花了我 5 年才選出"）
```

**★ 解析邏輯（Jinja2）：**
```jinja2
{% set parts = point.text.split('|') %}
{% set stars = parts[0] | int %}
{% set name = parts[1] %}
{% set desc = parts[2] %}
```

---

## 十三、第六批模板規劃 — 完整覆蓋 P2 缺口

填補 P2 四個缺口：Opinion、Checklist、FAQ、Milestone

---

### 風格 1 — `opinion.html`：Byline Card

**概念：** 個人觀點卡。強主觀視角，「我認為」開頭，建立 personal brand 的核心格式。雜誌 byline 感：作者名顯眼，觀點要「立場明確」、「有話直說」。

**視覺語言：**
- 靈感：Medium 首頁推薦卡、The Atlantic byline、Substack 封面
- 大型引號 or 破折號開頭，直接切入觀點
- 作者信息（brand_name 欄位）顯眼，在標題前出現
- 底色：溫暖奶白，讓觀點感覺「有人格」

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#FDFBF6` | sat≈10% ✓ |
| 主文字 | `#1A1814` | sat≈6% ✓ |
| 次文字 | `#786860` | sat≈8% ✓ |
| Accent | `#7A3B1E` | sat≈58% ✓ |
| 作者底框 | `rgba(122,59,30,0.08)` | — |
| 觀點底框 | `rgba(122,59,30,0.04)` | — |
| 分隔線 | `#DDD5C8` | sat≈7% ✓ |

**版面結構：**
```
┌─────────────────────────────────┐
│  ● NOZOMI 田野調查               │  ← 作者名（brand_name），●+名 badge
│  ─────────────────────────────  │
│                                 │
│  ——我認為，大多數人的問題不是      │  ← 破折號觀點句，Noto Serif 700
│  「不夠努力」，而是「不夠清醒」    │     clamp(17px,4.6vw,21px)
│                                 │
│  ┌─────────────────────────────┐│
│  │ 我的論據是這樣的：            ││  ← 論據框（淺底色），Noto Serif
│  │ · 努力的人很多，成功者卻少數  ││     13px，左縮排
│  │ · 差異在於：選對了方向嗎？    ││
│  │ · 清醒 = 知道自己要什麼       ││
│  └─────────────────────────────┘│
│                                 │
│  ─────────────────────────────  │
│  同意這個觀點嗎？留言告訴我   N  │  ← footer（CTA 文字放在 source 欄）
└─────────────────────────────────┘
```

**資料模型：**
```
title         = 核心觀點句（破折號開頭，如 "——我認為..."）
key_points    = 論據條目（3 條）
source        = CTA 文字 or 觀點出處
brand_name    = 作者名（顯眼展示）
```

---

### 風格 2 — `checklist.html`：Action List

**概念：** 可打勾的清單卡。心理學「完成感」觸發分享欲——人看到清單的反應是「我要截圖存起來」。與 `trace.html` 的差別：trace 是按順序執行的步驟，checklist 是可以任意完成的項目集，無順序依賴。

**視覺語言：**
- 靈感：Notion checklist、Things 3 任務清單、紙本核查表
- `[ ]` 核取框（ASCII，非 checkbox element）
- 標題前一個 checklist icon（SVG inline：帶勾的方框）
- 整體有輕微「表單感」：行線、方框、等寬數字標記

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F8F6F2` | sat≈6% ✓ |
| 主文字 | `#1C1A17` | sat≈6% ✓ |
| 次文字 | `#7A7268` | sat≈5% ✓ |
| Accent（核取框 + 標題） | `#1E6B3A` | sat≈64% ✓ |
| 核取框邊框 | `rgba(30,107,58,0.30)` | — |
| 行底（交替） | `rgba(30,107,58,0.03)` | — |
| 分隔線 | `#D8D4CE` | sat≈5% ✓ |

**版面結構：**
```
┌─────────────────────────────────┐
│ [✓] CHECKLIST          source   │  ← 頂部（SVG inline 勾框，非 emoji）
│ ─────────────────────────────── │
│                                 │
│  發文前必做的 10 件事              │  ← 主標題
│                                 │
│  [ ]  確認標題前 5 個字吸引人      │  ← 核取框 ASCII + 條目
│  [ ]  第一張圖衝擊力 > 3 秒       │     Outfit 13px/1.5
│  [ ]  CTA 放在第 3 行以前         │     交替行底色 accent dim
│  [ ]  加入數字（比例/次數/時間）   │
│  [ ]  標籤研究完成                │
│  [ ]  封面文字 < 20%              │
│  [ ]  發布時間對了嗎？             │
│  [ ]  有互動引導嗎？               │
│  ─────────────────────────────── │
│  0 / 8 完成               NOZOMI │  ← 進度（靜態）
└─────────────────────────────────┘
```

**資料模型：**
```
title         = 清單標題
key_points    = 清單條目（最多 10 條，超過自動縮小）
source        = 清單出處 or 場景說明
```

---

### 風格 3 — `faq.html`：Q&A Accordion

**概念：** 問答對話卡。Q 是問題（引發共鳴），A 是答案（建立權威）。每組問答是一個對話單位，視覺上用顏色或縮排區分 Q/A 雙方。適合常見疑問、知識拆解、FAQ 型內容。

**視覺語言：**
- 靈感：Stack Overflow 問答頁、產品說明書 FAQ 欄
- Q 行：背景略深，Q 字母 badge，accent 色
- A 行：背景白，縮排 12px，Serif 正文
- 整體像「對話」，有節奏感

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#F4F2EE` | sat≈5% ✓ |
| Q 行底 | `rgba(28,82,130,0.07)` | — |
| A 行底 | `#FAF9F6` | sat≈5% ✓ |
| Q 字母 badge | `#1C5282` | sat≈64% ✓ |
| A 字母 badge | `#8A8070` | sat≈5% ✓ |
| 主文字 | `#1A1814` | sat≈6% ✓ |
| 次文字 | `#726860` | sat≈8% ✓ |
| 邊框 | `rgba(28,82,130,0.12)` | — |

**版面結構：**
```
┌─────────────────────────────────┐
│ FAQ                    source   │
│ ─────────────────────────────── │
│ 最常被問到的 3 個問題              │  ← 主標題
│ ─────────────────────────────── │
│ ┌─ Q ──────────────────────────┐│
│ │  為什麼讀了書還是會忘？        ││  ← Q 行，accent 底色
│ └────────────────────────────── ┘│
│ ┌─ A ──────────────────────────┐│
│ │  因為輸入沒有配合輸出。大腦    ││  ← A 行，白底，縮排
│ │  保留的是「使用過的知識」。    ││
│ └────────────────────────────── ┘│
│ ┌─ Q ──────────────────────────┐│
│ │  一天要讀多久才夠？            ││
│ └────────────────────────────── ┘│
│ ┌─ A ──────────────────────────┐│
│ │  重點不在時長，而在密度。       ││
│ │  20 分鐘完全專注 > 2 小時發呆  ││
│ └────────────────────────────── ┘│
│ ─────────────────────────────── │
│ 閱讀研究所                NOZOMI │
└─────────────────────────────────┘
```

**資料模型：**
```
title         = 主標題（如 "最常被問到的 3 個問題"）
key_points[n].text = "Q：問題文字｜A：答案文字"（用｜分隔）
source        = 問題來源 / 知識域
```

**Jinja2 解析：**
```jinja2
{% set parts = point.text.split('｜') %}
{% set question = parts[0] | replace('Q：', '') %}
{% set answer = parts[1] | replace('A：', '') %}
```

---

### 風格 4 — `milestone.html`：Achievement Card

**概念：** 成就里程碑卡。數字說話——強調某個可量化的成就，讓它看起來像「大事件」。適合：粉絲數達標、作品完成、挑戰結束、學習成果。傳播邏輯：見證感 + 替作者慶祝 = 分享。

**視覺語言：**
- 靈感：Spotify Wrapped、Strava 成就徽章、GitHub profile stats
- 超大成就數字作為絕對主角（佔版面 35%）
- 金色系（非 LILA BAN 安全，amber）用於成就感標記
- 背景略有紋理（細格點，如 paper_data），讓成就感覺「有質地」

**色彩規格：**

| 用途 | 色值 | 飽和度 |
|------|------|--------|
| 背景 | `#FDFBF4` | sat≈12% ✓ |
| 主數字 | `#1A1814` | sat≈6% ✓ |
| 數字陰影（tinted） | `rgba(160,100,20,0.15)` | — |
| Accent（成就徽章） | `#A06418` | sat≈74% ✓ |
| 成就感文字 | `#7A5C28` | sat≈44% ✓ |
| 次文字 | `#7A7060` | sat≈8% ✓ |
| 分隔線 | `#DDD5C0` | sat≈10% ✓ |
| tinted shadow | `rgba(160,100,20,0.06)` | — |

**版面結構：**
```
┌─────────────────────────────────┐
│ MILESTONE              2026.03  │  ← badge + 日期
│ ─────────────────────────────── │
│                                 │
│         10,000                  │  ← 超大成就數字（居中）
│         ▬▬▬▬▬▬▬▬▬             │     Roboto Mono 900，clamp(48px)
│         位讀者                  │     數字下方單位說明，Outfit
│                                 │
│ ─────────────────────────────── │
│                                 │
│ 從第一篇文章到現在，我學到了：      │  ← 副標題，Noto Serif 16px
│                                 │
│ · 持續輸出比完美輸出重要           │
│ · 讀者真正想要的和你想的不一樣     │  ← 要點，Noto Sans TC 13px
│ · 轉折點不是靠運氣，是靠出現       │
│                                 │
│ ─────────────────────────────── │
│ 感謝每一位陪我走到這裡      NOZOMI│
└─────────────────────────────────┘
```

**資料模型：**
```
title         = "數字｜單位"（如 "10,000｜位讀者"）
key_points    = 里程碑感悟 / 學到的事（3 條）
source        = footer 致謝語句
```

---

## 十四、第五、六批總覽

| 批次 | 模板名 | 內容類型 | 視覺新鮮度 |
|------|--------|---------|----------|
| 第五批 | `ranking.html` | 排名 / Top N | 全新（amber 漸進）|
| 第五批 | `before_after.html` | 蛻變對比 | 全新（雙欄色差）|
| 第五批 | `concept.html` | 概念定義 | 全新（左色條）|
| 第五批 | `picks.html` | 精選推薦 | 全新（迷你卡片 ★）|
| 第六批 | `opinion.html` | 個人觀點 | 全新（作者 byline）|
| 第六批 | `checklist.html` | 核查清單 | 全新（[ ] 框）|
| 第六批 | `faq.html` | 問答 | 全新（Q/A 交替）|
| 第六批 | `milestone.html` | 里程碑 | 全新（超大數字）|

**完成後：** 31 種模板，覆蓋 19 / 23 種內容類型（83%）

---

### 共同 Taste-Skill 預審（第五、六批全部）

| 模板 | 預判風險 | 規則 | 預防措施 |
|------|---------|------|---------|
| `ranking` | `#01` 數字可能過亮 | NO NEON GLOW | `text-shadow` 僅 tinted 色，無外發光 |
| `ranking` | 排名用 `#` 符號，合規 | ANTI-EMOJI | ASCII 直接使用 |
| `before_after` | AFTER 欄可能用 `#FFFFFF` | NO PURE WHITE | 固定 `#EDF4EE` |
| `before_after` | 箭頭可能用 emoji `→` | ANTI-EMOJI | Unicode U+2192 `→`，非 emoji |
| `concept` | 左色條可能顏色過亮 | SAT < 80% | accent `#1C5282` sat=64% ✓ |
| `concept` | 方塊 bullet 誤用 emoji | ANTI-EMOJI | 純 CSS `div` 實作 |
| `picks` | `★` 星號可能視為 emoji | ANTI-EMOJI | U+2605 `★` 是 Unicode 符號，非 emoji（Black Star）|
| `opinion` | 破折號前可能加 emoji | ANTI-EMOJI | 純 `——` 破折號，無裝飾 |
| `checklist` | `[ ]` 框誤用 checkbox HTML | ANTI-EMOJI | 純文字 `[ ]`，CSS 樣式框線 |
| `faq` | `｜` 為全形符號，Jinja2 split 需對應 | DATA MODEL | 確保 Jinja2 用 `'｜'` split |
| `milestone` | 成就數字可能加 `🎉` emoji | ANTI-EMOJI [P0] | 絕對禁止，用 `◆` or CSS 圓點裝飾替代 |
| `milestone` | 背景格點可能用純 `rgba(0,0,0,x)` | TINTED SHADOW | 格點顏色用 amber 同色系 `rgba(160,100,20,0.04)` |

### 實作清單（第五批）

- [ ] `ranking.html` — amber 漸進 Top N + `text｜desc` 資料模型
- [ ] `before_after.html` — 雙欄色差 + 中央 `→` badge
- [ ] `concept.html` — 左色條 + 定義框 + 方塊 bullet
- [ ] `picks.html` — 迷你卡片 + `★|name|desc` 資料模型
- [ ] 更新 `renderer.py` VALID_THEMES
- [ ] 更新 `scripts/test_new_templates.py` 加入四組 fixture
- [ ] 運行截圖驗證

### 實作清單（第六批）

- [ ] `opinion.html` — byline badge + 觀點句 + 論據框
- [ ] `checklist.html` — `[ ]` 核取框 + 交替行底色
- [ ] `faq.html` — Q/A 對交替 + Jinja2 `｜` split
- [ ] `milestone.html` — 超大數字 + amber 格點底 + 里程碑感悟
- [ ] 更新 `renderer.py` VALID_THEMES
- [ ] 更新 `scripts/test_new_templates.py` 加入四組 fixture
- [ ] 運行截圖驗證

