"""
extractor.py - AI summarization module

Extracts structured key points from article text.
Supports Claude API, Gemini, GPT, and Claude CLI as providers.
"""

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ExtractionConfig:
    """User-controllable extraction parameters."""

    language: str = "zh-TW"
    tone: str = "professional"
    max_points: int = 5
    min_points: int = 3
    title_max_chars: int = 15
    point_max_chars: int = 50
    custom_instructions: str = ""
    mode: str = "card"  # "card" (key_points) or "article" (sections) or "smart" (AI layout)
    social_mode: bool = False  # True = social-media optimised: shorter text + hook keyword per point


_LANGUAGE_NAMES = {
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
}

_TONE_DESCRIPTIONS = {
    "professional": "專業、簡潔、客觀",
    "casual": "輕鬆、口語化、親切",
    "academic": "學術、嚴謹、引用數據",
    "marketing": "吸引眼球、強調價值、行動導向",
}


def _build_system_prompt(config: ExtractionConfig) -> str:
    """Build a system prompt from ExtractionConfig."""
    lang_name = _LANGUAGE_NAMES.get(config.language, config.language)
    tone_desc = _TONE_DESCRIPTIONS.get(config.tone, config.tone)

    custom_line = (
        f"\n- 附加要求：{config.custom_instructions}"
        if config.custom_instructions
        else ""
    )

    return f"""你是一位專業的文章摘要分析���。

使用 {lang_name} 輸出。語氣風格：{tone_desc}。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{{
  "title": "文章的核心標題（{config.title_max_chars}字以內）",
  "key_points": [
    {{"text": "重點內容（{config.point_max_chars}字以內）"}}
  ],
  "source": "來源信息（如果有，否則留空字串）",
  "theme_suggestion": "dark 或 light 或 gradient 或 warm_sun 或 cozy"
}}

規則：
- key_points 必須有 {config.min_points} 到 {config.max_points} 個重點
- title 要簡潔有力，能夠概括文章核心
- theme_suggestion：科技/商業類建議 dark，財經/分析類建議 gradient，生活/文化類建議 light，溫馨/日常類建議 cozy，創意/娛樂/正能量類建議 warm_sun

重點精簡規則（嚴格遵守）：
- 每條重點以動詞或關鍵名詞開頭，禁止虛詞開頭（「的」「了」「是」「在」「有」「會」）
- 刪除所有不影響理解的修飾詞（「非常」「相當」「基本上」「目前來看」「其實」「可以說」）
- 用具體數據取代模糊描述（「大幅成長」→「成長 40%」，「很多用戶」→「超過 10 萬用戶」）
- 一條重點只表達一個核心信息，禁止用逗號串聯多件事
- 優先保留：數據、結論、行動項；優先刪除：背景鋪墊、過渡句、重複內容{custom_line}
- 只返回 JSON，不要有任何前言或後語"""


def _build_article_prompt(config: ExtractionConfig) -> str:
    """Build a system prompt for article mode (condense + organize)."""
    lang_name = _LANGUAGE_NAMES.get(config.language, config.language)
    tone_desc = _TONE_DESCRIPTIONS.get(config.tone, config.tone)

    custom_line = (
        f"\n- 附加要求：{config.custom_instructions}"
        if config.custom_instructions
        else ""
    )

    return f"""你是一位專業的內容編輯，擅長將冗長文章精簡為條理分明的短文。

使用 {lang_name} 輸出。語氣風格：{tone_desc}。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{{
  "title": "文章的核心標題（{config.title_max_chars}字以內）",
  "sections": [
    {{
      "heading": "段落小標題（4-8字）",
      "body": ["第一個要點（15-25字）", "第二個要點（15-25字）"]
    }}
  ],
  "source": "來源信息（如果有，否則留空字串）",
  "theme_suggestion": "dark 或 light 或 gradient 或 warm_sun 或 cozy"
}}

規則：
- sections 必須恰好 3 個段落，不多不少
- 每個段落的 body 是一個字串陣列，每個元素是一個獨立要點（15-25字）
- 每個段落有 2-3 個要點，不多不少
- 每個段落必須有 heading（4-8 字的小標題），不可為空
- title 要簡潔有力，能夠概括文章核心
- theme_suggestion：科技/商業類建議 dark，財經/分析類建議 gradient，生活/文化類建議 light，溫馨/日常類建議 cozy，創意/娛樂/正能量類建議 warm_sun

精簡規則（嚴格遵守）：
- 每個要點是一句完整的短句，獨立可理解
- 刪除所有修飾詞、過渡句、背景鋪墊
- 用具體數據取代模糊描述
- 三段結構：核心概念→具體做法→關鍵細節
- 動詞或名詞開頭，禁止虛詞開頭{custom_line}
- 只返回 JSON，不要有任何前言或後語"""


