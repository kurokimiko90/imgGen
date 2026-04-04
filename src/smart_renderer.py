"""
smart_renderer.py - AI-driven dynamic layout generation.

Instead of static Jinja2 templates, the AI generates complete HTML+CSS
tailored to each specific piece of content — like designing a PPT slide
where every output is uniquely optimized.
"""

import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("imggen.smart_renderer")

# ---------------------------------------------------------------------------
# Format specs (mirrors screenshotter.FORMAT_DIMENSIONS)
# ---------------------------------------------------------------------------

FORMAT_SPECS: dict[str, dict[str, int]] = {
    "story":     {"width": 430, "height": 764},
    "square":    {"width": 430, "height": 430},
    "landscape": {"width": 430, "height": 242},
    "twitter":   {"width": 430, "height": 215},
}

# ---------------------------------------------------------------------------
# Color palettes (extracted from existing templates)
# ---------------------------------------------------------------------------

COLOR_PALETTES: dict[str, str] = {
    "dark_tech": """\
      --bg: #090d1a; --bg-card: rgba(37,99,235,0.07);
      --accent: #2563eb; --accent-dim: rgba(37,99,235,0.18);
      --text-primary: #dde2f0; --text-secondary: #8a90aa;
      --text-muted: #4a5070; --border: rgba(255,255,255,0.08);""",

    "warm_earth": """\
      --bg: #EAE5DE; --bg-card: #F4F1EC;
      --accent: #6B5A4E; --accent-dim: rgba(107,90,78,0.15);
      --text-primary: #2C2420; --text-secondary: #6B5A4E;
      --text-muted: #A89880; --border: #D4CCC2;""",

    "clean_light": """\
      --bg: #f8f7f4; --bg-card: #ffffff;
      --accent: #0284c7; --accent-dim: rgba(2,132,199,0.12);
      --text-primary: #1c1917; --text-secondary: #44403c;
      --text-muted: #78716c; --border: #e7e5e4;""",

    "bold_contrast": """\
      --bg: #F6F4F0; --bg-card: #FFFFFF;
      --accent: #C4540A; --accent-dim: rgba(196,84,10,0.12);
      --text-primary: #1E1C18; --text-secondary: #7A7060;
      --text-muted: #A89880; --border: #DED8D0;""",

    "soft_pastel": """\
      --bg: #FDF0F4; --bg-card: #FDF8FA;
      --accent: #C25A7A; --accent-dim: rgba(194,90,122,0.12);
      --text-primary: #2E1F28; --text-secondary: #8A6E78;
      --text-muted: #B8A0AA; --border: #E8C4D0;""",
}

# ---------------------------------------------------------------------------
# Design system CSS (shared foundation for all AI-generated layouts)
# ---------------------------------------------------------------------------

_DESIGN_SYSTEM_TEMPLATE = (
    "/* === DESIGN SYSTEM (shared across all smart layouts) === */\n"
    "@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900"
    "&family=Noto+Sans+TC:wght@400;500;700;900&display=swap');\n\n"
    "*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }\n\n"
    ":root {\n"
    "  --fs-title: clamp(22px, 6vw, 32px);\n"
    "  --fs-subtitle: clamp(16px, 4vw, 20px);\n"
    "  --fs-body: 16px;\n"
    "  --fs-secondary: 14px;\n"
    "  --fs-label: 11px;\n"
    "  /* palette tokens */\n"
    "  __PALETTE__\n"
    "}\n\n"
    "html, body {\n"
    "  width: __WIDTH__px;\n"
    "  height: __HEIGHT__px;\n"
    "  overflow: hidden;\n"
    "  background: var(--bg);\n"
    "  font-family: 'Outfit', 'Noto Sans TC', -apple-system, sans-serif;\n"
    "  -webkit-font-smoothing: antialiased;\n"
    "  color: var(--text-primary);\n"
    "}\n\n"
    "@keyframes fadeUp {\n"
    "  from { opacity: 0; transform: translateY(8px); }\n"
    "  to   { opacity: 1; transform: translateY(0); }\n"
    "}\n\n"
    ".animated {\n"
    "  animation: fadeUp 0.32s cubic-bezier(0.16,1,0.3,1) calc(var(--i, 0) * 0.08s) both;\n"
    "}\n"
)


