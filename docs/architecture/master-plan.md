# LevelUp 系統開發規劃

**基礎文件**: `docs/docs/levelUpPRD.md`
**版本**: 2.1
**日期**: 2026-03-31

---

## 目標

建立一個 AI 驅動的自動化系統，讓一個人同時高品質運營三個垂直社群帳號：
- **帳號 A**：AI 自動化（Build in Public）→ Threads、X
- **帳號 B**：PMP 職涯（高淨值變現）→ Threads、LinkedIn
- **帳號 C**：足球英文（流量沙盒）→ Threads、X、IG

**成功指標（12 週後）**：每日內容生產時間 < 30 分鐘 / 三帳號各 5 篇/週穩定更新

---

## imgGen 現有能力（可直接複用）

| 能力 | 複用方式 |
|------|---------|
| AI 摘要（Claude/Gemini/GPT）| 策展大腦的 Transform 層 |
| 28 種圖卡模板 + Smart Mode | 各帳號圖文內容的視覺輸出 |
| Playwright 截圖 | 圖卡生成自動化 |
| SQLite history.db | 擴展為內容狀態機資料庫 |
| Twitter/X 發布 | 發布管線（帳號 A、C）|
| Telegram Bot | 素材接收頻道 |
| 定時發布（APScheduler）| 黃金時段精準打擊 |

---

## 評分矩陣（User Impact × Feasibility × WOW）

| 功能 | 衝擊 | 可行性 | WOW | **總分** |
|------|:---:|:---:|:---:|:---:|
| Smart Mode + AI 自動選主題 | 5 | 5 | 5 | **125** |
| HITL 審核系統（audit.py 狀態機） | 5 | 5 | 4 | **100** |
| 策展大腦（RSS 爬蟲 + 3 帳號 AI Prompt）| 5 | 4 | 4 | **80** |
| Design Review Loop | 3 | 5 | 5 | **75** |
| 跨平台發布（Threads + X Adapter）| 5 | 3 | 4 | **60** |
| 先知模組（行事曆 + 預測內容）| 4 | 3 | 5 | **60** |
| 互動引擎（回覆 + 點讚 + 防封號）| 4 | 3 | 4 | **48** |
| 數據分析迴圈（Pandas + Prompt 回饋）| 3 | 4 | 4 | **48** |

---

## 文檔輸出策略

| Cycle | 文檔輸出 |
|-------|---------|
| Cycle 1–4（優先模塊） | **開始前**產出 `docs/cycle_N_spec.md`（PM Agent 輸出）；**完成後**更新 master-plan.md + PRD.md + PLAN.md |
| Cycle 5–8（後段模塊） | 僅**完成後**更新 master-plan.md + PRD.md |

---

## 執行規劃

---

### ★ Cycle 1｜基礎建設（週 1-2）✅ 完成

**評分**：地基，可行性最高
**文檔輸出**：開始前產出 `docs/cycle_1_spec.md` ✅
**Agent / Skill**：`architect` → `/database-migrations` → `tdd-guide` ✅
**完成日期**：2026-03-31

#### 交付物總結

| 項目 | 路徑 | 狀態 |
|------|------|------|
| 實施規格 | `docs/cycle_1_spec.md` | ✅ |
| 遷移腳本 | `src/migrations/001_add_levelup_columns.sql` | ✅ |
| Content 模型 | `src/content.py` | ✅ |
| DAO 層 | `src/db.py` | ✅ |
| 配置管理 | `src/config.py` (LevelUp 擴展) | ✅ |
| 帳號配置 | `~/.imggen/accounts.toml` | ✅ |
| 單元測試 | `tests/test_content.py` (24 tests) | ✅ |
| 整合測試 | `tests/test_db.py` (14 tests) + `tests/test_levelup_config.py` (8 tests) | ✅ |
| 測試覆蓋率 | `src/content.py` 100%, `src/db.py` 100%, `src/config.py` 100% | ✅ |

#### 測試結果
```
69 tests passed
- ContentStatus 合法/非法轉換全覆蓋
- Content 序列化往返無損
- DAO CRUD 操作正常
- LevelUpConfig TOML 解析正常
```