_VALID_CONTENT_TYPES = {
    "news", "opinion", "howto", "data", "comparison",
    "quote", "timeline", "ranking",
}

_VALID_LAYOUT_HINTS = {
    "hero_list", "grid", "timeline", "comparison",
    "quote_centered", "data_dashboard", "numbered_ranking",
}

_VALID_COLOR_MOODS = {
    "dark_tech", "warm_earth", "clean_light", "bold_contrast", "soft_pastel",
}


def _build_smart_prompt(config: ExtractionConfig) -> str:
    """Build a system prompt for smart mode (extract + content analysis)."""
    lang_name = _LANGUAGE_NAMES.get(config.language, config.language)
    tone_desc = _TONE_DESCRIPTIONS.get(config.tone, config.tone)

    custom_line = (
        f"\n- 附加要求：{config.custom_instructions}"
        if config.custom_instructions
        else ""
    )

    content_types = "|".join(sorted(_VALID_CONTENT_TYPES))
    layout_hints = "|".join(sorted(_VALID_LAYOUT_HINTS))
    color_moods = "|".join(sorted(_VALID_COLOR_MOODS))

    # Social mode: shorter text + hook field per point
    if config.social_mode:
        point_schema = (
            '{{"hook": "核心詞/數字（最多5字，例如：20分鐘/4屏佈局）", '
            '"text": "說明（最多{chars}字，必須1行內讀完）", "importance": 5}}'
        ).format(chars=min(config.point_max_chars, 22))
        social_rules = """
社群圖專用規則（最高優先級）：
- hook 是每個要點的「視覺鉤子」，設計師會以大字展示，必須是最核心的詞、數字或命令
  好的 hook：20分鐘 / 4屏佈局 / test-session / LaunchAgents
  壞的 hook：自動保存 / 使用特徵（太模糊）
- text 是 hook 的補充說明，用戶掃描完 hook 後看的，控制在 22 字內
- 3 秒法則：標題 + 所有 hook 在 3 秒內可以被掃描完畢
- 優先提取數字、命令、工具名稱作為 hook"""
    else:
        point_schema = f'{{"text": "重點內容（{config.point_max_chars}字以內）", "importance": 5}}'
        social_rules = ""

    return f"""你是一位專業的內容分析師兼版式設計顧問。

使用 {lang_name} 輸出。語氣風格：{tone_desc}。

你需要分析文章內容，提取重點，並判斷最適合的視覺呈現方式。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{{
  "title": "文章的核心標題（{config.title_max_chars}字以內）",
  "key_points": [
    {point_schema}
  ],
  "source": "來源信息（如果有，否則留空字串）",
  "content_type": "{content_types}",
  "layout_hint": "{layout_hints}",
  "color_mood": "{color_moods}"
}}

規則：
- key_points 必須有 {config.min_points} 到 {config.max_points} 個重點
- importance 為 1-5 的整數，5 為最重要
- title 要簡潔有力，能夠概括文章核心

content_type 判斷標準：
- news：新聞報導、時事消息
- opinion：觀點評論、社論
- howto：教學、步驟指南、方法論
- data：數據分析、統計報告、研究結果
- comparison：對比分析、優劣比較
- quote：名言金句、語錄、訪談精華
- timeline：時間線、歷程、事件順序
- ranking：排行榜、TOP-N、推薦清單

layout_hint 判斷標準（嚴格根據內容結構選擇，禁止預設 hero_list）：
- hero_list：明確有一個壓倒性主角重點 + 配角支撐（少用，只在真有主次時選）
- grid：3-4 個並列要點、地位相當、無明顯主次（最常見的清單類內容）
- timeline：有時間順序、步驟順序、流程的內容
- comparison：兩方或多方對比、優劣分析
- quote_centered：以引言/金句/觀點為核心的內容
- data_dashboard：數據密集、有具體數字、指標的內容
- numbered_ranking：有排名、優先順序、TOP-N 清單（技巧類、工具類推薦）

選擇原則：howto/技巧/工具類 → numbered_ranking 或 grid；新聞爆點 → hero_list；純步驟 → timeline

color_mood 判斷標準：
- dark_tech：科技、商業、嚴肅專業
- warm_earth：人文、歷史、溫暖質感
- clean_light：生活、教育、清爽簡潔
- bold_contrast：衝擊力強、對比鮮明、重要公告
- soft_pastel：輕鬆、創意、柔和氛圍

重點精簡規則（嚴格遵守）：
- 每條重點以動詞或關鍵名詞開頭，禁止虛詞開頭
- 刪除所有不影響理解的修飾詞
- 用具體數據取代模糊描述
- 一條重點只表達一個核心信息{social_rules}{custom_line}
- 只返回 JSON，不要有任何前言或後語"""


