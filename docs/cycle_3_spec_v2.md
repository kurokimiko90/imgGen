# Cycle 3 實施規格：Smart Mode + Design Review Loop

**版本**: 2.0（Planner Agent 產出，基於原始碼驗證）
**日期**: 2026-03-31
**評分**: 125（Smart Mode）/ 75（Design Review Loop）
**時程**: 第 3-4 週（與 Cycle 2 並行）

---

## 一、執行目標與成功指標

### 目標

將已完成的 Smart Mode 核心（`src/smart_renderer.py`、`src/extractor.py` 的 smart prompt）與尚未建立的 Design Review Loop 整合為完整的端到端功能，涵蓋 CLI、Web API、前端切換、以及自動化設計審查迴圈。

### 成功指標

| # | 指標 | 量化 |
|---|------|------|
| S1 | `--mode smart` CLI 執行產出 AI 動態圖卡 | 100% 成功率（含 fallback） |
| S2 | `--mode card` / `--mode article` 行為不變 | 現有測試全過，regression 0 |
| S3 | Design Review Loop 22 個測試全過 | 22/22 pass |
| S4 | Web UI Smart Mode toggle 可切換並正確呼叫 API | 手動驗證 |
| S5 | Pipeline 測試覆蓋 smart 路徑 | 新增 3+ 測試 |

---

## 二、前置依賴盤點

### 已完成（可直接複用）

| 模組 | 狀態 | 關鍵簽名 |
|------|------|---------|
| `src/smart_renderer.py` | ✅ 已完成 | `generate_smart_html(data, card_format, provider, color_mood, watermark_data, watermark_position, watermark_opacity, brand_name, thread_index, thread_total) -> str`（第 433-464 行） |
| `src/extractor.py` — smart prompt | ✅ 已完成 | `_build_smart_prompt(config)` 第 150-220 行；`_validate_smart_data(data, cfg)` 第 537-573 行 |
| `src/extractor.py` — `ExtractionConfig.mode` | ✅ 已完成 | `mode: str = "card"` 支援 `"card"` / `"article"` / `"smart"`（第 30 行） |
| `src/pipeline.py` — smart 路由 | ✅ 已完成 | `render_and_capture()` 第 81-93 行已有 `if options.mode == "smart"` 分支 |
| `src/pipeline.py` — `PipelineOptions.mode` | ✅ 已完成 | `mode: str = "card"` 第 33 行，已支援 `"smart"` |
| `main.py` — `--mode` 選項 | ✅ 已完成 | `--mode [card\|article\|smart]` 第 223-227 行 |
| `main.py` — smart mode CLI 輸出 | ✅ 已完成 | 第 545-547 行已印出 layout_hint、color_mood |
| `prompts/smart_layout_system.txt` | ✅ 已完成 | 30 行系統提示詞 |

### 需要新建

| 模組 | 說明 |
|------|------|
| `scripts/design_review_loop.py` | Design Review Loop 主腳本（6 個核心函數） |
| `prompts/design_review.txt` | Claude CLI 設計審查提示詞 |
| `tests/test_design_review_loop.py` | 22 個 TDD 測試 |
| `tests/test_smart_pipeline.py` | Smart mode pipeline 整合測試（3 個） |

### 需要修改

| 模組 | 說明 |
|------|------|
| `main.py` | 新增 `--color-mood` CLI 選項 |
| `src/pipeline.py` | `PipelineOptions` 新增 `color_mood`；`render_and_capture` 傳遞至 `generate_smart_html` |
| `web/api.py` | `GenerateRequest` 新增 `mode` + `color_mood`；`/api/meta` 新增 smart mode 元資料 |
| `requirements.txt` | 新增 `tinify>=2.0.0` |

---

## 三、現有 API 簽名確認（Planner Agent 實際讀取原始碼）

### 3.1 `src/smart_renderer.py` — `generate_smart_html()`

**第 433-464 行**：
```python
def generate_smart_html(
    data: dict[str, Any],
    card_format: str = "story",
    provider: str = "cli",
    color_mood: str | None = None,
    watermark_data: str | None = None,
    watermark_position: str = "bottom-right",
    watermark_opacity: float = 0.8,
    brand_name: str | None = None,
    thread_index: int | None = None,
    thread_total: int | None = None,
) -> str:
```
**結論**: 無需修改。

