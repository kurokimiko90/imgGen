# 文章轉圖片發文系統設計

## 系統概述

「文章 → 摘要 → 精美圖片卡片」pipeline：將長篇文章自動萃取核心觀點，生成適合手機觀看的精美圖片。

**核心思路**：不使用 AI 繪圖，改用 HTML+CSS 生成精美排版後截圖，效果穩定、文字正確、視覺可控。

---

## 核心架構

```
長文章輸入
    ↓
Claude 萃取核心觀點（3-5點）
    ↓
生成精美 HTML/CSS 卡片頁面
    ↓
Playwright 截圖
    ↓
輸出手機適合的圖片
```

---

## Agent 組合

| Agent | 用途 |
|-------|------|
| `frontend-slides` | 生成精美 HTML 卡片，支援動畫效果 |
| `e2e-runner` | 用 Playwright 截圖（headless browser） |
| `claude-api` | 文字摘要 pipeline 核心 |
| `content-engine` | 多平台內容輸出系統 |
| `fal-ai-media` | 如需 AI 生成背景圖片 |

**最小可行組合**：`claude-api` + `frontend-slides` + `e2e-runner`

---

## 實作計劃

### Phase 1: MVP

1. Claude API 摘要 → 輸出結構化 JSON（標題、3-5核心點、來源）
2. 套用 HTML 模板 → 生成卡片頁面（1080x1920 手機比例）
3. Playwright 截圖 → 輸出 PNG/WebP

### Phase 2: 擴展功能

- 多種卡片風格（暗色 / 亮色 / 漸層）
- 不同比例（9:16 Instagram Story / 1:1 方形 / 16:9 橫向）
- 自動加 logo、來源、QR code
- Telegram Bot 觸發（傳文章連結 → 回傳圖片）

---

## 擴展方向

1. **爬蟲整合** — 輸入 URL 自動抓取文章內容
2. **多語言** — 原文摘要 + 翻譯成中文
3. **排程發布** — 生成後自動發到 Telegram / Twitter
4. **品牌客製** — 不同客戶套不同視覺模板
5. **批量處理** — 一次處理多篇文章

---

## 技術選型建議

| 需求 | 方案 |
|------|------|
| 文字摘要 | Claude API (`claude-sonnet-4-6`) |
| HTML 卡片生成 | Node.js + Handlebars / Jinja2 模板 |
| 截圖 | Playwright（Node.js 或 Python） |
| 圖片輸出 | PNG / WebP，1080x1920px |
| 觸發方式 | CLI / Telegram Bot / REST API |

---

## 下一步

- [ ] 確認技術偏好（Node.js / Python）
- [ ] 設計 HTML 卡片模板視覺風格
- [ ] 實作 MVP pipeline
- [ ] 接入 Telegram Bot 觸發
