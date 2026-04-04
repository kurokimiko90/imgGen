"""
batch.py - Batch processing module for imgGen v2.0.

Provides async batch processing of multiple article inputs (URLs or file paths).
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any

from src.pipeline import PipelineOptions, render_and_capture, extract


def parse_batch_file(path: Path) -> list[str]:
    """Read batch file, skip blank lines and # comments, return list of entries.

    Args:
        path: Path to the plain-text batch file.

    Returns:
        List of non-blank, non-comment entry strings with whitespace stripped.
    """
    text = path.read_text(encoding="utf-8")
    entries = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        entries.append(stripped)
    return entries


def _fetch_url_content(url: str) -> str:
    """Fetch text content from a URL. Delegates to src.fetcher."""
    from src.fetcher import fetch_url_content
    return fetch_url_content(url)


def _process_text(
    entry: str,
    index: int,
    options: dict[str, Any],
    output_dir: Path,
) -> Path:
    """Run the single-entry pipeline for one batch entry.

    Resolves text from URL or file path, then runs:
    extract_key_points -> render_card -> take_screenshot.

    Args:
        entry: URL or file path string.
        index: 1-based entry index (used in output filename).
        options: Processing options (theme, format, provider, etc.).
        output_dir: Directory to write the output image.

    Returns:
        Path to the generated image file.
    """
    # Resolve article text
    if entry.startswith("http://") or entry.startswith("https://"):
        article_text = _fetch_url_content(entry)
    else:
        article_path = Path(entry)
        article_text = article_path.read_text(encoding="utf-8").strip()

    # Step 1: Extract key points
    data = extract(article_text, provider=options["provider"])

    # Step 2+3: Render + Screenshot
    theme = options["theme"]
    fmt = options["format"]
    ext = ".webp" if options.get("webp") else ".png"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"card_{theme}_{timestamp}_{fmt}_{index:03d}{ext}"

    pipe_opts = PipelineOptions(
        theme=theme,
        format=fmt,
        scale=options.get("scale", 2),
        webp=options.get("webp", False),
        watermark_data=options.get("watermark_data"),
        watermark_position=options.get("watermark_position", "bottom-right"),
        watermark_opacity=options.get("watermark_opacity", 0.8),
        brand_name=options.get("brand_name"),
    )

    return render_and_capture(data, pipe_opts, output_path)


async def process_entry(
    entry: str,
    index: int,
    options: dict[str, Any],
    output_dir: Path,
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    """Process a single batch entry within the semaphore.

    Args:
        entry: URL or file path string.
        index: 1-based entry index.
        options: Processing options dict.
        output_dir: Directory for output images.
        semaphore: Semaphore controlling max concurrency.

    Returns:
        Result dict with keys: index, input, status, and either output or error.
    """
    async with semaphore:
        loop = asyncio.get_running_loop()
        try:
            final_path = await loop.run_in_executor(
                None, _process_text, entry, index, options, output_dir
            )
            return {
                "index": index,
                "input": entry,
                "status": "ok",
                "output": str(final_path),
            }
        except Exception as e:  # noqa: BLE001
            return {
                "index": index,
                "input": entry,
                "status": "error",
                "error": str(e),
            }


async def run_batch(
    entries: list[str],
    options: dict[str, Any],
    output_dir: Path,
    workers: int = 3,
) -> list[dict[str, Any]]:
    """Run all entries concurrently with Semaphore(workers).

    Args:
        entries: List of URL or file path strings to process.
        options: Processing options dict shared across all entries.
        output_dir: Directory for output images.
        workers: Maximum concurrent entries to process.

    Returns:
        List of result dicts sorted by index, one per entry.
    """
    if not entries:
        return []

    semaphore = asyncio.Semaphore(workers)
    tasks = [
        process_entry(entry, index + 1, options, output_dir, semaphore)
        for index, entry in enumerate(entries)
    ]
    results = await asyncio.gather(*tasks)
    return sorted(results, key=lambda r: r["index"])
