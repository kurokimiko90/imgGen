# Token Optimization Plan — imgGen

## Context
Daily curation runs 15 AI calls/day (5 items × 3 accounts). Web API re-extracts every request. No deduplication. Model choice is suboptimal. Goal: implement 5 optimizations to reduce token usage by ~40-45%.

---

## Optimization 1: Batch AI Evaluation (P0)
**Target:** `scripts/daily_curation.py`  
**What:** Replace sequential `call_claude_api()` loop (5 items × 1 call each) with one batch call per account.

**Changes:**
- Add `call_claude_api_batch(prompt_file, items, provider="cli") -> list[dict]` function
  - Builds a single prompt: account template + all 5 items numbered
  - Asks Claude to return a JSON array of 5 decisions
  - Parses and maps results back to items by index
- Update `curate_for_account` to call the batch version
- Keep fallback to per-item calls on parse error

**Savings:** 4 AI calls/account/day = 12 calls/day saved (~40-50K tokens/day)

---

## Optimization 2: URL Deduplication Cache (P0)
**Target:** `src/db.py` + `scripts/daily_curation.py`

**Changes to `src/db.py`:**
- Add `find_by_source_url(url: str) -> Content | None` method
  - Queries `WHERE source_url = ? AND status != 'REJECTED' ORDER BY created_at DESC LIMIT 1`

**Changes to `scripts/daily_curation.py`:**
- Before `call_claude_api_batch()` in `curate_for_account`, filter out items whose `source_url` already exists in DB
- Log skipped duplicates

**Savings:** Prevents re-processing same articles across runs

---

## Optimization 3: Smart Model Selection (P1)
**Target:** `src/extractor.py` + `web/api.py`

**Changes:**
- Change `extract_key_points` default `model_variant` from `"sonnet"` → `"haiku"` (line 301)
- `daily_curation.py` already defaults to `model="haiku"` — no change needed
- In `web/api.py`, pass `model_variant="haiku"` for card/article modes; keep sonnet only for smart mode

**Savings:** Haiku is ~3x cheaper; appropriate for structured extraction tasks

---

## Optimization 4: Web API Response Cache (P1)
**Target:** `web/api.py`

**Changes:**
- Add module-level in-memory cache: `_extraction_cache: dict[str, tuple[dict, datetime]]`
- Add helpers `_cache_get(url) -> dict | None` (24h TTL) and `_cache_set(url, data)`
- In `api_generate`: after resolving URL, check cache before calling `run_pipeline`; on hit, call `render_and_capture` directly
- In `api_generate_multi`: cache the `extract()` result keyed by URL
- Only cache URL-based requests, keyed by `sha256(url)`

**Savings:** Repeated Web UI requests for same URL return instantly (0 tokens)

---

## Optimization 5: Prompt Caching via Anthropic API (P2)
**Target:** `src/extractor.py` — `_extract_with_claude()` (line 343)

**Changes:**
- Wrap system prompt with `cache_control={"type": "ephemeral"}` (Anthropic prompt caching API)
- Only applies to `provider="claude"` (API path); CLI path unchanged

**Savings:** ~90% token savings on repeated same-config extractions (system prompt ~800 tokens)

---

## Test Plan

| File | What to test |
|------|-------------|
| `tests/test_daily_curation.py` | `call_claude_api_batch` with mock subprocess; deduplication skips items in DB |
| `tests/test_db.py` | `find_by_source_url` — found / not-found / rejected ignored |
| `tests/test_extractor.py` (new) | Default model is haiku; smart mode still uses sonnet |
| `tests/test_api_cache.py` (new) | Cache hit returns cached data; cache miss calls pipeline; TTL expiry |

### Mocking approach (consistent with existing tests)
- `subprocess.run` patched with `MagicMock(returncode=0, stdout=VALID_JSON)`
- `ContentDAO` replaced with `MagicMock()` with preconfigured return values
- `run_pipeline` / `render_and_capture` patched for API cache tests
- Real SQLite temp DB for `test_db.py` (existing `tmp_path` pattern)

---

## Critical Files

| File | Modification |
|------|-------------|
| `scripts/daily_curation.py` | Batch function, dedup check |
| `src/db.py` | `find_by_source_url` method |
| `src/extractor.py` | Default model → haiku, prompt caching |
| `web/api.py` | In-memory extraction cache |
| `tests/test_daily_curation.py` | Expand tests |
| `tests/test_db.py` | Add source_url test |
| `tests/test_extractor.py` | New file |
| `tests/test_api_cache.py` | New file |

## Expected Savings
- Daily tokens: 30-52K → 18-28K (**↓ 40-45%**)
- Annual cost reduction: ~60-70%
