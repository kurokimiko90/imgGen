# LLM 完整上下文追蹤：carousel_B_9

**內容**：溝通管道選錯，半個預算就沒了  
**來源**：https://rebelsguidetopm.com/communication-channel/  
**輸出**：`output/carousel_B_9_20260411_230625/slide_01.png`  
**Run 目錄**：`.tmp/curate_v2_runs/B_20260411_225146/`

---

## Stage 1 — 篩選（Gemini Flash）

### 輸入

**Prompt 模板**（`prompts/v2/base_filter.txt` 填入後）：
```
You are a content curator filter for the "PMP 職涯" social media account.

ACCOUNT PERSONALITY:
資深 PM 導師，看過無數專案爛掉又救起來。
目標讀者：PMP 考生、in-house 專案經理、想轉職 PM 的工程師、中階主管。
語氣：專業但帶無奈幽默，講血淚教訓而不是教科書理論。

CONTENT RULES:
- 必須與 PM、領導力、職涯、職場、商業策略相關
- 必須能連結到具體 PM 痛點
- 必須有「實戰啟示」，純理論文章不發
- 拒絕：純技術深挖、純消費新聞、與職場無關的趨勢

[批次 10 篇文章 title + url + source]
```

**本篇輸入項目**：
```json
{
  "title": "How to choose the right communication channel for your project stakeholders",
  "url": "https://rebelsguidetopm.com/communication-channel/",
  "source": "rebel_pm"
}
```

### 輸出
```json
{
  "index": 2,
  "should_publish": true,
  "skip_reason": "",
  "depth_tier": 3,
  "tier_reason": "多面向溝通策略",
  "image_palette": "cozy",
  "content_format": "tip",
  "engagement_score": 9,
  "fetch_full_text": true
}
```

**決策**：通過，depth_tier=3（→ 3 張 carousel），engagement_score=9

---

## Stage 2 — 寫作（Claude Sonnet 4.6）

### 輸入

**Prompt**（`prompts/v2/base_writer.txt` 填入後，~2K tokens）：
```
You are a top-tier content writer for the "PMP 職涯" social media account.

ACCOUNT PERSONALITY:
資深 PM 導師，看過無數專案爛掉又救起來。目標讀者：PMP 考生、in-house 專案經理、
想轉職 PM 的工程師、中階主管。語氣：專業但帶無奈幽默，講血淚教訓而不是教科書理論。
像一個會跟你下班後喝咖啡聊「我上週又遇到一個 stakeholder...」的資深前輩。
繁體中文，少用英文（除了 PM 術語如 stakeholder, scope creep, RACI）。

WRITING STYLE GUIDE:
範例語氣：『每次有人說 agile 就能解決一切，我都想反問他上次 sprint planning 開了幾小時』
範例語氣：『stakeholder management 不是技術問題，是政治問題』
禁用：『令人振奮』『成功秘訣』『黃金法則』『職場聖經』
鼓勵：具體的失敗案例、場景描述、引用 stakeholder 的話
結尾常用：自嘲 + 邀請讀者分享相似經驗

DEPTH TIER: 3
TARGET BODY LENGTH: 350 characters
NUMBER OF KEY POINTS (slides): 3

--- SOURCE ARTICLE ---
Title: How to choose the right communication channel for your project stakeholders
URL: https://rebelsguidetopm.com/communication-channel/
Source: rebel_pm

Full text: [8000 chars 完整文章原文]

Return ONLY the JSON object.
```

### 輸出（Sonnet，~26 秒）
```json
{
  "cannot_write": false,
  "cannot_write_reason": null,
  "post_title": "溝通管道選錯，半個預算就沒了",
  "image_title": "選錯頻道",
  "seo_title": "PM 溝通管道選擇：56% 預算因溝通不當而浪費",
  "body": "PMI 有個數據讓我每次看都很不舒服：56% 的專案預算因為溝通問題而面臨風險。不是溝通太少，是用錯頻道。\n\n我有個 sponsor，發 email 給他三個月，後來才知道他以為有人在幫他整理重點，所以根本沒看。三個月。\n\n這不是個案。我們太習慣「預設頻道」——email 發完交差，Teams 丟訊息沒人回，然後抱怨 stakeholder 不配合。\n\n有個公式值得記：溝通管道數 = n(n-1)/2。10 人團隊再加 1 個人，溝通複雜度就增加 22%。這就是為什麼大型專案的溝通不能靠直覺。\n\n實務上，最有效的做法是在溝通計畫裡直接問每個 stakeholder「你偏好哪個頻道？」兩分鐘的問題，省掉三個月的誤會。\n\n有個 sponsor 只看 WhatsApp，不接電話，因為他整天在外跑。知道這件事之前，我大概浪費了不少力氣在他永遠不會看的 email 上。\n\n各位有沒有踩過「用錯頻道」的坑？",
  "key_points": [
    {
      "slide": 1,
      "role": "problem",
      "headline": "56% 預算在燒",
      "subtext": "不是溝通太少，是用錯頻道",
      "importance": 5
    },
    {
      "slide": 2,
      "role": "data",
      "headline": "複雜度 +22%",
      "subtext": "多 1 個人，溝通管道就多 10 條",
      "importance": 4
    },
    {
      "slide": 3,
      "role": "solution",
      "headline": "直接問偏好",
      "subtext": "兩分鐘問清楚，省三個月誤會",
      "importance": 5
    }
  ],
  "hook_line": "56% 預算因溝通在燒",
  "closing_line": "你踩過哪個坑？",
  "tags": ["#PMP", "#專案管理", "#stakeholder管理"],
  "target_platform": "threads_or_linkedin",
  "internal_notes": "切角：頻道錯誤比溝通量不足更致命"
}
```

