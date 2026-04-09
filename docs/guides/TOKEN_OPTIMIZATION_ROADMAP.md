# Token Optimization Roadmap

## Root Cause Analysis（2026-04-10 實測）

每次 `claude -p` 子進程 = 一個完整 Claude Code session，強制載入：
- `~/.claude/CLAUDE.md` + rules × 10 個文件 + memory + git status ≈ **8,300t overhead/call**

一次完整 pipeline（3 篇文章 × 5 slides）共 **25 次 claude -p 呼叫**：
- 總消耗 ~306,000t；其中 CLI overhead 占 **67%**，實際 payload 只有 33%
- Step 4（Smart Render 15 calls）是最大消耗點，占全流程 40%

## 實作狀態

| 優化項目 | 狀態 | 效果 |
|---------|------|------|
| P0: `--no-image` 旗標 | ✅ 已實作 | 跳過圖片生成，省 60% token |
| P1: PIL 取代 tinify | ✅ 已實作 | tinify 呼叫歸零（免費） |
| P2: 並行渲染 | ✅ 已實作 | 時間快 3.7x（token 不變） |
| P3: Prompt hash caching | ⬜ 待實作 | 省 10-20%（重複文章） |
| P4: Smart mode opt-in | ⬜ 待實作 | 省 50-70%（若改預設） |
| ~~API 直接呼叫~~ | ❌ 放棄 | 需要 ANTHROPIC_API_KEY |
| ~~Smart Render 批次化~~ | ❌ 放棄 | Timeout 風險高 |

---

## Current Cost Drivers

### High-Cost Operations (降序)
1. **Smart Mode Rendering** — 每張 slide 一個 claude -p session（8,300t overhead × N slides）
2. **Design Review Loop** — 5 次迭代 × Claude 視覺分析
3. **Daily Curation AI Evaluation** — 3 帳號並發批次評估（批次化後已改善）

### Estimated Monthly Cost
- 若每天跑 daily_curation × 1 + design_review_loop × 2：
  - daily_curation: 3 帳號 × 10 項 ÷ 5 (batch) = 6 API 呼叫/天
  - design_review_loop: 2 × 5 迭代 = 10 API 呼叫/天
  - **Total: ~480 API 呼叫/月** → Haiku: $15–20/月，Sonnet: $50–80/月

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
