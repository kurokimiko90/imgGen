"""
renderer.py - Jinja2 HTML rendering module

Renders beautiful HTML cards from extracted article data using themed templates.
"""

import base64
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
VALID_THEMES = {"dark", "light", "gradient", "warm_sun", "cozy",
                "hook", "quote", "quote_dark", "data_impact", "versus", "thread_card",
                "pop_split", "editorial", "luxury_data", "ai_theater",
                "studio", "broadsheet", "pastel", "paper_data",
                # Batch 4 — light content variants
                "bulletin_hook", "gallery_quote", "soft_versus", "trace",
                # Batch 5 — high-impact content types
                "ranking", "before_after", "concept", "picks",
                # Batch 6 — complete coverage
                "opinion", "checklist", "faq", "milestone"}
VALID_FORMATS = {"story", "square", "landscape", "twitter"}

_MIME_BY_EXTENSION = {
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}
ALLOWED_WATERMARK_EXTENSIONS = frozenset(_MIME_BY_EXTENSION)
VALID_WATERMARK_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


def load_watermark_data(path: "str | Path") -> str:
    """Read an image file and return a base64 data URI string.

    Args:
        path: Path to the image file (PNG, SVG, JPEG, or other).

    Returns:
        A data URI string, e.g. ``data:image/png;base64,....``

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Watermark file not found: {path}")

    ext = path.suffix.lower()
    if ext not in ALLOWED_WATERMARK_EXTENSIONS:
        raise ValueError(
            f"Unsupported watermark file type '{ext}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_WATERMARK_EXTENSIONS))}"
        )
    mime = _MIME_BY_EXTENSION[ext]
    raw = path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_card(
    data: dict[str, Any],
    theme: str = "dark",
    format: str = "story",
    watermark_data: "str | None" = None,
    watermark_position: str = "bottom-right",
    watermark_opacity: float = 0.8,
    brand_name: "str | None" = None,
    thread_index: "int | None" = None,
    thread_total: "int | None" = None,
) -> str:
    """
    Render an HTML card from extracted article data.

    Args:
        data: Dict with keys: title, key_points, source, theme_suggestion
        theme: One of 'dark', 'light', 'gradient'
        format: Output format - one of 'story', 'square', 'landscape', 'twitter'
        watermark_data: Optional base64 data URI for watermark image overlay.
        watermark_position: Corner for the overlay: top-left, top-right,
            bottom-left, or bottom-right.
        watermark_opacity: Float 0.0–1.0 controlling overlay transparency.
        brand_name: Optional text watermark (e.g. "@username").

    Returns:
        Rendered HTML string

    Raises:
        ValueError: If theme is invalid
        TemplateNotFound: If template file does not exist
    """
    if theme not in VALID_THEMES:
        raise ValueError(
            f"Invalid theme '{theme}'. Must be one of: {', '.join(sorted(VALID_THEMES))}"
        )

    if format not in VALID_FORMATS:
        raise ValueError(
            f"Invalid format '{format}'. Must be one of: {', '.join(sorted(VALID_FORMATS))}"
        )

    if watermark_position not in VALID_WATERMARK_POSITIONS:
        raise ValueError(
            f"Invalid watermark_position '{watermark_position}'. "
            f"Must be one of: {', '.join(sorted(VALID_WATERMARK_POSITIONS))}"
        )

    if not (0.0 <= watermark_opacity <= 1.0):
        raise ValueError(
            f"watermark_opacity must be between 0.0 and 1.0, got {watermark_opacity!r}"
        )

    if not TEMPLATES_DIR.exists():
        raise FileNotFoundError(
            f"Templates directory not found: {TEMPLATES_DIR}"
        )

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    # Choose template: article mode uses article.html, card mode uses {theme}.html
    is_article = "sections" in data and "key_points" not in data
    template_name = "article.html" if is_article else f"{theme}.html"

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise TemplateNotFound(
            f"Template '{template_name}' not found in {TEMPLATES_DIR}"
        ) from e

    rendered = template.render(
        title=data.get("title", ""),
        key_points=data.get("key_points", []),
        sections=data.get("sections", []),
        source=data.get("source", ""),
        theme=theme,
        format=format,
        watermark_data=watermark_data,
        watermark_position=watermark_position,
        watermark_opacity=watermark_opacity,
        brand_name=brand_name,
        thread_index=thread_index,
        thread_total=thread_total,
    )

    return rendered