def _build_design_system_css(palette: str, width: int, height: int) -> str:
    """Build design system CSS with palette and dimensions injected."""
    return (
        _DESIGN_SYSTEM_TEMPLATE
        .replace("__PALETTE__", palette)
        .replace("__WIDTH__", str(width))
        .replace("__HEIGHT__", str(height))
    )

# ---------------------------------------------------------------------------
# Layout pattern descriptions (guidance for the AI, not full templates)
# ---------------------------------------------------------------------------

LAYOUT_PATTERNS: dict[str, str] = {
    "hero_list": (
        "Large hero section for the most important point at top (bigger font, accent background), "
        "followed by smaller supporting points in a vertical list with numbered indicators."
    ),
    "grid": (
        "Equal-weight grid of cards (2-column for 4 items, or stacked rows). "
        "Each card has an icon/number, title text, and subtle border. Good for parallel items."
    ),
    "timeline": (
        "Vertical timeline with a thin line on the left, dots/circles at each node. "
        "Each point appears as a step with number and text. Good for sequential/process content."
    ),
    "comparison": (
        "Side-by-side or stacked comparison layout. Two sections with contrasting accent colors. "
        "Headers like 'Before/After' or 'A vs B'. Good for contrasting viewpoints."
    ),
    "quote_centered": (
        "Large centered quote with decorative quotation marks. Supporting context below in smaller text. "
        "Minimal layout with generous whitespace. Good for impactful single statements."
    ),
    "data_dashboard": (
        "Data-forward layout with large stat numbers, small labels, and bar/progress indicators. "
        "Grid of metric cards with accent-colored values. Good for data-heavy content."
    ),
    "numbered_ranking": (
        "Numbered list with large rank numbers (01, 02, 03...) on the left. "
        "All items use identical card styling — do NOT make the first item a hero or give it a different background. "
        "Use accent-colored number badges to indicate rank. Good for top-N lists, tips, tools."
    ),
}

# ---------------------------------------------------------------------------
# Watermark + thread badge HTML (injected post-generation)
# ---------------------------------------------------------------------------

_WATERMARK_CSS = """\
.watermark-overlay {
  position: fixed; z-index: 100;
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  pointer-events: none;
}
.watermark-top-left     { top: 16px; left: 16px; }
.watermark-top-right    { top: 16px; right: 16px; }
.watermark-bottom-left  { bottom: 16px; left: 16px; }
.watermark-bottom-right { bottom: 16px; right: 16px; }
.watermark-img { max-height: 80px; max-width: 200px; object-fit: contain; }
.watermark-text {
  font-size: 16px; font-weight: 600;
  color: var(--text-secondary); text-shadow: 0 1px 3px rgba(0,0,0,0.6);
}
.thread-badge {
  position: fixed; top: 12px; right: 12px; z-index: 200;
  font-size: 13px; font-weight: 700; letter-spacing: 0.06em;
  color: var(--accent); background: var(--bg-card, rgba(255,255,255,0.08));
  border: 1px solid var(--border); border-radius: 20px; padding: 4px 12px;
}
"""


def _build_watermark_html(
    watermark_data: str | None,
    watermark_position: str,
    watermark_opacity: float,
    brand_name: str | None,
    thread_index: int | None,
    thread_total: int | None,
) -> str:
    """Build watermark and thread badge HTML to inject."""
    parts: list[str] = []
    if thread_index:
        parts.append(
            f'<div class="thread-badge">{thread_index} / {thread_total}</div>'
        )
    if watermark_data or brand_name:
        inner = ""
        if watermark_data:
            inner += (
                f'<img class="watermark-img" src="{watermark_data}" '
                f'alt="" style="opacity: {watermark_opacity};" />'
            )
        if brand_name:
            inner += (
                f'<span class="watermark-text" '
                f'style="opacity: {watermark_opacity};">{brand_name}</span>'
            )
        parts.append(
            f'<div class="watermark-overlay watermark-{watermark_position}">'
            f'{inner}</div>'
        )
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

_PROMPT_DIR = Path(__file__).parent.parent / "prompts"