### 3.2 `src/pipeline.py` — `PipelineOptions` + `render_and_capture`

- `PipelineOptions`（第 19-33 行）：已含 `mode: str = "card"`
- `render_and_capture()`（第 81-93 行）：已有 `if options.mode == "smart"` 分支

**⚠️ 關鍵發現**：`render_and_capture` 呼叫 `generate_smart_html` 時**沒有傳遞 `color_mood`**（第 83-93 行）。這是 Cycle 3 要修復的核心缺口。

### 3.3 `src/extractor.py` — `ExtractionConfig`

- `ExtractionConfig`（第 19-30 行）：`mode: str = "card"` 已支援 `"smart"`
- Smart mode 驗證（第 537-573 行）：已完成 `content_type`、`layout_hint`、`color_mood` 正規化

**結論**: 無需修改。

### 3.4 `main.py` — 現有 Click 選項

已有選項（第 193-337 行）：`--text`, `--file`, `--url`, `--theme`, `--provider`, `--mode`, `--output`, `--format`, `--formats`, `--clipboard`, `--caption`, `--thread`, `--post`, `--scale`, `--webp/--no-webp`, `--config`, `--watermark`, `--watermark-position`, `--watermark-opacity`, `--brand-name`, `--batch`, `--workers`, `--output-dir`, `--preset`

**缺少**: `--color-mood`。第 571-572 行和第 608-609 行的 `PipelineOptions` 建構未傳遞 `color_mood`。

### 3.5 `web/api.py` — 現有 Endpoint

- `GenerateRequest`（第 77-91 行）：**缺少 `mode` 和 `color_mood` 欄位**
- `POST /api/generate`（第 171-225 行）：`PipelineOptions` 建構未傳遞 `mode`
- `GET /api/meta`（第 491-498 行）：只回傳 themes、formats、providers，**缺少 modes、color_moods、layout_patterns**

---

## 四、任務分解

### Phase 1：Pipeline 補丁 — `color_mood` 傳遞（修復已知缺口）

#### 任務 1.1：`PipelineOptions` 新增 `color_mood`

**檔案**: `src/pipeline.py`，第 19-33 行

**Before**:
```python
    mode: str = "card"  # "card", "article", or "smart"
```

**After**:
```python
    mode: str = "card"  # "card", "article", or "smart"
    color_mood: str | None = None  # smart mode color palette override
```

#### 任務 1.2：`render_and_capture` 傳遞 `color_mood`

**檔案**: `src/pipeline.py`，第 83-93 行

**Before**:
```python
        html_content = generate_smart_html(
            data,
            card_format=options.format,
            provider=options.provider,
            watermark_data=options.watermark_data,
            ...
        )
```

**After**: 新增一行 `color_mood=options.color_mood,`

**驗收**: `generate_smart_html` 收到使用者指定的 `color_mood`
**風險**: 低 — `color_mood=None` 時行為與原本完全相同

---

### Phase 2：CLI 新增 `--color-mood`

#### 任務 2.1：新增 Click 選項

**檔案**: `main.py`，第 227 行後

```python
@click.option(
    "--color-mood",
    default=None,
    type=click.Choice(
        ["dark_tech", "warm_earth", "clean_light", "bold_contrast", "soft_pastel"],
        case_sensitive=False,
    ),
    help="Color mood for smart mode. If omitted, AI auto-selects. [smart mode only]",
)
```

#### 任務 2.2：傳遞 `color_mood` 至 `PipelineOptions`

**檔案**: `main.py`，第 562-572 行（thread mode）和第 599-609 行（normal mode）

在所有 `PipelineOptions(...)` 建構中新增 `color_mood=color_mood,`

**驗收**:
```bash
python main.py --text "..." --mode smart --color-mood warm_earth  # 指定色彩
python main.py --text "..." --mode smart                          # AI 自動選
python main.py --text "..." --mode card --color-mood dark_tech    # 忽略，不影響 card
```

---

### Phase 3：Web API 支援 Smart Mode

#### 任務 3.1：`GenerateRequest` 新增欄位

**檔案**: `web/api.py`，第 77-91 行

新增：
```python
    mode: str = "card"  # "card", "article", or "smart"
    color_mood: str | None = None  # smart mode only
```