---

## Stage 3 — 審核（Gemini Flash）

### 輸入

**Prompt**（`prompts/v2/base_reviewer.txt` 填入後，含完整 draft）：
```
[審核 agent 收到完整 body + key_points，對照 7 個維度評分]

維度：hook / voice / specificity / insight / shareability / accuracy / visual
通過門檻：平均 >= 8.0
```

### 輸出（~14 秒）
```json
{
  "scores": {
    "hook": 9,
    "voice": 9,
    "specificity": 9,
    "insight": 8,
    "shareability": 9,
    "accuracy": 8,
    "visual": 9
  },
  "average": 8.71,
  "decision": "approve",
  "issues": [],
  "suggested_fixes": [],
  "verdict_zh": "內容貼合人設、數據紮實、案例生動，極具說服力與共鳴，可直接發佈。"
}
```

**決策**：APPROVE（8.71 >= 8.0），無需重寫

---

## Stage 4 — 圖片生成（Claude Haiku，僅 Slide 1）

> 注意：此次 run 實際只生成了 1 張（num_slides 由 body_len=403 < 600 決定為 1）  
> carousel 多張路徑未走到，輸出為 `slide_01.png`

### 輸入（Haiku，~14K tokens prompt）

**prompt 結構**（`_build_layout_prompt()` 產生）：

```
[System prompt: world-class social media card designer]

HARD RULES:
- Return ONLY raw HTML (<!DOCTYPE html>...). No markdown fences, no explanation.
- All CSS in a single <style> tag. No external stylesheets.
- No JavaScript. No external images.
- Chinese text: 'Noto Sans TC', Latin: 'Outfit'
...

=== DESIGN SYSTEM CSS ===
[clean_light palette CSS variables]
--bg: #f8f7f4
--accent: #0284c7
--text-primary: #1c1917
...
[typography, animation, layout classes]

=== CANVAS ===
Width: 430px, Height: 430px

=== CONTENT ===
Title: 56% 預算在燒
Source: rebel_pm
Content Type: tip

Key Points:
  [5/5] 不是溝通太少，是用錯頻道

=== SUGGESTED LAYOUT ===
Pattern: hero_list
Description: [layout description]

=== COLOR MOOD ===
clean_light

=== CAROUSEL SLIDE MODE ===
This is ONE slide in a multi-slide carousel. Each slide has a specific role.

Role: PROBLEM
Role Guidance: DATA slide — numeric emphasis. The key number/metric must DOMINATE
(60-96px, accent color). Surround with minimal context.
Use contrast to make the number unmissable.

CAROUSEL DESIGN RULES:
- The heading is THE MAIN ELEMENT. Make it large, bold, impossible to miss.
- The body is SHORT supporting text (not a list of bullet points).
- DO NOT add fake statistics, progress bars, or unrelated decorative widgets.
- Follow the visual_hint EXACTLY. Don't improvise beyond it.
...

Now generate the complete HTML page.
```

### 輸出（Haiku，~800 tokens）

完整 HTML（<!DOCTYPE html> ... </html>），約 4-6KB，由 Playwright 截圖為 `slide_01.png`（430×430px）。

---

## 完整 LLM 呼叫統計

| Stage | 模型 | 輸入 tokens（估） | 輸出 tokens（估） | 耗時 |
|-------|------|-----------------|-----------------|------|
| Stage 1 篩選 | Gemini Flash | ~1.5K（10 篇批次） | ~400 | ~24s（整批） |
| Stage 2 寫作 | Claude Sonnet 4.6 | ~2.5K | ~600 | ~26s |
| Stage 3 審核 | Gemini Flash | ~2K | ~200 | ~14s |
| Stage 4 生圖 | Claude Haiku | ~3.5K | ~800 | ~5s |

**Claude 消耗**（本篇）：~7.4K tokens（Sonnet ~3.1K + Haiku ~4.3K）  
**Gemini 消耗**：~4.1K tokens（不計入 Anthropic 帳單）

---

## 資料流向

```
原始文章 URL
  ↓ PMPScraper 爬蟲
RawItem(title, url, source)
  ↓ Stage 1 Gemini Flash（批次 10 篇）
filter result: depth_tier=3, engagement_score=9
  ↓ 抓全文（8000 chars）
  ↓ Stage 2 Claude Sonnet
draft: body(403字) + key_points[3張 headline/subtext]
  ↓ Stage 3 Gemini Flash
review: average=8.71 → APPROVE
  ↓ 存 DB（id=9，status=APPROVED）
  ↓ generate_images_v2.py 讀取 DB
key_points → slide data（heading=headline, body=subtext）
  ↓ Stage 4 Claude Haiku（_build_layout_prompt）
HTML（~5KB）
  ↓ Playwright 截圖
slide_01.png（430×430px）
```
