# Design Review Loop — 規劃文件

自動化設計審查腳本：截圖 → Claude CLI 視覺分析 → CSS 修正 → 循環，最多 5 次迭代。

---

## 整體架構

```
scripts/design_review_loop.py    ← 主腳本
prompts/design_review.txt        ← Claude CLI 系統提示詞
tests/test_design_review_loop.py ← TDD 測試
```

---

## 資料流

```
run(theme, template_path, max_iter=5)
  │
  ├─ ① generate_screenshot(theme)
  │       → output/review_iter_{n}.png
  │
  ├─ ② build_prompt(template_path, iteration)
  │       → 包含: CSS vars 清單 + 模板原始碼 + 設計規範
  │
  ├─ ③ call_claude_cli(image_path, prompt)
  │       → _compress_image_for_review(image_path)  ← tinify 壓縮
  │       → subprocess: claude -p - (base64 image 嵌入 prompt，經 stdin 傳入)
  │       → raw JSON string
  │
  ├─ ④ parse_review(raw) → ReviewResult
  │       score: int (1–10)
  │       issues: list[Issue]  (severity: CRITICAL/MAJOR/MINOR)
  │       css_patches: dict    ({--css-var: new_value}，僅自訂屬性)
  │       done: bool           (score >= 8 且無 CRITICAL)
  │       rationale: str
  │
  ├─ ⑤ if result.done → break，輸出報告
  │
  ├─ ⑥ apply_patches(template_path, css_patches)
  │       → 只套用 --var-name 格式的 patch（selector 格式一律跳過）
  │       → 備份原檔 template.html.bak_{n}
  │
  ├─ ⑦ 若 score < 前一次 → rollback 至備份，停止迭代
  │
  └─ 回到 ①，最多 5 次
```

---

## 核心模組與職責

六個純函數，每個都可以獨立測試。

```python
generate_screenshot(theme, output_path) -> Path
    # 調用既有 render_card + take_screenshot

build_prompt(template_path, iteration, css_var_list) -> str
    # 讀取 prompts/design_review.txt
    # 注入: 模板原始碼、CSS var 清單、迭代次數
    # 使用 str.replace() 替換佔位符（避免 .format() 誤解析 JSON 花括號）

_compress_image_for_review(image_path) -> bytes
    # 使用 tinify 壓縮 PNG（API key 由 TINIFY_API_KEY 環境變數或預設值提供）
    # 寫入暫存檔 → 讀回 bytes → 刪除暫存檔
    # 目的：將 ~1.6 MB 截圖壓縮至 ~100 KB，避免 Claude CLI 回報 Prompt too long

call_claude_cli(image_path, prompt, timeout=60) -> str
    # 呼叫 _compress_image_for_review 取得壓縮後 bytes
    # base64 編碼後嵌入 Markdown 圖片語法
    # 經 stdin 傳入 claude CLI（subprocess.run(["claude", "-p", "-"], input=...)）
    # 實際 timeout = 傳入值 × 3（Claude 回應時間較長）
    # 返回 stdout (raw JSON)

parse_review(raw_output) -> ReviewResult
    # 從 stdout 中萃取 JSON（允許前後有雜訊）
    # 驗證必要欄位
    # 強制規則：有 CRITICAL issue 時 done 永遠為 False

apply_patches(template_path, patches) -> list[str]
    # 備份原檔
    # 只套用 key 以 "--" 開頭的 CSS 自訂屬性 patch
    # selector >>> property 格式一律跳過（無法安全作用域）
    # 返回成功套用的 patch 清單
```

---

## 資料結構

```python
@dataclass
class Issue:
    severity: Literal["CRITICAL", "MAJOR", "MINOR"]
    description: str

@dataclass
class ReviewResult:
    score: int                  # 1–10，10 = 完美
    issues: list[Issue]
    css_patches: dict[str, str] # 僅 {"--var-name": new_value} 格式有效
    done: bool                  # True = score >= 8 且無 CRITICAL
    rationale: str              # 一句話總結
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

---

## Claude CLI Prompt 設計

`prompts/design_review.txt`

```
[PERSONA]
你是一位專注於社群媒體卡片設計的頂級 UI/UX 設計師，
精通移動端深色主題設計、版式層級與視覺重量分配。

[CONTEXT]
這是一張 1080×1920 社群媒體 Story 圖片截圖（迭代第 {iteration} 次）。
目標：視覺效果需貼近「在手機瀏覽器開啟手機版網頁」的飽滿感。
設計基準：dark_card.html（430px 移動端設計，經 meta viewport 縮放至畫布）。

[CSS VARIABLES AVAILABLE]
{css_var_list}

[TEMPLATE SOURCE]
{template_source}

[PATCH RULES — 嚴格遵守]
- css_patches 只能使用 CSS 自訂屬性格式：`"--var-name": "new-value"`
- 禁止使用 `selector >>> property` 格式
- 禁止修改 `*`、`html`、`body` 的任何屬性
- 禁止修改 `display`、`visibility`、`opacity` 屬性
- 每次最多建議 5 個 patch，聚焦最高影響力的變更

[TASK]
審查截圖，輸出**僅含 JSON** 的回覆（無其他文字）：

