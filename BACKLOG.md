# LevelUp 開發待辦清單

**更新日期**: 2026-03-31
**已完成**: Cycle 1 ✅ + Cycle 2 ✅ + Cycle 3 Phase 1-4 ✅ + Cycle 4 Phase 1-4 ✅ + Web UI Dashboard ✅ + DB 遷移套用 ✅

---

## 狀態圖例

- ✅ 已完成
- 📋 規格已就緒（有 spec 文件）
- ⏳ 待規格 / 待開始

---

## Cycle 1｜基礎建設 ✅

| 項目 | 狀態 |
|------|------|
| SQLite 遷移腳本（9 個新欄位） | ✅ `src/migrations/001_add_levelup_columns.sql` |
| Content dataclass + 狀態機 | ✅ `src/content.py` |
| ContentDAO CRUD | ✅ `src/db.py` |
| LevelUpConfig + AccountConfig | ✅ `src/config.py` |
| 帳號配置 | ✅ `~/.imggen/accounts.toml` |
| 測試（46 個，coverage 100%） | ✅ `tests/test_content.py` / `test_db.py` / `test_levelup_config.py` |

---

## Cycle 2｜策展大腦 ✅

**規格**: `docs/cycle_2_spec.md`
**前置依賴**: Cycle 1 ✅

| 項目 | 檔案 | 狀態 |
|------|------|------|
| 爬蟲基類 | `src/scrapers/base_scraper.py` | ✅ |
| 足球爬蟲（BBC Sport + API-Football） | `src/scrapers/football_scraper.py` | ✅ |
| 科技爬蟲（Hacker News + TechCrunch） | `src/scrapers/tech_scraper.py` | ✅ |
| PMP 爬蟲（HBR + PMI Blog） | `src/scrapers/pmp_scraper.py` | ✅ |
| 帳號 A Prompt（AI 自動化） | `prompts/account_a.txt` | ✅ |
| 帳號 B Prompt（PMP 職涯） | `prompts/account_b.txt` | ✅ |
| 帳號 C Prompt（足球英文） | `prompts/account_c.txt` | ✅ |
| 每日策展主控腳本 | `scripts/daily_curation.py` | ✅ |
| 測試（爬蟲 ×3 + 策展流程） | `tests/scrapers/` / `tests/test_daily_curation.py` | ✅ |

---

## Cycle 3｜Smart Mode + Design Review Loop 📋

**規格**: `docs/cycle_3_spec_v2.md`
**前置依賴**: 無（smart_renderer.py 已存在）

### Phase 1-2：管線補丁 + CLI ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| `PipelineOptions` 新增 `color_mood` 欄位 | `src/pipeline.py` | ✅ |
| `render_and_capture` 傳遞 `color_mood` | `src/pipeline.py` | ✅ |
| CLI 新增 `--color-mood` 選項 | `main.py` | ✅ |
| CLI 傳遞 `color_mood` 至 PipelineOptions（thread + normal） | `main.py` | ✅ |

### Phase 3：Web API 支援 ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| `GenerateRequest` 新增 `mode` + `color_mood` | `web/api.py` | ✅ |
| `/api/generate` 傳遞 `mode` 和 `color_mood` | `web/api.py` | ✅ |
| `/api/generate/multi` 同步修改 | `web/api.py` | ✅ |
| `/api/meta` 新增 smart mode 元資料 | `web/api.py` | ✅ |
| `_to_extraction_config()` 接受 mode 參數 | `web/api.py` | ✅ |

### Phase 4：Design Review Loop

| 項目 | 檔案 | 說明 |
|------|------|------|
| 審查 Prompt 文件 | `prompts/design_review.txt` | ✅ |
| ReviewResult / LoopSummary / Issue 資料結構 | `scripts/design_review_loop.py` | ✅ |
| `generate_screenshot()` | `scripts/design_review_loop.py` | ✅ |
| `build_prompt()` | `scripts/design_review_loop.py` | ✅ |
| `_compress_image_for_review()` | `scripts/design_review_loop.py` | ✅ |
| `call_claude_cli()` | `scripts/design_review_loop.py` | ✅ |
| `parse_review()` | `scripts/design_review_loop.py` | ✅ |
| `apply_patches()` | `scripts/design_review_loop.py` | ✅ |
| `run()` 主迴圈 | `scripts/design_review_loop.py` | ✅ |
| CLI 入口（argparse） | `scripts/design_review_loop.py` | ✅ |
| `tinify` 依賴 | `requirements.txt` | ✅ |
| 測試（22 個 DRL） | `tests/test_design_review_loop.py` | ✅ |