#### 任務 3.2：`/api/generate` 傳遞 `mode` 和 `color_mood`

**檔案**: `web/api.py`，第 181-191 行

新增 `mode=req.mode, color_mood=req.color_mood,` 至 `PipelineOptions` 建構。

修改 `_to_extraction_config()`（第 154-158 行）讓它接受 `mode` 參數：

```python
def _to_extraction_config(
    req_config: ExtractionConfigRequest | None,
    mode: str = "card",
) -> ExtractionConfig | None:
    if req_config is None:
        return ExtractionConfig(mode=mode) if mode != "card" else None
    return ExtractionConfig(**req_config.model_dump(), mode=mode)
```

#### 任務 3.3：`/api/generate/multi` 同步修改

與 3.2 同理。

#### 任務 3.4：`/api/meta` 新增 smart mode 元資料

**檔案**: `web/api.py`，第 491-498 行

```python
    from src.smart_renderer import COLOR_PALETTES, LAYOUT_PATTERNS
    return _ok(
        themes=sorted(VALID_THEMES),
        formats=sorted(VALID_FORMATS),
        providers=["cli", "claude", "gemini", "gpt"],
        modes=["card", "article", "smart"],
        color_moods=sorted(COLOR_PALETTES.keys()),
        layout_patterns={k: v for k, v in LAYOUT_PATTERNS.items()},
    )
```

---

### Phase 4：Design Review Loop（獨立，可與 Phase 1-3 並行）

#### 任務 4.1：`prompts/design_review.txt`（新建）

包含佔位符：`{iteration}`、`{css_var_list}`、`{template_source}`

#### 任務 4.2：資料結構定義

```python
@dataclass
class Issue:
    severity: Literal["CRITICAL", "MAJOR", "MINOR"]
    description: str

@dataclass
class ReviewResult:
    score: int           # 1-10
    issues: list[Issue]
    css_patches: dict[str, str]
    done: bool
    rationale: str
    iteration: int

@dataclass
class LoopSummary:
    theme: str
    total_iterations: int
    final_score: int
    done: bool
    final_screenshot: Path
    report_path: Path
    history: list[ReviewResult]
```

#### 任務 4.3-4.8：六個核心函數

| 函數 | 說明 |
|------|------|
| `generate_screenshot(theme, output_path) -> Path` | 用 Playwright 截圖 |
| `build_prompt(template_path, iteration, css_var_list) -> str` | 組合視覺截圖 + CSS 變數 + 模板原始碼 |
| `_compress_image_for_review(image_path) -> bytes` | tinify 壓縮 → base64 |
| `call_claude_cli(image_path, prompt, timeout=60) -> str` | Claude CLI stdin pipe |
| `parse_review(raw_output, iteration=1) -> ReviewResult` | JSON 萃取 + 驗證 |
| `apply_patches(template_path, patches, iteration) -> list[str]` | 只接受 `--var-name` 格式 |

#### 任務 4.9：`run()` 主迴圈

```python
def run(theme: str, template_path: Path, max_iter: int = 5, output_dir: Path | None = None) -> LoopSummary:
```

迴圈控制：
- `done=True` → 停止
- `max_iter` 到達 → 停止
- score 下降 → rollback 上一版 → 停止
- 有 CRITICAL issue → `done` 強制為 `False`

#### 任務 4.10：CLI 入口

```bash
python scripts/design_review_loop.py --theme dark
python scripts/design_review_loop.py --theme dark --max-iter 3
```

---

### Phase 5：Web UI 前端切換

Generate 頁新增：
- Smart / Template 切換 toggle
- 色彩心情選擇器（5 mood，含色票預覽）
- 佈局模式說明（7 種，hover 顯示描述）
- Smart 模式下隱藏 Theme 選擇器

**依賴**: Phase 3（`/api/meta` 提供元資料）

---

## 五、測試清單

### Design Review Loop 測試（22 個）

