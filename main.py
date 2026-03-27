"""
main.py - CLI entry point for imgGen

Article → Summary → Image Card pipeline.
Usage:
  python main.py --text "..."
  python main.py --file article.txt
  python main.py --url https://example.com/article --theme light
"""

import sys
from datetime import datetime
from pathlib import Path

import click
import httpx
from dotenv import load_dotenv

load_dotenv()

# Output directory relative to this file
OUTPUT_DIR = Path(__file__).parent / "output"


def _fetch_url_content(url: str) -> str:
    """Fetch text content from a URL."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = httpx.get(url, headers=headers, follow_redirects=True, timeout=30)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")
        if "html" in content_type:
            # Basic HTML stripping - remove tags
            import re
            text = response.text
            text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text
        else:
            return response.text

    except httpx.HTTPStatusError as e:
        raise click.ClickException(
            f"HTTP error fetching URL: {e.response.status_code} {e.response.reason_phrase}"
        ) from e
    except httpx.RequestError as e:
        raise click.ClickException(f"Network error fetching URL: {e}") from e


def _resolve_output_path(output: str | None, theme: str) -> Path:
    """Resolve the output file path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if output:
        path = Path(output)
        if not path.is_absolute():
            path = OUTPUT_DIR / path
        if not path.suffix:
            path = path.with_suffix(".png")
        return path
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return OUTPUT_DIR / f"card_{theme}_{timestamp}.png"


@click.command()
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
    default="dark",
    type=click.Choice(["dark", "light", "gradient"], case_sensitive=False),
    show_default=True,
    help="Visual theme for the image card.",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output filename (default: auto-generated timestamp in output/).",
)
def main(
    text: str | None,
    file: str | None,
    url: str | None,
    theme: str,
    output: str | None,
) -> None:
    """
    imgGen - Transform articles into beautiful image cards.

    Provide article content via --text, --file, or --url.
    """
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

    # --- Step 1: Extract key points ---
    click.echo("\n[1/3] Extracting key points with Claude API...", err=True)
    try:
        from src.extractor import extract_key_points
        data = extract_key_points(article_text)
    except EnvironmentError as e:
        raise click.ClickException(str(e)) from e
    except ValueError as e:
        raise click.ClickException(f"Extraction failed: {e}") from e
    except Exception as e:
        raise click.ClickException(f"Claude API error: {e}") from e

    click.echo(f"      Title: {data['title']}", err=True)
    click.echo(f"      Points: {len(data['key_points'])}", err=True)
    click.echo(f"      Suggested theme: {data['theme_suggestion']}", err=True)

    # Use AI-suggested theme only if user didn't explicitly set one
    # (Click default is "dark", so we always use what was passed)
    effective_theme = theme.lower()

    # --- Step 2: Render HTML ---
    click.echo(f"\n[2/3] Rendering HTML card (theme: {effective_theme})...", err=True)
    try:
        from src.renderer import render_card
        html_content = render_card(data, effective_theme)
    except Exception as e:
        raise click.ClickException(f"Rendering failed: {e}") from e

    click.echo(f"      HTML generated: {len(html_content)} bytes", err=True)

    # --- Step 3: Screenshot ---
    output_path = _resolve_output_path(output, effective_theme)
    click.echo(f"\n[3/3] Capturing screenshot → {output_path}", err=True)

    try:
        from src.screenshotter import take_screenshot
        final_path = take_screenshot(html_content, output_path)
    except RuntimeError as e:
        raise click.ClickException(str(e)) from e
    except Exception as e:
        raise click.ClickException(f"Screenshot failed: {e}") from e

    # --- Done ---
    file_size_kb = final_path.stat().st_size / 1024
    click.echo(
        f"\n  Done! Image saved to:\n  {final_path}\n"
        f"  Size: {file_size_kb:.1f} KB\n",
        err=True,
    )
    # Print path to stdout so it can be captured by scripts
    click.echo(str(final_path))


if __name__ == "__main__":
    main()