def _load_system_prompt() -> str:
    """Load the smart layout system prompt from file, or use inline fallback."""
    prompt_file = _PROMPT_DIR / "smart_layout_system.txt"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")
    return _INLINE_SYSTEM_PROMPT


_INLINE_SYSTEM_PROMPT = """\
You are a world-class web designer creating single-page visual cards.

You will receive:
1. A design system (CSS variables, fonts, animations) — you MUST use it
2. Content to display (title, key points with importance scores)
3. A suggested layout pattern and color mood
4. The exact canvas dimensions

Your job: generate a complete, self-contained HTML page that presents the content \
in the most visually compelling way possible, like a beautifully designed PPT slide.

HARD RULES:
- Return ONLY raw HTML (<!DOCTYPE html>...). No markdown fences, no explanation.
- All CSS must be in a single <style> tag. No external stylesheets (except the Google Fonts @import in the design system).
- No JavaScript. No external images.
- The page must render perfectly at the given canvas dimensions. Use overflow: hidden on html/body.
- Use the provided CSS variables for ALL colors. Do not invent new colors.
- Apply the .animated class with --i CSS variable for staggered fadeUp on content elements.
- Include a subtle footer at the bottom with source attribution and "NOZOMI" branding.
- All text must be EXACTLY as provided — do not rephrase, abbreviate, or omit any content.
- Use the suggested layout pattern as inspiration, but adapt creatively to fit the content.
- Ensure adequate visual hierarchy: the most important points should be visually prominent.
- Chinese text should use 'Noto Sans TC', Latin text should use 'Outfit'.
"""


def _build_layout_prompt(
    data: dict[str, Any],
    card_format: str,
    color_mood: str | None = None,
) -> str:
    """Build the full prompt for AI layout generation.

    Handles both standard points ({text, importance}) and social-mode points
    ({hook, text, importance}) — the system prompt already instructs the AI how
    to visually differentiate hook vs. detail text.
    """
    specs = FORMAT_SPECS.get(card_format, FORMAT_SPECS["story"])
    mood = color_mood or data.get("color_mood", "dark_tech")
    palette = COLOR_PALETTES.get(mood, COLOR_PALETTES["dark_tech"])

    design_css = _build_design_system_css(palette, specs["width"], specs["height"])

    layout_hint = data.get("layout_hint", "grid")
    pattern_desc = LAYOUT_PATTERNS.get(layout_hint, LAYOUT_PATTERNS["grid"])

    # Build point descriptions — include "hook" field when present
    point_lines: list[str] = []
    for p in data.get("key_points", []):
        imp = p.get("importance", 3)
        hook = p.get("hook", "")
        text = p.get("text", "")
        if hook:
            point_lines.append(f"  [{imp}/5] HOOK: {hook} | DETAIL: {text}")
        else:
            point_lines.append(f"  [{imp}/5] {text}")
    points_text = "\n".join(point_lines)

    # Detect social mode (points have hook fields)
    has_hooks = any(p.get("hook") for p in data.get("key_points", []))
    social_note = (
        "\nSOCIAL MODE: Points contain HOOK + DETAIL pairs. "
        "Display HOOK in large accent text (26-32px bold), DETAIL in small secondary text (13-14px). "
        "All point cards must look identical — no random dark backgrounds."
        if has_hooks else ""
    )

    system = _load_system_prompt()

    return f"""{system}

=== DESIGN SYSTEM CSS (include this in your <style> tag) ===
{design_css}

=== CANVAS ===
Width: {specs['width']}px, Height: {specs['height']}px
Everything must fit within this exact area. No scrolling.

=== CONTENT ===
Title: {data.get('title', '')}
Source: {data.get('source', '')}
Content Type: {data.get('content_type', 'news')}{social_note}

Key Points (importance/5 | HOOK = big visual keyword | DETAIL = supporting text):
{points_text}

=== SUGGESTED LAYOUT ===
Pattern: {layout_hint}
Description: {pattern_desc}

=== COLOR MOOD ===
{mood} — use the CSS variables from the design system above.

Now generate the complete HTML page."""


# ---------------------------------------------------------------------------
# AI provider call (adapted from caption.py pattern)
# ---------------------------------------------------------------------------

