# imgGen 迭代開發計畫

## 專案定位

**單人使用工具（一人公司）**
- 不做多用戶、雲端 SaaS、團隊協作功能
- 重點：個人效率、本地工作流、輸出品質、自動化

---

## 整體流程

```
Pre-work:
  └── 建立初始 docs/PRD.md（基於現有程式碼狀態）

Cycle N (N = 1..5):
  ├── [PM Agent] 讀取當前程式碼 + PRD.md
  │     └── 輸出 docs/roadmap_cycle_N.md（10版本規劃）
  │
  ├── [自動分析] 用評分矩陣選出最高分功能
  │     └── 準則：User Impact (1-5) × Feasibility (1-5) × WOW Factor (1-5)
  │
  ├── [TDD Guide Agent] 實現功能
  │     ├── 寫測試（RED）
  │     ├── 實現代碼（GREEN）
  │     └── 重構（IMPROVE）
  │
  ├── [Code Reviewer Agent] 審查實現
  │     └── 修復 CRITICAL/HIGH 問題
  │
  ├── 跑測試確認全過
  │
  └── [更新文件]
        ├── docs/PRD.md（已完成功能、下一版優先級）
        └── README.md（若 CLI/用法有變）
```

---

## 文件結構

```
docs/
  PLAN.md                  # 本文件：整體開發計畫
  PRD.md                   # 持續更新的產品需求文件
  CHANGELOG.md             # 每個 Cycle 的功能紀錄
  roadmap_cycle_1.md       # Cycle 1 的 10 版本規劃
  roadmap_cycle_2.md       # Cycle 2 重新規劃（基於新現況）
  roadmap_cycle_3.md
  roadmap_cycle_4.md
  roadmap_cycle_5.md
```

---

## 功能選擇評分準則

每個 Cycle 從 roadmap 中選出最高分功能實現：

| 維度 | 說明 | 分數 |
|-----|------|------|
| User Impact | 對日常使用的直接改善程度 | 1-5 |
| Feasibility | 在一個 Cycle 內可完整實現的可行性 | 1-5 |
| WOW Factor | 使用時的驚喜感、有感程度 | 1-5 |

**選勝者 = 三項分數乘積最高**

---

## 約束條件

- **單人使用**：不做多用戶、不做雲端、不做 SaaS
- **版本控制**：不做 git commit，重要版本手動備份到 Google Drive
- **文件優先**：每個 Cycle 必須輸出 roadmap MD，完成後更新 PRD
- **TDD 強制**：所有新功能先寫測試，測試覆蓋率 ≥ 80%
- **Review 必做**：TDD 完成後執行 code-reviewer agent

---

## 執行紀錄

| Cycle | 實現功能 | Roadmap 文件 | 狀態 |
|-------|---------|-------------|------|
| Pre-work | 建立 PRD.md | - | ✅ 完成 |
| 1 | v1.5 多社群格式輸出 | roadmap_cycle_1.md | ✅ 完成 |
| 2 | v1.6 Config File 支援 | roadmap_cycle_2.md | ✅ 完成 |
| 3 | v1.8 浮水印與個人品牌 | roadmap_cycle_3.md | ✅ 完成 |
| 4 | v2.0 批次處理（Batch Processing） | roadmap_cycle_4.md | ✅ 完成 |
| 5 | v2.4 Preset System（預設參數組合） | roadmap_cycle_5.md | ✅ 完成 |
