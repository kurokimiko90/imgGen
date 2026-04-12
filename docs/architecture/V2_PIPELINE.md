# v2 Pipeline 架構

## 三條使用路徑

| 路徑 | 腳本 | 定位 |
|---|---|---|
| 手動單篇 | `main.py` | 測試/快速出圖 |
| 自動化舊版 | `daily_curation.py` | 量大，質量一般 |
| v2 精品管道 | `curate_v2.py` + `generate_images_v2.py` | 發佈用，>=8 分才存 |

## v2 LLM 呼叫（每帳號，30 篇文章）

| 階段 | 模型 | 呼叫次數 | 說明 |
|---|---|---|---|
| Stage 1 篩選 | Gemini Flash | **1 次** | 全部批次，一個 prompt |
| Stage 2 寫作 | Claude Sonnet | N 次 | N = 通過篩選篇數 |
| Stage 3 審查 | Gemini Flash | N 次 | 逐篇 |
| Loop 重寫 | Claude Sonnet | 0~N 次 | 不過才重寫，max 1 次 |

有 `ANTHROPIC_API_KEY` → Stage 2/Loop 走 API；否則 fallback CLI。

## 生圖呼叫（`generate_images_v2.py`）

每張圖 1 次 `smart_renderer` 呼叫（生成 HTML layout）。

- v2 DB 有 `key_points` → 直接渲染，跳過 `extract()` CLI
- 舊資料無 `key_points` → 多 1 次 Haiku extract

`key_points` 由 `curate_v2.py` 存入 `reasoning` JSON 欄位（Stage 2 輸出）。

## 4 種渲染 mode

| mode | AI 做什麼 | 渲染方式 |
|---|---|---|
| `card` | 提取 3-5 條 key points | Jinja2 靜態（35 模板） |
| `article` | 壓縮成 3 段敘述 | 同上 |
| `smart` | 生成完整 HTML+CSS | Claude/API 動態生成（30 palette） |
| `carousel` | 拆成 3-7 張幻燈片 | 每張走 smart mode |

**35 模板 vs 30 palette：**
- 35 模板 = `card`/`article` mode 的 Jinja2 靜態模板
- 30 palette = `smart` mode 配色，從模板 `:root {}` 自動提取

## v2 關鍵模組

- `src/curation_v2/account_profiles.py` — 帳號設定（personality/rules/style）
- `src/curation_v2/stage1_filter.py` — 批次篩選
- `src/curation_v2/stage2_writer.py` — 高質量寫作
- `src/curation_v2/stage2_rewriter.py` — 基於回饋重寫
- `src/curation_v2/stage3_reviewer.py` — 7 維度評審
- `src/curation_v2/llm_clients.py` — API/CLI fallback 統一介面

## LLM 成本（2026-04-11）

**`smart_renderer` haiku bug 修復：**
- 之前 `_CLAUDE_MODELS` 沒有 `haiku`，API 路徑 fallback 到 Sonnet
- 現已修復：`_DEFAULT_CLAUDE_MODEL = "haiku"`
- 每張圖成本：~$0.03（Haiku）vs 之前 ~$0.12（Sonnet）

**prompt 大小：** ~3100 tokens input（含完整設計系統 CSS），每次完整傳入。
