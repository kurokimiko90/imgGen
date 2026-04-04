# Cycle 3 實施規格 — Smart Mode + Design Review Loop

**版本**: 1.0
**日期**: 2026-03-31
**評分**: 125（Smart Mode）/ 75（Design Review Loop）
**時程**: 第 3-4 週（與 Cycle 2 並行）
**PM Agent 輸出**

---

## 執行目標

將已完成的 `src/smart_renderer.py` 整合進 CLI 和 Web UI，並建立 Design Review Loop 自動化視覺品控腳本。

**成功指標**：
- `--mode smart` 可正常生成 AI 動態排版圖卡
- `--mode card` 行為零回歸
- Design Review Loop 22 個測試全過
- Web UI Smart Mode toggle 可切換並正確呼叫 API

---

## 前置依賴

- `src/smart_renderer.py` ✅ 已完成
- `prompts/smart_layout_system.txt` ✅ 已存在
- Cycle 1（Content 模型 + DB）✅ 已完成

---

## 任務分解

### 任務 1：CLI 整合

**修改檔案**: `main.py`

**變更內容**：

```python
# 新增 Click 選項
@click.option('--mode', type=click.Choice(['card', 'article', 'smart']), default='card',
              help='生成模式：card（預設）、article、smart（AI 動態排版）')
@click.option('--color-mood', type=click.Choice([
    'dark_tech', 'warm_earth', 'clean_light', 'bold_contrast', 'soft_pastel'
]), default=None, help='Smart 模式色彩心情（留空由 AI 自動選）')
```

**行為規則**：
- `--mode card`（預設）：走現有 `renderer.render_card()` 路徑，完全不變
- `--mode article`：走現有 article 路徑，完全不變
- `--mode smart`：走 `smart_renderer.generate_smart_html()` 路徑
- `--color-mood` 僅在 `--mode smart` 時生效；其他模式忽略並顯示 warning

**驗收標準**：
- [ ] `python main.py --text "..." --mode smart` 正常輸出圖卡
- [ ] `python main.py --text "..." --mode card` 行為與修改前完全一致
- [ ] `--color-mood` 在非 smart 模式下顯示 warning 並忽略

**依賴**: 無（smart_renderer.py 已存在）

---

### 任務 2：Pipeline 路由

**修改檔案**: `src/pipeline.py`

**變更內容**：

```python
from src.smart_renderer import generate_smart_html

def run_pipeline(input_text, mode='card', color_mood=None, theme=None, format='story', ...):
    # Step 1: Extract
    if mode == 'smart':
        data = extract(input_text, mode='smart')  # 需要額外欄位
    else:
        data = extract(input_text, mode=mode)

    # Step 2: Render
    if mode == 'smart':
        html = generate_smart_html(
            data,
            color_mood=color_mood,  # None = AI 自動選
            format=format
        )
    elif mode == 'article':
        html = render_article(data, theme=theme, format=format)
    else:
        html = render_card(data, theme=theme, format=format)

    # Step 3: Screenshot（不變）
    output_path = take_screenshot(html, format=format)
    return output_path
```

**行為規則**：
- `mode='card'` 和 `mode='article'` 走完全相同的舊路徑
- `mode='smart'` 路由至 `smart_renderer`
- `color_mood=None` 時由 AI 在 extraction 階段自動選擇

**驗收標準**：
- [ ] Smart 模式正確呼叫 `generate_smart_html()`
- [ ] Card / Article 模式不受任何影響
- [ ] color_mood 傳遞正確

**依賴**: 任務 1

---

### 任務 3：Extractor Smart 模式擴展

**修改檔案**: `src/extractor.py`

**新增 Smart 模式 Prompt**：

當 `mode='smart'` 時，Prompt 要求 AI 額外輸出以下欄位：

```json
{
  "title": "15字以內",
  "key_points": [
    {"text": "要點內容", "importance": 5}
  ],
  "layout_hint": "hero_list|grid|timeline|comparison|quote_centered|data_dashboard|numbered_ranking",
  "color_mood": "dark_tech|warm_earth|clean_light|bold_contrast|soft_pastel",
  "content_type": "news|analysis|tutorial|quote|data",
  "source": "來源"
}
```

**實作方式**：

```python
# ExtractionConfig 新增
@dataclass
class ExtractionConfig:
    # ... 現有欄位 ...
    mode: str = 'card'  # 'card' | 'article' | 'smart'

# extract() 內部
if config.mode == 'smart':
    system_prompt = load_smart_prompt()  # 載入 prompts/smart_layout_system.txt
    # 附加 JSON schema 要求
    # 附加 importance + layout_hint + color_mood 欄位要求
```

**驗收標準**：
- [ ] `extract(text, mode='smart')` 回傳含 `layout_hint` 和 `color_mood` 的 JSON
- [ ] `extract(text, mode='card')` 回傳格式與修改前完全一致
- [ ] `importance` 欄位為 1-5 整數

