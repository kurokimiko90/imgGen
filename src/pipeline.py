"""
pipeline.py - Core pipeline: extract → render → screenshot.

Provides reusable pipeline functions so that main.py, batch.py,
and future features (multi-format, thread, digest, watch) all share
the same extract→render→capture flow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.extractor import ExtractionConfig


@dataclass(frozen=True)
class PipelineOptions:
    """Immutable options for a single pipeline run."""

    theme: str = "dark"
    format: str = "story"
    provider: str = "cli"
    model_variant: str = "haiku"  # "haiku" (default, 3x cheaper), "sonnet", or "opus" for Claude provider
    scale: int = 2
    webp: bool = False
    watermark_data: str | None = None
    watermark_position: str = "bottom-right"
    watermark_opacity: float = 0.8
    brand_name: str | None = None
    extraction_config: ExtractionConfig | None = None
    mode: str = "card"  # "card", "article", or "smart"
    color_mood: str | None = None  # smart mode only: override color palette


def extract(
    article_text: str,
    provider: str = "cli",
    extraction_config: ExtractionConfig | None = None,
    model_variant: str = "haiku",
) -> dict[str, Any]:
    """Run AI extraction on article text.

    Returns:
        Dict with keys: title, key_points, source, theme_suggestion.

    Raises:
        EnvironmentError: If the required API key is missing.
        ValueError: If extraction or validation fails.
    """
    from src.extractor import extract_key_points

    return extract_key_points(
        article_text,
        provider=provider,
        config=extraction_config,
        model_variant=model_variant,
    )


def render_and_capture(
    data: dict[str, Any],
    options: PipelineOptions,
    output_path: Path,
    *,
    thread_index: int | None = None,
    thread_total: int | None = None,
) -> Path:
    """Render HTML from extracted data, then capture screenshot.

    This is the reusable render→screenshot step.  The caller is responsible
    for having already run extraction (or having ``data`` from another source
    such as digest synthesis).

    Args:
        data: Extracted article data (title, key_points, source, ...).
        options: Immutable pipeline options.
        output_path: Where to write the final image.
        thread_index: If in thread mode, the 1-based card index.
        thread_total: If in thread mode, total number of cards.

    Returns:
        Resolved Path to the saved image file.
    """
    from src.screenshotter import take_screenshot

    if options.mode == "smart":
        from src.smart_renderer import generate_smart_html
        html_content = generate_smart_html(
            data,
            card_format=options.format,
            provider=options.provider,
            model_variant=options.model_variant,
            color_mood=options.color_mood,
            watermark_data=options.watermark_data,
            watermark_position=options.watermark_position,
            watermark_opacity=options.watermark_opacity,
            brand_name=options.brand_name,
            thread_index=thread_index,
            thread_total=thread_total,
        )
    else:
        from src.renderer import render_card
        html_content = render_card(
            data,
            theme=options.theme,
            format=options.format,
            watermark_data=options.watermark_data,
            watermark_position=options.watermark_position,
            watermark_opacity=options.watermark_opacity,
            brand_name=options.brand_name,
            thread_index=thread_index,
            thread_total=thread_total,
        )

    return take_screenshot(
        html_content,
        output_path,
        format=options.format,
        scale=options.scale,
    )


def run_pipeline(
    article_text: str,
    options: PipelineOptions,
    output_path: Path,
) -> tuple[dict[str, Any], Path]:
    """Full pipeline: extract → render → screenshot.

    Args:
        article_text: Raw article text to summarize.
        options: Immutable pipeline options.
        output_path: Where to write the final image.

    Returns:
        Tuple of (extracted_data, final_image_path).
    """
    from src.extractor import ExtractionConfig as _EC

    extraction_config = options.extraction_config
    if extraction_config is None:
        extraction_config = _EC(mode=options.mode)
    elif extraction_config.mode != options.mode:
        extraction_config = _EC(
            **{**extraction_config.__dict__, "mode": options.mode}
        )

    data = extract(
        article_text,
        provider=options.provider,
        extraction_config=extraction_config,
        model_variant=options.model_variant,
    )
    final_path = render_and_capture(data, options, output_path)
    return data, final_path


def run_carousel_pipeline(
    article_text: str,
    options: PipelineOptions,
    output_dir: Path,
    num_slides: int = 5,
) -> tuple[dict[str, Any], list[Path]]:
    """Carousel pipeline: extract slides → render each → screenshot each.

    Args:
        article_text: Raw article text.
        options: Pipeline options (theme, format, provider, etc.).
        output_dir: Directory to write slide images into.
        num_slides: Number of slides to generate (3-7).

    Returns:
        Tuple of (extracted_data_with_slides, list_of_image_paths).
    """
    from src.extractor import ExtractionConfig as _EC

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extract with carousel mode
    extraction_config = _EC(
        mode="carousel",
        carousel_slides=num_slides,
        **({"social_mode": True} if options.mode == "smart" else {}),
    )

    data = extract(
        article_text,
        provider=options.provider,
        extraction_config=extraction_config,
        model_variant=options.model_variant,
    )

    slides = data.get("slides", [])
    if not slides:
        raise ValueError("Carousel extraction returned no slides")

    # Render each slide as a separate image
    image_paths: list[Path] = []
    total = len(slides)

    for slide in slides:
        idx = slide.get("slide_number", len(image_paths) + 1)
        slide_path = output_dir / f"slide_{idx:02d}.png"

        # Convert slide to the data format render_and_capture expects
        slide_data = {
            "title": slide.get("heading", ""),
            "key_points": [{"text": slide.get("body", "")}],
            "source": data.get("source", ""),
            "theme_suggestion": data.get("theme_suggestion", options.theme),
            # Pass carousel metadata for templates
            "_carousel": True,
            "_slide_role": slide.get("role", "point"),
            "_visual_hint": slide.get("visual_hint", ""),
        }

        path = render_and_capture(
            slide_data,
            options,
            slide_path,
            thread_index=idx,
            thread_total=total,
        )
        image_paths.append(path)

    return data, image_paths
