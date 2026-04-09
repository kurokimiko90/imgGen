# imgGen 精英 Agent 自動學習系統設計

## 核心架構

```
┌─────────────────────────────────────────────────┐
│  Layer 3: 學習層 — 記錄什麼有效、累積品味        │
│  Layer 2: 精英審查層 — 多角色 agent 把關品質       │
│  Layer 1: 生產層 — 現有 pipeline（extract→render→screenshot）│
└─────────────────────────────────────────────────┘
```

每張卡片經過生產→多角色審查→學習紀錄→回饋到下次生成，形成閉環。

---

## Layer 2：精英 Agent 團隊

在現有 `design_review_loop.py` 基礎上擴展為多角色並行審查。

### Agent 角色定義

| Agent 角色 | 審查什麼 | 輸出 |
|-----------|---------|------|
| **品牌策略師** | 語氣是否符合帳號人設、受眾共鳴度、hook 強度 | `content_score` + 改寫建議 |
| **視覺總監** | 排版層級、色彩對比、移動端飽滿度、字體搭配 | `design_score` + CSS patches |
| **文案編輯** | 錯字、斷句、字數限制、CTA 有效性 | `copy_score` + 修改版文案 |
| **受眾代表** | 「我刷到這張會停下來嗎？」冷感測試 | `scroll_stop_score` + 理由 |

### 實現：`scripts/elite_review.py`

```python
AGENTS = {
    "brand_strategist": "prompts/agents/brand_strategist.txt",
    "visual_director":  "prompts/agents/visual_director.txt",
    "copy_editor":      "prompts/agents/copy_editor.txt",
    "audience_proxy":   "prompts/agents/audience_proxy.txt",
}

async def elite_review(content, screenshot_path) -> ReviewVerdict:
    results = await asyncio.gather(*[
        run_agent(role, content, screenshot_path)
        for role, prompt in AGENTS.items()
    ])
    # 加權評分：視覺 30% + 文案 25% + 品牌 25% + 受眾 20%
    weighted = aggregate(results, weights=[0.30, 0.25, 0.25, 0.20])
    return ReviewVerdict(pass_threshold=7.5, ...)
```

### Agent Prompt 規範

每個 agent prompt 檔統一格式：

```
[PERSONA]
你是...（角色定義）

[EVALUATION CRITERIA]
1. ...
2. ...

[OUTPUT FORMAT]
{
  "score": <1-10>,
  "issues": [{"severity": "CRITICAL|MAJOR|MINOR", "description": "..."}],
  "suggestions": ["..."],
  "pass": true/false
}
```

### 通過門檻

- 加權總分 >= 7.5：自動通過
- 任一 agent 給出 CRITICAL issue：強制打回
- 加權總分 6.0-7.4：自動修補一輪後重審（最多 2 次）
- 加權總分 < 6.0：直接棄用

---

## Layer 3：學習紀錄系統

### 資料結構

```
~/.imggen/
├── profiles/
│   ├── account_a.yaml    # 帳號人設 + 歷史表現數據
│   ├── account_b.yaml
│   └── account_c.yaml
├── learnings/
│   ├── design_patterns.yaml   # 哪些 CSS 組合得高分
│   ├── copy_patterns.yaml     # 哪些 hook 句式有效
│   └── failures.yaml          # 被打回的案例 + 原因
└── taste_model.yaml           # 累積的品味偏好
```

### 帳號人設檔範例（`profiles/account_a.yaml`）

```yaml
name: "AI 自動化"
persona: "崩潰但繼續幹的工程師"
audience: "AI practitioners, dev founders"
tone_rules:
  - "帶點自嘲，不要像新聞稿"
  - "技術細節用英文，情緒用中文"
  - "hook 必須在前 15 字抓住人"

stats:
  total_cards: 0
  avg_score: 0
  pass_rate: 0

learned_preferences:   # ← 自動累積
  - "dark_tech 主題 scroll_stop_score 平均 8.2，遠高於其他"
  - "問句開頭的 body 平均分比陳述句高 1.3 分"
  - "超過 200 字的貼文受眾分數下降"

top_performing_examples:
  - title: "Claude Code 被砍了"
    score: 9.1
    reason: "共鳴感強"
```

### 學習紀錄範例（`learnings/design_patterns.yaml`）

```yaml
patterns:
  - rule: "dark_card 主題 + 漸層背景 + 大標題 bold → 視覺分 8+"
    confidence: 0.85
    sample_count: 12
    first_seen: "2026-04-01"

  - rule: "gallery_quote 主題在足球帳號表現優於 AI 帳號"
    confidence: 0.72
    sample_count: 8
    first_seen: "2026-04-05"
```

### 失敗紀錄範例（`learnings/failures.yaml`）

```yaml
failures:
  - pattern: "正文超過 250 字 + 無分段"
    avg_score: 4.8
    agent_flag: "audience_proxy"
    action: "限制 body 字數，強制加分段符號"

  - pattern: "light 主題用於深夜發文時段"
    avg_score: 5.2
    agent_flag: "visual_director"
    action: "根據發文時段自動選擇深/淺色主題"
```