# Model selection: Sonnet for balance, Opus for premium design quality
_CLAUDE_MODELS = {
    "sonnet": "claude-sonnet-4-6",      # Best balance for layout generation
    "opus": "claude-opus-4-6",           # Premium design with deeper reasoning
}
_DEFAULT_CLAUDE_MODEL = "sonnet"

_GEMINI_MODEL = "gemini-2.0-flash"
_GPT_MODEL = "gpt-4o-mini"

# Locate claude CLI dynamically so the path is correct on any machine.
import shutil as _shutil
_resolved_cli = _shutil.which("claude")
if _resolved_cli is None:
    _CLAUDE_CLI: str = ""  # Will raise RuntimeError at call time
else:
    _CLAUDE_CLI: str = _resolved_cli


def _call_provider(prompt: str, provider: str, model_variant: str = "sonnet") -> str:
    """Call the AI provider with a prompt, return raw response.

    Args:
        prompt: The full prompt for the AI.
        provider: One of "claude", "gemini", "gpt", "cli".
        model_variant: For Claude provider, "sonnet" or "opus" (default: "sonnet").

    Returns:
        The text response from the AI.
    """
    if provider == "claude":
        import anthropic
        model = _CLAUDE_MODELS.get(model_variant, _CLAUDE_MODELS[_DEFAULT_CLAUDE_MODEL])
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    if provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        model = genai.GenerativeModel(_GEMINI_MODEL)
        response = model.generate_content(prompt)
        return response.text

    if provider == "gpt":
        from openai import OpenAI
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=_GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
        )
        return response.choices[0].message.content or ""

    if provider == "cli":
        if not _CLAUDE_CLI:
            raise RuntimeError(
                "claude CLI not found in PATH. "
                "Install Claude Code: https://claude.ai/code"
            )
        env = {
            k: v for k, v in os.environ.items()
            if k not in {"CLAUDECODE", "ANTHROPIC_API_KEY"}
        }
        result = subprocess.run(
            [_CLAUDE_CLI, "-p",
             "--output-format", "text",
             "--model", model_variant],
            input=prompt,
            capture_output=True, text=True, timeout=180, env=env,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Claude CLI failed: {result.stderr.strip()}")
        return result.stdout

    raise ValueError(f"Unknown provider: {provider}")


# ---------------------------------------------------------------------------
# HTML validation / post-processing
# ---------------------------------------------------------------------------

_MAX_HTML_SIZE = 50_000  # 50 KB


def _validate_generated_html(html: str) -> str:
    """Validate and clean AI-generated HTML.

    Strips markdown fences, checks structural requirements,
    rejects script tags and external image references.

    Returns:
        Cleaned HTML string.

    Raises:
        ValueError: If HTML fails validation.
    """
    # Strip markdown code fences
    cleaned = html.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```html) and last line (```)
        end = len(lines) - 1 if lines[-1].strip().startswith("```") else len(lines)
        cleaned = "\n".join(lines[1:end]).strip()

    if len(cleaned) > _MAX_HTML_SIZE:
        raise ValueError(f"Generated HTML is too large ({len(cleaned)} bytes)")

    if not re.search(r"<!DOCTYPE\s+html|<html", cleaned, re.IGNORECASE):
        raise ValueError("Generated HTML is missing <!DOCTYPE html> or <html> tag")

    if re.search(r"<script\b", cleaned, re.IGNORECASE):
        raise ValueError("Generated HTML contains <script> tags (not allowed)")

    # Reject external image references (Google Fonts are OK)
    if re.search(r'src\s*=\s*["\']https?://', cleaned, re.IGNORECASE):
        raise ValueError("Generated HTML contains external image references")

    return cleaned


def _inject_overlays(
    html: str,
    watermark_html: str,
) -> str:
    """Inject watermark/thread badge markup and CSS into HTML."""
    if not watermark_html:
        return html

    # Inject watermark CSS into <style> tag
    style_inject = f"\n{_WATERMARK_CSS}\n"
    if "</style>" in html:
        html = html.replace("</style>", f"{style_inject}</style>", 1)

    # Inject watermark HTML before </body>
    if "</body>" in html:
        html = html.replace("</body>", f"\n{watermark_html}\n</body>", 1)

    return html


