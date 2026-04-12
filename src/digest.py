"""
digest.py - Weekly digest synthesis from generation history.

Takes multiple article summaries from the history database and uses AI
to synthesize them into a single curated digest card.
"""

import json
from typing import Any


DIGEST_PROMPT_TEMPLATE = """\
You are a content curator. Given these {count} article summaries generated \
over the past {days} days, synthesize a concise weekly digest.

Articles:
{articles_block}

Return ONLY a JSON object with these keys:
- "title": A compelling digest title (e.g. "AI & Tech Weekly Roundup")
- "digest_points": An array of objects, each with:
  - "article_title": Original article title (shortened if needed)
  - "insight": One sentence capturing the key takeaway (max 80 chars)
- "period": Human-readable date range (e.g. "Mar 21 – 28, 2026")
- "article_count": Number of articles summarized

Keep digest_points to at most 8 items. Prioritize variety and importance.
No markdown, no code fences, just the JSON.
"""


def build_digest_input(generations: list[dict[str, Any]]) -> str:
    """Format generation history rows into a text block for the AI prompt."""
    lines = []
    for i, gen in enumerate(generations, 1):
        title = gen.get("title", "Untitled")
        source = gen.get("source", "")
        points = gen.get("key_points_count", 0)
        created = gen.get("created_at", "")[:10]
        lines.append(
            f"{i}. [{created}] {title}"
            + (f" (source: {source})" if source else "")
            + f" — {points} key points"
        )
    return "\n".join(lines)


def generate_digest(
    generations: list[dict[str, Any]],
    days: int = 7,
    provider: str = "gemini",
) -> dict[str, Any]:
    """Synthesize a digest from generation history via AI.

    Args:
        generations: List of history rows (from list_generations).
        days: Number of days the digest covers.
        provider: AI provider to use.

    Returns:
        Dict with keys: title, digest_points, period, article_count.

    Raises:
        ValueError: If AI output is malformed or no generations provided.
    """
    if not generations:
        raise ValueError("No generation history to digest.")

    articles_block = build_digest_input(generations)

    prompt = DIGEST_PROMPT_TEMPLATE.format(
        count=len(generations),
        days=days,
        articles_block=articles_block,
    )

    from src.caption import _call_provider

    raw = _call_provider(prompt, provider)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(
            lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        )

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Digest AI returned invalid JSON: {e}") from e

    if not isinstance(result, dict):
        raise ValueError("Digest AI did not return a JSON object.")

    # Validate expected keys
    title = result.get("title", "Weekly Digest")
    digest_points = result.get("digest_points", [])
    if not isinstance(digest_points, list):
        digest_points = []

    # Normalize each point
    normalized_points = []
    for pt in digest_points[:8]:
        if isinstance(pt, dict):
            normalized_points.append({
                "article_title": str(pt.get("article_title", "")),
                "insight": str(pt.get("insight", "")),
            })

    return {
        "title": str(title),
        "digest_points": normalized_points,
        "period": str(result.get("period", "")),
        "article_count": len(generations),
    }
