"""
renderer.py - Jinja2 HTML rendering module

Renders beautiful HTML cards from extracted article data using themed templates.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
VALID_THEMES = {"dark", "light", "gradient"}


def render_card(data: dict[str, Any], theme: str = "dark") -> str:
    """
    Render an HTML card from extracted article data.

    Args:
        data: Dict with keys: title, key_points, source, theme_suggestion
        theme: One of 'dark', 'light', 'gradient'

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

    if not TEMPLATES_DIR.exists():
        raise FileNotFoundError(
            f"Templates directory not found: {TEMPLATES_DIR}"
        )

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )

    template_name = f"{theme}.html"

    try:
        template = env.get_template(template_name)
    except TemplateNotFound as e:
        raise TemplateNotFound(
            f"Template '{template_name}' not found in {TEMPLATES_DIR}"
        ) from e

    rendered = template.render(
        title=data.get("title", ""),
        key_points=data.get("key_points", []),
        source=data.get("source", ""),
        theme=theme,
    )

    return rendered