**依賴**: 無

---

### 任務 4：Design Review Loop

**新建檔案**: `scripts/design_review_loop.py`

**規格來源**: `docs/design_review_loop.md`（完整 22 個測試定義）

**七步驟流程**：

```
① generate_screenshot(template_path, theme, format)
    → 用 Playwright 截圖，輸出 PNG

② build_prompt(screenshot_path, css_vars, template_source)
    → 組合視覺截圖 + CSS 變數 + 模板原始碼
    → 生成結構化 Prompt 給 Claude

③ compress_image(screenshot_path)
    → tinify API 壓縮（節省 token）
    → 轉 base64

④ call_claude_cli(prompt, image_base64)
    → 透過 Claude CLI（stdin pipe）呼叫視覺評審
    → 回傳 JSON 評審結果

⑤ parse_review(raw_response) → ReviewResult
    → ReviewResult: {score: int, issues: list, css_patches: list, done: bool}
    → score: 1-10
    → done: True 當 score ≥ 8 且無 CRITICAL issue

⑥ apply_patches(template_path, css_patches)
    → 只套用 CSS variable 格式的修改（--var-name: value）
    → 拒絕任何非 CSS variable 的修改（安全機制）

⑦ 迴圈控制
    → 最多 max_iter 次（預設 5）
    → score 下降 → rollback 上一版 → 停止
    → done=True → 停止
```

**主函數**：

```python
@dataclass
class ReviewResult:
    score: int           # 1-10
    issues: list[str]    # 問題描述列表
    css_patches: list[dict]  # [{"var": "--bg-color", "value": "#1a1a2e"}]
    done: bool           # True = 品質達標

@dataclass
class LoopSummary:
    iterations: int
    initial_score: int
    final_score: int
    applied_patches: int
    stopped_reason: str  # "quality_met" | "max_iterations" | "score_declined" | "error"

def run(theme: str, template_path: str, max_iter: int = 5) -> LoopSummary:
    """執行設計審查迴圈"""
    ...
```

**驗收標準**：
- [ ] 七步驟各自可獨立測試
- [ ] CSS patch 只接受 `--var-name` 格式
- [ ] Score 下降時自動 rollback 並停止
- [ ] max_iter 到達時停止

**依賴**: tinify API key（環境變數 `TINIFY_API_KEY`）, Claude CLI

---

### 任務 5：Web UI Smart Mode 切換

**修改檔案**: `web/frontend/src/` 相關元件, `web/api.py`

**前端變更**：

```
Generate 頁新增：
├── Smart / Template 切換 toggle（預設 Template）
├── 色彩心情選擇器（Smart 模式下顯示）
│   ├── dark_tech     → 深色科技（色票：#0f0f23, #00d4ff）
│   ├── warm_earth    → 暖色大地（色票：#8B4513, #D2691E）
│   ├── clean_light   → 清爽明亮（色票：#FAFAFA, #2196F3）
│   ├── bold_contrast → 大膽對比（色票：#FF6B35, #004E89）
│   └── soft_pastel   → 柔和粉彩（色票：#FFB5E8, #B5DEFF）
├── 佈局模式說明（Smart 模式下顯示，hover 顯示描述）
│   ├── hero_list          → 主視覺 + 列表
│   ├── grid               → 網格排列
│   ├── timeline           → 時間軸
│   ├── comparison         → 比較對照
│   ├── quote_centered     → 引言置中
│   ├── data_dashboard     → 數據儀表板
│   └── numbered_ranking   → 排名列表
└── 當 toggle = Smart 時，隱藏 Theme 選擇器（由 AI 決定）
```

**後端 API 變更**：

```python
# web/api.py

@app.post("/api/generate")
async def generate(request: GenerateRequest):
    # 新增 mode 和 color_mood 參數
    # mode: "card" | "article" | "smart"
    # color_mood: Optional[str]
    ...
```

**驗收標準**：
- [ ] Toggle 切換正常，Smart 模式下顯示色彩心情和佈局說明
- [ ] Template 模式下隱藏 Smart 專屬控件
- [ ] API 正確處理 mode=smart 請求

**依賴**: 任務 1-3（後端路由完成後才能前端整合）

---

### 任務 6：測試套件

**檔案**：