#### 核心實施

✅ **1. SQLite Schema 遷移完成**
- 9 個新欄位已新增至 `src/migrations/001_add_levelup_columns.sql`
- 所有欄位含 DEFAULT 值，確保向後相容

✅ **2. Content 數據模型完成**
- `src/content.py` 實作 Content dataclass、3 個 Enum、狀態機邏輯
- `transition_to()` 拒絕非法轉換 (InvalidTransitionError)
- `to_dict()` / `from_dict()` 序列化支援

✅ **3. 帳號配置完成**
- `~/.imggen/accounts.toml` 三帳號設定已建立
- `LevelUpConfig` 類別可正確載入和解析 TOML

✅ **4. DAO 層完成**
- `src/db.py` 實作 ContentDAO，支援 CRUD 操作
- JSON 序列化 platform_status 和 engagement_data

✅ **5. 完整測試覆蓋**
- 46 個新測試，所有通過
- coverage: src/content.py 100%, src/db.py 100%, src/config.py (LevelUp) 100%

---

### ★ Cycle 2｜策展大腦（週 3-4）完成（2026-04-04）✅

**評分**：80
**文檔輸出**：開始前產出 `docs/cycle_2_spec.md`
**Agent / Skill**：`planner` → `/blueprint` → `/python-patterns` → `/python-testing` → `tdd-guide`

#### 交付成果

| 項目 | 路徑 | 狀態 |
|------|------|------|
| `BaseScraper` ABC + `RawItem` dataclass | `src/scrapers/base_scraper.py` | ✅ |
| `FootballScraper`（BBC RSS + API-Football） | `src/scrapers/football_scraper.py` | ✅ |
| `TechScraper`（HN API + TechCrunch RSS） | `src/scrapers/tech_scraper.py` | ✅ |
| `PMPScraper`（HBR RSS + PMI Blog RSS） | `src/scrapers/pmp_scraper.py` | ✅ |
| 帳號 A/B/C Prompt 檔案（含 `reasoning` 欄位） | `prompts/account_*.txt` | ✅ |
| `daily_curation.py`（async 多帳號策展） | `scripts/daily_curation.py` | ✅ |
| 23 個測試（scrapers + daily_curation） | `tests/scrapers/` + `tests/test_daily_curation.py` | ✅ |

#### 驗收標準
- [x] 每日執行後三帳號各有 ≥ 1 篇 DRAFT 進入 DB
- [x] 每篇 DRAFT 有非空的 `reasoning` 欄位
- [x] 任一爬蟲失敗不影響其他帳號

#### 原始任務清單

**1. `src/scrapers/` — 三個爬蟲**

| 檔案 | 資料源 | 輸出 |
|------|--------|------|
| `football_scraper.py` | API-Football（免費 100 req/day）+ BBC Sport RSS | 賽果、賽程、球員數據 |
| `tech_scraper.py` | Hacker News API + TechCrunch RSS + GitHub Trending | AI/科技新聞 |
| `pmp_scraper.py` | Harvard Business Review RSS + PMI Blog RSS | 管理/職涯文章 |

共用介面：
```python
class BaseScraper(ABC):
    def fetch(self) -> list[RawItem]:   # RawItem: {title, url, summary, published_at}
        ...
```

**2. `prompts/account_a.txt / b.txt / c.txt`** — 三套 AI Prompt

必須包含的 JSON schema（強制 reasoning 欄位）：
```json
{
  "title": "15 字以內",
  "body": "符合平台字數限制的貼文內文",
  "content_type": "NEWS_RECAP|PREDICTION|EDUCATIONAL",
  "reasoning": "為什麼這則素材值得發，預測它會火的理由",
  "tags": ["#tag1", "#tag2"],
  "image_suggestion": "圖卡版型建議（可選）"
}
```

**3. `scripts/daily_curation.py`** — 每日定時執行

```
執行流程：
  ① 讀取 accounts.toml
  ② 三帳號各自呼叫對應爬蟲（並發）
  ③ AI 分析（對應帳號 Prompt）→ 生成 JSON
  ④ 呼叫 imgGen pipeline → 生成圖卡
  ⑤ 寫入 DB，status = DRAFT
  ⑥ 輸出摘要：「今日新增 N 篇 DRAFT」
```

