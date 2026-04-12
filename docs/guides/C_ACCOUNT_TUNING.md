# C 帳號（足球英文）調優記錄

## 問題根源（2026-04-11 調查）

1. **評審邏輯誤判** — Gemini 對「史上首次」事實過度懷疑（accuracy 1/10），即使 BBC 驗證
   - 修復：`base_reviewer.txt` 改為基於內容邏輯而非知識 cutoff 評判

2. **文本提取失敗** — Google News URL 只提取 287 字摘要，Sonnet 編造內容
   - 修復：`curate_v2.py` Stage 2 檢查 full_text 長度，< 300 字時跳過

3. **球迷語氣不足** — Voice 5.5/10，讀起來平鋪直敘
   - 修復：強化 `account_profiles.py` 語氣範例（吐槽/驚嘆/戰術分析）

## 改進成果（實測 2 篇）
- ✅ Voice 提升：5.5 → 9/10
- ✅ Rewrite 迴圈有效：6.42 → 8.57 approval
- ✅ 平均分提升：5.79 → 6.43
- ⚠️ Accuracy 邏輯未生效（仍需根本架構改進）

## Phase 2：Stage 3 傳入原始文章
- `stage3_reviewer.py` 新增 `full_text` 參數
- `base_reviewer.txt` 新增 "--- ORIGINAL SOURCE ---" 區塊
- `curate_v2.py` 評審時傳入 `current_full_text`

## Phase 3：C 帳號內容長度特化
內容長度調整（用於圖片生成，非社交文案）：

| tier | 字數 | 用途 |
|---|---|---|
| 1 | 100 | 快訊標題 |
| 3 | 350 | 3-4 張 carousel |
| 5 | 550 | 詳細分析 |
| 7 | 800 | 深度報導 |

`cannot_write` 機制：源文本無法驗證核心事實時，Sonnet 輸出 `cannot_write=true` 而非編造。

## 爬蟲重構（兩層架構）

**Layer 1 — 俱樂部 BBC RSS（全收）：**
Brighton/Liverpool/Arsenal/Crystal Palace/Celtic/Monaco + Guardian CL → 直接 URL，trafilatura 正常提取

**Layer 2 — 大型媒體 RSS（姓名過濾）：**
BBC/ESPN/Sky/Guardian 全站 → `\b姓名\b` word-boundary 過濾，避免 "Ito" 誤匹配 "territory"

## 追蹤日本選手（20 人，截至 2025-08）
- PL: Mitoma(Brighton), Endo(Liverpool), Tomiyasu(Arsenal), Kamada(Crystal Palace)
- SPL: Furuhashi/Hatate/Maeda/Kobayashi(Celtic)
- BL: Doan(Freiburg), Ito H(Bayern), Itakura(Gladbach), Asano(Bochum)
- LL: Kubo(Real Sociedad)
- L1: Minamino(Monaco), Ito J(Reims), Nakamura(Reims)
- PT: Morita(Sporting CP)
- ERE: Ueda(Feyenoord), Sugawara(AZ)
- BEL: Machino(Gent)

⚠️ 轉籍時手動更新 `JAPAN_PLAYERS` dict，同步更新 `imgGen-lite`。
