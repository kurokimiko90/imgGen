"""
test_new_templates.py — Render and screenshot all 5 new social-media templates.

Usage:
    python scripts/test_new_templates.py
"""

import sys
from pathlib import Path

# Allow imports from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.renderer import render_card
from src.screenshotter import take_screenshot

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "test_new_templates"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Test fixtures ────────────────────────────────────────────────────────────

FIXTURES = [
    {
        "theme": "hook",
        "format": "square",
        "data": {
            "title": "為什麼努力工作的人，往往越來越窮？",
            "key_points": [
                {"text": "時間換金錢有根本缺陷：你的時間有上限，但市場的需求不是"},
                {"text": "財富積累的本質是讓資產替你工作，而非你替別人工作"},
                {"text": "大多數教育只教你如何成為好員工，而非如何建立資產"},
            ],
            "source": "《富爸爸 窮爸爸》精華",
        },
    },
    {
        "theme": "quote",
        "format": "story",
        "data": {
            "title": "來自《思考，快與慢》— 丹尼爾·康納曼",
            "key_points": [
                {
                    "text": "我們對自己所知甚少，卻對自己的判斷極度自信——這正是大多數錯誤決策的根源。"
                }
            ],
            "source": "丹尼爾·康納曼 / Daniel Kahneman",
        },
    },
    {
        "theme": "data_impact",
        "format": "square",
        "data": {
            "title": "47% 的現有工作將在 20 年內被 AI 取代",
            "key_points": [
                {"text": "高風險職業：資料輸入、客服電話、初級財務會計（自動化機率 > 85%）"},
                {"text": "低風險職業：創意設計、心理諮詢、複雜跨域決策（自動化機率 < 4%）"},
                {"text": "每年新增 AI 相關職位已超越被替代職位，但技能斷層仍是最大障礙"},
            ],
            "source": "牛津大學 Frey & Osborne 研究報告",
        },
    },
    {
        "theme": "versus",
        "format": "square",
        "data": {
            "title": "你讀了多少書，不重要——你怎麼讀，才是關鍵",
            "key_points": [
                {"text": "讀完就忘，從不複習"},
                {"text": "追量，忽略吸收品質"},
                {"text": "被動閱讀，無輸出"},
                {"text": "帶問題讀，主動連結"},
                {"text": "立即提取 3 個行動"},
                {"text": "費曼法則：講出來才算懂"},
            ],
            "source": "學習科學研究",
        },
    },
    {
        "theme": "quote_dark",
        "format": "story",
        "data": {
            "title": "來自《人類大歷史》— 哈拉瑞",
            "key_points": [
                {
                    "text": "你無法在顯微鏡下找到「民族」、「人權」或「金錢」——但正是這些共同的虛構，讓七十億人能夠合作。"
                }
            ],
            "source": "尤瓦爾·諾瓦·哈拉瑞",
        },
    },
    {
        "theme": "pop_split",
        "format": "square",
        "data": {
            "title": "你的朋友圈 vs 你本人",
            "key_points": [
                {"text": "每天發限時動態焦慮生活、覺得自己被世界拋下、刷到別人的高光就自我懷疑"},
                {"text": "其實根本沒在追蹤那些人、已讀不回才是真愛、週末最大的成就是不出門"},
            ],
            "source": "社群觀察日誌",
        },
    },
    {
        "theme": "editorial",
        "format": "square",
        "data": {
            "title": "為什麼閱讀讓你越來越聰明",
            "key_points": [
                {"text": "大腦在閱讀時會同步啟動語言、視覺與記憶神經迴路，等同每次翻頁都在做認知訓練"},
                {"text": "虛構故事可提升同理心：閱讀他人視角激活「鏡像神經元」，如同親身經歷"},
                {"text": "每天閱讀 30 分鐘的人，認知衰退風險比不閱讀者低達 32%（賓州大學長期研究）"},
            ],
            "source": "神經科學閱讀研究",
        },
    },
    {
        "theme": "luxury_data",
        "format": "square",
        "data": {
            "title": "全球 AI 市場規模正在爆炸",
            "key_points": [
                {"text": "$1.8T | 預估 2030 年市場規模"},
                {"text": "37% | 年均複合成長率 CAGR"},
                {"text": "4.2B | 全球 AI 活躍用戶數"},
                {"text": "中國與美國合計佔全球 AI 投資的 65%，歐盟監管框架拖慢歐洲佈局"},
                {"text": "生成式 AI 將在 2025–2027 年貢獻 40% 的新增 AI 收入"},
            ],
            "source": "Goldman Sachs & IDC 2024",
        },
    },
    {
        "theme": "ai_theater",
        "format": "square",
        "data": {
            "title": "AI 接管辦公室：一週實測報告",
            "key_points": [
                {"text": "day_01: 請 AI 寫週報 → 老闆說「這是你最好的週報」"},
                {"text": "day_03: 請 AI 回信 → 客戶說「你最近變得很體貼」"},
                {"text": "day_05: 請 AI 開會摘要 → 同事問「你有在認真聽嗎」"},
                {"text": "conclusion: status=REPLACED | confidence=0.97"},
            ],
            "source": "NOZOMI 田野調查 2026",
        },
    },
    {
        "theme": "studio",
        "format": "square",
        "data": {
            "title": "查理·芒格的三個終身受用原則",
            "key_points": [
                {"text": "反向思維：不問「怎麼成功」，先問「怎麼確保失敗」——把所有失敗路徑排除，剩下的就是答案"},
                {"text": "多元心智模型：從物理、生物、心理學各借一把尺，單一視角只能看見單一錯誤"},
                {"text": "耐心即護城河：大多數人高估一年能做的事，低估十年能積累的優勢"},
            ],
            "source": "Poor Charlie's Almanack",
        },
    },
    {
        "theme": "broadsheet",
        "format": "square",
        "data": {
            "title": "台積電擴產計畫震撼全球供應鏈",
            "key_points": [
                {"text": "2nm 製程良率突破 70%，量產時程提前至 2025 Q3，超越三星同期計畫"},
                {"text": "美國亞利桑那廠二期追加投資 $250 億，帶動當地半導體就業增加 2 萬人"},
                {"text": "AI 晶片需求帶動 CoWoS 封裝產能缺口，台積電計畫 2025 年底擴增 3 倍"},
            ],
            "source": "路透社 / 工商時報 2026",
        },
    },
    {
        "theme": "pastel",
        "format": "square",
        "data": {
            "title": "你不需要更多動力，你需要更好的環境",
            "key_points": [
                {"text": "意志力是有限資源，真正持久的改變靠的是讓好行為變得最省力"},
                {"text": "把書放在枕頭旁，把手機充電器放在另一個房間——環境比決心更誠實"},
                {"text": "你是周圍五個人的平均值，選擇你的環境就是選擇你的未來"},
            ],
            "source": "《原子習慣》James Clear",
        },
    },
    {
        "theme": "paper_data",
        "format": "square",
        "data": {
            "title": "全球氣溫已比工業化前高出 1.45°C",
            "key_points": [
                {"text": "2023 年成為有記錄以來最熱年份，打破過去 125,000 年的氣溫紀錄"},
                {"text": "北極海冰面積創歷史新低，比 1979 年基準減少 23%，融化速度超出模型預測"},
                {"text": "極端高溫事件頻率在 50 年內增加了 5 倍，熱浪致死人數每十年翻倍"},
            ],
            "source": "IPCC 2024 綜合報告",
        },
    },
    # ── Batch 4 — Light Content Variants ────────────────────────────────────
    {
        "theme": "bulletin_hook",
        "format": "square",
        "data": {
            "title": "為什麼讀了 100 本書的人，還是沒有變聰明？",
            "key_points": [
                {"text": "輸入量和輸出質量不成正比——大腦留下的是「使用過的知識」"},
                {"text": "閱讀只是獲取資訊，理解需要複述、應用和反芻"},
                {"text": "真正的學習發生在「你試圖解釋給別人聽」的那一刻"},
            ],
            "source": "學習科學研究",
        },
    },
    {
        "theme": "gallery_quote",
        "format": "square",
        "data": {
            "title": "你無法在顯微鏡下找到「民族」或「金錢」——但正是這些共同的虛構，讓七十億人能夠合作。",
            "key_points": [
                {"text": "尤瓦爾·諾瓦·哈拉瑞"},
                {"text": "《人類大歷史》"},
            ],
            "source": "Sapiens",
        },
    },
    {
        "theme": "soft_versus",
        "format": "square",
        "data": {
            "title": "你現在的閱讀方式，決定了十年後你的思考深度",
            "key_points": [
                {"text": "讀完就忘，從不複習"},
                {"text": "追量不追質，炫耀書單"},
                {"text": "被動吸收，無輸出"},
                {"text": "帶問題讀，主動連結"},
                {"text": "立即提取 3 個行動"},
                {"text": "費曼法則：講出來才算懂"},
            ],
            "source": "學習科學研究",
        },
    },
    {
        "theme": "trace",
        "format": "square",
        "data": {
            "title": "30 天建立晨間閱讀習慣的完整方法",
            "key_points": [
                {"text": "設定固定時間窗口（建議 06:30–07:00）"},
                {"text": "移除環境障礙：手機充電器移到另一個房間"},
                {"text": "第一週只讀 5 分鐘，降低啟動成本"},
                {"text": "用紙本書或 Kindle，避免 App 通知干擾"},
                {"text": "讀完立刻寫一句話：「我今天學到了＿＿」"},
                {"text": "第 21 天後開始挑戰長度，從 5 到 20 分鐘"},
            ],
            "source": "《原子習慣》James Clear",
        },
    },
    # ── Batch 5 — High-Impact Content Types ─────────────────────────────────
    {
        "theme": "ranking",
        "format": "square",
        "data": {
            "title": "改變我人生觀的 5 本書",
            "key_points": [
                {"text": "《窮爸爸富爸爸》｜重新定義什麼是資產與負債"},
                {"text": "《原子習慣》｜用系統取代目標的行為改變聖經"},
                {"text": "《思考，快與慢》｜揭開大腦兩套決策系統的秘密"},
                {"text": "《人類大歷史》｜用宏觀視角看清文明的本質"},
                {"text": "《反脆弱》｜為什麼不確定性反而是你的優勢"},
            ],
            "source": "個人書單 2026",
        },
    },
    {
        "theme": "before_after",
        "format": "square",
        "data": {
            "title": "同一個人，讀書方式不同，結果天差地別",
            "key_points": [
                {"text": "讀完就算，從不複習"},
                {"text": "追求數量，月讀 10 本"},
                {"text": "被動接收，沒有輸出"},
                {"text": "每章寫摘要，連結既有知識"},
                {"text": "精讀 3 本，深度理解勝過廣度"},
                {"text": "費曼法則：用自己的話解釋給朋友聽"},
            ],
            "source": "學習科學研究",
        },
    },
    {
        "theme": "concept",
        "format": "square",
        "data": {
            "title": "第一性原理｜First Principles",
            "key_points": [
                {"text": "從最基本的事實出發，不依賴類比或前人假設，重新推導出答案。"},
                {"text": "適用場景｜技術創新、成本優化、打破行業慣例"},
                {"text": "代表人物｜馬斯克（火箭）、費曼（物理教學）、笛卡兒（哲學）"},
                {"text": "常見誤解｜≠ 從頭創造，而是回到根本再重構"},
            ],
            "source": "思維框架系列",
        },
    },
    {
        "theme": "picks",
        "format": "square",
        "data": {
            "title": "讓我每年重讀一次的 4 本書",
            "key_points": [
                {"text": "4|《窮爸爸富爸爸》|財富觀的啟蒙，每次讀都有新發現"},
                {"text": "4|《原子習慣》|習慣系統的設計手冊，實用到異常"},
                {"text": "3|《思考，快與慢》|認知偏誤的完整地圖"},
                {"text": "3|《反脆弱》|顛覆你對風險的所有認知"},
            ],
            "source": "這份書單花了我 5 年才選出",
        },
    },
    # ── Batch 6 — Complete Coverage ─────────────────────────────────────────
    {
        "theme": "opinion",
        "format": "square",
        "data": {
            "title": "——我認為，大多數人的問題不是「不夠努力」，而是「不夠清醒」",
            "key_points": [
                {"text": "努力工作的人很多，但真正成功的人懂得選擇方向"},
                {"text": "清醒 = 知道自己真正想要什麼，並敢於拒絕其他"},
                {"text": "把精力花在槓桿點上，遠比無差別努力更有效"},
            ],
            "source": "同意這個觀點嗎？留言告訴我",
        },
    },
    {
        "theme": "checklist",
        "format": "square",
        "data": {
            "title": "發文前必做的 8 件事",
            "key_points": [
                {"text": "確認標題前 5 個字能抓住注意力"},
                {"text": "第一張圖的衝擊力 > 3 秒法則"},
                {"text": "CTA 放在第 3 行之前"},
                {"text": "內容包含至少一個具體數字"},
                {"text": "完成標籤研究，選 3 個精準標籤"},
                {"text": "封面文字佔比 < 20%"},
                {"text": "發布時間選在目標受眾活躍時段"},
                {"text": "準備好第一則留言引導互動"},
            ],
            "source": "社群發文 SOP",
        },
    },
    {
        "theme": "faq",
        "format": "square",
        "data": {
            "title": "讀書這件事，最常被問到的 3 個問題",
            "key_points": [
                {"text": "為什麼讀了書還是會忘？｜因為輸入沒有配合輸出，大腦保留的是「使用過的知識」"},
                {"text": "一天要讀多久才夠？｜重點不在時長，而在密度——20 分鐘完全專注 > 2 小時發呆"},
                {"text": "如何選擇下一本書？｜從你正在面對的問題出發，讓現實需求決定閱讀順序"},
            ],
            "source": "閱讀研究所",
        },
    },
    {
        "theme": "milestone",
        "format": "square",
        "data": {
            "title": "10,000｜位讀者",
            "key_points": [
                {"text": "從第一篇文章到現在，我學到了三件事："},
                {"text": "持續輸出比完美輸出重要——開始比準備好更關鍵"},
                {"text": "讀者真正想要的，往往和你以為的不一樣"},
                {"text": "轉折點不是靠運氣，是靠持續出現直到機會來臨"},
            ],
            "source": "感謝每一位陪我走到這裡",
        },
    },
    # ── Original thread_card fixture ────────────────────────────────────────
    {
        "theme": "thread_card",
        "format": "square",
        "thread_index": 2,
        "thread_total": 7,
        "data": {
            "title": "7 個改變我人生的思維框架",
            "key_points": [
                {"text": "第一性原理：質疑所有前提，從最基本的事實重新推導答案。馬斯克用它將火箭成本降低了 90%。"},
                {
                    "text": "反向思維：不問「如何成功」，而問「如何確保失敗」——然後避免那些行為。查理·芒格最愛用這個框架。"
                },
                {"text": "機會成本思維：每個「是」都是對其他所有事情說「不」。"},
                {"text": "系統 vs 目標：不要設定目標，建立系統——好系統會自動產出好結果。"},
                {"text": "圈子能力：只在自己真正懂的領域做決策，並誠實面對邊界在哪。"},
                {"text": "複利視角：問自己「這件事五年後會比今天更有價值嗎？」"},
                {"text": "魯棒性優先：在不確定的世界裡，比起追求最佳解，更應追求不會崩潰的解。"},
            ],
            "source": "思維框架系列",
        },
    },
]


def run():
    print(f"\n生成測試圖片 → {OUTPUT_DIR}\n{'─' * 48}")
    for fixture in FIXTURES:
        theme = fixture["theme"]
        fmt = fixture.get("format", "story")
        data = fixture["data"]
        thread_index = fixture.get("thread_index")
        thread_total = fixture.get("thread_total")

        html = render_card(
            data,
            theme=theme,
            format=fmt,
            thread_index=thread_index,
            thread_total=thread_total,
        )

        out_path = OUTPUT_DIR / f"test_{theme}.png"
        take_screenshot(html, out_path, format=fmt)
        print(f"  [{theme:14s}]  {out_path.name}")

    print(f"\n完成！共 {len(FIXTURES)} 張\n")


if __name__ == "__main__":
    run()