**4. 測試（TDD）**

```
tests/scrapers/test_football_scraper.py
  test_fetch_returns_raw_items()         # mock httpx response
  test_empty_response_handled()
  test_malformed_rss_handled()

tests/test_daily_curation.py
  test_draft_written_to_db()             # mock scrapers + AI
  test_three_accounts_run_independently()
  test_failed_scraper_does_not_block_others()
```

#### 驗收標準
- [ ] 每日執行後三帳號各有 ≥ 1 篇 DRAFT 進入 DB
- [ ] 每篇 DRAFT 有非空的 `reasoning` 欄位
- [ ] 任一爬蟲失敗不影響其他帳號

---

### ★ Cycle 3｜Smart Mode + Design Review Loop（週 3-4，與 Cycle 2 並行）

**評分**：125 / 75
**文檔輸出**：`docs/cycle_3_spec_v2.md` ✅（Planner Agent，基於原始碼驗證）
**Agent / Skill**：`/blueprint` → `/python-patterns` → `tdd-guide` → Design Review Loop

#### Phase 1-3 完成（2026-03-31）✅

| 項目 | 路徑 | 狀態 |
|------|------|------|
| `PipelineOptions.color_mood` 欄位 | `src/pipeline.py` | ✅ |
| `render_and_capture` 傳遞 `color_mood` | `src/pipeline.py` | ✅ |
| CLI `--color-mood` 選項（5 mood 可選） | `main.py` | ✅ |
| `GenerateRequest.mode` + `.color_mood` | `web/api.py` | ✅ |
| `/api/generate` 路由 `mode` + `color_mood` | `web/api.py` | ✅ |

#### Phase 4 完成（2026-04-04）✅

| 項目 | 路徑 | 狀態 |
|------|------|------|
| `design_review_loop.py`（screenshot→Claude→CSS patch→iterate） | `scripts/design_review_loop.py` | ✅ |
| 22 個測試（TestGenerateScreenshot/BuildPrompt/CallClaudeCli/ParseReview/ApplyPatches/RunLoop） | `tests/test_design_review_loop.py` | ✅ |
| `/api/meta` 回傳 `modes`, `color_moods`, `layout_patterns` | `web/api.py` | ✅ |

**Phase 5：Web UI Smart Mode Toggle**（待開發）

#### 待完成（Phase 5）

**Phase 4：Design Review Loop / Phase 5：Web UI Smart Mode Toggle**

**1. CLI 整合**

```bash
# 新增旗標
python main.py --url URL --mode smart --color-mood dark_tech
python main.py --file notes.md --mode smart  # color-mood 由 AI 自動選
```

`main.py` 變更：
- 新增 `--mode [card|article|smart]` 選項（預設 card）
- 新增 `--color-mood [dark_tech|warm_earth|clean_light|bold_contrast|soft_pastel]`

**2. `src/pipeline.py` 路由**

```python
def run_pipeline(input, mode='card', color_mood=None, ...):
    data = extract(input, mode=mode)          # 現有
    if mode == 'smart':
        html = smart_renderer.generate_smart_html(data, color_mood=color_mood)
    else:
        html = renderer.render_card(data, ...)  # 現有
    path = screenshotter.take_screenshot(html)
    return path
```

**3. `src/extractor.py` 擴展（smart 模式新增欄位）**

Smart 模式 Prompt 需要 AI 額外輸出：
```json
{
  "title": "...",
  "key_points": [{"text": "...", "importance": 5}],
  "layout_hint": "hero_list|grid|timeline|comparison|quote_centered|data_dashboard|numbered_ranking",
  "color_mood": "dark_tech|warm_earth|clean_light|bold_contrast|soft_pastel",
  "content_type": "news|analysis|tutorial|quote|data"
}
```

**4. `scripts/design_review_loop.py`**（per `docs/design_review_loop.md` 完整規格）