# Legacy hardcoded prompt — kept as fallback reference (now generated by _build_system_prompt)
SYSTEM_PROMPT = """你是一位專業的文章摘要分析師，專門將長篇文章提煉成簡潔有力的重點摘要。

你的任務是從提供的文章中提取關鍵信息，並以結構化的 JSON 格式返回。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{
  "title": "文章的核心標題（15字以內，有力且吸引人）",
  "key_points": [
    {
      "text": "重點內容（30-50字，清晰且具體）"
    }
  ],
  "source": "來源信息（如果文章中有提及，否則留空字串）",
  "theme_suggestion": "dark 或 light 或 gradient 或 warm_sun 或 cozy（根據文章內容和情感基調建議）"
}

規則：
- key_points 必須有 3 到 5 個重點
- title 要簡潔有力，能夠概括文章核心
- theme_suggestion：科技/商業類建議 dark，財經/分析類建議 gradient，生活/文化類建議 light，溫馨/日常類建議 cozy，創意/娛樂/正能量類建議 warm_sun

重點精簡規則（嚴格遵守）：
- 每條重點以動詞或關鍵名詞開頭，禁止虛詞開頭（「的」「了」「是」「在」「有」「會」）
- 刪除所有不影響理解的修飾詞（「非常」「相當」「基本上」「目前來看」「其實」「可以說」）
- 用具體數據取代模糊描述（「大幅成長」→「成長 40%」，「很多用戶」→「超過 10 萬用戶」）
- 一條重點只表達一個核心信息，禁止用逗號串聯多件事
- 優先保留：數據、結論、行動項；優先刪除：背景鋪墊、過渡句、重複內容
- 只返回 JSON，不要有任何前言或後語"""

USER_PROMPT_TEMPLATE = "請分析以下文章並提取關鍵重點：\n\n{article_text}"

CLAUDE_MODEL = "claude-sonnet-4-6"
GEMINI_MODEL = "gemini-2.0-flash"
GPT_MODEL = "gpt-4o-mini"

# Locate claude CLI dynamically so the path is correct on any machine.
import shutil as _shutil
_resolved = _shutil.which("claude")
if _resolved is None:
    raise EnvironmentError(
        "claude CLI not found in PATH. "
        "Install Claude Code: https://claude.ai/code"
    )