{
  "score": <1-10，10 = 完美>,
  "issues": [
    {"severity": "CRITICAL|MAJOR|MINOR", "description": "具體問題"}
  ],
  "css_patches": {
    "--var-name": "new-value"
  },
  "done": <score >= 8 且無 CRITICAL 則 true>,
  "rationale": "一句話總結當前最大問題"
}
```

### Image 傳入方式

```python
# tinify 壓縮後 base64 嵌入 prompt，經 stdin 傳入（避免 ARG_MAX 限制）
compressed_bytes = _compress_image_for_review(image_path)
image_b64 = base64.b64encode(compressed_bytes).decode()
image_block = f"![screenshot](data:image/png;base64,{image_b64})"
full_prompt = f"{image_block}\n\n{prompt_text}"

result = subprocess.run(["claude", "-p", "-"], input=full_prompt, ...)
```

---

## Patch 安全策略

### 為何禁止 `selector >>> property` 格式

原設計允許 `"selector >>> property": "new-value"`，但實作時發現：

- 現有 regex 實作（`(prop:\s*)[^;]+(;)`）沒有作用域，會全域替換所有符合的 property
- Claude 曾生成 `"* >>> margin": "26px"`，導致 `*, *::before, *::after { margin: 0 }` 被覆寫，版面完全崩壞

**決策**：`apply_patches` 只套用 `--var-name` 格式。CSS 自訂屬性名稱唯一，替換安全。

### Rollback 機制

每次迭代套用 patch 後，若下一次 score < 前一次 score：

1. 從 `.bak_{n}` 備份恢復 template
2. 停止迭代（不繼續惡化）

---

## TDD 測試計劃

`tests/test_design_review_loop.py`（22 個測試）

```python
class TestGenerateScreenshot:
    test_returns_path_that_exists()
    test_overwrites_existing_file()

class TestBuildPrompt:
    test_contains_iteration_number()
    test_contains_template_source()
    test_contains_css_var_list()

class TestCallClaudeCli:
    test_returns_string_output()           # mock _compress_image_for_review + subprocess
    test_raises_on_timeout()               # mock _compress_image_for_review + subprocess
    test_raises_on_nonzero_exit()          # mock _compress_image_for_review + subprocess

class TestParseReview:
    test_parses_valid_json()
    test_extracts_json_from_noisy_output() # JSON 前後有多餘文字
    test_raises_on_missing_score()
    test_done_is_false_when_critical_exists()

class TestApplyPatches:
    test_applies_css_var_patch()
    test_applies_multiple_patches()
    test_skips_selector_patches()          # selector >>> property 及 * 全域選擇器必須跳過
    test_preserves_unrelated_css()
    test_creates_backup_file()
    test_returns_list_of_applied_patches()

class TestRunLoop:
    test_stops_at_max_iterations()         # mock call_claude_cli
    test_stops_early_when_done_true()      # mock: done=True at iter 2
    test_applies_patches_each_iteration()
    test_returns_loop_summary()
```

---

## 執行介面

```bash
# 單一主題，預設 5 次迭代
.venv/bin/python scripts/design_review_loop.py --theme dark

# 指定最大迭代次數
.venv/bin/python scripts/design_review_loop.py --theme dark --max-iter 3

# 指定輸出目錄
.venv/bin/python scripts/design_review_loop.py --theme dark --output-dir output/review/
```

### 手動生成截圖（main.py）

```bash
# 生成 dark 主題圖片
.venv/bin/python main.py --text "文章內容..." --theme dark --output test_dark.png
```

### 終端輸出範例

```
[Iter 1/5] score=6  CRITICAL:0 MAJOR:2 MINOR:2  → applying 5 patches
           "Hero card 背景過淡使最重要的 #01 要點淹沒在頁面中"

[Iter 2/5] score=7  CRITICAL:0 MAJOR:1 MINOR:2  → applying 5 patches
           "Hero card 背景與邊框強度不足，視覺層級差異偏弱"

[Iter 3/5] score=5  CRITICAL:0 MAJOR:2 MINOR:2  → applying 4 patches
           "accent-bg opacity 不足..."
           ⚠ 分數下降（7→5），已 rollback，停止迭代

✗ 達到最大迭代次數（5 次），未達標準
  最終截圖: output/review_iter_3.png
  報告:     output/design_review_dark_20260328.json
```

---

## 實作順序（TDD）

1. **RED**：寫完 `tests/test_design_review_loop.py` 所有測試（全部失敗）
2. 建立 `prompts/design_review.txt`
3. **GREEN**：實作 `scripts/design_review_loop.py` 讓所有測試通過
4. **整合測試**：實際執行一輪 loop 驗證端到端流程

---

## 依賴

- Python 標準庫：`subprocess`, `json`, `re`, `base64`, `os`, `tempfile`, `pathlib`, `dataclasses`
- 專案既有：`src.renderer.render_card`, `src.screenshotter.take_screenshot`
- 外部：`claude` CLI（需在 PATH 中）
- 外部：`tinify`（`pip install tinify`）、API key 由 `TINIFY_API_KEY` 環境變數提供