# ---------------------------------------------------------------------------
# Fallback: map color_mood to closest existing template theme
# ---------------------------------------------------------------------------

_MOOD_TO_THEME: dict[str, str] = {
    "dark_tech": "dark",
    "warm_earth": "editorial",
    "clean_light": "light",
    "bold_contrast": "ranking",
    "soft_pastel": "pastel",
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_smart_html(
    data: dict[str, Any],
    card_format: str = "story",
    provider: str = "cli",
    model_variant: str = "sonnet",
    color_mood: str | None = None,
    watermark_data: str | None = None,
    watermark_position: str = "bottom-right",
    watermark_opacity: float = 0.8,
    brand_name: str | None = None,
    thread_index: int | None = None,
    thread_total: int | None = None,
) -> str:
    """Generate a complete HTML page with AI-driven layout.

    Args:
        data: Extracted article data (from smart mode extraction).
        card_format: Output format (story/square/landscape/twitter).
        provider: AI provider for layout generation (claude/gemini/gpt/cli).
        model_variant: For Claude provider, "sonnet" or "opus" (default: "sonnet").
        color_mood: Override color mood (default: from data).
        watermark_data: Base64 data URI for watermark image.
        watermark_position: Corner for watermark overlay.
        watermark_opacity: Watermark transparency (0.0-1.0).
        brand_name: Optional text watermark.
        thread_index: Thread card index (1-based).
        thread_total: Total cards in thread.

    Returns:
        Complete HTML string ready for Playwright screenshot.

    Raises:
        ValueError: If AI output fails validation after retry.
        RuntimeError: If provider call fails.
    """
    prompt = _build_layout_prompt(data, card_format, color_mood)

    watermark_html = _build_watermark_html(
        watermark_data, watermark_position, watermark_opacity,
        brand_name, thread_index, thread_total,
    )

    # Attempt 1
    try:
        raw_html = _call_provider(prompt, provider, model_variant)
        html = _validate_generated_html(raw_html)
        return _inject_overlays(html, watermark_html)
    except ValueError as e:
        logger.warning("Smart layout attempt 1 failed validation: %s. Retrying...", e)

    # Attempt 2: retry with stricter instruction
    retry_prompt = (
        prompt + "\n\nIMPORTANT: Your previous response was invalid. "
        "Return ONLY raw HTML starting with <!DOCTYPE html>. "
        "No markdown, no explanation, no code fences."
    )
    try:
        raw_html = _call_provider(retry_prompt, provider, model_variant)
        html = _validate_generated_html(raw_html)
        return _inject_overlays(html, watermark_html)
    except (ValueError, RuntimeError) as e:
        logger.warning("Smart layout attempt 2 failed: %s. Falling back to template.", e)

    # Fallback: use existing Jinja2 template
    return _fallback_to_template(
        data, card_format, color_mood,
        watermark_data, watermark_position, watermark_opacity,
        brand_name, thread_index, thread_total,
    )


def _fallback_to_template(
    data: dict[str, Any],
    card_format: str,
    color_mood: str | None,
    watermark_data: str | None,
    watermark_position: str,
    watermark_opacity: float,
    brand_name: str | None,
    thread_index: int | None,
    thread_total: int | None,
) -> str:
    """Fall back to Jinja2 template rendering when AI layout fails."""
    from src.renderer import render_card

    mood = color_mood or data.get("color_mood", "dark_tech")
    theme = _MOOD_TO_THEME.get(mood, "dark")

    # Smart mode data has extra fields; render_card only needs the basics
    card_data = {
        "title": data.get("title", ""),
        "key_points": [
            {"text": p["text"]}
            for p in data.get("key_points", [])
        ],
        "source": data.get("source", ""),
        "theme_suggestion": theme,
    }

    logger.info("Falling back to template theme '%s'", theme)
    return render_card(
        card_data,
        theme=theme,
        format=card_format,
        watermark_data=watermark_data,
        watermark_position=watermark_position,
        watermark_opacity=watermark_opacity,
        brand_name=brand_name,
        thread_index=thread_index,
        thread_total=thread_total,
    )