```python
def run(theme, template_path, max_iter=5) -> LoopSummary:
    # ① generate_screenshot
    # ② build_prompt（注入 CSS vars + 模板原始碼）
    # ③ call_claude_cli（tinify 壓縮 → base64 → stdin）
    # ④ parse_review → ReviewResult（score/issues/css_patches/done）
    # ⑤ if done: break
    # ⑥ apply_patches（只套用 --var-name 格式）
    # ⑦ score 下降 → rollback → stop
```

**5. Web UI 切換**

Generate 頁新增：
- Smart / Template 切換 toggle
- 色彩心情選擇器（5 個 mood，含色票預覽）
- 佈局模式說明（7 種，hover 顯示描述）

**6. 測試（TDD）**

```
tests/test_smart_pipeline.py
  test_smart_mode_calls_smart_renderer()
  test_card_mode_calls_renderer()        # 不影響現有行為
  test_color_mood_override()

tests/test_design_review_loop.py（22 個，per design_review_loop.md）
  TestGenerateScreenshot × 2
  TestBuildPrompt × 3
  TestCallClaudeCli × 3
  TestParseReview × 4
  TestApplyPatches × 6
  TestRunLoop × 4
```

#### 驗收標準
- [x] CLI `--mode smart --color-mood dark_tech` 正確傳遞至 `generate_smart_html()`
- [x] `--mode card` 行為與原本完全相同（regression 0，46 tests pass）
- [x] Design Review Loop 22 個測試全過
- [ ] Web UI Smart Mode toggle 可切換並正確呼叫 API（Phase 5，待開發）

---

### ★ Web UI｜Dashboard（與 Cycle 3 並行）完成（2026-03-31）✅

**規格**：`docs/webui_review_dashboard_spec.md`
**評分**：80

| 項目 | 路徑 | 狀態 |
|------|------|------|
| `GET /api/content/stats` | `web/api.py` | ✅ |
| `GET /api/content/recent` | `web/api.py` | ✅ |
| `GET /api/content/schedule` | `web/api.py` | ✅ |
| `GET /api/accounts` | `web/api.py` | ✅ |
| `constants/accounts.ts` | `web/frontend/src/constants/` | ✅ |
| `DashboardPage.tsx` + 6 元件 | `web/frontend/src/` | ✅ |
| 4 個 TanStack Query hooks | `web/frontend/src/api/queries.ts` | ✅ |
| App.tsx + Sidebar.tsx | `web/frontend/src/` | ✅ |
| DB 遷移套用（`001_add_levelup_columns.sql`） | `~/.imggen/history.db` | ✅ |

---

### ★ Cycle 4｜HITL 審核系統（週 5-6）完成（2026-04-04）✅

**評分**：100
**文檔輸出**：開始前產出 `docs/cycle_4_spec.md`
**Agent / Skill**：`/blueprint` → `/python-testing` → `tdd-guide`

#### 交付成果

| 項目 | 路徑 | 狀態 |
|------|------|------|
| `preflight_check()`（7 條規則，含 X/Threads/IG/LinkedIn 字數檢查） | `src/preflight.py` | ✅ |
| `calculate_scheduled_time()` / `assign_scheduled_times()`（不可變，while 滾動） | `src/scheduler.py` | ✅ |
| `export_drafts_to_markdown()` / `parse_markdown_review()` / `import_markdown_review()` | `src/markdown_io.py` | ✅ |
| `audit.py` CLI（--account/--batch/--export-md/--import-md/--db-path） | `scripts/audit.py` | ✅ |
| 36 個測試（preflight + scheduler + markdown_io + audit） | `tests/test_*.py` | ✅ |

#### 驗收標準
- [x] 核准後 `scheduled_time` 自動對應帳號黃金時段
- [x] IG 無圖時 Pre-flight 攔截並顯示警告
- [x] Markdown 匯出後可在手機編輯、回寫後正確更新 DB
- [ ] 週日 15 分鐘內可完成 21 篇批次審核（待實際操作驗證）

#### 原始任務清單

**1. `scripts/audit.py`** — 終端機互動式審核