### Phase 5：Web UI Smart Mode 切換

| 項目 | 檔案 | 說明 |
|------|------|------|
| Smart / Template toggle | `web/frontend/src/` | ⬜ |
| 色彩心情選擇器（5 mood + 色票） | `web/frontend/src/` | ⬜ |
| 佈局模式說明（7 種） | `web/frontend/src/` | ⬜ |

---

## Cycle 4｜HITL 審核系統 ✅

**規格**: `docs/cycle_4_spec.md`
**前置依賴**: Cycle 1 ✅（Cycle 2 需有 DRAFT 資料，但可用測試資料）

### Phase 1：Pre-flight Check ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| `preflight_check()` + 7 條規則 | `src/preflight.py` | ✅ |
| 測試（9 個） | `tests/test_preflight.py` | ✅ |

### Phase 2：排程計算 ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| `calculate_scheduled_time()` | `src/scheduler.py` | ✅ |
| `assign_scheduled_times()` | `src/scheduler.py` | ✅ |
| 測試（7 個） | `tests/test_scheduler.py` | ✅ |

### Phase 3：Markdown 匯出/回寫 ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| `export_markdown()` | `src/markdown_io.py` | ✅ |
| `parse_markdown()` | `src/markdown_io.py` | ✅ |
| `import_markdown()` | `src/markdown_io.py` | ✅ |
| 測試（11 個） | `tests/test_markdown_io.py` | ✅ |

### Phase 4：audit.py 主程式 ✅

| 項目 | 檔案 | 說明 |
|------|------|------|
| Click CLI 入口（5 個選項） | `scripts/audit.py` | ✅ |
| `_run_interactive()` 審核主迴圈 | `scripts/audit.py` | ✅ |
| `_display_content()` 終端機顯示 | `scripts/audit.py` | ✅ |
| `_handle_action()` A/E/D/S/Q 操作 | `scripts/audit.py` | ✅ |
| `_open_editor()` $EDITOR 整合 | `scripts/audit.py` | ✅ |
| 批次模式（`--batch`） | `scripts/audit.py` | ✅ |
| 測試（9 個） | `tests/test_audit.py` | ✅ |

---

## Cycle 5｜跨平台發布 ⏳

**規格**: `docs/master-plan.md`（輕量描述）
**前置依賴**: Cycle 4

| 項目 | 檔案 | 說明 |
|------|------|------|
| Threads Adapter | `src/adapters/threads_adapter.py` | ⬜ |
| X Adapter | `src/adapters/x_adapter.py` | ⬜ |
| 圖片中轉站（Imgur API） | `src/media_staging.py` | ⬜ |
| 發布主控腳本 | `scripts/dispatcher.py` | ⬜ |
| macOS launchd 定時排程 | `launchd/com.imggen.dispatcher.plist` | ⬜ |
| 錯誤重試機制 | `scripts/dispatcher.py` | ⬜ |

---

## Cycle 6｜互動引擎 ⏳

**規格**: `docs/master-plan.md`（輕量描述）
**前置依賴**: Cycle 5

| 項目 | 檔案 | 說明 |
|------|------|------|
| 留言監聽 + AI 分類 | `scripts/check_comments.py` | ⬜ |
| 自動點讚（去重機制） | `scripts/check_comments.py` | ⬜ |
| 防封號（random delay + 日限額） | `scripts/check_comments.py` | ⬜ |

---

## Cycle 7｜先知模組 ⏳

**規格**: `docs/master-plan.md`（輕量描述）
**前置依賴**: Cycle 2

| 項目 | 檔案 | 說明 |
|------|------|------|
| 行事曆爬蟲（API-Football 賽程） | `src/scrapers/calendar_scraper.py` | ⬜ |
| 預測引擎（回顧 + 預測雙軌） | `scripts/oracle.py` | ⬜ |
| 預測 Prompt（三帳號） | `prompts/prediction_a/b/c.txt` | ⬜ |
| 自動排程（target_date - 24h） | `scripts/oracle.py` | ⬜ |

---

## Cycle 8｜數據分析迴圈 ⏳

**規格**: `docs/master-plan.md`（輕量描述）
**前置依賴**: Cycle 5

