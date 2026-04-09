# Claude 可用工具分析（基於 Gemini_說_分析指南.md）

> 本機 Claude Code 可用於本項目的 Agents 和 Skills，按任務階段分類。

---

## 一、策劃（Strategy & Planning）

### Agents

| Agent | 用途 | 對應項目需求 |
|---|---|---|
| **planner** | 將需求拆解為實施計畫 | 拆解 8 週路線圖的每個階段 |
| **architect** | 系統架構決策 | 設計三層架構（策展大腦→內容倉庫→發布系統） |
| **Product Manager** (subagent) | 產品全生命週期管理 | 定義三帳號的定位、MVP 範圍、迭代策略 |

### Skills

| Skill | 用途 | 對應項目需求 |
|---|---|---|
| `/plan` | 需求重述 + 風險評估 + 實施方案 | 生成階段 1-5 的結構化計畫 |
| `/blueprint` | 一句話 → 逐步藍圖 | 快速將「三帳號自動化運營」轉為任務清單 |

---

## 二、調研（Research）

### Agents

| Agent | 用途 | 對應項目需求 |
|---|---|---|
| **general-purpose** | 多步驟研究任務 | 調研各平台 API 限制、競品分析 |
| **Social Media Strategist** (subagent) | 跨平台社媒策略 | 研究 Threads/X/IG 的演算法特性 |
| **SEO Specialist** (subagent) | 搜索優化研究 | Calendar Marketing 的關鍵詞和趨勢研究 |
| **Trend Researcher** (subagent) | 趨勢識別和機會評估 | 科技圈、職涯、足球的趨勢預測 |

### Skills

| Skill | 用途 | 對應項目需求 |
|---|---|---|
| `/deep-research` | 多源深度調研 | 爆款內容拆解、研究 10 個爆紅帖文的共性 |
| `/market-research` | 市場研究、競爭分析 | AI/PMP/足球英文 三個領域的市場定位 |
| `/search-first` | 先搜索後編碼 | 找現有爬蟲框架、發布工具、MCP Server |
| `/exa-search` | 神經語義搜索 | 發現跨領域的內容靈感和案例 |
| `/docs` | 查詢最新庫文檔 | 確認 Meta Graph API、X API 的最新用法 |

---

## 三、詳細計畫（Detailed Planning）

### Agents

| Agent | 用途 | 對應項目需求 |
|---|---|---|
| **Software Architect** (subagent) | 系統設計、DDD、架構模式 | SQLite schema、HITL 狀態機、發布流水線 |
| **Database Optimizer** (subagent) | Schema 設計和查詢優化 | 設計內容倉庫的 SQLite 結構 |
| **Backend Architect** (subagent) | 後端架構和 API 設計 | 多平台 Adapter 層設計 |

### Skills

| Skill | 用途 | 對應項目需求 |
|---|---|---|
| `/api-design` | REST API 設計模式 | 統一內容 API → 多平台 Adapter |
| `/database-migrations` | 數據庫遷移最佳實踐 | SQLite 內容倉庫的 schema 演進 |
| `/python-patterns` | Python 慣用模式 | 爬蟲、發布腳本的代碼規範 |
| `/docker-patterns` | 容器化模式 | 部署爬蟲和發布服務 |
| `/deployment-patterns` | 部署流程和 CI/CD | launchd 定時任務、監控告警 |

---

## 四、處理各種細節（Implementation & Execution）

### Agents

| Agent | 用途 | 對應項目需求 |
|---|---|---|
| **tdd-guide** | 測試驅動開發 | 每個模組先寫測試再實現 |
| **code-reviewer** | 代碼審查 | 每個模組完成後審查質量 |
| **security-reviewer** | 安全分析 | API 密鑰管理、防止帳號洩露 |
| **build-error-resolver** | 修復構建錯誤 | API 對接出錯時快速定位 |
| **Content Creator** (subagent) | 內容策略和文案 | 為三帳號生成內容模板 |
| **Twitter Engager** (subagent) | X 平台互動策略 | 自動導流和留言策略設計 |
| **Instagram Curator** (subagent) | IG 視覺內容策略 | 圖文/輪播的視覺設計方向 |
| **Analytics Reporter** (subagent) | 數據分析和報告 | 階段 5 的三個月數據分析 |
| **Data Engineer** (subagent) | 數據管道建設 | 爬蟲 → AI 分析 → 存儲的管道設計 |

### Skills

| Skill | 用途 | 對應項目需求 |
|---|---|---|
| `/data-scraper-agent` | 自動化數據採集 Agent | 構建爬蟲抓取目標數據（層 1：策展大腦） |
| `/content-engine` | 平台原生內容系統 | 三帳號差異化內容生成 |
| `/crosspost` | 多平台內容分發 | Threads / X / IG 同步發布 |
| `/x-api` | X/Twitter API 整合 | X 帳號的發布和互動自動化 |
| `/article-writing` | 寫文章、指南、教程 | 帳號 1 的技術拆解文 |
| `/tdd` | TDD 工作流 | 爬蟲和發布模組的測試 |
| `/security-review` | 安全審查 | API 密鑰、OAuth token 管理 |
| `/prompt-optimize` | 優化 AI 提示詞 | 優化「爆款拆解」「趨勢預測」「評論分析」三個 Skill 的提示詞 |
| `/verification-loop` | 全面驗證系統 | 每個模組完成後的端到端驗證 |
| `/autonomous-loops` | 自治 Agent 循環模式 | 監控帖文互動 → AI 分析 → 自動回覆的閉環 |

---

## 五、多 Agent 協作編排

| 工具 | 用途 |
|---|---|
| `/devfleet` | 並行啟動多個 Claude Code Agent 處理獨立模組 |
| `/orchestrate` | 順序 + tmux/worktree 編排複雜工作流 |

---

## 推薦啟動順序

```
第 1 步 ─ /plan                    → 生成結構化實施計畫
第 2 步 ─ architect Agent          → 確定三層架構的技術選型
第 3 步 ─ /deep-research           → 調研各平台 API + 爆款內容特徵
第 4 步 ─ /search-first            → 找現有工具和框架（避免重複造輪子）
第 5 步 ─ tdd-guide + code-reviewer → 逐模組實現和審查
第 6 步 ─ /devfleet                → 並行處理三帳號的獨立工作
```

---

*生成日期：2026-03-31*