```
執行介面：
  $ python scripts/audit.py
  $ python scripts/audit.py --account A    # 只審某帳號
  $ python scripts/audit.py --batch        # 快速批次模式
  $ python scripts/audit.py --export-md    # 匯出 review.md

單篇展示格式：
  ────────────────────────────────────────
  [帳號 A] NEWS_RECAP  ·  2026-04-01
  標題：Claude 4.5 支援原生工具呼叫
  內文：...（完整貼文）
  Reasoning：「Claude 升版是 AI 帳號核心受眾每週必看話題，
              預計互動率高於平均 2×」
  圖卡：output/draft_xxx.png
  ────────────────────────────────────────
  (A) 核准  (E) 編輯並核准  (D) 捨棄  (S) 跳過  (Q) 離開
```

**2. 狀態機轉換**

```
audit.py 操作 → DB 狀態變更：
  A（核准）  → status: APPROVED，scheduled_time 自動填入帳號黃金時段
  E（編輯）  → 開啟 $EDITOR 編輯 body，儲存後 → APPROVED
  D（捨棄）  → status: REJECTED
  S（跳過）  → status 維持 PENDING_REVIEW，不動
```

**3. Pre-flight Check**（核准時自動觸發）

```python
def preflight_check(content: Content) -> list[str]:  # 回傳 warning list
    warnings = []
    if 'x' in platforms and len(content.body) > 280:
        warnings.append("X 字數超限（{len} / 280），將自動截斷")
    if 'threads' in platforms and len(content.body) > 500:
        warnings.append("Threads 字數超限，將自動拆串文")
    if 'instagram' in platforms and not content.image_path:
        warnings.append("IG 需要圖片，目前無附圖")
    return warnings
```

**4. Markdown 匯出 / 回寫**

```bash
python scripts/audit.py --export-md        # 輸出 review.md
python scripts/audit.py --import-md review.md  # 回寫 DB
```

`review.md` 格式：
```markdown
## [PENDING] 帳號A · 2026-04-01 · NEWS_RECAP
**標題**: Claude 4.5 ...
**內文**: ...
**Reasoning**: ...
**Action**: APPROVE  <!-- 改成 APPROVE/REJECT/SKIP -->
```

**5. 測試（TDD）**

```
tests/test_audit.py
  test_approve_sets_status_approved()
  test_approve_sets_scheduled_time()
  test_reject_sets_status_rejected()
  test_preflight_warns_x_overlength()
  test_preflight_warns_ig_no_image()
  test_preflight_passes_clean_content()
  test_export_md_writes_all_pending()
  test_import_md_updates_db_correctly()
  test_batch_mode_processes_all_drafts()
```


---

### Cycle 5｜跨平台發布（週 5-6）

**文檔**：輕量更新 master-plan.md + PRD.md
**Agent / Skill**：`tdd-guide` → `security-reviewer`（API Token 處理）

| 任務 | 細節 |
|------|------|
| Platform Adapters | `src/adapters/threads_adapter.py`、`src/adapters/x_adapter.py` |
| 媒體中轉站 | Imgur API 上傳圖卡取得公開 URL |
| `scripts/dispatcher.py` | 掃描 APPROVED + scheduled_time <= now → 發布 → PUBLISHED |
| macOS launchd | `launchd/com.imggen.dispatcher.plist`，每小時觸發 |
| 錯誤重試 | RATE_LIMIT / PARTIAL_SUCCESS 處理 |

---

### Cycle 6｜互動引擎（週 7-8）

**文檔**：輕量更新
**Agent / Skill**：`tdd-guide`

| 任務 | 細節 |
|------|------|
| 留言監聽 | `scripts/check_comments.py`：AI 分類 + 草稿存 CSV |
| 轉發點讚 | 自動點讚，`engagement_log` 去重 |
| 防封號 | random delay + 每帳號 ≤ 20 則/天限制 |

---

### Cycle 7｜先知模組（週 9-12）

**文檔**：輕量更新
**Agent / Skill**：`planner` → `tdd-guide`

| 任務 | 細節 |
|------|------|
| 行事曆爬蟲 | API-Football 賽程 + `tech_events.json` 手動維護 |
| 預測引擎 | `scripts/oracle.py`：回顧 + 預測雙軌 |
| 自動排程 | target_event_date - 24h → scheduled_time |

---

### Cycle 8｜數據分析迴圈（週 9-12）

