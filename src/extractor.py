"""
extractor.py - Claude API summarization module

Extracts structured key points from article text using Claude claude-sonnet-4-6.
"""

import json
import os
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """你是一位專業的文章摘要分析師，專門將長篇文章提煉成簡潔有力的重點摘要。

你的任務是從提供的文章中提取關鍵信息，並以結構化的 JSON 格式返回。

請嚴格按照以下 JSON 格式返回，不要包含任何其他文字：

{
  "title": "文章的核心標題（15字以內，有力且吸引人）",
  "key_points": [
    {
      "emoji": "相關的 emoji 符號",
      "text": "重點內容（30-50字，清晰且具體）"
    }
  ],
  "source": "來源信息（如果文章中有提及，否則留空字串）",
  "theme_suggestion": "dark 或 light 或 gradient（根據文章內容和情感基調建議）"
}

規則：
- key_points 必須有 3 到 5 個重點
- 每個重點的 emoji 必須與內容高度相關
- title 要簡潔有力，能夠概括文章核心
- theme_suggestion：科技/商業類建議 dark，生活/文化類建議 light，創意/娛樂類建議 gradient
- 只返回 JSON，不要有任何前言或後語"""

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024


def extract_key_points(article_text: str) -> dict[str, Any]:
    """
    Extract structured key points from article text using Claude API.

    Args:
        article_text: The full article text to analyze

    Returns:
        A dict with keys: title, key_points, source, theme_suggestion

    Raises:
        ValueError: If the API response cannot be parsed as valid JSON
        anthropic.APIError: If the API call fails
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Please set it or create a .env file based on .env.example"
        )

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"請分析以下文章並提取關鍵重點：\n\n{article_text}",
            }
        ],
    )

    raw_response = message.content[0].text.strip()

    # Strip markdown code blocks if present
    if raw_response.startswith("```"):
        lines = raw_response.split("\n")
        raw_response = "\n".join(lines[1:-1])

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Claude returned invalid JSON. Raw response:\n{raw_response}\n\nError: {e}"
        ) from e

    _validate_extracted_data(result)

    return result


def _validate_extracted_data(data: dict[str, Any]) -> None:
    """Validate that the extracted data has all required fields."""
    required_fields = ["title", "key_points", "source", "theme_suggestion"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field in Claude response: '{field}'")

    if not isinstance(data["key_points"], list):
        raise ValueError("'key_points' must be a list")

    if not 3 <= len(data["key_points"]) <= 5:
        raise ValueError(
            f"'key_points' must have 3-5 items, got {len(data['key_points'])}"
        )

    for i, point in enumerate(data["key_points"]):
        if not isinstance(point, dict):
            raise ValueError(f"key_points[{i}] must be a dict")
        if "emoji" not in point or "text" not in point:
            raise ValueError(f"key_points[{i}] must have 'emoji' and 'text' fields")

    valid_themes = {"dark", "light", "gradient"}
    if data["theme_suggestion"] not in valid_themes:
        data["theme_suggestion"] = "dark"
