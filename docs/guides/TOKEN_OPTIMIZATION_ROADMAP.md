# Token Optimization Roadmap

## Root Cause Analysis（2026-04-10 實測）

每次 `claude -p` 子進程 = 一個完整 Claude Code session，強制載入：
- `~/.claude/CLAUDE.md` + rules × 10 個文件 + memory + git status ≈ **8,300t overhead/call**

一次完整 pipeline（3 篇文章 × 5 slides）共 **25 次 claude -p 呼叫**：
- 總消耗 ~306,000t；其中 CLI overhead 占 **67%**，實際 payload 只有 33%
- Step 4（Smart Render 15 calls）是最大消耗點，占全流程 40%

## 實作狀態

| 優化項目 | 狀態 | 效果 | 實測 |
|---------|------|------|------|
| P0: `--no-image` 旗標 | ✅ 已實作 | 跳過圖片生成，省 60% token | — |
| P1: PIL 取代 tinify | ✅ 已實作 | tinify 呼叫歸零（免費） | — |
| P2: 並行渲染 | ✅ 已實作 | 時間快 3.7x（token 不變） | — |
| P3: Extractor 預設 Haiku | ✅ 早已實作 | `extract_key_points` + `_call_claude` 預設 haiku | — |
| P4: Carousel 一次摘取 | ✅ 早已實作 | `run_carousel_pipeline` 只呼叫一次 extract() | — |
| P5: `--dry-run` 跳過 AI | ✅ 已實作（2026-04-10） | dry-run 零 AI 呼叫，用 fixture 替代 | — |
| **P8: 動態 depth_tier 分配** | ✅ 已實作（2026-04-10） | **tier-driven carousel：tier=1 單圖，tier=3/5/7 多 slides** | **Account A 測試：9 calls（-40%）；Account C dry-run 通過** |
| **P9: Palette 自動載入 + Carousel Role Prompt** | ✅ 已實作（2026-04-11） | **解鎖 Account A 配色單調（30 個 palette）+ 改進 carousel first-attempt 成功率** | **muse_spark 5 slides 全部 first-attempt 成功，無重試** |
| P6: Prompt hash caching | ⬜ 待實作 | 省 10-20%（重複文章） | — |
| P7: Smart mode opt-in | ⬜ 待實作 | 省 50-70%（若改預設，但質量下降風險高）| — |
| ~~API 直接呼叫~~ | ❌ 放棄 | 需要 ANTHROPIC_API_KEY（`--bare` mode 強制 API key） | — |
| ~~Smart Render 批次化~~ | ❌ 放棄 | Timeout 風險高 | — |
| ~~Smart Renderer 改 Haiku~~ | ❌ 放棄 | HTML 生成質量明顯變差，retry 率上升 | — |
| ~~A1+A2 固定截斷~~ | ❌ 放棄 | 被 P8 替代（動態更優雅） | — |

---

## P8 實作細節 — depth_tier 動態 Carousel 分配（2026-04-10）

### 設計原理
將輪播圖 slides 數**由內容質量決定**，而非固定值：
- **tier=1** → 1 slide（事件快訊、單一數據點）
- **tier=3** → 3 slides（觀點論述、工具深挖、迷你案例）
- **tier=5** → 5 slides（系統教學、完整案例）
- **tier=7** → 7 slides（長篇內容，罕見）

### 實作
1. `prompts/account_a.txt` 新增 `depth_tier` + `depth_reason` 欄位，附詳細判準
2. 推廣 account_b.txt / account_c.txt（已完成，待驗證 B 爬蟲）
3. `daily_curation.py`：
   - 批次評估結果正規化 tier（非 1/3/5/7 → 強制 1）
   - 並行渲染改為 **per-item tier-driven**
   - 輸出 tier 分佈摘要（便於觀察 AI 判斷穩定度）

### 實測結果（Account A，2026-04-10）
| Run | 模式 | tier 分佈 | Sonnet calls | 配額省幅 |
|---|---|---|---|---|
| 1 | `--no-image` | tier1×9 | 9 | -40% |
| 2 | `--no-image` | tier1×6, tier3×1 | 9 | -40% |
| 3 | 完整渲染 | tier1×2 | 2 | (8 duplicate) |