| 項目 | 檔案 | 說明 |
|------|------|------|
| Twitter Analytics API 收集 | `scripts/collect_analytics.py` | ⬜ |
| Pandas 統計報告 + Matplotlib 圖表 | `scripts/analytics_report.py` | ⬜ |
| Prompt 回饋機制 | `prompts/prompt_weights.toml` | ⬜ |
| 淘汰評估腳本（8 週） | `scripts/kill_switch_eval.py` | ⬜ |
| A/B 主題測試（同素材多主題 render） | `scripts/collect_analytics.py` | ⬜ |

---

## Web UI｜Dashboard ✅

**規格**: `docs/webui_review_dashboard_spec.md`
**完成日期**: 2026-03-31

| 項目 | 檔案 | 說明 |
|------|------|------|
| 後端：`GET /api/content/stats` | `web/api.py` | ✅ |
| 後端：`GET /api/content/recent` | `web/api.py` | ✅ |
| 後端：`GET /api/content/schedule` | `web/api.py` | ✅ |
| 後端：`GET /api/accounts` | `web/api.py` | ✅ |
| `constants/accounts.ts`（帳號 + 狀態顏色常數） | `web/frontend/src/constants/` | ✅ |
| `DashboardPage.tsx` | `web/frontend/src/pages/` | ✅ |
| `AccountCard` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| `ScheduleTimeline` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| `HealthCard` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| `RecentContentList` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| `StatusBadge` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| `QuickActions` 元件 | `web/frontend/src/features/dashboard/` | ✅ |
| hooks：`useContentStats / useRecentContent / useScheduledContent / useAccounts` | `web/frontend/src/api/queries.ts` | ✅ |
| App.tsx + Sidebar.tsx 路由/導覽更新 | `web/frontend/src/` | ✅ |
| DB 遷移套用至 `~/.imggen/history.db` | 手動執行 | ✅ |
| 測試 | `web/frontend/src/features/dashboard/__tests__/` | ⬜ |

---

## Web UI｜Content Review 📋

**規格**: `docs/webui_review_dashboard_spec.md`
**前置依賴**: Cycle 4（preflight + scheduler）

| 項目 | 檔案 | 說明 |
|------|------|------|
| 後端：`GET /api/content/pending` | `web/api.py` | ⬜ |
| 後端：`POST /api/content/{id}/approve` | `web/api.py` | ⬜ |
| 後端：`POST /api/content/{id}/reject` | `web/api.py` | ⬜ |
| 後端：`POST /api/content/{id}/edit` | `web/api.py` | ⬜ |
| 後端：`POST /api/content/batch-approve` | `web/api.py` | ⬜ |
| `ReviewPage.tsx` | `web/frontend/src/pages/` | ⬜ |
| `ReviewFilters` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `ReviewCardGrid` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `ReviewCard` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `PreflightWarnings` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `EditModal` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `BatchActions` 元件 | `web/frontend/src/features/review/` | ⬜ |
| `useReviewStore` Zustand store | `web/frontend/src/stores/` | ⬜ |
| 測試（前端 11 + 後端 9） | `tests/` / `web/frontend/src/features/review/__tests__/` | ⬜ |

---

## Web UI｜Account Settings 📋

**規格**: `docs/webui_schedule_curation_settings_spec.md`
**前置依賴**: Cycle 1 ✅（可立即開始）

| 項目 | 檔案 | 說明 |
|------|------|------|
| 後端：`GET /api/accounts` | `web/api.py` | ⬜ |
| 後端：`GET /api/accounts/{id}/prompt` | `web/api.py` | ⬜ |
| 後端：`PUT /api/accounts/{id}` | `web/api.py` | ⬜ |
| 後端：`POST /api/accounts/{id}/preview` | `web/api.py` | ⬜ |
| config.py 新增 TOML 寫入功能 | `src/config.py` | ⬜ |
| `AccountSettingsPage.tsx` | `web/frontend/src/pages/` | ⬜ |
| `AccountCard` 元件（設定頁） | `web/frontend/src/features/settings/` | ⬜ |
| `PlatformsField` 元件 | `web/frontend/src/features/settings/` | ⬜ |
| `ColorMoodField` + `ColorSwatchGrid` | `web/frontend/src/features/settings/` | ⬜ |
| `PromptEditorSection` 元件 | `web/frontend/src/features/settings/` | ⬜ |
| `CardPreview` 元件 | `web/frontend/src/features/settings/` | ⬜ |
| `useSettingsStore` Zustand store | `web/frontend/src/stores/` | ⬜ |
| 測試（前端 4 + 後端 5） | `tests/` / `web/frontend/src/features/settings/__tests__/` | ⬜ |