---

## 自動學習迴路

### 在 `daily_curation.py` 末尾加入

```python
async def learning_loop(today_results: list[ReviewVerdict]):
    """從今天的審查結果中提取可重用知識"""

    high_scores = [r for r in today_results if r.final_score >= 8]
    low_scores  = [r for r in today_results if r.final_score < 6]

    # 1. 提取成功模式
    if high_scores:
        patterns = await extract_patterns(high_scores)
        append_to("~/.imggen/learnings/design_patterns.yaml", patterns)

    # 2. 記錄失敗原因
    if low_scores:
        failures = await analyze_failures(low_scores)
        append_to("~/.imggen/learnings/failures.yaml", failures)

    # 3. 更新帳號人設
    for account in accounts:
        stats = calculate_account_stats(account, today_results)
        update_profile(account, stats)

    # 4. 回饋到 prompt — 下次生成時自動注入學習成果
    rebuild_prompts_with_learnings()
```

### extract_patterns 的邏輯

```python
async def extract_patterns(high_score_results):
    """讓 LLM 從高分卡片中歸納共通規則"""
    prompt = f"""
分析以下 {len(high_score_results)} 張高分卡片的共通點。
提煉出 3-5 條可重用的設計/文案規則。

卡片資料：
{json.dumps([r.to_summary() for r in high_score_results], ensure_ascii=False)}

輸出格式：
[{{"rule": "...", "confidence": 0.0-1.0, "category": "design|copy|tone"}}]
"""
    return await call_llm(prompt)
```

---

## Prompt 自動進化

### 動態 Prompt 組裝（`src/extractor.py` 擴展）

```python
def build_enhanced_prompt(account: str, base_prompt: str) -> str:
    """將學習成果注入到生成 prompt 中"""
    learnings = load_learnings()
    profile = load_profile(account)

    injection = f"""
[LEARNED PATTERNS — 從過去 {profile['stats']['total_cards']} 張卡片中提煉]
DO:
{chr(10).join('- ' + p['rule'] for p in learnings['top_patterns'][:5])}

AVOID:
{chr(10).join('- ' + f['pattern'] + ' → ' + f['action'] for f in learnings['top_failures'][:3])}

THIS ACCOUNT PREFERS:
{chr(10).join('- ' + p for p in profile['learned_preferences'][:5])}
"""
    return base_prompt + injection
```

### 閉環流程

```
base prompt (account_a.txt)
    + learnings/design_patterns.yaml top 5
    + learnings/failures.yaml top 3 反面案例
    + profiles/account_a.yaml learned_preferences
    ↓
動態組裝增強版 prompt → extractor → renderer → screenshot
    ↓
elite_review (4 agent 並行審查)
    ↓
learning_loop (提煉知識、更新人設)
    ↓
下一次生成自動使用更新後的知識 ← 閉環
```

---

## 實施計劃（方案 B — 已採用）

> 原始方案（4 agent + YAML）經批判性審查後，採用精簡版方案 B：
> - 4 agent → 2 agent（內容+視覺）
> - YAML → SQLite（復用現有 ContentDAO 的 DB）
> - LLM 歸納學習 → 純 SQL 統計 + 啟發式規則
> - Token 成本：+100%（vs 原方案 +500%）

### 已完成

| 產出 | 檔案 | 說明 |
|------|------|------|
| DB Migration | `src/migrations/005_add_review_and_learnings.sql` | review_scores 欄位 + learnings 表 |
| LearningDAO | `src/learning.py` | 純 SQL 學習數據存取，無 LLM |
| 內容審查 Agent | `prompts/agents/content_reviewer.txt` | 品牌+文案+受眾（合併） |
| 視覺審查 Agent | `prompts/agents/visual_reviewer.txt` | 排版+色彩+飽滿度 |
| Elite Review | `scripts/elite_review.py` | 2 agent 並行 + 學習回路 |

### 待做

| 項目 | 說明 |
|------|------|
| 整合到 daily_curation | 在 generate_image 後自動跑 elite_review |
| Prompt 注入學習成果 | `_build_learnings_injection()` 已實現，需整合到 extractor |
| 累積 100+ 筆數據後 | 接入社交媒體 API 收集真實互動數據 |

---

## 與現有系統的整合點

| 現有模組 | 改動 | 說明 |
|---------|------|------|
| `src/learning.py` | **新增** | LearningDAO — 純 SQL 學習數據存取 |
| `scripts/elite_review.py` | **新增** | 2 agent 並行審查 + 學習回路 |
| `src/migrations/005_*` | **新增** | review_scores + learnings 表 |
| `prompts/agents/` | **新增** | 2 個角色 prompt |
| `scripts/daily_curation.py` | 待整合 | 在圖片生成後呼叫 elite_review |