CLAUDE_CLI: str = _resolved

# 精簡 prompt，專為 CLI -p 參數設計（單行、最小 token）
CLI_PROMPT_TEMPLATE = (
    "從以下文章提取3-5重點，只回JSON不加其他文字，格式："
    '{{"title":"15字內標題","key_points":[{{"text":"30-50字重點"}}],'
    '"source":"來源或空字串","theme_suggestion":"dark/light/gradient/warm_sun/cozy"}}。'
    "科技商業→dark，財經分析→gradient，生活文化→light，溫馨日常→cozy，創意娛樂→warm_sun。"
    "精簡規則：動詞或名詞開頭，刪除虛詞修飾詞，用數據取代模糊描述，一條一個核心信息。\n\n文章：{article_text}"
)


def extract_key_points(
    article_text: str,
    provider: str = "cli",
    config: ExtractionConfig | None = None,
    model_variant: str = "haiku",
) -> dict[str, Any]:
    """
    Extract structured key points from article text.

    Args:
        article_text: The full article text to analyze
        provider: "cli" (default), "claude", "gemini", or "gpt"
        config: Optional extraction configuration. None uses defaults.
        model_variant: Claude model variant for CLI/API — "haiku" (default, 3x cheaper), "sonnet", or "opus".

    Returns:
        A dict with keys: title, key_points, source, theme_suggestion

    Raises:
        ValueError: If provider is unknown or response cannot be parsed
        EnvironmentError: If required API key is missing
    """
    cfg = config or ExtractionConfig()
    if cfg.mode == "smart":
        system_prompt = _build_smart_prompt(cfg)
    elif cfg.mode == "article":
        system_prompt = _build_article_prompt(cfg)
    else:
        system_prompt = _build_system_prompt(cfg)

    if provider == "claude":
        return _extract_with_claude(article_text, system_prompt, cfg)
    elif provider == "gemini":
        return _extract_with_gemini(article_text, system_prompt, cfg)
    elif provider == "gpt":
        return _extract_with_gpt(article_text, system_prompt, cfg)
    elif provider == "cli":
        return _extract_with_claude_cli_sync(article_text, cfg, model_variant=model_variant)
    else:
        raise ValueError(f"Unknown provider '{provider}'. Choose 'claude', 'gemini', 'gpt', or 'cli'.")


def _extract_with_claude(
    article_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    config: ExtractionConfig | None = None,
) -> dict[str, Any]:
    """Extract key points using Anthropic Claude API."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it or create a .env file based on .env.example"
        )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(article_text=article_text),
            }
        ],
    )
    raw = message.content[0].text.strip()
    return _parse_and_validate(raw, provider="claude", config=config)


def _extract_with_gemini(
    article_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    config: ExtractionConfig | None = None,
) -> dict[str, Any]:
    """Extract key points using Google Gemini API."""
    import google.generativeai as genai

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it or create a .env file based on .env.example"
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    response = model.generate_content(
        USER_PROMPT_TEMPLATE.format(article_text=article_text),
        generation_config=genai.GenerationConfig(
            max_output_tokens=1024,
            temperature=0.3,
        ),
    )
    raw = response.text.strip()
    return _parse_and_validate(raw, provider="gemini", config=config)


def _extract_with_gpt(
    article_text: str,
    system_prompt: str = SYSTEM_PROMPT,
    config: ExtractionConfig | None = None,
) -> dict[str, Any]:
    """Extract key points using OpenAI GPT API."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it or create a .env file based on .env.example"
        )

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=GPT_MODEL,
        max_tokens=1024,
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(article_text=article_text)},
        ],
    )
    raw = response.choices[0].message.content.strip()
    return _parse_and_validate(raw, provider="gpt", config=config)


