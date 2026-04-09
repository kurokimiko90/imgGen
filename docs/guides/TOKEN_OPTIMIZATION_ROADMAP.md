# Token Optimization Roadmap

## Current Cost Drivers

### High-Cost Operations (降序)
1. **Design Review Loop** — 5 次迭代 × Claude 視覺分析
2. **Smart Mode Rendering** — 每張卡片動態生成 HTML+CSS
3. **Daily Curation AI Evaluation** — 3 帳號並發批次評估
4. **Image Compression** — tinify API 呼叫

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

## Detailed Implementation Plan

### Phase 1: P0 + P4 (Immediate, Low Risk)
- [ ] Add `--no-image` flag to daily_curation
- [ ] Replace tinify with PIL in design_review_loop
- [ ] Test both changes in dry-run mode

**Estimated savings:** 30–50% of current token spend

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