| # | 類別 | 測試名稱 |
|---|------|---------|
| 1 | GenerateScreenshot | `test_returns_path_that_exists` |
| 2 | GenerateScreenshot | `test_overwrites_existing_file` |
| 3 | BuildPrompt | `test_contains_iteration_number` |
| 4 | BuildPrompt | `test_contains_template_source` |
| 5 | BuildPrompt | `test_contains_css_var_list` |
| 6 | CallClaudeCli | `test_returns_string_output` |
| 7 | CallClaudeCli | `test_raises_on_timeout` |
| 8 | CallClaudeCli | `test_raises_on_nonzero_exit` |
| 9 | ParseReview | `test_parses_valid_json` |
| 10 | ParseReview | `test_extracts_json_from_noisy_output` |
| 11 | ParseReview | `test_raises_on_missing_score` |
| 12 | ParseReview | `test_done_is_false_when_critical_exists` |
| 13 | ApplyPatches | `test_applies_css_var_patch` |
| 14 | ApplyPatches | `test_applies_multiple_patches` |
| 15 | ApplyPatches | `test_skips_selector_patches` |
| 16 | ApplyPatches | `test_preserves_unrelated_css` |
| 17 | ApplyPatches | `test_creates_backup_file` |
| 18 | ApplyPatches | `test_returns_list_of_applied_patches` |
| 19 | RunLoop | `test_stops_at_max_iterations` |
| 20 | RunLoop | `test_stops_early_when_done_true` |
| 21 | RunLoop | `test_applies_patches_each_iteration` |
| 22 | RunLoop | `test_returns_loop_summary` |

### Smart Pipeline 測試（3 個）

| # | 測試名稱 |
|---|---------|
| 1 | `test_smart_mode_calls_smart_renderer` |
| 2 | `test_card_mode_calls_renderer` |
| 3 | `test_color_mood_override` |

---

## 六、依賴關係圖

```
Phase 1: Pipeline 補丁
  1.1 (PipelineOptions +color_mood)
      └── 1.2 (render_and_capture 傳遞)
              ├── Phase 2: CLI (--color-mood)
              └── Phase 3: Web API (mode + color_mood)
                      └── Phase 5: Web UI 前端

Phase 4: Design Review Loop（獨立，可與 Phase 1-3 並行）
  4.1 (prompt) → 4.4 (build_prompt)
  4.5 (compress) → 4.6 (call_claude_cli)
  4.2-4.8 全部完成 → 4.9 (run 主迴圈) → 4.10 (CLI)
```

**關鍵**：Phase 1-3 與 Phase 4 可完全並行。

---

## 七、實施順序建議

**線 A（Smart Mode 管線整合，~0.5 天）**：
1. 寫 `tests/test_smart_pipeline.py`（RED）
2. Phase 1 → Phase 2 → Phase 3（GREEN）
3. Phase 5（Web UI）

**線 B（Design Review Loop，~2 天）**：
1. 寫 `tests/test_design_review_loop.py` 全 22 個（RED）
2. 建立 `prompts/design_review.txt`
3. 實作 `scripts/design_review_loop.py`（GREEN）

---

## 八、風險與緩解

| 風險 | 嚴重度 | 緩解 |
|------|--------|------|
| Claude CLI 回應超時 | 高 | timeout x 3（預設 180 秒），超時拋 `TimeoutError` |
| tinify API key 未設定 | 中 | fallback 至原始檔案 |
| CSS patch 破壞模板 | 高 | 只接受 `--var-name` 格式 + score 下降自動 rollback |
| `generate_smart_html` 輸出無效 HTML | 中 | 已有二次重試 + template fallback（第 473-499 行） |
| Web API `mode` 破壞前端 | 低 | 預設值 `"card"`，不傳時行為不變 |

---

## 九、驗收檢查清單

### Pipeline 整合
- [ ] `python main.py --text "..." --mode smart` 成功產出圖卡
- [ ] `python main.py --text "..." --mode smart --color-mood warm_earth` 使用指定色彩
- [ ] `--mode card` 和 `--mode article` 零回歸

### Design Review Loop
- [ ] `python scripts/design_review_loop.py --theme dark` 完成至少一次迭代
- [ ] Score 下降時自動 rollback 並停止
- [ ] 輸出 JSON 報告
- [ ] 22 個測試全過

### Web API
- [ ] `POST /api/generate` 接受 `mode: "smart"` 和 `color_mood`
- [ ] `GET /api/meta` 回傳 `modes`、`color_moods`、`layout_patterns`

### 向後相容
- [ ] 所有新增參數皆有預設值，不傳時行為不變
- [ ] 現有所有測試不受影響
