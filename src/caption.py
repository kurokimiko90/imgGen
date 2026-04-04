"""
caption.py - Platform-specific caption generation.

Generates ready-to-post text captions for Twitter, LinkedIn, and Instagram
from extracted article data via a separate AI call.
"""

import json
from pathlib import Path
from typing import Any

VALID_PLATFORMS = {"twitter", "linkedin", "instagram"}

PLATFORM_RULES = {
    "twitter": {
        "max_chars": 280,
        "instructions": "Max 280 characters. Punchy and engaging. Include 2-3 relevant hashtags.",
    },
    "linkedin": {
        "max_chars": 3000,
        "instructions": "1-2 short paragraphs. Professional, thought-leadership tone. "
                        "End with a question to invite discussion.",
    },
    "instagram": {
        "max_chars": 2200,
        "instructions": "Storytelling tone with line breaks between sentences. "
                        "Add a block of 8-12 relevant hashtags at the end.",
    },
}


def _build_caption_prompt(data: dict[str, Any], platforms: list[str]) -> str:
    """Build a prompt asking the AI to generate platform-specific captions."""
    platform_specs = []
    for p in platforms:
        rules = PLATFORM_RULES[p]
        platform_specs.append(
            f'- "{p}": {rules["instructions"]} (max {rules["max_chars"]} chars)'
        )

    points_text = "\n".join(
        f"  - {pt['text']}" for pt in data.get("key_points", [])
    )

    return (
        f"Based on this article summary, generate social media captions.\n\n"
        f"Title: {data.get('title', '')}\n"
        f"Key Points:\n{points_text}\n"
        f"Source: {data.get('source', '')}\n\n"
        f"Generate captions for these platforms:\n"
        + "\n".join(platform_specs) + "\n\n"
        f"Return ONLY a JSON object with platform names as keys and caption strings as values.\n"
        f"Example: {json.dumps({p: '...' for p in platforms})}\n"
        f"No markdown, no code fences, just the JSON."
    )


def generate_captions(
    data: dict[str, Any],
    platforms: list[str],
    provider: str = "cli",
) -> dict[str, str]:
    """Generate captions for given platforms from extracted article data.

    Makes a separate AI call (not bundled into extraction) so each prompt
    is specialized for its task.

    Args:
        data: Extracted article data (title, key_points, source).
        platforms: List of platform names (twitter, linkedin, instagram).
        provider: AI provider to use for generation.

    Returns:
        Dict mapping platform name to caption text.

    Raises:
        ValueError: If any platform name is invalid or AI output is malformed.
        EnvironmentError: If the required API key is missing.
    """
    invalid = [p for p in platforms if p not in VALID_PLATFORMS]
    if invalid:
        raise ValueError(
            f"Invalid platform(s): {', '.join(invalid)}. "
            f"Valid: {', '.join(sorted(VALID_PLATFORMS))}"
        )

    prompt = _build_caption_prompt(data, platforms)

    # Use the same provider infrastructure as extractor
    raw_response = _call_provider(prompt, provider)

    # Parse JSON response
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(
            lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
        )

    try:
        captions = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Caption AI returned invalid JSON: {e}") from e

    if not isinstance(captions, dict):
        raise ValueError("Caption AI did not return a JSON object.")

    # Ensure all requested platforms are present
    result: dict[str, str] = {}
    for p in platforms:
        text = captions.get(p, "")
        if not isinstance(text, str):
            text = str(text)
        # Trim to max chars
        max_chars = PLATFORM_RULES[p]["max_chars"]
        result[p] = text[:max_chars]

    return result


def _call_provider(prompt: str, provider: str) -> str:
    """Call the AI provider with a simple text prompt, return raw response."""
    import os
    import shutil
    import subprocess

    if provider == "claude":
        import anthropic
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key or api_key == "your_anthropic_key_here":
            raise ValueError(
                "ANTHROPIC_API_KEY not configured. Use provider='cli' instead."
            )
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    if provider == "gemini":
        import google.generativeai as genai
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key or api_key == "your_google_key_here":
            raise ValueError(
                "GOOGLE_API_KEY not configured. Use provider='cli' instead."
            )
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text

    if provider == "gpt":
        from openai import OpenAI
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or api_key == "your_openai_key_here":
            raise ValueError(
                "OPENAI_API_KEY not configured. Use provider='cli' instead."
            )
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return response.choices[0].message.content or ""

    if provider == "cli":
        claude_cli = shutil.which("claude")
        if not claude_cli:
            raise RuntimeError(
                "claude CLI not found. Install via: https://claude.ai/code"
            )

        # Filter env to avoid interfering with claude CLI's auth
        env = {
            k: v for k, v in os.environ.items()
            if k not in {"CLAUDECODE", "ANTHROPIC_API_KEY"}
        }

        result = subprocess.run(
            [claude_cli, "-p", "--output-format", "text", "--model", "sonnet"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI failed: {result.stderr.strip()}")
        return result.stdout

    raise ValueError(f"Unknown provider: {provider}")


def save_captions(
    captions: dict[str, str],
    base_path: Path,
) -> Path:
    """Save captions to a .txt file alongside the image.

    Args:
        captions: Dict of platform -> caption text.
        base_path: Path to the generated image file (e.g. card_dark_xxx.png).

    Returns:
        Path to the saved caption file.
    """
    caption_path = base_path.with_suffix(".captions.txt")
    lines = []
    for platform, text in captions.items():
        lines.append(f"=== {platform.upper()} ===")
        lines.append(text)
        lines.append("")
    caption_path.write_text("\n".join(lines), encoding="utf-8")
    return caption_path