**結論：** 
- ✅ tier 判斷穩定（傾向保守，符合設計「寧可低估」）
- ✅ 配額省幅 -40 ~ 87%（取決於爬蟲重複度 + tier 分佈）
- ✅ 運行於生產環境無異常

### 推廣進度
- ✅ Account A — 實測驗證完畢，投入生產
- ✅ Account C — dry-run 通過（tier1×9，符合快訊特性）
- ⏳ Account B — 爬蟲異常，待調查

---

## P9 實作細節 — Palette 自動載入 + Carousel Role Prompt（2026-04-11）

### 問題診斷
調查「為什麼 smart mode 生成的圖永遠黑底藍」發現 4 層硬編碼：
1. `prompts/account_a.txt` 寫死 `Color mood: dark_tech.`
2. JSON schema 例子也寫 `image_suggestion: "dark_tech"`
3. 批次評估 Claude 照做，三篇文章都返回 `dark_tech`
4. `src/smart_renderer.py` 的 `COLOR_PALETTES` 只有 5 個（`dark_tech` / `warm_earth` / `clean_light` / `bold_contrast` / `soft_pastel`）

更大問題：**templates/ 目錄有 35 個 Jinja2 主題，每個都有獨特配色（warm_sun 橙漸層、luxury_data 黑紅、milestone 金褐、editorial 棕灰…），全部被 smart mode 遺棄**。設計資產割裂，smart mode 只能在 5 個窮酸選項裡轉。

### 實作

**1. Palette 自動載入（`src/smart_renderer.py`）**

新增 `_load_palettes_from_templates()`，模組載入時掃描 `templates/*.html`：
- `_parse_root_vars()` 用 regex 提取 `:root { --var: value; }` 區塊的所有 CSS 變數
- `_VAR_CANDIDATES` heuristic 映射表把非標準變數名（`--orange`、`--ruby`、`--text-ink`、`--brown-deep`）歸類到 `bg` / `accent` / `text_primary` / `text_secondary` / `text_muted` / `border` 6 個標準 slot
- `_build_palette_from_vars()` 組裝成 `COLOR_PALETTES` 相容的 CSS block
- Fallback：`bg` 和 `text_primary` 缺失就跳過該 template；`accent` 缺失就 fallback 到 `text_primary`；其他欄位用中性默認值

結果：
- **25 個成功提取**（dark / light / editorial / warm_sun / cozy / luxury_data / milestone / picks / ranking / hook / quote_dark / data_impact …）
- **5 個失敗**（`gradient` / `quote` / `versus` / `pop_split` / `ai_theater`）— 特殊雙色或玻璃態結構，fallback 到 5 個手寫 palette
- **最終 COLOR_PALETTES = 30 個**（25 自動 + 5 fallback）

**2. Carousel 專用 Prompt（`_build_layout_prompt`）**

讀取 `_carousel` / `_slide_role` / `_visual_hint` / `_thread_index` / `_thread_total`，為 5 個 slide role 注入專屬設計指導：
- `hook`: 單一焦點元素，40-56px 巨大 heading
- `point`: 清晰層級，一個視覺錨點
- `data`: 關鍵數字主導（60-96px），accent 色突出
- `quote`: editorial 風，大引號 + 斜體
- `cta`: 明確行動按鈕 + 箭頭

還加了「CAROUSEL DESIGN RULES」硬規則：heading 為主元素、body 是短文本不是 key points list、禁止 fake widgets、禁止 dashboard chrome。

**3. Account A Prompt 解鎖（`prompts/account_a.txt`）**

移除 `Color mood: dark_tech.` 硬編碼，改為 30 個 palette 的分類選擇指南（深色系 / 淺色系 / 彩色系 × 內容類型），告訴 Claude「AI 自動化帳號不代表必須 dark」。JSON schema 的 `image_suggestion` 默認值從 `dark_tech` 改為 `dark`（更通用）。

**4. Archive 重建腳本（`scripts/regenerate_carousel_smart.py`）**

讀取 `.tmp/carousel_data.json` 的已提取 slide 結構，用 smart mode 直接渲染，跳過 extract 步驟。支援指定 palette 覆蓋。Parallel 渲染（ThreadPoolExecutor max_workers=5）。