```
tests/test_smart_pipeline.py
  test_smart_mode_calls_smart_renderer()     # mock smart_renderer
  test_card_mode_calls_renderer()            # 確認不影響現有行為
  test_article_mode_calls_article_renderer() # 確認不影響現有行為
  test_color_mood_override()                 # 指定 mood 時傳遞正確
  test_color_mood_none_uses_ai()             # None 時由 AI 選

tests/test_smart_extractor.py
  test_smart_mode_returns_layout_hint()      # 回傳含 layout_hint
  test_smart_mode_returns_color_mood()       # 回傳含 color_mood
  test_smart_mode_returns_importance()       # key_points 含 importance
  test_card_mode_unchanged()                 # card 模式格式不變

tests/test_design_review_loop.py（22 個，per docs/design_review_loop.md）
  TestGenerateScreenshot:
    test_screenshot_created()                # PNG 檔案存在
    test_screenshot_dimensions()             # 符合 format 尺寸

  TestBuildPrompt:
    test_prompt_contains_css_vars()          # Prompt 包含 CSS 變數
    test_prompt_contains_template_source()   # Prompt 包含模板原始碼
    test_prompt_contains_image()             # Prompt 包含截圖 base64

  TestCallClaudeCli:
    test_returns_json()                      # 回傳有效 JSON
    test_handles_timeout()                   # 超時處理
    test_handles_invalid_response()          # 無效回應處理

  TestParseReview:
    test_extracts_score()                    # score 1-10
    test_extracts_issues()                   # issues 列表
    test_extracts_css_patches()              # css_patches 列表
    test_handles_malformed_json()            # 畸形 JSON 處理

  TestApplyPatches:
    test_applies_css_variable()              # --var-name 正確套用
    test_rejects_non_variable()              # 拒絕非 CSS variable
    test_multiple_patches()                  # 多個 patch 依序套用
    test_rollback_on_failure()               # 失敗時回滾
    test_preserves_non_patched_vars()        # 未修改的變數不動
    test_empty_patches_noop()               # 空 patch 列表不動

  TestRunLoop:
    test_stops_on_quality_met()              # score ≥ 8 + done → 停止
    test_stops_on_max_iterations()           # 達到 max_iter → 停止
    test_stops_on_score_decline()            # score 下降 → rollback → 停止
    test_returns_loop_summary()              # 回傳 LoopSummary
```

**驗收標準**：
- [ ] 22 個 Design Review Loop 測試全過
- [ ] Smart pipeline 測試全過
- [ ] 總覆蓋率 ≥ 80%

**依賴**: 任務 1-5

---

## 交付物總覽

| 交付物 | 類型 | 路徑 | 狀態 |
|--------|------|------|------|
| CLI 旗標 | Python (修改) | `main.py` | 待改 |
| Pipeline 路由 | Python (修改) | `src/pipeline.py` | 待改 |
| Extractor 擴展 | Python (修改) | `src/extractor.py` | 待改 |
| Design Review Loop | Python (新建) | `scripts/design_review_loop.py` | 待建 |
| Web UI 元件 | React (修改) | `web/frontend/src/` | 待改 |
| API 擴展 | Python (修改) | `web/api.py` | 待改 |
| Pipeline 測試 | Python (新建) | `tests/test_smart_pipeline.py` | 待建 |
| Extractor 測試 | Python (新建) | `tests/test_smart_extractor.py` | 待建 |
| DRL 測試 | Python (新建) | `tests/test_design_review_loop.py` | 待建 |
| 本文檔 | MD | `docs/cycle_3_spec.md` | ✅ |

---

## 依賴關係

```
任務 3 (Extractor 擴展)
    ↓
任務 2 (Pipeline 路由) ← 需要 Extractor smart 模式
    ↓
任務 1 (CLI 整合) ← 需要 Pipeline 路由
    ↓
任務 5 (Web UI) ← 需要後端 API 完成

任務 4 (Design Review Loop) ← 獨立，可與 1-3 並行開發
任務 6 (測試) ← 需要所有實作完成
```

**建議實施順序**：
1. 任務 3 → 任務 2 → 任務 1（Pipeline 鏈，循序）
2. 任務 4（與上述並行）
3. 任務 5（等後端完成）
4. 任務 6（最後驗證）

---

## 風險 & 緩解

| 風險 | 緩解策略 |
|------|---------|
| smart_renderer.py 與 pipeline 整合不一致 | 先讀 smart_renderer 的 API 簽名，確認參數對應 |
| Extractor smart 模式 Prompt 品質不穩 | 設計 fallback：若缺欄位，用預設值填充 |
| Design Review Loop tinify API 限制 | 免費方案 500 次/月，開發階段夠用；CI 用 mock |
| Web UI 改動影響現有功能 | Smart 控件隱藏在 toggle 後，不動 Template 模式 UI |

---

## 驗收檢查清單

- [ ] `--mode smart` 端到端生成圖卡
- [ ] `--mode card` 零回歸（輸出與修改前一致）
- [ ] `--color-mood` 正確傳遞至 smart_renderer
- [ ] Design Review Loop 七步驟各自通過單元測試
- [ ] CSS patch 安全機制有效（拒絕非 variable）
- [ ] Web UI toggle 正常切換
- [ ] 22 + 9 = 31 個新測試全過
- [ ] 覆蓋率 ≥ 80%