**文檔**：輕量更新
**Agent / Skill**：`tdd-guide`

| 任務 | 細節 |
|------|------|
| 績效收集 | Twitter Analytics API → `engagement_data` |
| Pandas 儀表板 | 主題收藏率、時段分析、Matplotlib 圖表 |
| Prompt 回饋 | 分析結果 → `prompt_weights.toml` |
| 8 週淘汰評估 | `kill_switch_eval.py`：三帳號表現比較報告 |
| A/B 主題測試 | 同素材多主題 render，engagement 對比 |

---

## 標準 Agent 工作流

```
1. PM Agent（複雜 Cycle 才用） → docs/cycle_N_spec.md
2. TDD Guide                   → RED → GREEN → IMPROVE
3. Design Review Loop          → 涉及圖卡/UI 時，最多 5 次迭代
4. 更新文件                    → master-plan.md + PRD.md + PLAN.md
```

---

## 關鍵檔案架構

```
imgGen/
├── src/
│   ├── content.py                    # Cycle 1
│   ├── scrapers/
│   │   ├── base_scraper.py           # Cycle 2
│   │   ├── football_scraper.py       # Cycle 2
│   │   ├── tech_scraper.py           # Cycle 2
│   │   ├── pmp_scraper.py            # Cycle 2
│   │   └── calendar_scraper.py       # Cycle 7
│   ├── adapters/
│   │   ├── threads_adapter.py        # Cycle 5
│   │   └── x_adapter.py             # Cycle 5
│   ├── media_staging.py              # Cycle 5
│   ├── smart_renderer.py             # ✅ 已完成，Cycle 3 整合
│   └── publisher.py                  # ✅ 已完成，Cycle 5 擴展
├── scripts/
│   ├── daily_curation.py             # Cycle 2
│   ├── audit.py                      # Cycle 4
│   ├── dispatcher.py                 # Cycle 5
│   ├── check_comments.py             # Cycle 6
│   ├── oracle.py                     # Cycle 7
│   ├── collect_analytics.py          # Cycle 8
│   ├── analytics_report.py           # Cycle 8
│   ├── kill_switch_eval.py           # Cycle 8
│   └── design_review_loop.py         # Cycle 3
├── prompts/
│   ├── account_a.txt                 # Cycle 2
│   ├── account_b.txt                 # Cycle 2
│   ├── account_c.txt                 # Cycle 2
│   ├── prediction_a/b/c.txt          # Cycle 7
│   └── smart_layout_system.txt       # ✅ 已存在
├── launchd/
│   └── com.imggen.dispatcher.plist   # Cycle 5
└── ~/.imggen/
    ├── accounts.toml                  # Cycle 1
    ├── prompt_weights.toml            # Cycle 8
    └── history.db                     # ✅ 已存在，Cycle 1 擴展
```

---

## 12 週時程

| 週次 | Cycle | 交付物 | 文檔 | 狀態 |
|------|-------|--------|------|------|
| 1-2 | 1 | DB schema + 狀態機 + accounts.toml | ✅ cycle_1_spec.md | ✅ 完成 |
| 3-4 | 2 | RSS × 3 + 三帳號 Prompt + 每日草稿 | cycle_2_spec.md | ⏳ 待開始 |
| 3-4 | 3 | Smart Mode CLI/API Phase 1-3 ✅ + DRL + Web UI toggle | cycle_3_spec_v2.md | 🔄 Phase 1-3 完成 |
| 3-4 | - | Web UI Dashboard | webui_review_dashboard_spec.md | ✅ 完成 |
| 5-6 | 4 | audit.py + 批次審核 + Pre-flight | cycle_4_spec.md | ⏳ 待開始 |
| 5-6 | 5 | Threads/X Adapter + dispatcher | 輕量更新 | ⏳ 待開始 |
| 7-8 | 6 | 留言監聽 + 點讚 + 防封號 | 輕量更新 | ⏳ 待開始 |
| 9-12 | 7 | 行事曆爬蟲 + 先知預測 | 輕量更新 | ⏳ 待開始 |
| 9-12 | 8 | Analytics + Prompt 回饋 + 淘汰評估 | 輕量更新 | ⏳ 待開始 |
