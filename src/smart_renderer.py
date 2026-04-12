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

# ---------------------------------------------------------------------------
# Color palettes — fallback hand-crafted + auto-loaded from templates/*.html
# ---------------------------------------------------------------------------

_FALLBACK_PALETTES: dict[str, str] = {
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

    "gradient": """\
      --bg: #0a1628; --bg-card: rgba(255,255,255,0.08);
      --accent: #06b6d4; --accent-dim: rgba(6,182,212,0.20);
      --text-primary: #ffffff; --text-secondary: rgba(255,255,255,0.88);
      --text-muted: rgba(255,255,255,0.50); --border: rgba(255,255,255,0.16);""",

    "soft_pastel": """\
      --bg: #FDF0F4; --bg-card: #FDF8FA;
      --accent: #C25A7A; --accent-dim: rgba(194,90,122,0.12);
      --text-primary: #2E1F28; --text-secondary: #8A6E78;
      --text-muted: #B8A0AA; --border: #E8C4D0;""",
}


# Templates that are structural (not themable) — skip them during palette loading
_NON_PALETTE_TEMPLATES = frozenset({
    "article", "thread_card", "digest", "dark_card", "stats",
})

# Variable name candidates for heuristic mapping (ordered by preference)
_VAR_CANDIDATES: dict[str, tuple[str, ...]] = {
    "bg": ("bg", "bg-main", "cream", "card-bg"),
    "bg_card": ("bg-card", "card", "glass-bg-strong", "glass-bg", "bg"),
    "accent": (
        "accent", "orange", "amber", "ruby", "rose", "brown-main",
        "cyan", "gold", "red", "blue", "green", "purple",
    ),
    "accent_dim": ("accent-dim", "accent-bg", "accent-glow", "accent-light"),
    "text_primary": (
        "text-primary", "text-main", "text-deep", "text", "text-ink",
        "brown-deep", "text-white",
    ),
    "text_secondary": (
        "text-secondary", "text-mid", "text-soft", "text-main",
        "brown-mid", "brown-main",
    ),
    "text_muted": (
        "text-muted", "text-dim", "text-faint", "text-light",
        "brown-faint", "brown-soft",
    ),
    "border": ("border", "border-dim", "line", "glass-border"),
}

# Neutral defaults for missing fields
_PALETTE_DEFAULTS: dict[str, str] = {
    "bg_card": "rgba(0,0,0,0.03)",
    "accent_dim": "rgba(0,0,0,0.10)",
    "text_secondary": "#666666",
    "text_muted": "#999999",
    "border": "rgba(0,0,0,0.08)",
}


def _parse_root_vars(html: str) -> dict[str, str]:
    """Extract all CSS variables from the first :root { ... } block."""
    import re
    root_match = re.search(r":root\s*\{([^}]+)\}", html, re.DOTALL)
    if not root_match:
        return {}
    block = root_match.group(1)
    vars_found: dict[str, str] = {}
    for m in re.finditer(r"--([a-z0-9-]+)\s*:\s*([^;]+);", block, re.IGNORECASE):
        name = m.group(1).strip().lower()
        value = m.group(2).strip()
        # Skip font-size tokens
        if name.startswith("fs-") or name.startswith("shadow") or name.startswith("fs"):
            continue
        vars_found[name] = value
    return vars_found