### 實測結果（muse_spark，2026-04-11）

| 測試 | 結果 |
|---|---|
| hook slide 單獨測試（light palette） | ✅ Meta 藍漸層 + "16" 特寫，符合 visual_hint |
| 完整 5 slides parallel（light palette） | ✅ 5 slides 全部 first-attempt 成功，無重試 |
| 5 個 role 指導效果 | ✅ hook/point/data/quote/cta 全部被正確執行 |
| 視覺一致性 | ✅ 白底 + 藍 accent 跨 5 slides 協調 |

**小瑕疵：** Slide 4 的 "4/5" 進度標籤和 Claude 生成的 "04/" 文字撞在一起，watermark injector 和 Claude 生成的 carousel chrome 衝突。待後續修復（加在 prompt 禁止 Claude 自生成 "N/M" 類文字，或從 pipeline 側剝離）。

### 尚未驗證
- ⏳ Account A prompt 改動的效果（明早批次評估才會看到 Claude 是否真的選不同 palette）
- ⏳ 其他 palette（`warm_sun` / `editorial` / `luxury_data` 等）在 carousel 中的實際效果
- ⏳ Account B / C 的 prompt 尚未同步解鎖

### 真實 Token 節省
P9 **不直接減少 claude -p 呼叫數**，而是通過：
1. **降低重試率**（visual_hint + role guidance 讓 first-attempt 成功率 ↑）
2. **減少盲目創作**（Claude 有明確指導，不再發散嘗試）

實測：muse_spark 5 slides first-attempt 全部成功，**0 次重試**。對比之前 smart mode 的平均重試率（約 20-30%），節省約 20% 的 Sonnet render tokens。

組合 P8 + P9 後，預估 Sonnet render tokens 從基準 ~1350/月 → ~216-432/月（-68 ~ 84%）。

---

## Current Cost Drivers

### High-Cost Operations (降序)
1. **Smart Mode Rendering** — 每張 slide 一個 claude -p session（~8,300t overhead × N slides，經 P8 優化後平均 N 變小）
2. **Design Review Loop** — 5 次迭代 × Claude 視覺分析
3. **Daily Curation AI Evaluation** — 3 帳號並發批次評估（已批次化）

### Estimated Monthly Cost（P8 後）
- 若每天跑 daily_curation × 1 + design_review_loop × 2：
  - daily_curation: 3 帳號 × 10 項 ÷ 5 (batch) = 6 API 呼叫/天（但 Sonnet renders 從 45 → ~9-18 via P8）
  - design_review_loop: 2 × 5 迭代 = 10 API 呼叫/天
  - **Total: ~480 API 呼叫/月，Sonnet renders 從 ~1350 → ~270-540**（-60 ~ 80%）
  - **Cost: 預估 Haiku $20-30/月，Sonnet $10-30/月**（vs 原 $50-100/月）

---

## Quick Wins (優先度)

### P0 — Add `--no-image` Flag to daily_curation
**Goal:** Skip image generation, only evaluate content.

```bash
python scripts/daily_curation.py --no-image
# Saves 3×10 smart_renderer calls per day
```

**Implementation:**
- Add `--no-image` click option
- Skip `generate_image()` call
- Cost reduction: 30–50% for curation workflow

---

### P1 — Reduce design_review_loop Max Iterations
**Goal:** Lower from 5 to 3 iterations.

**Current:** Each iteration = 1 Claude visual call + 1 tinify call  
**After:** 3 iterations = 40% fewer API calls

**Change:** In `design_review_loop.py`, find `max_iterations = 5` → `max_iterations = 3`

**Cost reduction:** 40% for design review workflow

---

### P2 — Prompt Hash Caching for Extractor
**Goal:** Cache extraction results for identical prompts.

**Mechanism:**
- Hash the system_prompt + user_prompt + article_text
- Check `.tmp/extraction_cache.json` before calling Claude
- Store successful results with TTL (24 hours)