---

## Web UI｜Scheduling 📋

**規格**: `docs/webui_schedule_curation_settings_spec.md`
**前置依賴**: Cycle 4（APPROVED 內容）

| 項目 | 檔案 | 說明 |
|------|------|------|
| 後端：`GET /api/contents/scheduled` | `web/api.py` | ⬜ |
| 後端：`PATCH /api/contents/{id}/reschedule` | `web/api.py` | ⬜ |
| 後端：`GET /api/contents/{id}` | `web/api.py` | ⬜ |
| ContentDAO 新增 `find_scheduled()` | `src/db.py` | ⬜ |
| `constants/accounts.ts`（帳號顏色常數） | `web/frontend/src/constants/` | ⬜ |
| `SchedulingPage.tsx` | `web/frontend/src/pages/` | ⬜ |
| `WeekCalendarGrid` 元件（含 DnD） | `web/frontend/src/features/scheduling/` | ⬜ |
| `MonthCalendarGrid` 元件 | `web/frontend/src/features/scheduling/` | ⬜ |
| `ScheduleCard` 元件 | `web/frontend/src/features/scheduling/` | ⬜ |
| `ContentDetailDrawer` 元件 | `web/frontend/src/features/scheduling/` | ⬜ |
| `ViewToggle` + `WeekNavigator` 元件 | `web/frontend/src/features/scheduling/` | ⬜ |
| `useSchedulingStore` Zustand store | `web/frontend/src/stores/` | ⬜ |
| 測試（前端 6 + 後端 4） | `tests/` / `web/frontend/src/features/scheduling/__tests__/` | ⬜ |

---

## Web UI｜Curation 📋

**規格**: `docs/webui_schedule_curation_settings_spec.md`
**前置依賴**: Cycle 2（scrapers + daily_curation）

| 項目 | 檔案 | 說明 |
|------|------|------|
| 後端：`GET /api/contents/drafts` | `web/api.py` | ⬜ |
| 後端：`POST /api/curation/trigger`（SSE） | `web/api.py` | ⬜ |
| 後端：`PATCH /api/contents/{id}/status` | `web/api.py` | ⬜ |
| 後端：`GET /api/curation/stats` | `web/api.py` | ⬜ |
| ContentDAO 新增 `find_drafts()` | `src/db.py` | ⬜ |
| ContentDAO 新增 `get_curation_stats()` | `src/db.py` | ⬜ |
| `CurationPage.tsx` | `web/frontend/src/pages/` | ⬜ |
| `TriggerCurationButton` 元件 | `web/frontend/src/features/curation/` | ⬜ |
| `CurationProgressModal` 元件（SSE） | `web/frontend/src/features/curation/` | ⬜ |
| `CurationStatsBar` 元件 | `web/frontend/src/features/curation/` | ⬜ |
| `DraftContentList` + `DraftDetailPanel` | `web/frontend/src/features/curation/` | ⬜ |
| `ReasoningCard` 元件 | `web/frontend/src/features/curation/` | ⬜ |
| `useCurationStore` Zustand store | `web/frontend/src/stores/` | ⬜ |
| 測試（前端 4 + 後端 4） | `tests/` / `web/frontend/src/features/curation/__tests__/` | ⬜ |

---

## 可立即開始（零依賴）

| 項目 | 預估工作量 |
|------|-----------|
| Web UI Account Settings（Cycle 1 已完成） | 中 |
| Cycle 3 Phase 4：Design Review Loop | 中 |
| Cycle 4：HITL 審核系統（preflight + scheduler + audit.py） | 大 |

## 參考文件

| 文件 | 說明 |
|------|------|
| `docs/master-plan.md` | 總體規劃 v2.1 |
| `docs/cycle_1_spec.md` | Cycle 1 規格（已完成） |
| `docs/cycle_2_spec.md` | Cycle 2 規格 |
| `docs/cycle_3_spec_v2.md` | Cycle 3 規格（基於原始碼驗證） |
| `docs/cycle_4_spec.md` | Cycle 4 規格（基於原始碼驗證） |
| `docs/webui_review_dashboard_spec.md` | Web UI A/B 規格 |
| `docs/webui_schedule_curation_settings_spec.md` | Web UI C/D/E 規格 |
| `docs/design_review_loop.md` | Design Review Loop 詳細規格 |
