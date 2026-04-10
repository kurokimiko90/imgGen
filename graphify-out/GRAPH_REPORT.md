# Graph Report - src/ scripts/ docs/  (2026-04-09)

## Corpus Check
- 72 files · ~86,887 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 422 nodes · 738 edges · 44 communities detected
- Extraction: 73% EXTRACTED · 27% INFERRED · 0% AMBIGUOUS · INFERRED: 197 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## God Nodes (most connected - your core abstractions)
1. `Content` - 42 edges
2. `ContentStatus` - 36 edges
3. `ContentDAO` - 35 edges
4. `LevelUpConfig` - 21 edges
5. `RawItem` - 20 edges
6. `FootballScraper` - 18 edges
7. `AccountType` - 17 edges
8. `PipelineOptions` - 17 edges
9. `PMPScraper` - 16 edges
10. `TechScraper` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Prompt Logger LLM Tracking` --implements--> `log_prompt_call()`  [INFERRED]
  docs/guides/PROMPT_LOGGER_GUIDE.md → src/prompt_logger.py
- `Smart Mode AI-Driven Dynamic Layouts` --implements--> `generate_smart_html()`  [INFERRED]
  docs/guides/SMART_MODE_GUIDE.md → src/smart_renderer.py
- `HITL Review Workflow` --implements--> `audit.py HITL Review Script`  [INFERRED]
  docs/prd/levelUpPRD.md → scripts/audit.py
- `Cycle 4 Spec — HITL` --rationale_for--> `audit.py HITL Review Script`  [EXTRACTED]
  docs/specs/cycle_4_spec.md → scripts/audit.py
- `Web UI Review+Curation Spec` --conceptually_related_to--> `audit.py HITL Review Script`  [EXTRACTED]
  docs/specs/webui_review_curation_spec.md → scripts/audit.py

## Hyperedges (group relationships)
- **imgGen Core Pipeline** — pipeline_extract, pipeline_render_and_capture, extractor_extract_key_points, renderer_render_card, screenshotter_take_screenshot [EXTRACTED 1.00]
- **LLM Call Logging Pattern** — extractor_extract_with_claude, extractor_extract_with_claude_cli, caption_generate_captions, prompt_logger_log_prompt_call, llm_forge_reporter_record_llm_call [EXTRACTED 1.00]
- **LevelUp Content State Machine** — content_Content, content_ContentStatus, db_ContentDAO, preflight_preflight_check, markdown_io_import_markdown [EXTRACTED 0.95]
- **HITL Review Workflow** — scripts_audit, content_Content, db_ContentDAO, preflight_preflight_check, markdown_io_export_markdown [EXTRACTED 1.00]
- **Daily Curation Pipeline** — scripts_daily_curation, scrapers_football, pipeline_run_pipeline, db_ContentDAO, content_Content [EXTRACTED 1.00]
- **LevelUp Full Automation Pipeline** — concept_levelup_system, concept_hitl_review, concept_content_state_machine, report_automation_pipeline, concept_accounts_abc [EXTRACTED 1.00]
- **imgGen Core System** — concept_html_css_rendering, concept_smart_mode, prd_imggen, arch_system_design [EXTRACTED 1.00]

## Communities

### Community 0 - "Audit & Review Workflow"
Cohesion: 0.08
Nodes (51): scripts/audit.py — Human-in-the-loop content review system.  Usage:     python s, Execute a review action and return a description string., Run the interactive review loop. Returns summary dict., Print a single content card for review., Open $EDITOR with *body*, returning the edited content., Universal raw content item from any scraper source., RawItem, LevelUpConfig (+43 more)

### Community 1 - "AI Extraction Engine"
Cohesion: 0.09
Nodes (39): _build_article_prompt(), _build_smart_prompt(), _build_system_prompt(), extract_key_points(), _extract_with_claude(), _extract_with_claude_cli(), _extract_with_claude_cli_sync(), _extract_with_gemini() (+31 more)

### Community 2 - "Scraper Framework"
Cohesion: 0.1
Nodes (14): ABC, BaseScraper, src/scrapers/base_scraper.py - Abstract base class for all content scrapers.  De, Abstract base class for all content scrapers., Filter out incomplete RawItems (missing title, url, or published_at)., BaseScraper, FootballScraper, src/scrapers/football_scraper.py - Football news scraper.  Sources:   - BBC Spor (+6 more)

### Community 3 - "Config & Account System"
Cohesion: 0.11
Nodes (24): AccountConfig, delete_preset(), get_default(), list_presets(), load_config(), load_preset(), _parse_toml_file(), _parse_toml_full() (+16 more)

### Community 4 - "Architecture & Planning Docs"
Cohesion: 0.09
Nodes (25): LevelUp Master Plan, Three Accounts (A:AI/B:PMP/C:Football), Content Status State Machine, HITL Review Workflow, LevelUp Multi-Account Automation System, User Persona: Solo Operator, Content, ContentStatus (+17 more)

### Community 5 - "Caption Generation"
Cohesion: 0.09
Nodes (18): _build_caption_prompt(), _call_provider(), generate_captions(), caption.py - Platform-specific caption generation.  Generates ready-to-post text, Call the AI provider with a simple text prompt, return raw response., Save captions to a .txt file alongside the image.      Args:         captions: D, Build a prompt asking the AI to generate platform-specific captions., Generate captions for given platforms from extracted article data.      Makes a (+10 more)

### Community 6 - "Smart Mode Dynamic Layouts"
Cohesion: 0.13
Nodes (21): Smart Mode AI-Driven Dynamic Layouts, Smart Mode Guide, _build_design_system_css(), _build_layout_prompt(), _build_watermark_html(), _call_provider(), _fallback_to_template(), generate_smart_html() (+13 more)

### Community 7 - "Design Review Loop"
Cohesion: 0.14
Nodes (21): apply_patches(), build_prompt(), call_claude_cli(), _compress_image_for_review(), _extract_css_vars(), generate_screenshot(), Issue, LoopSummary (+13 more)

### Community 8 - "Generation History DB"
Cohesion: 0.17
Nodes (19): _connect(), get_generation_by_id(), get_stats(), init_db(), list_generations(), _migrate_extracted_data(), history.py - SQLite history log for all imgGen generations.  Stores metadata abo, Get a single generation by id. Returns None if not found. (+11 more)

### Community 9 - "URL Fetcher"
Cohesion: 0.22
Nodes (13): _extract_article_text(), _extract_meta(), _extract_thread_items(), _fetch_threads_content(), fetch_url_content(), _is_threads_url(), _parse_post(), fetcher.py - URL content fetching for imgGen.  Shared implementation used by bot (+5 more)

### Community 10 - "File Watcher"
Cohesion: 0.19
Nodes (9): _DebouncedHandler, watcher.py - Folder monitoring for automatic card generation.  Watches a directo, Tracks file events with a debounce window., Record a file event (created or modified)., Process any events past the debounce window., Read file content, handling .url files specially., Watch a directory for new/modified files and invoke callback.      This function, _read_file_content() (+1 more)

### Community 11 - "Batch Processing"
Cohesion: 0.2
Nodes (11): _fetch_url_content(), parse_batch_file(), process_entry(), _process_text(), batch.py - Batch processing module for imgGen v2.0.  Provides async batch proces, Process a single batch entry within the semaphore.      Args:         entry: URL, Run all entries concurrently with Semaphore(workers).      Args:         entries, Read batch file, skip blank lines and # comments, return list of entries.      A (+3 more)

### Community 12 - "LLM Forge Reporter"
Cohesion: 0.33
Nodes (11): calculate_cost(), flush_and_shutdown(), flush_offline_queue(), hash_text(), init_llm_forge_auto_report(), LLMCallRecord, load_offline_queue(), LLM-Forge 自動上傳層 將每個 LLM 調用自動報告到中央 Hub 離線隊列機制（失敗時本地保存） (+3 more)

### Community 13 - "Daily Curation Pipeline"
Cohesion: 0.5
Nodes (7): _call_claude(), call_claude_api(), call_claude_api_batch(), curate_for_account(), generate_image(), _load_prompt(), main()

### Community 14 - "HITL Audit Script"
Cohesion: 0.57
Nodes (6): audit(), _display_content(), _handle_action(), _open_editor(), _print_summary(), _run_interactive()

### Community 15 - "Misc: digest"
Cohesion: 0.4
Nodes (5): build_digest_input(), generate_digest(), digest.py - Weekly digest synthesis from generation history.  Takes multiple art, Format generation history rows into a text block for the AI prompt., Synthesize a digest from generation history via AI.      Args:         generatio

### Community 16 - "Misc: screenshotter"
Cohesion: 0.4
Nodes (5): screenshotter.py - Playwright screenshot module  Takes screenshots of HTML conte, Async implementation of screenshot capture.      Args:         html_content: Ful, Take a screenshot of HTML content and save as PNG or WebP.      Args:         ht, take_screenshot(), _take_screenshot_async()

### Community 17 - "Misc: renderer"
Cohesion: 0.33
Nodes (5): load_watermark_data(), renderer.py - Jinja2 HTML rendering module  Renders beautiful HTML cards from ex, Read an image file and return a base64 data URI string.      Args:         path:, Render an HTML card from extracted article data.      Args:         data: Dict w, render_card()

### Community 18 - "Misc: scheduler"
Cohesion: 0.4
Nodes (5): assign_scheduled_times(), calculate_scheduled_time(), src/scheduler.py - Scheduled time calculation for LevelUp content publishing.  A, Return the next available publish datetime for *publish_time* (HH:MM).      If *, Assign scheduled_time to each Content in *contents*.      Each item is offset by

### Community 19 - "Misc: publisher"
Cohesion: 0.4
Nodes (5): _check_twitter_credentials(), publish_to_twitter(), publisher.py - Social media publishing integration.  Currently supports Twitter, Validate that all required Twitter env vars are set.      Returns:         Dict, Upload an image and post a tweet.      Args:         image_path: Path to the ima

### Community 20 - "Misc: clipboard"
Cohesion: 0.4
Nodes (5): copy_image_to_clipboard(), is_clipboard_supported(), clipboard.py - macOS clipboard integration for image files., Return True if running on macOS (clipboard copy is supported)., Copy an image file to the macOS clipboard.      Uses ``osascript`` to set the cl

### Community 21 - "Misc: content content transition to"
Cohesion: 0.4
Nodes (4): InvalidTransitionError, Raised when a state transition is not permitted by the state machine., Validate and apply a state transition.          Args:             new_status: Th, Exception

### Community 22 - "Misc: config levelupconfig save"
Cohesion: 0.5
Nodes (2): Update one account's settings and write back to accounts.toml.          Only pro, Write the current accounts to accounts.toml using _write_toml.

### Community 23 - "Misc: plan main"
Cohesion: 0.67
Nodes (3): imgGen Development Plan, Cycle 1 Roadmap, Cycle 2 Roadmap

### Community 24 - "Misc: config AccountConfig"
Cohesion: 1.0
Nodes (2): AccountConfig, LevelUpConfig

### Community 25 - "Misc: scripts design review"
Cohesion: 1.0
Nodes (1): Cycle 3 Spec v2

### Community 26 - "Misc: concept webui phases"
Cohesion: 1.0
Nodes (2): LevelUp Web UI Phase A-E, LevelUp Web UI Implementation Report

### Community 27 - "Misc: init"
Cohesion: 1.0
Nodes (0): 

### Community 28 - "Misc: content rationale 110"
Cohesion: 1.0
Nodes (1): Deserialize from dict, converting strings back to Enums and datetimes.

### Community 29 - "Misc: base scraper rationale 28"
Cohesion: 1.0
Nodes (1): Fetch latest content items from the source.          Subclasses must implement t

### Community 30 - "Misc: pipeline PipelineOptions"
Cohesion: 1.0
Nodes (1): PipelineOptions

### Community 31 - "Misc: extractor ExtractionConfig"
Cohesion: 1.0
Nodes (1): ExtractionConfig

### Community 32 - "Misc: scrapers RawItem"
Cohesion: 1.0
Nodes (1): RawItem

### Community 33 - "Misc: roadmap cycle3"
Cohesion: 1.0
Nodes (1): Cycle 3 Roadmap

### Community 34 - "Misc: roadmap cycle4"
Cohesion: 1.0
Nodes (1): Cycle 4 Roadmap

### Community 35 - "Misc: roadmap cycle5"
Cohesion: 1.0
Nodes (1): Cycle 5 Roadmap

### Community 36 - "Misc: spec cycle2"
Cohesion: 1.0
Nodes (1): Cycle 2 Spec — Curation Brain

### Community 37 - "Misc: spec webui unified"
Cohesion: 1.0
Nodes (1): Web UI LevelUp Unified Spec

### Community 38 - "Misc: arch system design"
Cohesion: 1.0
Nodes (1): Article-to-Image System Design

### Community 39 - "Misc: arch ux architecture"
Cohesion: 1.0
Nodes (1): imgGen UX Architecture

### Community 40 - "Misc: report automation pipeline"
Cohesion: 1.0
Nodes (1): Automation Pipeline Status Report

### Community 41 - "Misc: backlog levelup backlog"
Cohesion: 1.0
Nodes (1): LevelUp Development Backlog

### Community 42 - "Misc: concept token optimization"
Cohesion: 1.0
Nodes (1): Token Optimization (Haiku/Sonnet Tiering)

### Community 43 - "Misc: concept html css rendering"
Cohesion: 1.0
Nodes (1): HTML+CSS Rendering (No AI Image)

## Knowledge Gaps
- **140 isolated node(s):** `digest.py - Weekly digest synthesis from generation history.  Takes multiple art`, `Format generation history rows into a text block for the AI prompt.`, `Synthesize a digest from generation history via AI.      Args:         generatio`, `screenshotter.py - Playwright screenshot module  Takes screenshots of HTML conte`, `Async implementation of screenshot capture.      Args:         html_content: Ful` (+135 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Misc: config AccountConfig`** (2 nodes): `AccountConfig`, `LevelUpConfig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: scripts design review`** (2 nodes): `design_review_loop.py`, `Cycle 3 Spec v2`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: concept webui phases`** (2 nodes): `LevelUp Web UI Phase A-E`, `LevelUp Web UI Implementation Report`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: init`** (1 nodes): `__init__.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: content rationale 110`** (1 nodes): `Deserialize from dict, converting strings back to Enums and datetimes.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: base scraper rationale 28`** (1 nodes): `Fetch latest content items from the source.          Subclasses must implement t`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: pipeline PipelineOptions`** (1 nodes): `PipelineOptions`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: extractor ExtractionConfig`** (1 nodes): `ExtractionConfig`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: scrapers RawItem`** (1 nodes): `RawItem`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: roadmap cycle3`** (1 nodes): `Cycle 3 Roadmap`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: roadmap cycle4`** (1 nodes): `Cycle 4 Roadmap`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: roadmap cycle5`** (1 nodes): `Cycle 5 Roadmap`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: spec cycle2`** (1 nodes): `Cycle 2 Spec — Curation Brain`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: spec webui unified`** (1 nodes): `Web UI LevelUp Unified Spec`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: arch system design`** (1 nodes): `Article-to-Image System Design`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: arch ux architecture`** (1 nodes): `imgGen UX Architecture`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: report automation pipeline`** (1 nodes): `Automation Pipeline Status Report`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: backlog levelup backlog`** (1 nodes): `LevelUp Development Backlog`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: concept token optimization`** (1 nodes): `Token Optimization (Haiku/Sonnet Tiering)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Misc: concept html css rendering`** (1 nodes): `HTML+CSS Rendering (No AI Image)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PipelineOptions` connect `Audit & Review Workflow` to `AI Extraction Engine`, `Batch Processing`?**
  _High betweenness centrality (0.179) - this node is a cross-community bridge._
- **Why does `LevelUpConfig` connect `Audit & Review Workflow` to `Config & Account System`, `Misc: config levelupconfig save`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `render_and_capture()` connect `AI Extraction Engine` to `Misc: screenshotter`, `Misc: renderer`, `Smart Mode Dynamic Layouts`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `Content` (e.g. with `ContentDAO` and `src/db.py - Data Access Object for Content records in the LevelUp system.  Persi`) actually correct?**
  _`Content` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `ContentStatus` (e.g. with `ContentDAO` and `src/db.py - Data Access Object for Content records in the LevelUp system.  Persi`) actually correct?**
  _`ContentStatus` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 19 inferred relationships involving `ContentDAO` (e.g. with `Content` and `ContentStatus`) actually correct?**
  _`ContentDAO` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `LevelUpConfig` (e.g. with `scripts/audit.py — Human-in-the-loop content review system.  Usage:     python s` and `Print a single content card for review.`) actually correct?**
  _`LevelUpConfig` has 13 INFERRED edges - model-reasoned connections that need verification._