"""
main.py - CLI entry point for imgGen

Article → Summary → Image Card pipeline.
Usage:
  python main.py --text "..."
  python main.py --file article.txt
  python main.py --url https://example.com/article --theme light
  python main.py --batch entries.txt --workers 3 --output-dir ./output
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

import click
from dotenv import load_dotenv

from src.batch import run_batch
from src.config import (
    delete_preset,
    get_default,
    list_presets,
    load_config,
    load_preset,
    save_preset,
)

load_dotenv()

# Output directory relative to this file
OUTPUT_DIR = Path(__file__).parent / "output"


def _fetch_url_content(url: str) -> str:
    """Fetch text content from a URL, converting errors to ClickException."""
    from src.fetcher import fetch_url_content
    try:
        return fetch_url_content(url)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e


def _resolve_output_path(
    output: "str | None",
    theme: str,
    card_format: str = "story",
    webp: bool = False,
    output_dir: "str | None" = None,
) -> Path:
    """Resolve the output file path.

    Args:
        output: Explicit output filename/path from --output flag.
        theme: Theme name used in auto-generated filenames.
        card_format: Format name used in auto-generated filenames.
        webp: When True, use .webp extension instead of .png.
        output_dir: Base directory for auto-generated paths. When None,
            falls back to OUTPUT_DIR (the default output/ folder).
    """
    base_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    ext = ".webp" if webp else ".png"

    if output:
        path = Path(output)
        if not path.is_absolute():
            path = base_dir / path
        if not path.suffix:
            path = path.with_suffix(ext)
        return path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return base_dir / f"card_{theme}_{timestamp}_{card_format}{ext}"


def _run_batch_mode(
    batch_file: str,
    workers: int,
    output_dir_override: "str | None",
    theme: "str | None",
    provider: "str | None",
    card_format: "str | None",
    scale: "str | None",
    webp: "bool | None",
    config: "str | None",
    watermark: "str | None",
    watermark_position: "str | None",
    watermark_opacity: "float | None",
    brand_name: "str | None",
) -> None:
    """Execute batch mode: parse file, run all entries, write report."""
    from src.batch import parse_batch_file

    # Resolve config
    config_path = Path(config) if config else None
    cfg = load_config(config_path=config_path)

    effective_theme = theme if theme is not None else get_default(cfg, "theme", "dark")
    effective_provider = provider if provider is not None else get_default(cfg, "provider", "cli")
    effective_format = card_format if card_format is not None else get_default(cfg, "format", "story")
    effective_scale = int(scale) if scale is not None else int(get_default(cfg, "scale", 2))
    effective_webp = webp if webp is not None else get_default(cfg, "webp", False)

    # Watermark config resolution
    _wm_from_config = get_default(cfg, "watermark", None)
    effective_watermark = watermark if watermark is not None else _wm_from_config
    if effective_watermark is not None and watermark is None:
        from src.renderer import ALLOWED_WATERMARK_EXTENSIONS
        _wm_path = Path(effective_watermark)
        if not _wm_path.exists():
            raise click.ClickException(f"Config watermark file not found: {effective_watermark}")
        if _wm_path.suffix.lower() not in ALLOWED_WATERMARK_EXTENSIONS:
            raise click.ClickException(
                f"Config watermark '{_wm_path.name}' has unsupported type '{_wm_path.suffix}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_WATERMARK_EXTENSIONS))}"
            )

    effective_watermark_position = (
        watermark_position if watermark_position is not None
        else get_default(cfg, "watermark_position", "bottom-right")
    )
    effective_watermark_opacity = (
        watermark_opacity if watermark_opacity is not None
        else float(get_default(cfg, "watermark_opacity", 0.8))
    )
    effective_brand_name = brand_name if brand_name is not None else get_default(cfg, "brand_name", None)

    # Load watermark data URI if needed
    watermark_data_uri: "str | None" = None
    if effective_watermark is not None:
        from src.renderer import load_watermark_data
        watermark_data_uri = load_watermark_data(Path(effective_watermark))

    # Resolve output directory
    cfg_output_dir = get_default(cfg, "output_dir", None)
    if output_dir_override is not None:
        resolved_output_dir = Path(output_dir_override)
    elif cfg_output_dir is not None:
        resolved_output_dir = Path(cfg_output_dir)
    else:
        resolved_output_dir = OUTPUT_DIR
    resolved_output_dir.mkdir(parents=True, exist_ok=True)

    # Parse the batch file
    entries = parse_batch_file(Path(batch_file))

    options = {
        "theme": effective_theme,
        "format": effective_format,
        "provider": effective_provider,
        "scale": effective_scale,
        "webp": effective_webp,
        "watermark_data": watermark_data_uri,
        "watermark_position": effective_watermark_position,
        "watermark_opacity": effective_watermark_opacity,
        "brand_name": effective_brand_name,
    }

    click.echo(f"\nBatch mode: {len(entries)} entries, {workers} workers", err=True)

    # Run batch processing
    results = asyncio.run(run_batch(entries, options, resolved_output_dir, workers=workers))

    # Compute summary counts
    succeeded = sum(1 for r in results if r.get("status") == "ok")
    failed = sum(1 for r in results if r.get("status") == "error")
    total = len(results)

    # Print summary to stderr
    click.echo(f"\nBatch complete: {succeeded} succeeded, {failed} failed", err=True)
    if failed:
        click.echo("Failed entries:", err=True)
        for r in results:
            if r.get("status") == "error":
                click.echo(f"  [{r['index']}] {r['input']} - {r.get('error', 'unknown error')}", err=True)

    # Write batch_report.json
    report = {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }
    report_path = resolved_output_dir / "batch_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    click.echo(f"\nReport written to: {report_path}", err=True)


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--text", "-t",
    default=None,
    help="Article text to process directly.",
)
@click.option(
    "--file", "-f",
    default=None,
    type=click.Path(exists=True, readable=True),
    help="Path to a text file containing the article.",
)
@click.option(
    "--url", "-u",
    default=None,
    help="URL to fetch article content from.",
)
@click.option(
    "--theme",
    default=None,
    type=click.Choice(["dark", "light", "gradient", "warm_sun", "cozy"], case_sensitive=False),
    help="Visual theme for the image card. [default: dark]",
)
@click.option(
    "--provider", "-p",
    default=None,
    type=click.Choice(["claude", "gemini", "gpt", "cli"], case_sensitive=False),
    help="AI provider for summarization. [default: cli]",
)
@click.option(
    "--model",
    default=None,
    type=click.Choice(["sonnet", "opus"], case_sensitive=False),
    help="Claude model variant for smart mode: sonnet (balanced) or opus (premium). [default: sonnet]",
)
@click.option(
    "--mode",
    default=None,
    type=click.Choice(["card", "article", "smart"], case_sensitive=False),
    help="Extraction mode: card (key points), article (condensed prose), or smart (AI-driven layout). [default: card]",
)
@click.option(
    "--color-mood",
    "color_mood",
    default=None,
    type=click.Choice(["dark_tech", "warm_editorial", "minimal_white", "vibrant_pop", "nature_calm"], case_sensitive=False),
    help="Color mood for smart mode (overrides AI choice). Ignored for card/article modes.",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output filename (default: auto-generated timestamp in output/).",
)
@click.option(
    "--format", "card_format",
    default=None,
    type=click.Choice(["story", "square", "landscape", "twitter"], case_sensitive=False),
    help="Output format / aspect ratio. [default: story]",
)
@click.option(
    "--formats",
    "multi_formats",
    default=None,
    help="Comma-separated formats for multi-output (e.g. story,square,twitter). "
         "Mutually exclusive with --format.",
)
@click.option(
    "--clipboard",
    is_flag=True,
    default=False,
    help="Copy the generated image to macOS clipboard.",
)
@click.option(
    "--caption",
    "caption_platforms",
    default=None,
    help="Generate text captions for platforms (e.g. twitter,linkedin,instagram or 'all').",
)
@click.option(
    "--thread",
    is_flag=True,
    default=False,
    help="Thread mode: generate one card per key point with sequential numbering.",
)
@click.option(
    "--post",
    "post_platform",
    default=None,
    type=click.Choice(["twitter"], case_sensitive=False),
    help="Post the generated image to a platform (e.g. twitter).",
)
@click.option(
    "--scale",
    default=None,
    type=click.Choice(["1", "2"]),
    help="Output resolution scale (1x or 2x Retina). [default: 2]",
)
@click.option(
    "--webp/--no-webp",
    default=None,
    help="Save as WebP instead of PNG. --no-webp overrides config webp=true.",
)
@click.option(
    "--config",
    default=None,
    type=click.Path(),
    help="Path to a TOML config file (overrides auto-discovery of ~/.imggenrc).",
)
@click.option(
    "--watermark",
    default=None,
    type=click.Path(exists=True),
    help="PNG or SVG image file to overlay as logo watermark.",
)
@click.option(
    "--watermark-position",
    default=None,
    type=click.Choice(["top-left", "top-right", "bottom-left", "bottom-right"], case_sensitive=False),
    help="Watermark corner position. [default: bottom-right]",
)
@click.option(
    "--watermark-opacity",
    default=None,
    type=float,
    help="Watermark opacity 0.0–1.0. [default: 0.8]",
)
@click.option(
    "--brand-name",
    default=None,
    help="Text watermark (e.g. '@username') rendered as styled overlay.",
)
@click.option(
    "--batch",
    "batch_file",
    default=None,
    type=click.Path(exists=True),
    help="Plain text file with one URL or file path per line to process as a batch.",
)
@click.option(
    "--workers",
    default=3,
    type=int,
    show_default=True,
    help="Max concurrent entries when using --batch.",
)
@click.option(
    "--output-dir",
    "output_dir",
    default=None,
    type=click.Path(),
    help="Output directory for batch runs (overrides config output_dir).",
)
@click.option(
    "--social",
    is_flag=True,
    default=False,
    help="Social mode: extract hook keywords + short detail per point for 3-second scannable cards. "
         "Best with --mode smart.",
)
@click.option(
    "--preset",
    "preset_name",
    default=None,
    help="Apply a saved preset. Explicit CLI flags override preset values.",
)
@click.pass_context
def main(
    ctx: click.Context,
    text: str | None,
    file: str | None,
    url: str | None,
    theme: str | None,
    provider: str | None,
    model: str | None,
    mode: str | None,
    color_mood: str | None,
    output: str | None,
    card_format: str | None,
    multi_formats: str | None,
    clipboard: bool,
    caption_platforms: str | None,
    thread: bool,
    post_platform: str | None,
    scale: str | None,
    webp: bool | None,
    config: str | None,
    watermark: str | None,
    watermark_position: str | None,
    watermark_opacity: float | None,
    brand_name: str | None,
    batch_file: str | None,
    workers: int,
    output_dir: str | None,
    social: bool,
    preset_name: str | None,
) -> None:
    """
    imgGen - Transform articles into beautiful image cards.

    Provide article content via --text, --file, or --url.
    For batch processing, use --batch with a file listing URLs or paths.
    Use 'imggen preset --help' to manage saved parameter presets.
    """
    # If a subcommand (e.g. 'preset') is being invoked, skip the pipeline
    if ctx.invoked_subcommand is not None:
        return

    # --- Mutual exclusion: --batch vs --text/--file/--url ---
    if batch_file is not None:
        if text or file or url:
            raise click.UsageError(
                "--batch is mutually exclusive with --text, --file, and --url."
            )
        _run_batch_mode(
            batch_file=batch_file,
            workers=workers,
            output_dir_override=output_dir,
            theme=theme,
            provider=provider,
            card_format=card_format,
            scale=scale,
            webp=webp,
            config=config,
            watermark=watermark,
            watermark_position=watermark_position,
            watermark_opacity=watermark_opacity,
            brand_name=brand_name,
        )
        return

    # --- Mutual exclusions ---
    if card_format is not None and multi_formats is not None:
        raise click.UsageError("--format and --formats are mutually exclusive.")
    if thread and multi_formats is not None:
        raise click.UsageError("--thread and --formats are mutually exclusive.")

    # --- Parse --formats ---
    from src.renderer import VALID_FORMATS
    format_list: list[str] | None = None
    if multi_formats is not None:
        format_list = [f.strip().lower() for f in multi_formats.split(",") if f.strip()]
        invalid = [f for f in format_list if f not in VALID_FORMATS]
        if invalid:
            raise click.UsageError(
                f"Invalid format(s): {', '.join(invalid)}. "
                f"Valid: {', '.join(sorted(VALID_FORMATS))}"
            )
        if not format_list:
            raise click.UsageError("--formats requires at least one format.")

    # --- Config resolution ---
    config_path = Path(config) if config else None
    cfg = load_config(config_path=config_path)

    # --- Preset resolution ---
    # Priority: CLI flag > preset value > config [defaults] > built-in default
    preset: dict = {}
    if preset_name is not None:
        preset = load_preset(preset_name, config_path=config_path)
        if not preset:
            raise click.ClickException(
                f"Preset '{preset_name}' not found. "
                "Use 'imggen preset list' to see available presets."
            )

    def _p(key, cli_value, fallback):
        """Return cli_value if set, else preset value, else config default."""
        if cli_value is not None:
            return cli_value
        if key in preset:
            return preset[key]
        return get_default(cfg, key, fallback)

    effective_theme = _p("theme", theme, "dark")
    effective_provider = _p("provider", provider, "cli")
    effective_model = _p("model", model, "sonnet")  # "sonnet" or "opus" for smart mode
    effective_format = _p("format", card_format, "story")
    _scale_raw = scale if scale is not None else (
        str(preset["scale"]) if "scale" in preset else None
    )
    effective_scale = int(_scale_raw) if _scale_raw is not None else int(get_default(cfg, "scale", 2))
    effective_webp = _p("webp", webp, False)
    effective_output_dir = get_default(cfg, "output_dir", None)

    # Watermark config resolution
    _wm_from_config = get_default(cfg, "watermark", None)
    effective_watermark = watermark if watermark is not None else _wm_from_config
    # Validate config-sourced watermark path (CLI path is validated by click.Path(exists=True))
    if effective_watermark is not None and watermark is None:
        from src.renderer import ALLOWED_WATERMARK_EXTENSIONS
        _wm_path = Path(effective_watermark)
        if not _wm_path.exists():
            raise click.ClickException(f"Config watermark file not found: {effective_watermark}")
        if _wm_path.suffix.lower() not in ALLOWED_WATERMARK_EXTENSIONS:
            raise click.ClickException(
                f"Config watermark '{_wm_path.name}' has unsupported type '{_wm_path.suffix}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_WATERMARK_EXTENSIONS))}"
            )
    effective_watermark_position = _p("watermark_position", watermark_position, "bottom-right")
    _raw_opacity = watermark_opacity if watermark_opacity is not None else (
        preset.get("watermark_opacity") if "watermark_opacity" in preset
        else get_default(cfg, "watermark_opacity", 0.8)
    )
    effective_watermark_opacity = float(_raw_opacity)
    effective_brand_name = _p("brand_name", brand_name, None)

    # --- Input resolution ---
    sources = [s for s in [text, file, url] if s]
    if len(sources) == 0:
        raise click.UsageError(
            "Please provide article content via --text, --file, or --url."
        )
    if len(sources) > 1:
        raise click.UsageError(
            "Please provide only one of --text, --file, or --url."
        )

    # Get article text
    if text:
        article_text = text.strip()
    elif file:
        try:
            article_text = Path(file).read_text(encoding="utf-8").strip()
        except OSError as e:
            raise click.ClickException(f"Cannot read file '{file}': {e}") from e
    else:
        click.echo(f"  Fetching content from URL: {url}", err=True)
        article_text = _fetch_url_content(url)

    if not article_text:
        raise click.ClickException("Article text is empty.")

    if len(article_text) < 20:
        raise click.ClickException(
            f"Article text is too short ({len(article_text)} chars). "
            "Please provide meaningful content."
        )

    click.echo(f"\n  Article length: {len(article_text)} characters", err=True)

    # --- Build pipeline options ---
    from src.pipeline import PipelineOptions, extract, render_and_capture
    from src.renderer import load_watermark_data

    watermark_data_uri: str | None = None
    if effective_watermark is not None:
        try:
            watermark_data_uri = load_watermark_data(Path(effective_watermark))
        except FileNotFoundError as e:
            raise click.ClickException(str(e)) from e

    # --- Step 1: Extract content (one AI call) ---
    effective_mode = _p("mode", mode, "card")
    effective_color_mood = _p("color_mood", color_mood, None)
    from src.extractor import ExtractionConfig
    extraction_config = ExtractionConfig(mode=effective_mode, social_mode=social)

    step1_labels = {
        "article": "Condensing article",
        "smart": "Analyzing content structure",
    }
    step1_label = step1_labels.get(effective_mode, "Extracting key points")
    click.echo(f"\n[1/3] {step1_label} with {effective_provider.capitalize()} API...", err=True)
    try:
        data = extract(article_text, provider=effective_provider, extraction_config=extraction_config)
    except EnvironmentError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(f"Extraction failed: {e}") from e
    except Exception as e:
        raise click.ClickException(f"API error: {e}") from e

    click.echo(f"      Title: {data['title']}", err=True)
    if effective_mode == "article":
        click.echo(f"      Sections: {len(data['sections'])}", err=True)
    else:
        click.echo(f"      Points: {len(data['key_points'])}", err=True)
    if effective_mode == "smart":
        click.echo(f"      Layout: {data.get('layout_hint', 'hero_list')}", err=True)
        click.echo(f"      Mood: {data.get('color_mood', 'dark_tech')}", err=True)
    else:
        click.echo(f"      Suggested theme: {data.get('theme_suggestion', 'dark')}", err=True)

    # --- Steps 2+3: Render + Screenshot ---
    generated_paths: list[Path] = []

    if thread:
        # Thread mode: one card per key_point
        thread_format = card_format if card_format else effective_format
        total_cards = len(data["key_points"])
        click.echo(f"\n  Thread mode: generating {total_cards} cards...", err=True)

        for idx, point in enumerate(data["key_points"], start=1):
            thread_data = {**data, "key_points": [point]}
            pipe_opts = PipelineOptions(
                theme=effective_theme,
                format=thread_format,
                provider=effective_provider,
                model_variant=effective_model,
                scale=effective_scale,
                webp=effective_webp,
                watermark_data=watermark_data_uri,
                watermark_position=effective_watermark_position,
                watermark_opacity=effective_watermark_opacity,
                brand_name=effective_brand_name,
                mode=effective_mode,
                color_mood=effective_color_mood,
            )
            ext = ".webp" if effective_webp else ".png"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            theme_label = effective_theme if effective_mode != "smart" else "smart"
            out = (Path(effective_output_dir) if effective_output_dir else OUTPUT_DIR) / (
                f"thread_{idx:02d}_{theme_label}_{timestamp}{ext}"
            )
            out.parent.mkdir(parents=True, exist_ok=True)
            click.echo(f"  [{idx}/{total_cards}] -> {out}", err=True)

            try:
                final_path = render_and_capture(
                    thread_data, pipe_opts, out,
                    thread_index=idx, thread_total=total_cards,
                )
            except (FileNotFoundError, RuntimeError) as e:
                raise click.ClickException(str(e)) from e
            except Exception as e:
                raise click.ClickException(f"Render/screenshot failed: {e}") from e

            generated_paths.append(final_path)
    else:
        # Normal mode: single or multi-format
        formats_to_render = format_list if format_list else [effective_format]

        for fmt in formats_to_render:
            pipe_opts = PipelineOptions(
                theme=effective_theme,
                format=fmt,
                provider=effective_provider,
                model_variant=effective_model,
                scale=effective_scale,
                webp=effective_webp,
                watermark_data=watermark_data_uri,
                watermark_position=effective_watermark_position,
                watermark_opacity=effective_watermark_opacity,
                brand_name=effective_brand_name,
                mode=effective_mode,
                color_mood=effective_color_mood,
            )
            out = _resolve_output_path(
                output if len(formats_to_render) == 1 else None,
                effective_theme,
                card_format=fmt,
                webp=effective_webp,
                output_dir=effective_output_dir,
            )
            if effective_mode == "smart":
                render_label = f"Generating AI layout (format: {fmt})"
            else:
                render_label = f"Rendering HTML card (theme: {effective_theme}, format: {fmt})"
            click.echo(f"\n[2/3] {render_label}...", err=True)
            click.echo(f"[3/3] Capturing screenshot -> {out}", err=True)

            try:
                final_path = render_and_capture(data, pipe_opts, out)
            except (FileNotFoundError, RuntimeError) as e:
                raise click.ClickException(str(e)) from e
            except Exception as e:
                raise click.ClickException(f"Render/screenshot failed: {e}") from e

            generated_paths.append(final_path)

    # --- Caption ---
    generated_captions: dict[str, str] = {}
    if caption_platforms:
        from src.caption import VALID_PLATFORMS as CAPTION_PLATFORMS, generate_captions, save_captions
        platforms = (
            sorted(CAPTION_PLATFORMS) if caption_platforms == "all"
            else [p.strip().lower() for p in caption_platforms.split(",") if p.strip()]
        )
        try:
            click.echo(f"\n  Generating captions for: {', '.join(platforms)}...", err=True)
            generated_captions = generate_captions(data, platforms, provider=effective_provider)
            for platform, text in generated_captions.items():
                click.echo(f"\n  [{platform.upper()}]\n  {text}", err=True)
            caption_file = save_captions(generated_captions, generated_paths[0])
            click.echo(f"\n  Captions saved to: {caption_file}", err=True)
        except (ValueError, EnvironmentError, RuntimeError) as e:
            click.echo(f"\n  Caption generation failed: {e}", err=True)

    # --- Clipboard ---
    if clipboard:
        from src.clipboard import copy_image_to_clipboard
        last_image = generated_paths[-1]
        try:
            copy_image_to_clipboard(last_image)
            click.echo("  Image copied to clipboard.", err=True)
        except RuntimeError as e:
            click.echo(f"  Clipboard copy failed: {e}", err=True)

    # --- Post to platform ---
    if post_platform == "twitter":
        from src.publisher import publish_to_twitter
        last_image = generated_paths[-1]
        tweet_text = generated_captions.get("twitter", "")
        try:
            click.echo("\n  Posting to Twitter...", err=True)
            tweet_url = publish_to_twitter(last_image, caption=tweet_text)
            click.echo(f"  Posted: {tweet_url}", err=True)
        except (EnvironmentError, RuntimeError) as e:
            click.echo(f"  Twitter posting failed: {e}", err=True)

    # --- History ---
    try:
        from src.history import record_generation
        source_url = url if url else None
        for p in generated_paths:
            record_generation(
                url=source_url,
                title=data["title"],
                theme=effective_theme,
                format=p.stem.split("_")[-1] if format_list else effective_format,
                provider=effective_provider,
                output_path=str(p),
                file_size=p.stat().st_size,
                key_points_count=len(data["key_points"]),
                source=data.get("source"),
                mode="multi" if format_list else "single",
            )
    except Exception as e:  # noqa: BLE001 — history is non-critical
        click.echo(f"  History recording failed: {e}", err=True)

    # --- Done ---
    for p in generated_paths:
        file_size_kb = p.stat().st_size / 1024
        click.echo(
            f"\n  Done! Image saved to:\n  {p}\n"
            f"  Size: {file_size_kb:.1f} KB",
            err=True,
        )
    # Print paths to stdout so they can be captured by scripts
    for p in generated_paths:
        click.echo(str(p))


# ---------------------------------------------------------------------------
# preset subcommand group
# ---------------------------------------------------------------------------


def _get_config_path_from_ctx(ctx: click.Context) -> "Path | None":
    """Walk up the Click context chain to find the --config value from main."""
    current = ctx
    while current is not None:
        config_val = current.params.get("config")
        if config_val is not None:
            return Path(config_val)
        current = current.parent
    return None


@click.group(name="preset")
@click.pass_context
def preset_group(ctx: click.Context) -> None:
    """Manage saved parameter presets."""


@preset_group.command(name="save")
@click.argument("name")
@click.option("--theme", default=None,
              type=click.Choice(["dark", "light", "gradient", "warm_sun", "cozy"], case_sensitive=False))
@click.option("--format", "card_format", default=None,
              type=click.Choice(["story", "square", "landscape", "twitter"], case_sensitive=False))
@click.option("--provider", "-p", default=None,
              type=click.Choice(["claude", "gemini", "gpt", "cli"], case_sensitive=False))
@click.option("--scale", default=None, type=click.Choice(["1", "2"]))
@click.option("--webp/--no-webp", default=None)
@click.option("--watermark-position", default=None,
              type=click.Choice(["top-left", "top-right", "bottom-left", "bottom-right"],
                                case_sensitive=False))
@click.option("--watermark-opacity", default=None, type=float)
@click.option("--brand-name", default=None)
@click.pass_context
def preset_save(
    ctx: click.Context,
    name: str,
    theme: str | None,
    card_format: str | None,
    provider: str | None,
    scale: str | None,
    webp: bool | None,
    watermark_position: str | None,
    watermark_opacity: float | None,
    brand_name: str | None,
) -> None:
    """Save current options as a named preset.

    Example: imggen preset save weekly-ig --theme gradient --format story
    """
    config_path = _get_config_path_from_ctx(ctx)

    values: dict = {}
    if theme is not None:
        values["theme"] = theme
    if card_format is not None:
        values["format"] = card_format
    if provider is not None:
        values["provider"] = provider
    if scale is not None:
        values["scale"] = int(scale)
    if webp is not None:
        values["webp"] = webp
    if watermark_position is not None:
        values["watermark_position"] = watermark_position
    if watermark_opacity is not None:
        values["watermark_opacity"] = watermark_opacity
    if brand_name is not None:
        values["brand_name"] = brand_name

    save_preset(name, values, config_path=config_path)
    click.echo(f"Preset '{name}' saved with {len(values)} option(s).")


@preset_group.command(name="load")
@click.argument("name")
@click.pass_context
def preset_load(ctx: click.Context, name: str) -> None:
    """Show the saved preset values (printed as TOML key = value pairs)."""
    config_path = _get_config_path_from_ctx(ctx)

    values = load_preset(name, config_path=config_path)
    if not values:
        raise click.ClickException(f"Preset '{name}' not found.")

    click.echo(f"[preset.{name}]")
    for key, val in values.items():
        if isinstance(val, bool):
            click.echo(f"{key} = {'true' if val else 'false'}")
        elif isinstance(val, str):
            click.echo(f'{key} = "{val}"')
        else:
            click.echo(f"{key} = {val}")


@preset_group.command(name="list")
@click.pass_context
def preset_list(ctx: click.Context) -> None:
    """List all saved presets with key parameters."""
    config_path = _get_config_path_from_ctx(ctx)

    presets = list_presets(config_path=config_path)
    if not presets:
        click.echo("No presets saved.")
        return

    for preset_name, values in presets.items():
        summary_parts = [f"{k}={v}" for k, v in values.items()]
        summary = ", ".join(summary_parts)
        click.echo(f"  {preset_name}: {summary}")


@preset_group.command(name="delete")
@click.argument("name")
@click.pass_context
def preset_delete(ctx: click.Context, name: str) -> None:
    """Delete a saved preset."""
    config_path = _get_config_path_from_ctx(ctx)

    deleted = delete_preset(name, config_path=config_path)
    if deleted:
        click.echo(f"Preset '{name}' deleted.")
    else:
        click.echo(f"Preset '{name}' not found.", err=True)


# Register the preset subcommand group on main
main.add_command(preset_group, name="preset")


# ---------------------------------------------------------------------------
# history subcommand group
# ---------------------------------------------------------------------------


@click.group(name="history")
def history_group() -> None:
    """View and search generation history."""


@history_group.command(name="list")
@click.option("--days", default=None, type=int, help="Show only entries from the last N days.")
@click.option("--limit", default=20, type=int, show_default=True, help="Max entries to show.")
def history_list(days: int | None, limit: int) -> None:
    """List recent card generations."""
    from src.history import list_generations

    rows = list_generations(days=days, limit=limit)
    if not rows:
        click.echo("No generation history found.")
        return

    for r in rows:
        created = r["created_at"][:16]
        click.echo(
            f"  [{created}] {r['theme']}/{r['format']}  "
            f"{r['title']}"
        )


@history_group.command(name="search")
@click.argument("query")
@click.option("--limit", default=20, type=int, show_default=True)
def history_search(query: str, limit: int) -> None:
    """Search generation history by title or URL."""
    from src.history import search_generations

    rows = search_generations(query, limit=limit)
    if not rows:
        click.echo(f"No results for '{query}'.")
        return

    for r in rows:
        created = r["created_at"][:16]
        click.echo(
            f"  [{created}] {r['theme']}/{r['format']}  "
            f"{r['title']}"
        )


@history_group.command(name="stats")
@click.option("--days", default=None, type=int, help="Stats from the last N days only.")
@click.option("--visual", is_flag=True, default=False, help="Generate a visual stats card image.")
@click.option("--format", "card_format", default="story",
              type=click.Choice(["story", "square", "landscape", "twitter"], case_sensitive=False))
@click.option("--output", "-o", default=None, help="Output path for visual stats card.")
def history_stats(days: int | None, visual: bool, card_format: str, output: str | None) -> None:
    """Show generation statistics (optionally as a visual card)."""
    from src.history import get_stats

    stats = get_stats(days=days)

    if not visual:
        click.echo(f"  Total cards: {stats['total']}")
        click.echo(f"  Avg points:  {stats['avg_points']}")
        if stats["by_theme"]:
            click.echo("  By theme:")
            for item in stats["by_theme"]:
                click.echo(f"    {item['name']}: {item['count']}")
        if stats["by_provider"]:
            click.echo("  By provider:")
            for item in stats["by_provider"]:
                click.echo(f"    {item['name']}: {item['count']}")
        return

    # Visual mode: render stats as an image card
    from jinja2 import Environment, FileSystemLoader
    from src.screenshotter import take_screenshot

    total = stats["total"]

    def _add_pct(items: list[dict]) -> list[dict]:
        if not items or total == 0:
            return items
        return [{**item, "pct": round(item["count"] / total * 100)} for item in items]

    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    template = env.get_template("stats.html")

    html = template.render(
        total_cards=total,
        theme_distribution=_add_pct(stats["by_theme"]),
        provider_distribution=_add_pct(stats["by_provider"]),
        avg_points=stats["avg_points"],
        date_range=stats["date_range"],
        recent_titles=stats["recent_titles"],
        format=card_format,
    )

    out_path = Path(output) if output else (
        Path(__file__).parent / "output" / f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    final = take_screenshot(html, out_path, format=card_format, scale=2)
    click.echo(str(final))


main.add_command(history_group, name="history")


# ---------------------------------------------------------------------------
# watch subcommand
# ---------------------------------------------------------------------------


@main.command(name="watch")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--theme", default="dark",
              type=click.Choice(["dark", "light", "gradient", "warm_sun", "cozy"],
                                case_sensitive=False))
@click.option("--format", "card_format", default="story",
              type=click.Choice(["story", "square", "landscape", "twitter"],
                                case_sensitive=False))
@click.option("--provider", default="cli", help="AI provider for extraction.")
@click.option("--output-dir", default=None, type=click.Path(),
              help="Output directory (default: ./output/).")
def watch_command(
    directory: str,
    theme: str,
    card_format: str,
    provider: str,
    output_dir: str | None,
) -> None:
    """Watch a directory for new .txt/.md/.url files and auto-generate cards.

    Example: imggen watch ~/articles/ --theme dark --format story
    Press Ctrl+C to stop.
    """
    import logging

    from src.pipeline import PipelineOptions, run_pipeline
    from src.watcher import _read_file_content, watch_directory

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    out_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    opts = PipelineOptions(
        theme=theme,
        format=card_format,
        provider=provider,
    )

    def _on_file(path: Path) -> None:
        click.echo(f"\n  New file detected: {path.name}", err=True)
        try:
            content = _read_file_content(path)
        except Exception as e:
            click.echo(f"  Read failed: {e}", err=True)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = out_dir / f"card_{theme}_{timestamp}.png"
        try:
            data, final = run_pipeline(content, opts, out_path)
            click.echo(f"  Generated: {final}", err=True)

            # Record to history
            from src.history import record_generation
            record_generation(
                title=data["title"],
                theme=theme,
                format=card_format,
                provider=provider,
                output_path=str(final),
                file_size=final.stat().st_size,
                key_points_count=len(data["key_points"]),
                source=data.get("source"),
                mode="watch",
            )
        except Exception as e:
            click.echo(f"  Generation failed: {e}", err=True)

    click.echo(f"  Watching {directory} for .txt/.md/.url files...", err=True)
    click.echo("  Press Ctrl+C to stop.\n", err=True)
    watch_directory(Path(directory), _on_file)


# ---------------------------------------------------------------------------
# digest subcommand
# ---------------------------------------------------------------------------


@main.command(name="digest")
@click.option("--days", default=7, type=int, show_default=True,
              help="Number of days to include in the digest.")
@click.option("--theme", default="dark",
              type=click.Choice(["dark", "light", "gradient", "warm_sun", "cozy"],
                                case_sensitive=False))
@click.option("--format", "card_format", default="story",
              type=click.Choice(["story", "square", "landscape", "twitter"],
                                case_sensitive=False))
@click.option("--provider", default="cli", help="AI provider for digest synthesis.")
@click.option("--output", "-o", default=None, help="Output path for the digest card.")
def digest_command(
    days: int,
    theme: str,
    card_format: str,
    provider: str,
    output: str | None,
) -> None:
    """Synthesize recent articles into a weekly digest card.

    Requires generation history (from previous runs).
    Example: imggen digest --days 7 --theme gradient
    """
    from src.digest import generate_digest
    from src.history import list_generations
    from src.screenshotter import take_screenshot

    rows = list_generations(days=days, limit=50)
    if not rows:
        raise click.ClickException(
            f"No generation history in the last {days} days. "
            "Run some card generations first."
        )

    click.echo(f"Synthesizing digest from {len(rows)} article(s)...", err=True)

    digest_data = generate_digest(rows, days=days, provider=provider)

    # Render digest template
    from jinja2 import Environment, FileSystemLoader

    templates_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)), autoescape=True)
    template = env.get_template("digest.html")

    html = template.render(
        title=digest_data["title"],
        digest_points=digest_data["digest_points"],
        period=digest_data["period"],
        article_count=digest_data["article_count"],
        format=card_format,
    )

    out_path = Path(output) if output else (
        OUTPUT_DIR / f"digest_{theme}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    final = take_screenshot(html, out_path, format=card_format, scale=2)
    click.echo(str(final))


if __name__ == "__main__":
    main()