def _find_var(vars_found: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    """Return the first matching variable value from the candidate list."""
    for cand in candidates:
        if cand in vars_found:
            val = vars_found[cand]
            # Skip non-color values (clamp, var(...), etc.)
            if val.startswith("clamp(") or val.startswith("calc("):
                continue
            return val
    return None


def _build_palette_from_vars(vars_found: dict[str, str]) -> str | None:
    """Build a standardized palette CSS block from parsed template variables.

    Returns None if critical fields (bg, accent, text-primary) cannot be resolved.
    """
    resolved: dict[str, str] = {}
    for key, candidates in _VAR_CANDIDATES.items():
        val = _find_var(vars_found, candidates)
        if val:
            resolved[key] = val

    # Require at minimum: bg + text_primary. Accent is nice-to-have.
    if "bg" not in resolved or "text_primary" not in resolved:
        return None
    if "accent" not in resolved:
        resolved["accent"] = resolved["text_primary"]

    # Fill in missing fields with neutral defaults
    for key, default in _PALETTE_DEFAULTS.items():
        resolved.setdefault(key, default)

    return (
        f"      --bg: {resolved['bg']}; --bg-card: {resolved['bg_card']};\n"
        f"      --accent: {resolved['accent']}; --accent-dim: {resolved['accent_dim']};\n"
        f"      --text-primary: {resolved['text_primary']}; --text-secondary: {resolved['text_secondary']};\n"
        f"      --text-muted: {resolved['text_muted']}; --border: {resolved['border']};"
    )


def _load_palettes_from_templates() -> dict[str, str]:
    """Scan templates/*.html and auto-extract palettes from their :root blocks.

    Returns:
        Mapping of template_name → CSS palette block compatible with COLOR_PALETTES.
    """
    templates_dir = Path(__file__).parent.parent / "templates"
    if not templates_dir.is_dir():
        return {}

    result: dict[str, str] = {}
    for tpl in sorted(templates_dir.glob("*.html")):
        name = tpl.stem
        if name in _NON_PALETTE_TEMPLATES:
            continue
        try:
            html = tpl.read_text(encoding="utf-8")
        except OSError:
            continue
        vars_found = _parse_root_vars(html)
        if not vars_found:
            continue
        palette = _build_palette_from_vars(vars_found)
        if palette:
            result[name] = palette
    return result


# Public COLOR_PALETTES = fallbacks + auto-loaded from templates.
# Fallback names take precedence for backwards compatibility.
COLOR_PALETTES: dict[str, str] = {
    **_load_palettes_from_templates(),
    **_FALLBACK_PALETTES,
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
        "Top section: a prominent title/heading in large bold text (32-40px), optionally with a "
        "key stat or accent-colored label beneath it. "
        "Below: 2-4 cards in a vertical list. Each card MUST have two text layers: "
        "(1) a bold title (主標, 17-20px) and (2) a smaller subtitle/detail (副標, 13-15px, muted color). "
        "First card should be visually heavier than the rest (larger font or accent-left-border) — NOT all equal height. "
        "Do NOT use numbered indicators or icons — rely on the two-layer text hierarchy."
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


def _build_layout_content_block(
    data: dict[str, Any],
    card_format: str,
    color_mood: str | None = None,
) -> str:
    """Build only the content-specific block for a layout (no system prompt, no CSS).

    Used by batch prompt builders to share CSS once and repeat only content.
    """
    specs = FORMAT_SPECS.get(card_format, FORMAT_SPECS["story"])
    mood = color_mood or data.get("color_mood", "dark_tech")
    layout_hint = data.get("layout_hint", "grid")
    pattern_desc = LAYOUT_PATTERNS.get(layout_hint, LAYOUT_PATTERNS["grid"])

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

    return (
        f"Title: {data.get('title', '')}\n"
        f"Content Type: {data.get('content_type', 'news')}\n"
        f"Layout Pattern: {layout_hint} — {pattern_desc}\n"
        f"Color Mood: {mood}\n"
        f"Key Points:\n{points_text}"
    )


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

    # Carousel slide mode — use visual_hint + role from extractor to guide design
    # This reduces Claude's improvisation burden and improves first-attempt success rate
    is_carousel = data.get("_carousel", False)
    slide_role = data.get("_slide_role", "")
    visual_hint = data.get("_visual_hint", "")
    thread_idx = data.get("_thread_index")
    thread_total = data.get("_thread_total")

    carousel_note = ""
    if is_carousel:
        role_guidance = {
            "hook": (
                "HOOK slide — the opening. Design for MAXIMUM visual impact: "
                "oversized heading (40-56px), minimal body text, generous whitespace, "
                "single focal element. Goal: make the viewer stop scrolling."
            ),
            "point": (
                "POINT slide — a core insight. Clear hierarchy: bold heading (28-36px), "
                "body as supporting statement (14-16px), one strong visual anchor. "
                "Clean, readable, focused on one idea."
            ),
            "data": (
                "DATA slide — numeric emphasis. The key number/metric must DOMINATE "
                "(60-96px, accent color). Surround with minimal context. "
                "Use contrast to make the number unmissable."
            ),
            "quote": (
                "QUOTE slide — editorial voice. Large serif-style quotation (24-32px italic), "
                "opening quotation mark as decorative element, attribution in small caps. "
                "Whitespace-heavy, magazine-like."
            ),
            "cta": (
                "CTA slide — action trigger. Bold heading, clear directive, "
                "visual arrow/button indicating next action. "
                "Accent color on the CTA element. Leave no doubt about what to do next."
            ),
        }.get(slide_role, "Balanced layout with clear heading and readable body.")

        thread_position = ""
        if thread_idx and thread_total:
            thread_position = f"\nPosition: slide {thread_idx} of {thread_total} in carousel"

        carousel_note = f"""

=== CAROUSEL SLIDE MODE ===
This is ONE slide in a multi-slide carousel. Each slide has a specific role.

Role: {slide_role.upper()}
Role Guidance: {role_guidance}
Visual Hint (from content analyst): {visual_hint}{thread_position}

CAROUSEL DESIGN RULES (critical for visual quality):
- The heading is THE MAIN ELEMENT. Make it large, bold, impossible to miss.
- The body is SHORT supporting text (not a list of bullet points). Display it cleanly below the heading.
- DO NOT add fake statistics, progress bars, or unrelated decorative widgets at the bottom.
- DO NOT treat the body as "key points" — it's a single paragraph of 1-2 sentences.
- Follow the visual_hint EXACTLY. Don't improvise beyond it.
- Since this is a slide, NO "key insights" header, NO "工具使用心得" label, NO metadata chrome.
- The whole canvas should feel like a single powerful slide, not a dashboard.

PROGRESS INDICATOR — CRITICAL:
- DO NOT generate any "{thread_idx or 1}/{thread_total or 5}", "{thread_idx or 1} / {thread_total or 5}",
  "SLIDE {thread_idx or 1}/{thread_total or 5}", "0{thread_idx or 1}", "{thread_idx or 1}.", or any other
  slide-position / page-number text anywhere in your HTML.
- The pipeline automatically injects a "{thread_idx or 1} / {thread_total or 5}" badge in the corner after
  your HTML is generated. Any progress text you add will COLLIDE with the auto-injected badge.
- Same for any "CORE INSIGHT", "SLIDE X OF Y", "PART X" section labels — omit them entirely.
- The reader already knows which slide they're on from the injected badge.
"""

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
{mood} — use the CSS variables from the design system above.{carousel_note}

=== GENERATION PROCESS (2-step, mandatory) ===

[DESIGN AGENT] Think first (output as HTML comment <!-- DESIGN: ... -->):
1. Visual hierarchy: which element dominates, which supports?
2. How to adapt the layout pattern to this specific content?
3. Font size decisions for title vs points (give px values)
4. One distinctive visual choice that makes this layout memorable

[BUILD AGENT] Then implement:
- Follow your DESIGN AGENT decisions above exactly
- Use the CSS variables for ALL colors — no hardcoded values
- Generate complete, self-contained HTML

Now output the HTML."""


# ---------------------------------------------------------------------------
# AI provider call (adapted from caption.py pattern)
# ---------------------------------------------------------------------------

# Model selection: Haiku for HTML generation (cheap), Sonnet/Opus for premium
_CLAUDE_MODELS = {
    "haiku": "claude-haiku-4-5-20251001",  # Fast and cheap for HTML layout
    "sonnet": "claude-sonnet-4-6",          # Higher quality layout generation
    "opus": "claude-opus-4-6",              # Premium design with deeper reasoning
}
_DEFAULT_CLAUDE_MODEL = "haiku"

_GEMINI_MODEL = "gemini-2.5-flash"
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
            capture_output=True, text=True, timeout=600, env=env,
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
        # Remove first line (```html) and last closing fence (handles trailing newlines)
        end = next(
            (i for i in range(len(lines) - 1, 0, -1) if lines[i].strip().startswith("```")),
            len(lines),
        )
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
    provider: str = "gemini",
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
    # Inject thread position into data so carousel prompt has position context
    prompt_data = dict(data)
    if thread_index is not None:
        prompt_data["_thread_index"] = thread_index
    if thread_total is not None:
        prompt_data["_thread_total"] = thread_total

    prompt = _build_layout_prompt(prompt_data, card_format, color_mood)

    watermark_html = _build_watermark_html(
        watermark_data, watermark_position, watermark_opacity,
        brand_name, thread_index, thread_total,
    )

    def _save_raw_debug(raw: str) -> Path:
        debug_dir = Path(__file__).resolve().parent.parent / "output" / "debug"
        debug_dir.mkdir(parents=True, exist_ok=True)
        import datetime
        raw_path = debug_dir / f"raw_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        raw_path.write_text(raw, encoding="utf-8")
        return raw_path

    # Attempt 1
    try:
        raw_html = _call_provider(prompt, provider, model_variant)
        html = _validate_generated_html(raw_html)
        return _inject_overlays(html, watermark_html)
    except ValueError as e:
        raw_path = _save_raw_debug(raw_html if 'raw_html' in dir() else "")
        logger.warning("Smart layout attempt 1 failed validation: %s. raw → %s. Retrying...", e, raw_path)

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
        raw_path = _save_raw_debug(raw_html if 'raw_html' in dir() else "")
        logger.warning("Smart layout attempt 2 failed: %s. raw → %s. Falling back to template.", e, raw_path)

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


# ---------------------------------------------------------------------------
# Batch single-card generation (N contents × 1 layout/mood, CSS sent once)
# ---------------------------------------------------------------------------

_CONTENT_BATCH_MAX = 5  # Gemini safe batch size before timeout


def _build_content_batch_prompt(
    items: list[dict],
    card_format: str,
    color_mood: str,
    layout_hint: str | None = None,
) -> str:
    """Shared CSS once + N content blocks, each wrapped in ===CONTENT:{id}===."""
    specs = FORMAT_SPECS.get(card_format, FORMAT_SPECS["story"])
    mood = color_mood
    palette = COLOR_PALETTES.get(mood, COLOR_PALETTES["dark_tech"])
    design_css = _build_design_system_css(palette, specs["width"], specs["height"])
    system = _load_system_prompt()

    hint = layout_hint or items[0].get("layout_hint", "grid")
    pattern_desc = LAYOUT_PATTERNS.get(hint, LAYOUT_PATTERNS["grid"])

    content_blocks = []
    for item in items:
        point_lines = []
        for p in item.get("key_points", []):
            imp = p.get("importance", 3)
            hook = p.get("hook", "")
            text = p.get("text", "")
            if hook:
                point_lines.append(f"  [{imp}/5] HOOK: {hook} | DETAIL: {text}")
            else:
                point_lines.append(f"  [{imp}/5] {text}")
        content_blocks.append(
            f"===CONTENT:{item['_batch_id']}===\n"
            f"Title: {item.get('title', '')}\n"
            f"Source: {item.get('source', '')}\n"
            f"Key Points:\n" + "\n".join(point_lines)
        )

    return f"""{system}

=== DESIGN SYSTEM CSS (shared across ALL cards below — include in every <style> tag) ===
{design_css}

=== CANVAS ===
Width: {specs['width']}px, Height: {specs['height']}px
Everything must fit within this exact area. No scrolling.

=== LAYOUT (identical for all cards) ===
Pattern: {hint} — {pattern_desc}
Color Mood: {mood}

=== INSTRUCTIONS ===
Generate HTML for {len(items)} different content items using the same layout and palette.
The layout structure and CSS variables must be IDENTICAL across all outputs.
Only the content (title, key points) changes between cards.

For EACH card follow the 2-step process:
[DESIGN AGENT] Think first (output as <!-- DESIGN: ... -->):
  - Font size for title vs points (px values)
  - One visual choice that suits this specific content

[BUILD AGENT] Then implement using shared CSS variables.

Output format for EACH card — use EXACTLY these markers:
===CONTENT:{{id}}===
<!DOCTYPE html>...===END===

No explanation outside the markers. No markdown fences.

{"".join(f'{b}' + chr(10) for b in content_blocks)}"""


def _parse_content_batch_response(raw: str) -> dict[str, str]:
    """Parse ===CONTENT:{id}=== ... ===END=== blocks from batch response."""
    results: dict[str, str] = {}
    pattern = re.compile(r"===CONTENT:([^=]+)===\s*(.*?)\s*===END===", re.DOTALL)
    for m in pattern.finditer(raw):
        results[m.group(1).strip()] = m.group(2).strip()
    if not results:
        # Loose fallback
        loose = re.compile(
            r"===\s*CONTENT\s*:\s*([^=]+?)\s*===\s*(.*?)\s*===\s*END\s*===",
            re.DOTALL | re.IGNORECASE,
        )
        results = {m.group(1).strip(): m.group(2).strip() for m in loose.finditer(raw)}
    return results


def batch_render_single_cards(
    items: list[dict],
    card_format: str,
    color_mood: str,
    layout_hint: str | None = None,
    provider: str = "gemini",
    model_variant: str = "sonnet",
    max_batch: int = _CONTENT_BATCH_MAX,
) -> dict[str, str]:
    """Render N single-card HTMLs in batched LLM calls (CSS sent once per batch).

    Args:
        items: List of extracted data dicts, each must have '_batch_id' key.
        card_format: "square" or "story".
        color_mood: Palette name (e.g. "bold_contrast").
        layout_hint: Override layout pattern; defaults to first item's layout_hint.
        provider: LLM provider.
        model_variant: Model variant for Claude provider.
        max_batch: Max items per LLM call (default 5, Gemini safe limit).

    Returns:
        Dict mapping _batch_id → validated HTML string.
        Missing items (parse failure) are omitted — caller handles fallback.
    """
    import datetime

    all_results: dict[str, str] = {}

    for start in range(0, len(items), max_batch):
        chunk = items[start: start + max_batch]
        prompt = _build_content_batch_prompt(chunk, card_format, color_mood, layout_hint)

        try:
            raw = _call_provider(prompt, provider, model_variant)
        except Exception as e:
            logger.warning("batch_render chunk %d-%d provider error: %s", start, start + len(chunk), e)
            continue

        html_map = _parse_content_batch_response(raw)

        if not html_map:
            # Single-item fallback: if Gemini omitted markers, treat entire raw as HTML
            if len(chunk) == 1 and "<!DOCTYPE html" in raw:
                bid = chunk[0]["_batch_id"]
                try:
                    all_results[bid] = _validate_generated_html(raw)
                    logger.info("batch_render: single-item marker-less fallback used for id=%s", bid)
                    continue
                except ValueError:
                    pass
            debug_dir = Path(__file__).resolve().parent.parent / "output" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            raw_path = debug_dir / f"batch_raw_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            raw_path.write_text(raw, encoding="utf-8")
            logger.warning("batch_render chunk parse 0/%d — raw saved to %s", len(chunk), raw_path)
            continue

        for item in chunk:
            bid = item["_batch_id"]
            raw_html = html_map.get(bid, "")
            if not raw_html:
                logger.warning("batch_render: missing HTML for id=%s", bid)
                continue
            try:
                all_results[bid] = _validate_generated_html(raw_html)
            except ValueError as e:
                logger.warning("batch_render: validation failed for id=%s: %s", bid, e)

    return all_results
