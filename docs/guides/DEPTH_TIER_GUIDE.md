# depth_tier 動態 Carousel 分配指南

## 概述

`depth_tier` 是內容深度評估欄位，決定輪播圖張數。由 Claude 在批次評估時自動判斷，目標是**根據內容質量優化配額消耗**。

| Tier | Slides | 適用內容 | 特徵 |
|---|---|---|---|
| **1** | 1 | 事件快訊、單一數據、單項技巧 | 一句話能說完 |
| **3** | 3 | 觀點論述、工具深挖、迷你案例 | 論點 + 2-3 個論據 |
| **5** | 5 | 系統教學、完整案例、多維對比 | 完整敘事弧 |
| **7** | 7 | 長篇 tutorial、複雜議題 | 罕見，預設避免 |

## AI 判準（Prompt 側）

### Account A（AI 自動化）
```
depth_tier 判斷標準：
- 1：事件快訊、單一數據點、產品發布、價格調整、公告 — 一句話能說完的內容
- 3：觀點論述（論點+2-3個論據）、單一工具/技巧深挖、迷你案例、產品對比
- 5：系統教學、完整案例剖析、多維對比、Top-N 深度列表
- 7：長篇 tutorial 或複雜多視角議題（罕見）

判斷原則：寧可低估，不要高估。不確定時選 1。
```

### Account B（PMP 職涯）
```
- 1：單一職涯事件、人事異動、法規更新、單項技能技巧
- 3：職涯故事（背景→轉折→收穫）、PM 痛點分析（問題+解方）、流程改善案例
- 5：完整 PM 方法論教學、複雜人際衝突案例研析、職涯轉換全流程
- 7：MBA 級別課程或複雜組織變革案例（罕見）
```

### Account C（足球英文）
```
- 1：比賽結果、轉會傳聞、單場進球、排名更新
- 3：賽事深度評論（戰術+關鍵時刻）、球員故事（背景→成長→成就）、轉會分析
- 5：完整賽季回顧、複雜戰術體系分析、球隊重建全流程
- 7：紀錄片級別內容（罕見）
```

## 運行流程

### 1. 批次評估（Haiku）
```python
# daily_curation.py 呼叫 call_claude_api_batch()
ai_outputs = [
    {
        "should_publish": True,
        "depth_tier": 3,        # ← Claude 判斷
        "depth_reason": "觀點文章，有2個論據可展開",
        ...
    },
    ...
]
```

### 2. 正規化（Validation）
```python
# 若 depth_tier ∉ {1, 3, 5, 7}，強制 1
if tier not in (1, 3, 5, 7):
    tier = 1  # Safe default
```

### 3. per-item 並行渲染
```python
def _resolve_tier(ai_output):
    """Return (use_carousel, slide_count)"""
    tier = ai_output.get("depth_tier", 1)
    if tier == 1:
        return False, 1      # Single image
    else:
        return True, tier    # Carousel with N slides
```

### 4. 日誌輸出
```
[A] Tier distribution: tier1×6, tier3×1 (total Sonnet render calls: 9)
```

## CLI 使用

### 預設行為（tier-driven）
```bash
python scripts/daily_curation.py --account A
# tier=1 → 單圖，tier=3 → 3-slide carousel，tier=5 → 5-slide carousel
```

### 強制 Override（測試用）
```bash
python scripts/daily_curation.py --account A --carousel --slides 5
# 所有文章都用 5-slide carousel，無論 tier 是多少
```

### 評估不含圖片（省 60% token）
```bash
python scripts/daily_curation.py --account A --no-image
# 只評估，不渲染。用 tier 分佈驗證 AI 判斷
```

### 乾跑模式（零 AI 呼叫）
```bash
python scripts/daily_curation.py --account A --dry-run
# 用 fixture 數據（預設 tier=1），驗證流程
```

## 監控指標

### Tier 分佈
```
[A] Tier distribution: tier1×6, tier3×1, tier5×0 (total Sonnet render calls: 9)
```

**解讀：**
- tier1×6 = 6 篇單圖（6 次 Sonnet render）
- tier3×1 = 1 篇 3-slide carousel（3 次 Sonnet render）
- **總 9 次**（vs 原本固定 carousel-5×7 = 35 次）

### 穩定性檢查
連續 5 天觀察 tier 分佈：
- ✅ 穩定：分佈在各 tier 的比例相近（反映內容多樣性）
- ⚠️ 偏差：全是 tier=1 或全是 tier=5（表示 AI 判斷過激進或過保守）

若發現偏差，調整 prompt 的「寧可低估」語氣。

## 配額影響

### 實測（Account A，2026-04-10）

| 場景 | Sonnet renders | 配額占用 |
|---|---|---|
| 原本 carousel-5×3 | 15 | 30% / run |
| depth_tier 分配 | ~9 | ~18% / run |
| 節省幅度 | -40% | -40% |

### 長期趨勢（預估月度）
- **Carousel-5 固定：** ~1,350 renders / 月，Sonnet cost ~$50-100 / 月
- **depth_tier 動態：** ~270-540 renders / 月，Sonnet cost ~$10-30 / 月
- **節省：** -60 ~ 80%

## 常見問題

### Q: 為什麼 AI 還是全選 tier=1？
A: 正常行為。Account A 的 14 個源大半是 Reddit 帖文和快訊，tier=1 符合實況。如果確實有深度文章卻被判 tier=1，檢查 prompt 裡「寧可低估」的語氣是否過強。

### Q: 如何強制某篇文章用 tier=5？
A: 目前無法在 CLI 層面指定。若想測試 tier=5，用 `--carousel --slides 5` 強制所有文章。長期可考慮在 DB schema 加 `user_override_tier` 欄位。

### Q: depth_reason 是幹嘛的？
A: 日誌記錄 AI 選 tier 的理由（e.g. "觀點文章，有2個論據可展開"），便於事後驗證 tier 判斷是否合理。

### Q: 為什麼不直接用 tier=1 省最多？
A: 因為深度內容（tier=5）實際上值得多投資。固定 tier=1 等於浪費了好內容的潛力。depth_tier 是**質量決定資源分配** — 符合內容運營的直觀邏輯。

## 下一步（Layer 2 學習回路）

1-2 週觀察後，若 tier 判斷穩定：
- 記錄 elite_review 打分 + 對應的 tier
- 找出「tier 低但打分高」或「tier 高但打分低」的案例
- 作為 few-shot 例子注入 prompt（Cycle 5 自動進化）

不改代碼邏輯，只改 prompt — 體現「學習 = prompt 進化」的設計理念。

## 相關文檔

- `docs/guides/TOKEN_OPTIMIZATION_ROADMAP.md` — 整體優化進度
- `prompts/account_*.txt` — 各帳號的 depth_tier 判準
- `scripts/daily_curation.py` — 實裝邏輯（`_resolve_tier`, tier distribution logging）