def _extract_with_claude_cli_sync(
    article_text: str,
    config: ExtractionConfig | None = None,
    model_variant: str = "sonnet",
) -> dict[str, Any]:
    """Synchronous version of extract_with_claude_cli.

    Uses subprocess.run() instead of asyncio for compatibility
    with synchronous calling code (e.g., daily_curation.py).
    """
    import subprocess
    import shutil

    cfg = config or ExtractionConfig()
    if cfg.mode == "smart":
        system_prompt = _build_smart_prompt(cfg)
    elif cfg.mode == "article":
        system_prompt = _build_article_prompt(cfg)
    else:
        system_prompt = _build_system_prompt(cfg)

    user_prompt = USER_PROMPT_TEMPLATE.format(article_text=article_text)

    # Find claude CLI
    claude_cli = shutil.which("claude")
    if not claude_cli:
        raise RuntimeError(
            "claude CLI not found. Install Claude Code: https://claude.ai/code"
        )

    # Filter env to avoid interference with claude CLI's auth
    env = {k: v for k, v in os.environ.items() if k not in {"CLAUDECODE", "ANTHROPIC_API_KEY"}}

    result = subprocess.run(
        [claude_cli, "-p", "--system-prompt", system_prompt, "--output-format", "text", "--model", model_variant],
        input=user_prompt,
        capture_output=True,
        text=True,
        timeout=120,
        env=env,
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude CLI failed: {result.stderr.strip()}")

    raw = result.stdout.strip()
    return _parse_and_validate(raw, provider="cli", config=cfg)


async def _extract_with_claude_cli(
    article_text: str,
    config: ExtractionConfig | None = None,
    model_variant: str = "sonnet",
) -> dict[str, Any]:
    """Extract key points by calling the claude CLI binary via subprocess.

    Uses stdin to pass the prompt, supporting arbitrarily long inputs.
    System prompt is passed via --system-prompt flag.
    """
    cfg = config or ExtractionConfig()
    if cfg.mode == "smart":
        system_prompt = _build_smart_prompt(cfg)
    elif cfg.mode == "article":
        system_prompt = _build_article_prompt(cfg)
    else:
        system_prompt = _build_system_prompt(cfg)
    user_prompt = USER_PROMPT_TEMPLATE.format(article_text=article_text)

    # Remove vars that interfere with claude CLI's own auth
    _exclude = {"CLAUDECODE", "ANTHROPIC_API_KEY"}
    env = {k: v for k, v in os.environ.items() if k not in _exclude}

    proc = await asyncio.create_subprocess_exec(
        CLAUDE_CLI, "-p",
        "--system-prompt", system_prompt,
        "--output-format", "text",
        "--model", model_variant,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await proc.communicate(input=user_prompt.encode())

    if proc.returncode != 0:
        err = stderr.decode().strip()
        raise RuntimeError(f"claude CLI exited with code {proc.returncode}: {err}")

    raw = stdout.decode().strip()
    return _parse_and_validate(raw, provider="cli", config=cfg)


def _parse_and_validate(
    raw: str,
    provider: str,
    config: ExtractionConfig | None = None,
) -> dict[str, Any]:
    """Strip markdown fences, parse JSON, and validate structure."""
    # Strip markdown code blocks if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1])

    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"{provider} returned invalid JSON.\nRaw response:\n{raw}\n\nError: {e}"
        ) from e

    _validate_extracted_data(result, config=config)
    return result


def _validate_extracted_data(
    data: dict[str, Any],
    config: ExtractionConfig | None = None,
) -> None:
    """Validate that the extracted data has all required fields.

    Uses config's min/max points for validation range. Defaults to 3-5.
    Supports both card mode (key_points) and article mode (sections).
    """
    cfg = config or ExtractionConfig()

    if cfg.mode == "smart":
        _validate_smart_data(data, cfg)
    elif cfg.mode == "article":
        _validate_article_data(data)
    else:
        _validate_card_data(data, cfg)


def _validate_card_data(data: dict[str, Any], cfg: ExtractionConfig) -> None:
    """Validate card mode extraction output."""
    required_fields = ["title", "key_points", "source", "theme_suggestion"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in response: '{field}'")

    if not isinstance(data["key_points"], list):
        raise ValueError("'key_points' must be a list")

    if not cfg.min_points <= len(data["key_points"]) <= cfg.max_points:
        raise ValueError(
            f"'key_points' must have {cfg.min_points}-{cfg.max_points} items, "
            f"got {len(data['key_points'])}"
        )

    for i, point in enumerate(data["key_points"]):
        if not isinstance(point, dict):
            raise ValueError(f"key_points[{i}] must be a dict")
        if "text" not in point:
            raise ValueError(f"key_points[{i}] must have a 'text' field")

    valid_themes = {"dark", "light", "gradient", "warm_sun", "cozy"}
    if data["theme_suggestion"] not in valid_themes:
        data["theme_suggestion"] = "dark"


def _validate_article_data(data: dict[str, Any]) -> None:
    """Validate article mode extraction output."""
    required_fields = ["title", "sections", "source", "theme_suggestion"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in response: '{field}'")

    if not isinstance(data["sections"], list):
        raise ValueError("'sections' must be a list")

    if not 2 <= len(data["sections"]) <= 5:
        raise ValueError(
            f"'sections' must have 2-4 items, got {len(data['sections'])}"
        )

    for i, section in enumerate(data["sections"]):
        if not isinstance(section, dict):
            raise ValueError(f"sections[{i}] must be a dict")
        if "body" not in section:
            raise ValueError(f"sections[{i}] must have a 'body' field")
        # Normalize body: accept both string and list
        if isinstance(section["body"], str):
            section["body"] = [section["body"]]
        if not isinstance(section["body"], list):
            raise ValueError(f"sections[{i}].body must be a string or list")

    valid_themes = {"dark", "light", "gradient", "warm_sun", "cozy"}
    if data["theme_suggestion"] not in valid_themes:
        data["theme_suggestion"] = "dark"


def _validate_smart_data(data: dict[str, Any], cfg: ExtractionConfig) -> None:
    """Validate smart mode extraction output."""
    required_fields = ["title", "key_points", "source"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in response: '{field}'")

    if not isinstance(data["key_points"], list):
        raise ValueError("'key_points' must be a list")

    if not cfg.min_points <= len(data["key_points"]) <= cfg.max_points:
        raise ValueError(
            f"'key_points' must have {cfg.min_points}-{cfg.max_points} items, "
            f"got {len(data['key_points'])}"
        )

    for i, point in enumerate(data["key_points"]):
        if not isinstance(point, dict):
            raise ValueError(f"key_points[{i}] must be a dict")
        if "text" not in point:
            raise ValueError(f"key_points[{i}] must have a 'text' field")
        # Normalize importance: default to 3 if missing or invalid
        imp = point.get("importance")
        if not isinstance(imp, int) or not 1 <= imp <= 5:
            point["importance"] = 3

    # Normalize content_type
    if data.get("content_type") not in _VALID_CONTENT_TYPES:
        data["content_type"] = "news"

    # Normalize layout_hint — fallback based on content_type, not always hero_list
    if data.get("layout_hint") not in _VALID_LAYOUT_HINTS:
        _content_type_fallbacks = {
            "news": "hero_list",
            "opinion": "hero_list",
            "howto": "numbered_ranking",
            "data": "data_dashboard",
            "comparison": "comparison",
            "quote": "quote_centered",
            "timeline": "timeline",
            "ranking": "numbered_ranking",
        }
        data["layout_hint"] = _content_type_fallbacks.get(
            data.get("content_type", "news"), "grid"
        )

    # Normalize color_mood
    if data.get("color_mood") not in _VALID_COLOR_MOODS:
        data["color_mood"] = "dark_tech"