**File:** `src/cache.py` (new)
```python
def get_cached_extraction(prompt_hash: str) -> dict | None:
    """Check cache for extraction result."""
    ...

def cache_extraction(prompt_hash: str, result: dict) -> None:
    """Store extraction result with timestamp."""
    ...
```

**Integration:** Modify `extractor.py` _extract_with_claude() to check cache first.

**Cost reduction:** 10–20% (only helps if same article scraped multiple times)

---

### P3 — Smart Mode Degradation
**Goal:** Fall back to template rendering if smart mode is too expensive.

**Current:** Always try smart mode, fallback only on error  
**After:** Smart mode only for high-value content (e.g., featured posts)

**Implementation:**
```python
def should_use_smart_mode(content: Content) -> bool:
    # Return False by default, True only for explicitly marked content
    return content.metadata.get("use_smart_design", False)
```

**Cost reduction:** 50–70% if smart mode is opt-in instead of default

---

### P4 — Compress Image Before Visual Analysis
**Goal:** Reduce token cost of design_review_loop image analysis.

**Current:** Compress with tinify (separate API)  
**After:** Use built-in PIL/Pillow compression (free)

**Change in `design_review_loop.py`:**
```python
def _compress_image_for_review(image_path: Path) -> bytes:
    """Use PIL instead of tinify."""
    from PIL import Image
    img = Image.open(image_path)
    img.thumbnail((800, 600))
    ...
    return compressed_bytes
```

**Cost reduction:** 100% for tinify calls (one less API per iteration)

---

## 並行渲染實作細節（P2，已完成）

### `src/pipeline.py` — `run_carousel_pipeline`
```python
run_carousel_pipeline(..., parallel=True, max_workers=5)
```
- `parallel=True`（預設）：用 `ThreadPoolExecutor` 同時渲染所有 slides
- 實測：5 slides 從 284s → 78s（3.7x 加速）
- Token 數不變；品質相同（每個 slide 仍獨立 prompt）

### `scripts/daily_curation.py` — 多文章並行
- 同帳號多篇文章的 `generate_image()` 改為 `ThreadPoolExecutor` 並行
- 3 篇文章：以前 3 × 78s = 3.9 分鐘 → 現在 ~78s

---

## Detailed Implementation Plan

### ✅ Phase 1: P0 + P1 (完成)
- [x] Add `--no-image` flag to daily_curation
- [x] Replace tinify with PIL in design_review_loop

### ✅ Phase 2: 並行渲染 (完成)
- [x] `run_carousel_pipeline` parallel=True（ThreadPoolExecutor）
- [x] `curate_for_account` 多文章並行圖片生成

### ⬜ Phase 3: P3 Prompt Caching（待實作）
- [ ] `src/extractor.py` 加入 prompt hash cache
- [ ] TTL 24 小時，存於 `.tmp/extraction_cache.json`

**已實現節省：** 時間快 3.7x；`--no-image` 時省 60% token

### Phase 2: P1 + P2 (Next Sprint)
- [ ] Reduce design_review_loop max iterations to 3
- [ ] Implement extraction cache with 24-hour TTL
- [ ] Test cache hit rates over 1 week

**Estimated savings:** Additional 20–30%

### Phase 3: P3 (Optional, Design Decision)
- [ ] Make smart mode opt-in via content metadata
- [ ] Create CLI flag: `--smart-mode` (default: false)

**Estimated savings:** Additional 20–40% (if enabled)

---

## Monitoring

### Before Optimization
Run this to log current cost:
```bash
python scripts/daily_curation.py --dry-run
python scripts/design_review_loop.py dark --max-iterations 5
# Note: Print total API calls + estimated cost
```

### After Each Phase
```bash
# Check prompt_logger statistics
curl http://localhost:8001/api/prompts/stats

# Or run audit
python scripts/audit.py --show-costs
```

---

## Backward Compatibility
- `--no-image` is additive; old commands still work
- PIL compression is internal; no CLI changes
- Cache is optional; miss gracefully
- Smart mode opt-in doesn't break existing workflows

---

## Success Criteria
- [ ] Phase 1: 30–50% token reduction (verified via logs)
- [ ] Phase 2: 50–70% total reduction
- [ ] Phase 3: 70–90% total reduction (if enabled)
- [ ] All tests pass; no regressions
